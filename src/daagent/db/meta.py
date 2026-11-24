"""元数据辅助：从数据 DISTINCT 取候选全集（V0.4；SQLite table_registry 留 V0.5 接④穷尽探查）。"""

import duckdb


def distinct_values(con: duckdb.DuckDBPyConnection, table: str, column: str) -> list[str]:
    rows = con.execute(f"SELECT DISTINCT {column} FROM {table} ORDER BY {column}").fetchall()
    return [r[0] for r in rows]
