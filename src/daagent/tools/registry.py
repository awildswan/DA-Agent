"""工具注册表：声明可用工具，插拔式（加/减工具只改这里，不动 runner）。"""

from daagent.tools import database, knowledge, user


def build_tools(okf, ds, interactive: bool = False):
    """构建工具集。interactive=True 加 ask_user（澄清）。"""
    tools = []
    tools += knowledge.make(okf)
    tools += database.make(ds)
    if interactive:
        tools += user.make()
    return tools, {t.name: t for t in tools}
