"""交付闸门（值域守卫）离线单测。"""

from daagent.delivery_check.declarations import Declarations
from daagent.delivery_check.guards import ValueDomain, run_guards, value_domain_check


def test_value_domain_passes_when_all_allowed():
    vd = ValueDomain(
        category="region",
        allowed=["华东区", "华南区", "华北区"],
        universe=["华东区", "华南区", "华北区", "华中区"],
    )
    assert value_domain_check("华东区 3 单、华南区 2 单、华北区 1 单", vd) == []


def test_value_domain_flags_unknown():
    vd = ValueDomain(
        category="region",
        allowed=["华东区", "华南区", "华北区"],
        universe=["华东区", "华南区", "华北区", "华中区"],
    )
    assert value_domain_check("华东区 3 单、华中区 1 单", vd) == ["华中区"]


def test_value_domain_no_suffix_false_positive():
    # 「各区域」不该被误判成实体「各区」
    vd = ValueDomain(
        category="region",
        allowed=["华东区", "华南区", "华北区"],
        universe=["华东区", "华南区", "华北区", "华中区"],
    )
    assert value_domain_check("各区域的订单量分别是多少", vd) == []


def test_self_correction_loop():
    from daagent.delivery_check.declarations import DEFAULT_DECLARATIONS
    from daagent.runner import _deliver

    calls = {"n": 0}

    def conclude(q, r):
        return "华中区 1 单"  # 第一版：踩陷阱

    def correct(q, r, reds):
        calls["n"] += 1
        return "华东区 3 单、华南区 2 单、华北区 1 单"  # 修正后：合规

    conclusion, reds = _deliver(conclude, correct, "q", "r", DEFAULT_DECLARATIONS)
    assert reds == []
    assert calls["n"] == 1
    assert conclusion == "华东区 3 单、华南区 2 单、华北区 1 单"


def test_self_correction_discloses_residual():
    from daagent.delivery_check.declarations import DEFAULT_DECLARATIONS
    from daagent.runner import _deliver

    def conclude(q, r):
        return "华中区 1 单"

    def correct(q, r, reds):
        return "华中区 1 单（不在标准区域，请人工确认）"  # 仍提华中区，闸门继续拦

    conclusion, reds = _deliver(conclude, correct, "q", "r", DEFAULT_DECLARATIONS)
    assert len(reds) == 1  # 2 轮后残留，如实披露
    assert "华中区" in conclusion


def test_run_guards_aggregates():
    decl = Declarations(
        value_domains=[
            ValueDomain(
                category="region",
                allowed=["华东区", "华南区", "华北区"],
                universe=["华东区", "华南区", "华北区", "华中区"],
            )
        ]
    )
    reds = run_guards("华中区 1 单", decl)
    assert len(reds) == 1
    assert reds[0].kind == "value_domain"
    assert "华中区" in reds[0].message
