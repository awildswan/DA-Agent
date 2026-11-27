"""数据库工具：列清单 / 看结构 / 看样例 / 执行 SQL。"""

from langchain_core.tools import tool

from daagent.db.query import _format_result
from daagent.skills.sql import _guard


def make(ds):
    @tool
    def list_tables() -> str:
        """列出可用表。"""
        return "、".join(ds.list_tables())

    @tool
    def describe_table(table: str) -> str:
        """返回指定表的 schema。"""
        return ds.describe_table(table)

    @tool
    def sample_data(table: str, limit: int = 5) -> str:
        """看表的前 N 行样例（确认字段取值）。"""
        return ds.sample_data(table, limit)

    @tool
    def list_connections() -> str:
        """列出当前数据源与表（表登记）。"""
        from daagent.db.registry import TableRegistry

        return TableRegistry(ds).summary()

    @tool
    def execute_query(sql: str) -> str:
        """执行一条只读 SQL，返回结果行。"""
        _guard(sql)
        ds.con.execute(sql)
        return _format_result(ds.con, ds.con.fetchall())

    return [list_tables, describe_table, sample_data, list_connections, execute_query]
