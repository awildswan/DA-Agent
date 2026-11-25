"""Trace 离线单测。"""

from daagent.tracing.tracer import Trace


def test_trace_spans_record():
    t = Trace()
    with t.span("a"):
        pass
    with t.span("b"):
        pass
    assert len(t.spans) == 2
    assert t.spans[0].name == "a"
    assert t.spans[1].duration_ms >= 0


def test_trace_summary():
    t = Trace()
    with t.span("取数"):
        pass
    assert "取数" in t.summary()
