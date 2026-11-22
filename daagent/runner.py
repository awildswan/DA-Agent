"""agent runner：V0.1 最小闭环（⑤生成 SQL → ⑥执行 → ⑨交付）。

环节见 docs/02-design/MODULE_DESIGN.md。V0.1 只做单跳取数，不接闸门 / 知识库 / 探查。
"""

import re

from langchain_openai import ChatOpenAI

from daagent.config import get_settings
from daagent.db.sample import sample_db, schema_str

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
    """从 LLM 输出里取 SQL：剥掉 ```sql 围栏与行尾分号。"""
    text = text.strip()
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
    return text.strip().rstrip(";").strip()


def _guard(sql: str) -> None:
    """只读守卫：先抹字符串字面量，再词边界匹配禁词。"""
    stripped = re.sub(r"'(?:[^']|'')*'", "''", sql)
    for kw in _FORBIDDEN:
        if re.search(rf"\b{kw}\b", stripped, re.IGNORECASE):
            raise ValueError(f"只读守卫拦截：SQL 含禁词 {kw}")


def _format(con, rows) -> str:
    cols = [d[0] for d in con.description]
    if len(rows) == 1 and len(cols) == 1:
        return str(rows[0][0])
    return "; ".join(str(dict(zip(cols, r))) for r in rows)


def run(question: str) -> str:
    s = get_settings()
    llm = ChatOpenAI(
        model=s.deepseek_model,
        api_key=s.openai_api_key,
        base_url=s.openai_api_base,
        temperature=0,
    )
    con = sample_db()
    schema = schema_str()

    system = (
        "你是数据分析助手。根据给定数据库 schema，把用户的大白话问题转成一条只读 SQL（仅 SELECT）。"
        "只输出 SQL，不要解释，不要 markdown 围栏。"
    )
    resp = llm.invoke(
        [("system", system), ("human", f"数据库 schema：\n{schema}\n\n问题：{question}")]
    )
    sql = _extract_sql(resp.content)
    _guard(sql)

    con.execute(sql)
    rows = con.fetchall()
    result = _format(con, rows)

    return f"{result}\n来源：orders 表（SQL：{sql}）"
