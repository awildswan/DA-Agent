"""SQL 只读守卫（⑥执行安全）：禁词词边界匹配，宁误拦不漏放。"""

import re

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


def _guard(sql: str) -> None:
    """先抹字符串字面量，再词边界匹配禁词（is_deleted 列名不误伤）。"""
    stripped = re.sub(r"'(?:[^']|'')*'", "''", sql)
    for kw in _FORBIDDEN:
        if re.search(rf"\b{kw}\b", stripped, re.IGNORECASE):
            raise ValueError(f"只读守卫拦截：SQL 含禁词 {kw}")
