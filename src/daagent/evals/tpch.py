"""TPC-H 查询评测：金牌 = 官方 SQL 直查真值，执行准确率（顺序无关结果集）。

- 用独立空 OKF（不继承 sample 的概念，避免语义污染）。
- NL 问题说清聚合口径（明细营收 = l_extendedprice*(1-l_discount) 之和）。
"""

import os
import tempfile
import time

from daagent.db.datasource import get_datasource
from daagent.orchestration.runner import run_structured

QUERIES = [
    (
        "Q3",
        "统计 BUILDING 市场部客户在 1995-03-15 前下单、且在 1995-03-15 后发货的订单，"
        "营收按明细行计算（l_extendedprice*(1-l_discount) 之和），按营收降序取前 10，"
        "输出订单号、营收、下单日期、发货优先级（o_shippriority）。",
        "SELECT l_orderkey, SUM(l_extendedprice * (1 - l_discount)) AS revenue, "
        "o_orderdate, o_shippriority "
        "FROM customer, orders, lineitem "
        "WHERE c_mktsegment = 'BUILDING' AND c_custkey = o_custkey AND l_orderkey = o_orderkey "
        "AND o_orderdate < DATE '1995-03-15' AND l_shipdate > DATE '1995-03-15' "
        "GROUP BY l_orderkey, o_orderdate, o_shippriority "
        "ORDER BY revenue DESC, o_orderdate LIMIT 10",
    ),
    (
        "Q4",
        "统计 1993 年 7-9 月下单、且存在某行明细承诺日期早于收货日期的订单，"
        "按订单优先级（o_orderpriority）分组计数。",
        "SELECT o_orderpriority, COUNT(*) AS order_count FROM orders "
        "WHERE o_orderdate >= DATE '1993-07-01' AND o_orderdate < DATE '1993-10-01' "
        "AND EXISTS (SELECT 1 FROM lineitem WHERE l_orderkey = o_orderkey "
        "AND l_commitdate < l_receiptdate) "
        "GROUP BY o_orderpriority ORDER BY o_orderpriority",
    ),
    (
        "Q6",
        "统计 1994 全年、折扣在 0.05 到 0.07 之间、数量小于 24 的明细，"
        "总营收 = SUM(l_extendedprice * l_discount)。",
        "SELECT SUM(l_extendedprice * l_discount) AS revenue FROM lineitem "
        "WHERE l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1995-01-01' "
        "AND l_discount BETWEEN 0.05 AND 0.07 AND l_quantity < 24",
    ),
    (
        "Q10",
        "统计 1993 年第四季度退货（l_returnflag='R'）的客户，"
        "营收按明细行计算（l_extendedprice*(1-l_discount) 之和），按营收降序取前 20，"
        "输出客户号、姓名、营收、账户余额、国家、地址、电话、备注。",
        "SELECT c_custkey, c_name, SUM(l_extendedprice * (1 - l_discount)) AS revenue, "
        "c_acctbal, n_name, c_address, c_phone, c_comment "
        "FROM customer, orders, lineitem, nation "
        "WHERE c_custkey = o_custkey AND l_orderkey = o_orderkey "
        "AND o_orderdate >= DATE '1993-10-01' AND o_orderdate < DATE '1994-01-01' "
        "AND l_returnflag = 'R' AND c_nationkey = n_nationkey "
        "GROUP BY c_custkey, c_name, c_acctbal, c_phone, n_name, c_address, c_comment "
        "ORDER BY revenue DESC LIMIT 20",
    ),
]


def _norm(rows) -> list:
    """顺序无关结果集：每行元组化 + 排序。"""
    return sorted(tuple(str(x) for x in r) for r in rows)


def _matches(agent_rows, gold_rows) -> bool:
    """允许 agent 多列：完全一致，或 agent 的结果里存在与 gold 列数相同的投影能对上。"""
    a = _norm(agent_rows)
    g = _norm(gold_rows)
    if a == g:
        return True
    if not g or not a:
        return not g and not a
    ng, na = len(g[0]), len(a[0])
    if na < ng or na > 10:
        return False
    from itertools import combinations

    return any(
        sorted(tuple(str(r[c]) for c in cols) for r in a) == g
        for cols in combinations(range(na), ng)
    )


def run_tpch(limit: int | None = None) -> tuple[int, int]:
    os.environ["DAAGENT_DATASOURCE"] = "tpch"
    ds = get_datasource()
    con = ds.con
    okf_root = tempfile.mkdtemp(prefix="tpch_okf_")
    items = QUERIES[:limit] if limit else QUERIES
    correct = 0
    for qid, nl, sql in items:
        t0 = time.time()
        try:
            gold = _norm(con.execute(sql).fetchall())
        except Exception as e:  # noqa: BLE001
            print(f"{qid}: 金牌 SQL 失败 {e}")
            continue
        executed: list[str] = []

        def on_event(e):
            if e.get("type") == "tool_call" and e.get("name") == "execute_query":
                s = (e.get("args") or {}).get("sql", "")
                if s:
                    executed.append(s)

        try:
            run_structured(nl, okf_root=okf_root, on_event=on_event)
        except Exception as e:  # noqa: BLE001
            print(f"{qid}: agent 失败 {e}")
            continue
        ok = False
        for s in executed:
            try:
                if _matches(con.execute(s).fetchall(), gold):
                    ok = True
                    break
            except Exception:  # noqa: BLE001
                pass
        correct += ok
        print(f"{qid}: {'✅' if ok else '❌'}  {time.time() - t0:.1f}s  (agent 跑了 {len(executed)} 条 SQL)")
    print(f"\n执行准确率：{correct}/{len(items)}")
    return correct, len(items)
