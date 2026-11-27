"""守卫声明：从 OKF 知识库加载 + 候选全集从数据 DISTINCT 自动取。

不再硬编码声明：守卫声明是知识库的一部分（被机制执行，不只被引用），
候选全集由数据 DISTINCT 自动推导（真实系统从元数据取）。
"""

from daagent.db.meta import distinct_values
from daagent.delivery_check.guards import (
    Declarations,
    RelationshipDecl,
    TruthDecl,
    ValueDomain,
)

DEFAULT_GUARDS_CONTENT = """# orders 守卫声明

## 允许
region = 华东、华南、华北

## 关系 0.02
总销售额 = 华东、华南、华北、华中

## 核对 0.01
总销售额 = SELECT SUM(amount) FROM orders WHERE status = 'paid'
"""


def _split(s: str) -> list[str]:
    return [x.strip() for x in s.replace("、", ",").replace("，", ",").split(",") if x.strip()]


def build_declarations(okf, con, table: str = "orders") -> Declarations:
    """从 OKF 读守卫声明（guards/<table>），候选全集从数据 DISTINCT 取，组装 Declarations。"""
    content = okf.read("guards", table)
    decls = Declarations()
    if not content:
        return decls

    section = None
    tolerance = None
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            parts = line[3:].split()
            section = parts[0]
            tolerance = float(parts[1]) if len(parts) > 1 else None
            continue
        if line.startswith("#"):
            continue
        if section == "允许":
            cat, vals = line.split("=", 1)
            try:
                universe = distinct_values(con, table, cat.strip())
            except Exception:  # noqa: BLE001  # 该列不适用于当前数据源，降级为空全集
                universe = []
            decls.value_domains.append(
                ValueDomain(category=cat.strip(), allowed=_split(vals), universe=universe)
            )
        elif section == "关系":
            total, parts = line.split("=", 1)
            decls.relationships.append(
                RelationshipDecl(
                    total_label=total.strip(),
                    part_labels=_split(parts),
                    tolerance=tolerance or 0.02,
                )
            )
        elif section == "核对":
            label, sql = line.split("=", 1)
            decls.truth_checks.append(
                TruthDecl(label=label.strip(), sql=sql.strip(), tolerance=tolerance or 0.01)
            )
    return decls
