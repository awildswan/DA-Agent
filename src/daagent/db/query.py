"""查询结果格式化。"""


def _format_result(con, rows) -> str:
    cols = [d[0] for d in con.description]
    return "\n".join(", ".join(f"{c}={v}" for c, v in zip(cols, r)) for r in rows)
