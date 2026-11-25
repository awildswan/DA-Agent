"""L1 打分器 离线单测。"""

from daagent.evals.cases import Case
from daagent.evals.scorer import score


def test_score_all_pass():
    c = Case("x", "q", [6], "orders")
    r = score("有效订单 6 笔，来源 orders 表", c)
    assert r["passed"] is True
    assert r["数字命中"] and r["来源标注"] and r["首句先答"]


def test_score_missing_number():
    c = Case("x", "q", [6], "orders")
    r = score("有效订单 5 笔，来源 orders 表", c)
    assert r["数字命中"] is False and r["passed"] is False


def test_score_missing_source():
    c = Case("x", "q", [6], "orders")
    r = score("有效订单 6 笔", c)
    assert r["来源标注"] is False
