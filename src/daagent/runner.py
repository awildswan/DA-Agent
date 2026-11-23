"""agent runner：最小闭环 + 交付闸门（值域/关系/核对真值）+ 自纠环。

链路：⑤生成 SQL → ⑥执行 → ⑨交付（自然语言结论）→ ⑦交付闸门 → ⑧自纠（≤2 轮）。
"""

import re

from langchain_openai import ChatOpenAI

from daagent.config import get_settings
from daagent.db.sample import sample_db, schema_str
from daagent.delivery_check.declarations import DEFAULT_DECLARATIONS
from daagent.delivery_check.guards import RedFlag, run_guards, truth_check

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
    "你是数据分析助手。根据给定数据库 schema，把用户的大白话问题转成一条只读 SQL（仅 SELECT）。"
    "只输出 SQL，不要解释，不要 markdown 围栏。"
)

_CONCLUDE_SYSTEM = (
    "你是数据分析助手。根据查询结果，用一句自然语言回答用户问题。"
    "规则：① 首句直接给出数字；② 区域等实体名称必须用查询结果里的标准值，不要自己造；"
    "③ 数字必须来自查询结果，查不到就写「未知」。"
)

_CORRECT_SYSTEM = (
    "你上一版结论被交付闸门拦下，请修正。"
    "规则：① 每个数字必须来自下方查询结果或直查真值，查不到就写「未知」；"
    "② 实体名称必须用标准值，不要自己造；③ 只输出修正后的结论。"
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


def _generate_sql(llm, question: str) -> str:
    resp = llm.invoke(
        [("system", _SQL_SYSTEM), ("human", f"数据库 schema：\n{schema_str()}\n\n问题：{question}")]
    )
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

    sql = _generate_sql(llm, question)
    _guard(sql)
    con.execute(sql)
    rows = con.fetchall()
    result = _format_result(con, rows)

    # 核对 SQL 真值（直查，进修正指令做接地）
    truths = []
    for t in DEFAULT_DECLARATIONS.truth_checks:
        con.execute(t.sql)
        truths.append((t.label, float(con.fetchone()[0] or 0), t.tolerance))

    def check(conclusion: str) -> list[RedFlag]:
        reds = run_guards(conclusion, DEFAULT_DECLARATIONS)
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

    if reds:
        tail = "⚠️ 自纠后仍有 " + "；".join(r.message for r in reds) + "（请人工复核）"
    else:
        tail = ""

    return f"{conclusion}\n{tail}\n来源：orders 表（SQL：{sql}）".strip()
