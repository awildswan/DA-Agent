"""环境 smoke：config 加载 + sqlglot 解析 + duckdb 执行 + langchain 可导入。"""

import duckdb
import langchain_core  # noqa: F401
import sqlglot

from daagent.config import Settings


def test_config_defaults():
    s = Settings(_env_file=None)  # 不读 .env，用默认值
    assert s.deepseek_model == "deepseek-flash"
    assert s.query_row_limit == 200


def test_sqlglot_parse():
    parsed = sqlglot.parse_one("SELECT a FROM t WHERE x = 1")
    assert parsed is not None


def test_duckdb_execute():
    con = duckdb.connect()
    con.execute("CREATE TABLE t(x INT)")
    con.execute("INSERT INTO t VALUES (1), (2)")
    assert con.execute("SELECT SUM(x) FROM t").fetchone()[0] == 3
