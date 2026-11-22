"""交付闸门守卫（V0.2）：值域守卫。

关系守卫 + 核对 SQL 直查真值留 V0.3（需要数字锚点提取 + 万/亿归一化，接真实数据再做）。
"""

from dataclasses import dataclass, field


@dataclass
class RedFlag:
    kind: str
    message: str


@dataclass
class ValueDomain:
    category: str
    allowed: list[str]
    universe: list[str]  # 候选全集（来自数据 DISTINCT；真实系统从元数据取）


@dataclass
class Declarations:
    value_domains: list[ValueDomain] = field(default_factory=list)


def value_domain_check(conclusion: str, vd: ValueDomain) -> list[str]:
    """值域守卫：结论里出现的候选实体，若不在允许值域内 → 违规。

    相比 daw 的完整版（剥前缀散文 + 零使用语境降级），这里是简化版——用「候选全集」精确匹配，
    规避了「各区域 → 各区」这类后缀误伤；语境降级等真实数据接上再补。
    """
    allowed = set(vd.allowed)
    return sorted(e for e in vd.universe if e in conclusion and e not in allowed)


def run_guards(conclusion: str, declarations: Declarations) -> list[RedFlag]:
    reds: list[RedFlag] = []
    for vd in declarations.value_domains:
        for e in value_domain_check(conclusion, vd):
            reds.append(
                RedFlag("value_domain", f"「{e}」不在 {vd.category} 允许值域 {vd.allowed}")
            )
    return reds
