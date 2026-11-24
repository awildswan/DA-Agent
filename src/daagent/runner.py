"""agent runner：最小闭环 + 交付闸门 + 自纠环 + 越用越懂（①召回 ②语义映射 ⑪沉淀）。

链路：①召回 OKF 口径 → ⑤生成 SQL → ⑥执行 → ⑨交付 → ⑦闸门 → ⑧自纠 → ⑪沉淀。
沉淀用结构化 JSON（让 LLM 输出 JSON，而非解析自由文本）。
"""

import json
import re
from pathlib import Path

from langchain_openai import ChatOpenAI

from daagent.config import get_settings
from daagent.db.sample import sample_db, schema_str
from daagent.delivery_check.declarations import DEFAULT_GUARDS_CONTENT, build_declarations
from daagent.delivery_check.guards import RedFlag, run_guards, truth_check
from daagent.okf.store import OkfStore

# 只读禁词（词边界匹配，宁误拦不漏放）
_FORBIDDEN = (
    "DROP",
    "DELETE",
    "UPDATE",
    "ALTER",
    "INSERT",
    "TRUNCATE",
    "CREATE",
    "ATTACH",
    "DETACH",
)

_SQL_SYSTEM = (
    "你是数据分析助手。根据给定数据库 schema 和已知业务口径，把用户的大白话问题转成一条只读 SQL（仅 SELECT）。"
    "如果已知业务口径里有相关定义，沿用它的口径。只输出 SQL，不要解释，不要 markdown 围栏。"
)

_CONCLUDE_SYSTEM = (
    "你是数据分析助手。根据查询结果，用一句自然语言回答用户问题。"
    "规则：① 首句直接给出数字；② 如果问题含业务概念（如'有效订单'），先说明采用的口径再给数字；"
    "③ 区域等实体名称用查询结果里的标准值；④ 数字必须来自查询结果，查不到写「未知」。"
)

_CORRECT_SYSTEM = (
    "你上一版结论被交付闸门拦下，请修正。"
    "规则：① 每个数字必须来自下方查询结果或直查真值，查不到写「未知」；"
    "② 实体名称必须用标准值；③ 只输出修正后的结论。"
)

_CONCEPT_SYSTEM = (
    "你在一次取数中使用了一个业务概念。"
    "用一句话记录它的取数口径（必须来自本次 SQL 的真实过滤条件，不要空泛）。"
    "输出 JSON：{\"concept\": \"概念名\", \"definition\": \"口径\"}。"
    "例如：concept=\"有效订单\", definition=\"status='paid'（已支付）\"。"
    "没有业务概念则 {\"concept\": null}。只输出 JSON，不要 markdown 围栏。"
)


def _extract_sql(text: str) -> str:
    text = text.strip()
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
    return text.strip().rstrip(";").strip()


def _guard(sql: str) -> None:
    stripped = re.sub(r"'(?:[^']|'')*'", "''", sql)
    for kw in _FORBIDDEN:
        if re.search(rf"\b{kw}\b", stripped, re.IGNORECASE):
            raise ValueError(f"只读守卫拦截：SQL 含禁词 {kw}")


def _format_result(con, rows) -> str:
    cols = [d[0] for d in con.description]
    return "\n".join(", ".join(f"{c}={v}" for c, v in zip(cols, r)) for r in rows)


def _recall_concepts(okf: OkfStore) -> str:
    """① 召回：读 OKF concepts，返回「已知业务口径」文本（无则空串）。"""
    concepts = [
        okf.read(cat, name)
        for cat, name in okf.list_blocks()
        if cat == "concepts"
    ]
    concepts = [c for c in concepts if c]
    if not concepts:
        return ""
    return "已知业务口径（之前确认过的，请沿用）：\n" + "\n".join(f"- {c}" for c in concepts)


def _parse_concept_json(text: str) -> dict | None:
    """解析 LLM 输出的概念 JSON（剥掉 ```json 围栏）。结构化，不用正则抽字段。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and data.get("concept"):
        return {"concept": data["concept"], "definition": data.get("definition", "")}
    return None


def _generate_sql(llm, question: str, concepts_text: str) -> str:
    human = f"数据库 schema：\n{schema_str()}\n\n{concepts_text}\n\n问题：{question}"
    resp = llm.invoke([("system", _SQL_SYSTEM), ("human", human)])
    return _extract_sql(resp.content)


def _conclude(llm, question: str, result: str) -> str:
    resp = llm.invoke(
        [("system", _CONCLUDE_SYSTEM), ("human", f"问题：{question}\n查询结果：\n{result}")]
    )
    return resp.content.strip()


def _correct(llm, question: str, result: str, reds: list[RedFlag], truths) -> str:
    red_text = "\n".join(f"- {r.message}" for r in reds)
    truth_text = "\n".join(f"- {label} 直查真值 = {tv:g}" for label, tv, _ in truths)
    resp = llm.invoke(
        [
            ("system", _CORRECT_SYSTEM),
            (
                "human",
                f"问题：{question}\n查询结果：\n{result}\n\n直查真值：\n{truth_text}\n\n"
                f"闸门拦下的问题：\n{red_text}",
            ),
        ]
    )
    return resp.content.strip()


def _extract_concept(llm, question: str, conclusion: str, sql: str) -> dict | None:
    """⑪ 沉淀：让 LLM 判断是否用了业务概念，结构化输出 JSON；definition 接地到本次 SQL。"""
    resp = llm.invoke(
        [
            ("system", _CONCEPT_SYSTEM),
            ("human", f"问题：{question}\n结论：{conclusion}\n本次 SQL：{sql}"),
        ]
    )
    return _parse_concept_json(resp.content)


_VAGUE = ("未展开", "具体定义", "未给出", "该口径")


def _valid_concept(concept: str, definition: str) -> bool:
    """写入守卫：拒写空定义 / 自指（同义反复）/ 空泛定义（对齐 daw 的写入守卫）。"""
    if not concept or not definition:
        return False
    if concept in definition:
        return False
    return not any(v in definition for v in _VAGUE)


def _deliver(conclude, correct, check, question, result, max_rounds: int = 2):
    """⑦ 交付闸门 → ⑧ 自纠环（≤ max_rounds 轮），conclude/correct/check 可注入（便于测试）。"""
    conclusion = conclude(question, result)
    reds = check(conclusion)
    for _ in range(max_rounds):
        if not reds:
            break
        conclusion = correct(question, result, reds)
        reds = check(conclusion)
    return conclusion, reds


def run(question: str) -> str:
    s = get_settings()
    llm = ChatOpenAI(
        model=s.deepseek_model,
        api_key=s.openai_api_key,
        base_url=s.openai_api_base,
        temperature=0,
    )
    con = sample_db()

    # 守卫声明从 OKF 加载（首次运行自动播种）
    okf = OkfStore(Path("data/okf"))
    if okf.read("guards", "orders") is None:
        okf.write("guards", "orders", DEFAULT_GUARDS_CONTENT)
    declarations = build_declarations(okf, con)

    # ① 召回：把已确认的业务口径注入生成 SQL 的上下文
    concepts_text = _recall_concepts(okf)

    sql = _generate_sql(llm, question, concepts_text)
    _guard(sql)
    con.execute(sql)
    rows = con.fetchall()
    result = _format_result(con, rows)

    # 核对 SQL 真值（直查，进修正指令做接地）
    truths = []
    for t in declarations.truth_checks:
        con.execute(t.sql)
        truths.append((t.label, float(con.fetchone()[0] or 0), t.tolerance))

    def check(conclusion: str) -> list[RedFlag]:
        reds = run_guards(conclusion, declarations)
        for label, tv, tol in truths:
            f = truth_check(conclusion, label, tv, tol)
            if f:
                reds.append(f)
        return reds

    conclusion, reds = _deliver(
        lambda q, r: _conclude(llm, q, r),
        lambda q, r, fl: _correct(llm, q, r, fl, truths),
        check,
        question,
        result,
    )

    # ⑪ 沉淀：用了业务口径 → 结构化 JSON → 写回 OKF（干净交付 + 定义有效才沉淀）
    if not reds:
        concept = _extract_concept(llm, question, conclusion, sql)
        if concept and _valid_concept(concept["concept"], concept["definition"]):
            okf.write(
                "concepts",
                concept["concept"],
                f"{concept['concept']} = {concept['definition']}",
            )

    if reds:
        tail = "⚠️ 自纠后仍有 " + "；".join(r.message for r in reds) + "（请人工复核）"
    else:
        tail = ""

    return f"{conclusion}\n{tail}\n来源：orders 表（SQL：{sql}）".strip()
