"""守卫声明：通用（从数据自动推导）+ 业务（OKF 声明）两路。

- build_generic_declarations(ds)：任何数据源都能用，值域 = 所有文本列的 DISTINCT 值。
- build_declarations(okf, con)：业务声明（OKF guards/<table>），候选全集从数据 DISTINCT 取。
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


def build_generic_declarations(ds) -> Declarations:
    """通用守卫：从数据自动推导值域（所有文本列的 DISTINCT 值），不按数据集写声明。

    任何数据源（sample / TPC-H / 真实库）都能用：agent 提到的实体若不在任何文本列的值里 → 疑似编造。
    """
    decls = Declarations()
    con = ds.con
    for table in ds.list_tables():
        try:
            cols = con.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = ? AND data_type IN ('VARCHAR','TEXT','CHAR')",
                [table],
            ).fetchall()
        except Exception:  # noqa: BLE001
            continue
        for (col,) in cols:
            try:
                vals = [
                    str(r[0])
                    for r in con.execute(
                        f'SELECT DISTINCT "{col}" FROM "{table}" WHERE "{col}" IS NOT NULL LIMIT 50'
                    ).fetchall()
                ]
            except Exception:  # noqa: BLE001
                continue
            if vals:
                decls.value_domains.append(
                    ValueDomain(category=f"{table}.{col}", allowed=vals, universe=vals)
                )
    return decls


def build_declarations(okf, con, table: str = "orders") -> Declarations:
    """业务守卫：从 OKF 读守卫声明（guards/<table>），候选全集从数据 DISTINCT 取。"""
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
