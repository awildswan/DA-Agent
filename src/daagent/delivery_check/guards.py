"""交付闸门守卫：值域守卫 + 关系守卫 + 核对 SQL 真值。"""

import re
from dataclasses import dataclass, field

_UNITS = {"万": 10_000, "亿": 100_000_000}


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


def value_domain_check(conclusion: str, vd: ValueDomain) -> list[str]:
    """值域守卫：结论里出现的候选实体，若不在允许值域内 → 违规。"""
    allowed = set(vd.allowed)
    return sorted(e for e in vd.universe if e in conclusion and e not in allowed)


def _extract_amount(text: str, label: str) -> float | None:
    """在 label 之后提取第一个数字（万 / 亿归一化到元）。"""
    idx = text.find(label)
    if idx < 0:
        return None
    seg = text[idx + len(label): idx + len(label) + 24]
    m = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(万|亿)?", seg)
    if not m:
        return None
    val = float(m.group(1).replace(",", ""))
    unit = m.group(2) or ""
    return val * _UNITS.get(unit, 1.0)


def relationship_check(conclusion: str, decl: RelationshipDecl) -> RedFlag | None:
    """关系守卫：总数 与 各分部之和 差额超容差 → 红灯（宁漏不误：提取不到不判）。"""
    total = _extract_amount(conclusion, decl.total_label)
    parts = [_extract_amount(conclusion, p) for p in decl.part_labels]
    if total is None or any(p is None for p in parts):
        return None
    s = sum(parts)
    if abs(total - s) > total * decl.tolerance:
        return RedFlag(
            "relationship",
            f"「{decl.total_label}」{total:g} 与各分部之和 {s:g} 不符（差 {abs(total - s):g}）",
        )
    return None


def truth_check(conclusion: str, label: str, truth_value: float, tolerance: float) -> RedFlag | None:
    """核对 SQL 真值：结论里的数字 与 直查真值 不符 → 红灯。"""
    got = _extract_amount(conclusion, label)
    if got is None:
        return None
    if abs(got - truth_value) > truth_value * tolerance:
        return RedFlag("truth", f"「{label}」{got:g} 与直查真值 {truth_value:g} 不符")
    return None


def run_guards(conclusion: str, declarations: Declarations) -> list[RedFlag]:
    """文本级守卫：值域 + 关系（核对 SQL 真值需直查，由 runner 单独调用 truth_check）。"""
    reds: list[RedFlag] = []
    for vd in declarations.value_domains:
        for e in value_domain_check(conclusion, vd):
            reds.append(
                RedFlag("value_domain", f"「{e}」不在 {vd.category} 允许值域 {vd.allowed}")
            )
    for r in declarations.relationships:
        f = relationship_check(conclusion, r)
        if f:
            reds.append(f)
    return reds
