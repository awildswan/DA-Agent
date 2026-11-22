"""最小 smoke：验证环境跑得通（config / sqlglot / duckdb / langchain），不调 LLM。

用法：`python -m daagent`，打印 SMOKE OK 即环境就绪。
"""

import duckdb
import langchain_core  # noqa: F401  确保可导入
import sqlglot

from daagent.config import get_settings


def main() -> None:
    s = get_settings()
    print(
        f"[config] model={s.deepseek_model} base={s.openai_api_base} "
        f"row_limit={s.query_row_limit}"
    )

    # sqlglot：解析 + 结构校验
    sql = "SELECT region, COUNT(*) FROM dw_order WHERE status = 'paid' GROUP BY region"
    parsed = sqlglot.parse_one(sql)
    print(f"[sqlglot] parsed: {type(parsed).__name__}")

    # duckdb：内存执行
    con = duckdb.connect()
    con.execute("CREATE TABLE t(region VARCHAR, n INT)")
    con.execute("INSERT INTO t VALUES ('华东', 10), ('华南', 20)")
    rows = con.execute(
        "SELECT region, SUM(n) FROM t GROUP BY region ORDER BY region"
    ).fetchall()
    print(f"[duckdb] {rows}")

    print("SMOKE OK")


if __name__ == "__main__":
    main()
