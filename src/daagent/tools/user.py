"""用户交互工具：澄清反问。"""

from langchain_core.tools import tool


def make():
    @tool
    def ask_user(question: str) -> str:
        """业务口径或需求有歧义时，反问用户确认，返回用户的回答。"""
        return input(f"（需要你确认）{question}\n你: ")

    return [ask_user]
