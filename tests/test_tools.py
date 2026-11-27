"""工具注册表 单测。"""

from daagent.db.datasource import sample_source
from daagent.okf.store import OkfStore
from daagent.tools import build_tools


def test_build_tools_non_interactive(tmp_path):
    okf = OkfStore(tmp_path / "okf", git=False)
    ds = sample_source()
    tools, by_name = build_tools(okf, ds, interactive=False)
    names = {t.name for t in tools}
    assert names == {
        "search_knowledge",
        "record_concept",
        "list_tables",
        "describe_table",
        "sample_data",
        "list_connections",
        "execute_query",
    }
    assert set(by_name) == names


def test_build_tools_interactive_adds_ask_user(tmp_path):
    okf = OkfStore(tmp_path / "okf", git=False)
    ds = sample_source()
    tools, _ = build_tools(okf, ds, interactive=True)
    assert "ask_user" in {t.name for t in tools}
