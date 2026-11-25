"""知识工具：OKF 口径召回 + 沉淀。"""

from langchain_core.tools import tool

from daagent.okf.recall import _recall_concepts, _valid_concept


def make(okf):
    @tool
    def search_knowledge(query: str) -> str:
        """搜索已确认的业务口径。"""
        return _recall_concepts(okf) or "（知识库暂无已确认口径）"

    @tool
    def record_concept(name: str, definition: str) -> str:
        """记录一个业务口径（概念 = 取数定义）。"""
        if not _valid_concept(name, definition):
            return "未记录（定义无效：空/自指/空泛）"
        okf.write("concepts", name, f"{name} = {definition}")
        return f"已记录：{name} = {definition}"

    return [search_knowledge, record_concept]
