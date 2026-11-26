"""会话持久化 + 上下文压缩 离线单测。"""

from daagent.agent.compact import compact
from daagent.db.chat import ChatStore


def test_chat_store_roundtrip(tmp_path):
    s = ChatStore(str(tmp_path / "chat.db"))
    s.save("s1", "user", "华东有多少订单")
    s.save("s1", "agent", "3 单", trace=[{"type": "tool_call", "name": "execute_query", "args": {}}])
    rows = s.load("s1")
    assert rows[0] == ("user", "华东有多少订单", None)
    assert rows[1][0] == "agent" and rows[1][1] == "3 单"
    assert rows[1][2][0]["name"] == "execute_query"


def test_chat_store_session_isolation(tmp_path):
    s = ChatStore(str(tmp_path / "chat.db"))
    s.save("s1", "user", "a")
    s.save("s2", "user", "b")
    assert s.load("s1") == [("user", "a", None)]
    assert s.load("s2") == [("user", "b", None)]


class _Msg:
    def __init__(self, content, type="human"):
        self.content = content
        self.type = type


class _FakeLLM:
    def invoke(self, messages):
        return type("R", (), {"content": "摘要：已确认 有效订单=paid"})()


def test_compact_short_history_untouched():
    msgs = [_Msg("system"), _Msg("你好"), _Msg("3 单")]
    assert compact(msgs, _FakeLLM()) == msgs


def test_compact_long_history_summarizes():
    msgs = [_Msg("system")] + [_Msg(f"轮{i}") for i in range(12)]
    out = compact(msgs, _FakeLLM(), keep_last=4)
    assert len(out) < len(msgs)
    assert any("历史摘要" in m[1] for m in out if isinstance(m, tuple))
