"""会话打分 单测。"""

from daagent.evals.session_score import score_session


def test_score_session_all_pass():
    rec = {
        "answer": "有效订单 6 笔，来源 orders 表",
        "events": [
            {"type": "tool_call", "name": "search_knowledge", "args": {}},
            {"type": "tool_call", "name": "execute_query", "args": {}},
        ],
    }
    s = score_session(rec)
    assert s["交付形态（来源标注）"] is True
    assert s["首句先答数字"] is True
    assert s["知识行为（召回/沉淀）"] is True
    assert s["验证倾向（真查了数据）"] is True


def test_score_session_all_fail():
    rec = {"answer": "这是无数字无出处的答案", "events": []}
    s = score_session(rec)
    assert all(v is False for v in s.values())
