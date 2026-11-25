"""交付闸门（值域 / 关系 / 核对真值）+ 自纠环 离线单测（结构化数据）。"""

from daagent.db.sample import sample_db
from daagent.delivery_check.declarations import (
    DEFAULT_GUARDS_CONTENT,
    Declarations,
    build_declarations,
)
from daagent.delivery_check.guards import (
    RelationshipDecl,
    ValueDomain,
    relationship_check,
    run_guards,
    truth_check,
    value_domain_check,
)
from daagent.agent.loop import _deliver
from daagent.okf.store import OkfStore


# --- 值域守卫 ---

def test_value_domain_passes_when_all_allowed():
    vd = ValueDomain(
        category="region",
        allowed=["华东", "华南", "华北"],
        universe=["华东", "华南", "华北", "华中"],
    )
    assert value_domain_check(["华东", "华南", "华北"], vd) == []


def test_value_domain_flags_unknown():
    vd = ValueDomain(
        category="region",
        allowed=["华东", "华南", "华北"],
        universe=["华东", "华南", "华北", "华中"],
    )
    assert value_domain_check(["华东", "华中"], vd) == ["华中"]


def test_value_domain_ignores_irrelevant_entities():
    vd = ValueDomain(
        category="region",
        allowed=["华东", "华南", "华北"],
        universe=["华东", "华南", "华北", "华中"],
    )
    # 非候选全集的实体（如"订单"）不判
    assert value_domain_check(["订单"], vd) == []


# --- 关系守卫 ---

def test_relationship_passes_when_reconciles():
    decl = RelationshipDecl(total_label="总销售额", part_labels=["华东", "华南", "华北", "华中"])
    nums = {"总销售额": 1000, "华东": 450, "华南": 350, "华北": 120, "华中": 80}
    assert relationship_check(nums, decl) is None


def test_relationship_flags_mismatch():
    decl = RelationshipDecl(total_label="总销售额", part_labels=["华东", "华南", "华北", "华中"])
    nums = {"总销售额": 900, "华东": 450, "华南": 350, "华北": 120, "华中": 80}
    f = relationship_check(nums, decl)
    assert f is not None and f.kind == "relationship"


def test_relationship_skips_when_part_missing():
    # 宁漏不误：某分部缺数字 → 不判
    decl = RelationshipDecl(total_label="总销售额", part_labels=["华东", "华南", "华北", "华中"])
    assert relationship_check({"总销售额": 1000}, decl) is None


# --- 核对 SQL 真值 ---

def test_truth_check_passes():
    assert truth_check({"总销售额": 1000}, "总销售额", 1000, 0.01) is None


def test_truth_check_flags():
    f = truth_check({"总销售额": 900}, "总销售额", 1000, 0.01)
    assert f is not None and f.kind == "truth"


# --- 守卫声明从 OKF + DISTINCT 加载 ---

def test_build_declarations_from_okf_and_distinct(tmp_path):
    okf = OkfStore(tmp_path / "okf", git=False)
    okf.write("guards", "orders", DEFAULT_GUARDS_CONTENT)
    con = sample_db()
    decls = build_declarations(okf, con)

    assert decls.value_domains[0].allowed == ["华东", "华南", "华北"]
    assert set(decls.value_domains[0].universe) == {"华东", "华南", "华北", "华中"}
    assert decls.relationships[0].total_label == "总销售额"
    assert decls.truth_checks[0].label == "总销售额"


def test_build_declarations_empty_when_no_guards(tmp_path):
    okf = OkfStore(tmp_path / "okf", git=False)
    decls = build_declarations(okf, sample_db())
    assert decls.value_domains == []
    assert decls.relationships == []
    assert decls.truth_checks == []


# --- 自纠环 ---

def test_self_correction_loop():
    def conclude(q, r):
        return {"answer": "总销售额 900 元", "numbers": {"总销售额": 900}, "entities": []}

    def correct(q, r, reds):
        return {"answer": "总销售额 1000 元", "numbers": {"总销售额": 1000}, "entities": []}

    def check(c):
        return [] if c["numbers"].get("总销售额") == 1000 else [
            type("F", (), {"kind": "truth", "message": "900 与真值 1000 不符"})()
        ]

    structured, reds = _deliver(conclude, correct, check, "q", "r")
    assert reds == []
    assert structured["numbers"]["总销售额"] == 1000


def test_self_correction_discloses_residual():
    def conclude(q, r):
        return {"answer": "华中 1 单", "numbers": {}, "entities": ["华中"]}

    def correct(q, r, reds):
        return {"answer": "华中 1 单（不在标准区域）", "numbers": {}, "entities": ["华中"]}

    def check(c):
        return [type("F", (), {"kind": "value_domain", "message": "「华中」不在允许值域"})()]

    structured, reds = _deliver(conclude, correct, check, "q", "r")
    assert len(reds) == 1
    assert "华中" in structured["entities"]


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
    reds = run_guards({"entities": ["华中"], "numbers": {}}, decl)
    assert len(reds) == 1 and reds[0].kind == "value_domain"
