"""数据库工具：列清单 / 看结构 / 执行 SQL。"""

from langchain_core.tools import tool

from daagent.db.query import _format_result
from daagent.db.sample import list_tables as db_list_tables, schema_for_table
from daagent.skills.sql import _guard


def make(con):
    @tool
    def list_tables() -> str:
        """列出可用表。"""
        return "、".join(db_list_tables())

    @tool
    def describe_table(table: str) -> str:
        """返回指定表的 schema。"""
        return schema_for_table(table)

    @tool
    def execute_query(sql: str) -> str:
        """执行一条只读 SQL，返回结果行。"""
        _guard(sql)
        con.execute(sql)
        return _format_result(con, con.fetchall())

    return [list_tables, describe_table, execute_query]
