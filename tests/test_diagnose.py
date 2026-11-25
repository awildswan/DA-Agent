"""业务诊断 离线单测（只测纯函数，不调 LLM）。"""

from daagent.agent.diagnose import _append_diagnosis


def test_append_diagnosis_when_present():
    assert _append_diagnosis("6 单", "诊断结论：...") == "6 单\n\n诊断结论：..."


def test_append_diagnosis_skips_when_not_needed():
    assert _append_diagnosis("6 单", "无需诊断") == "6 单"
    assert _append_diagnosis("6 单", "") == "6 单"
