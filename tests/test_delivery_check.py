"""交付闸门（值域 / 关系 / 核对真值）+ 自纠环 离线单测。"""

from daagent.delivery_check.declarations import DEFAULT_DECLARATIONS, Declarations
from daagent.delivery_check.guards import (
    RelationshipDecl,
    ValueDomain,
    relationship_check,
    run_guards,
    truth_check,
    value_domain_check,
)
from daagent.runner import _deliver


# --- 值域守卫 ---

def test_value_domain_passes_when_all_allowed():
    vd = ValueDomain(
        category="region",
        allowed=["华东", "华南", "华北"],
        universe=["华东", "华南", "华北", "华中"],
    )
    assert value_domain_check("华东 3 单、华南 2 单、华北 1 单", vd) == []


def test_value_domain_flags_unknown():
    vd = ValueDomain(
        category="region",
        allowed=["华东", "华南", "华北"],
        universe=["华东", "华南", "华北", "华中"],
    )
    assert value_domain_check("华东 3 单、华中 1 单", vd) == ["华中"]


def test_value_domain_no_false_positive_on_common_word():
    vd = ValueDomain(
        category="region",
        allowed=["华东", "华南", "华北"],
        universe=["华东", "华南", "华北", "华中"],
    )
    assert value_domain_check("各区域的订单量分别是多少", vd) == []


# --- 关系守卫 ---

def test_relationship_passes_when_reconciles():
    decl = RelationshipDecl(total_label="总销售额", part_labels=["华东", "华南", "华北", "华中"])
    c = "总销售额 1000 元，华东 450、华南 350、华北 120、华中 80"
    assert relationship_check(c, decl) is None


def test_relationship_flags_mismatch():
    decl = RelationshipDecl(total_label="总销售额", part_labels=["华东", "华南", "华北", "华中"])
    c = "总销售额 900 元，华东 450、华南 350、华北 120、华中 80"  # 900 ≠ 1000
    f = relationship_check(c, decl)
    assert f is not None and f.kind == "relationship"


def test_relationship_skips_when_part_missing():
    # 宁漏不误：某个分部没提取到 → 不判
    decl = RelationshipDecl(total_label="总销售额", part_labels=["华东", "华南", "华北", "华中"])
    assert relationship_check("总销售额 1000 元", decl) is None


def test_relationship_normalizes_wan():
    decl = RelationshipDecl(total_label="总销售额", part_labels=["华东", "华南"])
    c = "总销售额 1 万，华东 0.4 万、华南 0.6 万"  # 10000 = 4000 + 6000
    assert relationship_check(c, decl) is None


# --- 核对 SQL 真值 ---

def test_truth_check_passes():
    assert truth_check("总销售额 1000 元", "总销售额", 1000, 0.01) is None


def test_truth_check_flags():
    f = truth_check("总销售额 900 元", "总销售额", 1000, 0.01)
    assert f is not None and f.kind == "truth"


# --- 自纠环 ---

def test_self_correction_loop():
    def conclude(q, r):
        return "总销售额 900 元"  # 错

    def correct(q, r, reds):
        return "总销售额 1000 元"  # 修正后对

    def check(c):
        return [] if "1000" in c else [
            type("F", (), {"kind": "truth", "message": "900 与真值 1000 不符"})()
        ]

    conclusion, reds = _deliver(conclude, correct, check, "q", "r")
    assert reds == []
    assert "1000" in conclusion


def test_self_correction_discloses_residual():
    def conclude(q, r):
        return "华中 1 单"

    def correct(q, r, reds):
        return "华中 1 单（不在标准区域，请人工确认）"

    def check(c):
        return [type("F", (), {"kind": "value_domain", "message": "「华中」不在允许值域"})()]

    conclusion, reds = _deliver(conclude, correct, check, "q", "r")
    assert len(reds) == 1
    assert "华中" in conclusion


def test_run_guards_aggregates():
    decl = Declarations(
        value_domains=[
            ValueDomain(
                category="region",
                allowed=["华东", "华南", "华北"],
                universe=["华东", "华南", "华北", "华中"],
            )
        ]
    )
    reds = run_guards("华中 1 单", decl)
    assert len(reds) == 1 and reds[0].kind == "value_domain"
