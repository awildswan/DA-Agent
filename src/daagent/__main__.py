"""入口：`python -m daagent`（smoke）或 `python -m daagent ask "问题"`（V0.1 最小闭环）。"""

import sys

import duckdb
import langchain_core  # noqa: F401
import sqlglot

from daagent.config import get_settings


def smoke() -> None:
    s = get_settings()
    print(
        f"[config] model={s.deepseek_model} base={s.openai_api_base} "
        f"row_limit={s.query_row_limit}"
    )
    sql = "SELECT region, COUNT(*) FROM dw_order WHERE status = 'paid' GROUP BY region"
    print(f"[sqlglot] parsed: {type(sqlglot.parse_one(sql)).__name__}")
    con = duckdb.connect()
    con.execute("CREATE TABLE t(region VARCHAR, n INT)")
    con.execute("INSERT INTO t VALUES ('华东', 10), ('华南', 20)")
    rows = con.execute(
        "SELECT region, SUM(n) FROM t GROUP BY region ORDER BY region"
    ).fetchall()
    print(f"[duckdb] {rows}")
    print("SMOKE OK")


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "chat":
        from daagent.agent.runner import chat

        chat()
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "eval":
        from daagent.evals.cases import CASES, SQL_CASES
        from daagent.evals.run import print_report, run_eval

        print("=== L1 业务口径集 ===")
        print_report(run_eval(CASES), "L1")
        print("\n=== L2 SQL 准确率 ===")
        print_report(run_eval(SQL_CASES), "L2")
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "ask":
        from daagent.agent.runner import run

        q = " ".join(sys.argv[2:])
        if not q:
            print('用法: python -m daagent ask "问题"')
            return
        print(run(q))
    else:
        smoke()


if __name__ == "__main__":
    main()
