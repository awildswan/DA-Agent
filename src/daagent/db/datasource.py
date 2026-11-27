"""数据源抽象：连接管理 + schema 探查 + 执行（解绑单数据集）。

- sample_source()：V1 三表示例库（orders / products / order_items）。
- tpch_source()：TPC-H 8 表星型（从 data/tpch/*.parquet 建视图，不占内存）。
- get_datasource()：按环境变量 DAAGENT_DATASOURCE=sample|tpch 选择（默认 sample）。
"""

import os
from pathlib import Path

import duckdb

TPCH_TABLES = ["customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"]


class DataSource:
    def __init__(self, con, name: str = "default"):
        self.con = con
        self.name = name
        try:
            self.con.execute("SET TimeZone='UTC'")
        except Exception:  # noqa: BLE001
            pass

    def list_tables(self) -> list[str]:
        try:
            return [r[0] for r in self.con.execute("SHOW TABLES").fetchall()]
        except Exception:  # noqa: BLE001
            return []

    def describe_table(self, table: str) -> str:
        try:
            rows = self.con.execute(f"DESCRIBE {table}").fetchall()
        except Exception:  # noqa: BLE001
            return f"未知表 {table}（可用表：{self.list_tables()}）"
        return "\n".join(f"- {r[0]} {r[1]}" for r in rows)

    def sample_data(self, table: str, limit: int = 5) -> str:
        try:
            cur = self.con.execute(f"SELECT * FROM {table} LIMIT {limit}")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        except Exception as e:  # noqa: BLE001
            return f"取样失败：{e}"
        lines = [" | ".join(cols)]
        for r in rows:
            lines.append(" | ".join(str(x) for x in r))
        return "\n".join(lines)


def sample_source() -> DataSource:
    from daagent.db.sample import sample_db

    return DataSource(sample_db(), name="sample")


def tpch_source() -> DataSource:
    con = duckdb.connect()
    for t in TPCH_TABLES:
        p = Path(f"data/tpch/{t}.parquet")
        if p.exists():
            con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{p.as_posix()}')")
    return DataSource(con, name="tpch")


def get_datasource() -> DataSource:
    """按环境变量选数据源：DAAGENT_DATASOURCE=sample|tpch（默认 sample）。"""
    if os.environ.get("DAAGENT_DATASOURCE", "sample").lower() == "tpch":
        return tpch_source()
    return sample_source()
