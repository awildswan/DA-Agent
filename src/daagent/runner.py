"""agent runner：最小闭环 + 交付闸门 + 自纠环 + 越用越懂（①召回 ②语义映射 ⑪沉淀）。

链路：①召回 OKF 口径 → ⑤生成 SQL → ⑥执行 → ⑨交付（结构化 JSON 结论）→ ⑦闸门 → ⑧自纠 → ⑪沉淀。
结论用结构化 JSON（answer/numbers/entities），守卫查结构，不解析自由文本。
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
from daagent.prompts import load_prompt

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


def _parse_json(text: str) -> dict | None:
    """解析 LLM 输出的 JSON（剥掉 ```json 围栏）。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _parse_conclusion_json(text: str) -> dict:
    """解析结构化结论，失败时给兜底（不 crash）。"""
    data = _parse_json(text)
    if not isinstance(data, dict) or not data.get("answer"):
        return {"answer": "（结论解析失败）", "numbers": {}, "entities": []}
    return {
        "answer": str(data["answer"]),
        "numbers": data.get("numbers") or {},
        "entities": data.get("entities") or [],
    }


def _parse_concept_json(text: str) -> dict | None:
    data = _parse_json(text)
    if isinstance(data, dict) and data.get("concept"):
        return {"concept": data["concept"], "definition": data.get("definition", "")}
    return None


_VAGUE = ("未展开", "具体定义", "未给出", "该口径")


def _valid_concept(concept: str, definition: str) -> bool:
    """写入守卫：拒写空定义 / 自指（同义反复）/ 空泛定义。"""
    if not concept or not definition:
        return False
    if concept in definition:
        return False
    return not any(v in definition for v in _VAGUE)


def _generate_sql(llm, question: str, concepts_text: str) -> str:
    human = f"数据库 schema：\n{schema_str()}\n\n{concepts_text}\n\n问题：{question}"
    resp = llm.invoke([("system", load_prompt("sql")), ("human", human)])
    return _extract_sql(resp.content)


def _conclude(llm, question: str, result: str, sql: str) -> dict:
    """⑨ 交付：结构化结论（answer/numbers/entities），接地到本次 SQL + 结果。"""
    resp = llm.invoke(
        [
            ("system", load_prompt("conclude")),
            ("human", f"问题：{question}\n本次 SQL：{sql}\n查询结果：\n{result}"),
        ]
    )
    return _parse_conclusion_json(resp.content)


def _correct(llm, question: str, result: str, reds: list[RedFlag], truths) -> dict:
    red_text = "\n".join(f"- {r.message}" for r in reds)
    truth_text = "\n".join(f"- {label} 直查真值 = {tv:g}" for label, tv, _ in truths)
    resp = llm.invoke(
        [
            ("system", load_prompt("correct")),
            (
                "human",
                f"问题：{question}\n查询结果：\n{result}\n直查真值：\n{truth_text}\n\n"
                f"闸门拦下的问题：\n{red_text}",
            ),
        ]
    )
    return _parse_conclusion_json(resp.content)


def _extract_concept(llm, question: str, conclusion: str, sql: str) -> dict | None:
    """⑪ 沉淀：让 LLM 判断是否用了业务概念，结构化输出 JSON；definition 接地到本次 SQL。"""
    resp = llm.invoke(
        [
            ("system", load_prompt("concept")),
            ("human", f"问题：{question}\n结论：{conclusion}\n本次 SQL：{sql}"),
        ]
    )
    return _parse_concept_json(resp.content)


def _deliver(conclude, correct, check, question, result, max_rounds: int = 2):
    """⑦ 交付闸门 → ⑧ 自纠环（≤ max_rounds 轮），conclude/correct/check 可注入（便于测试）。"""
    structured = conclude(question, result)
    reds = check(structured)
    for _ in range(max_rounds):
        if not reds:
            break
        structured = correct(question, result, reds)
        reds = check(structured)
    return structured, reds


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

    def check(structured: dict) -> list[RedFlag]:
        reds = run_guards(structured, declarations)
        numbers = structured.get("numbers", {}) or {}
        for label, tv, tol in truths:
            f = truth_check(numbers, label, tv, tol)
            if f:
                reds.append(f)
        return reds

    structured, reds = _deliver(
        lambda q, r: _conclude(llm, q, r, sql),
        lambda q, r, fl: _correct(llm, q, r, fl, truths),
        check,
        question,
        result,
    )

    answer = structured.get("answer", "（结论解析失败）")

    # ⑪ 沉淀：用了业务口径 → 结构化 JSON → 写回 OKF（干净交付 + 定义有效才沉淀）
    if not reds:
        concept = _extract_concept(llm, question, answer, sql)
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

    return f"{answer}\n{tail}\n来源：orders 表（SQL：{sql}）".strip()
