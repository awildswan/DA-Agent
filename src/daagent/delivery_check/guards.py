"""交付闸门守卫：值域守卫 + 关系守卫 + 核对 SQL 真值（结构化数据，不解析文本）。"""

from dataclasses import dataclass, field


@dataclass
class RedFlag:
    kind: str
    message: str


@dataclass
class ValueDomain:
    category: str
    allowed: list[str]
    universe: list[str]  # 候选全集（真实系统从数据 DISTINCT 取）


@dataclass
class RelationshipDecl:
    total_label: str
    part_labels: list[str]
    tolerance: float = 0.02


@dataclass
class TruthDecl:
    label: str
    sql: str  # 直查真值 SQL
    tolerance: float = 0.01


@dataclass
class Declarations:
    value_domains: list[ValueDomain] = field(default_factory=list)
    relationships: list[RelationshipDecl] = field(default_factory=list)
    truth_checks: list[TruthDecl] = field(default_factory=list)


def value_domain_check(entities: list[str], vd: ValueDomain) -> list[str]:
    """值域守卫：实体列表里，候选全集中不在允许值域内的 → 违规。"""
    allowed = set(vd.allowed)
    universe = set(vd.universe)
    return sorted(e for e in entities if e in universe and e not in allowed)


def relationship_check(numbers: dict, decl: RelationshipDecl) -> RedFlag | None:
    """关系守卫：numbers[总数] 与各分部之和 差额超容差 → 红灯（宁漏不误：缺数字不判）。"""
    total = numbers.get(decl.total_label)
    parts = [numbers.get(p) for p in decl.part_labels]
    if total is None or any(p is None for p in parts):
        return None
    s = sum(parts)
    if abs(total - s) > total * decl.tolerance:
        return RedFlag(
            "relationship",
            f"「{decl.total_label}」{total:g} 与各分部之和 {s:g} 不符（差 {abs(total - s):g}）",
        )
    return None


def truth_check(numbers: dict, label: str, truth_value: float, tolerance: float) -> RedFlag | None:
    """核对 SQL 真值：numbers[label] 与 直查真值 不符 → 红灯（缺数字不判）。"""
    got = numbers.get(label)
    if got is None:
        return None
    if abs(got - truth_value) > truth_value * tolerance:
        return RedFlag("truth", f"「{label}」{got:g} 与直查真值 {truth_value:g} 不符")
    return None


def run_guards(structured: dict, declarations: Declarations) -> list[RedFlag]:
    """文本级守卫：值域 + 关系（核对 SQL 真值需直查，由 runner 单独调用 truth_check）。

    structured = {"numbers": {标签: 数字}, "entities": [实体...]}
    """
    reds: list[RedFlag] = []
    entities = structured.get("entities", []) or []
    numbers = structured.get("numbers", {}) or {}
    for vd in declarations.value_domains:
        for e in value_domain_check(entities, vd):
            reds.append(
                RedFlag("value_domain", f"「{e}」不在 {vd.category} 允许值域 {vd.allowed}")
            )
    for r in declarations.relationships:
        f = relationship_check(numbers, r)
        if f:
            reds.append(f)
    return reds
