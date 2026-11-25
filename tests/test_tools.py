"""工具注册表 单测。"""

from daagent.db.sample import sample_db
from daagent.okf.store import OkfStore
from daagent.tools import build_tools


def test_build_tools_non_interactive(tmp_path):
    okf = OkfStore(tmp_path / "okf", git=False)
    con = sample_db()
    tools, by_name = build_tools(okf, con, interactive=False)
    names = {t.name for t in tools}
    assert names == {"search_knowledge", "record_concept", "list_tables", "describe_table", "execute_query"}
    assert set(by_name) == names


def test_build_tools_interactive_adds_ask_user(tmp_path):
    okf = OkfStore(tmp_path / "okf", git=False)
    con = sample_db()
    tools, _ = build_tools(okf, con, interactive=True)
    assert "ask_user" in {t.name for t in tools}
