"""TPC-H 22 查询评测：金牌 = 官方 SQL 直查真值，执行准确率（顺序无关结果集）。

- 用独立空 OKF（不继承 sample 概念）。
- NL 说清聚合口径。
- 允许 agent 多列（在它的列里找 gold 的投影）。
"""

import os
import tempfile
import time

from daagent.db.datasource import get_datasource
from daagent.orchestration.runner import run_structured

QUERIES = [
    (
        "Q1",
        "统计 1998-12-01 前 90 天内发货的明细，按退货标志和状态分组，输出数量合计、"
        "基础营收合计、折后营收合计、含税折后营收合计、平均数量、平均单价、平均折扣、订单数。",
        "SELECT l_returnflag, l_linestatus, SUM(l_quantity), SUM(l_extendedprice), "
        "SUM(l_extendedprice * (1 - l_discount)), SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)), "
        "AVG(l_quantity), AVG(l_extendedprice), AVG(l_discount), COUNT(*) FROM lineitem "
        "WHERE l_shipdate <= DATE '1998-12-01' - INTERVAL '90' DAY "
        "GROUP BY l_returnflag, l_linestatus ORDER BY l_returnflag, l_linestatus",
    ),
    (
        "Q2",
        "找出欧洲地区、尺寸 15、类型含 BRASS 的零件的最低成本供应商，输出账户余额、供应商名、"
        "国家、零件号、制造商、地址、电话、备注，按账户余额降序取前 100。",
        "SELECT s_acctbal, s_name, n_name, p_partkey, p_mfgr, s_address, s_phone, s_comment "
        "FROM part, supplier, partsupp, nation, region "
        "WHERE p_partkey = ps_partkey AND s_suppkey = ps_suppkey AND p_size = 15 "
        "AND p_type LIKE '%BRASS' AND s_nationkey = n_nationkey AND n_regionkey = r_regionkey "
        "AND r_name = 'EUROPE' AND ps_supplycost = (SELECT MIN(ps_supplycost) "
        "FROM partsupp, supplier, nation, region WHERE p_partkey = ps_partkey "
        "AND s_suppkey = ps_suppkey AND s_nationkey = n_nationkey AND n_regionkey = r_regionkey "
        "AND r_name = 'EUROPE') ORDER BY s_acctbal DESC, n_name, s_name, p_partkey LIMIT 100",
    ),
    (
        "Q3",
        "统计 BUILDING 市场部客户在 1995-03-15 前下单、且在 1995-03-15 后发货的订单，"
        "营收按明细行计算（l_extendedprice*(1-l_discount) 之和），按营收降序取前 10，"
        "输出订单号、营收、下单日期、发货优先级（o_shippriority）。",
        "SELECT l_orderkey, SUM(l_extendedprice * (1 - l_discount)) AS revenue, o_orderdate, o_shippriority "
        "FROM customer, orders, lineitem WHERE c_mktsegment = 'BUILDING' AND c_custkey = o_custkey "
        "AND l_orderkey = o_orderkey AND o_orderdate < DATE '1995-03-15' AND l_shipdate > DATE '1995-03-15' "
        "GROUP BY l_orderkey, o_orderdate, o_shippriority ORDER BY revenue DESC, o_orderdate LIMIT 10",
    ),
    (
        "Q4",
        "统计 1993 年 7-9 月下单、且存在某行明细承诺日期早于收货日期的订单，按订单优先级分组计数。",
        "SELECT o_orderpriority, COUNT(*) FROM orders "
        "WHERE o_orderdate >= DATE '1993-07-01' AND o_orderdate < DATE '1993-10-01' "
        "AND EXISTS (SELECT 1 FROM lineitem WHERE l_orderkey = o_orderkey AND l_commitdate < l_receiptdate) "
        "GROUP BY o_orderpriority ORDER BY o_orderpriority",
    ),
    (
        "Q5",
        "统计 1994 年亚洲地区的营收（明细营收之和），按国家名分组，按营收降序。",
        "SELECT n_name, SUM(l_extendedprice * (1 - l_discount)) AS revenue "
        "FROM customer, orders, lineitem, supplier, nation, region "
        "WHERE c_custkey = o_custkey AND l_orderkey = o_orderkey AND l_suppkey = s_suppkey "
        "AND c_nationkey = s_nationkey AND s_nationkey = n_nationkey AND n_regionkey = r_regionkey "
        "AND r_name = 'ASIA' AND o_orderdate >= DATE '1994-01-01' AND o_orderdate < DATE '1995-01-01' "
        "GROUP BY n_name ORDER BY revenue DESC",
    ),
    (
        "Q6",
        "统计 1994 全年、折扣在 0.05 到 0.07 之间、数量小于 24 的明细，总营收 = SUM(l_extendedprice * l_discount)。",
        "SELECT SUM(l_extendedprice * l_discount) FROM lineitem "
        "WHERE l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1995-01-01' "
        "AND l_discount BETWEEN 0.05 AND 0.07 AND l_quantity < 24",
    ),
    (
        "Q7",
        "统计 1995-1996 年法国与德国之间的发货量（明细营收），按供应商国家、客户国家、年份分组，按三者升序。",
        "SELECT supp_nation, cust_nation, l_year, SUM(volume) AS revenue FROM ("
        "SELECT n1.n_name AS supp_nation, n2.n_name AS cust_nation, "
        "EXTRACT(YEAR FROM l_shipdate) AS l_year, l_extendedprice * (1 - l_discount) AS volume "
        "FROM supplier, lineitem, orders, customer, nation n1, nation n2 "
        "WHERE s_suppkey = l_suppkey AND o_orderkey = l_orderkey AND c_custkey = o_custkey "
        "AND s_nationkey = n1.n_nationkey AND c_nationkey = n2.n_nationkey "
        "AND ((n1.n_name = 'FRANCE' AND n2.n_name = 'GERMANY') OR (n1.n_name = 'GERMANY' AND n2.n_name = 'FRANCE')) "
        "AND l_shipdate BETWEEN DATE '1995-01-01' AND DATE '1996-12-31') AS shipping "
        "GROUP BY supp_nation, cust_nation, l_year ORDER BY supp_nation, cust_nation, l_year",
    ),
    (
        "Q8",
        "统计 1995-1996 年、零件类型 ECONOMY ANODIZED STEEL、美洲地区，巴西的市场份额，按年份分组升序。",
        "SELECT o_year, SUM(CASE WHEN nation = 'BRAZIL' THEN volume ELSE 0 END) / SUM(volume) AS mkt_share FROM ("
        "SELECT EXTRACT(YEAR FROM o_orderdate) AS o_year, l_extendedprice * (1 - l_discount) AS volume, "
        "n2.n_name AS nation FROM part, supplier, lineitem, orders, customer, nation n1, nation n2, region "
        "WHERE p_partkey = l_partkey AND s_suppkey = l_suppkey AND l_orderkey = o_orderkey "
        "AND o_custkey = c_custkey AND c_nationkey = n1.n_nationkey AND n1.n_regionkey = r_regionkey "
        "AND r_name = 'AMERICA' AND s_nationkey = n2.n_nationkey "
        "AND o_orderdate BETWEEN DATE '1995-01-01' AND DATE '1996-12-31' "
        "AND p_type = 'ECONOMY ANODIZED STEEL') AS all_nations GROUP BY o_year ORDER BY o_year",
    ),
    (
        "Q9",
        "统计所有零件名含 green 的订单利润（明细营收 - 供应成本×数量），按国家、年份分组，按国家升序、年份降序。",
        "SELECT nation, o_year, SUM(amount) AS sum_profit FROM ("
        "SELECT n_name AS nation, EXTRACT(YEAR FROM o_orderdate) AS o_year, "
        "l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity AS amount "
        "FROM part, supplier, lineitem, partsupp, orders, nation "
        "WHERE s_suppkey = l_suppkey AND ps_suppkey = l_suppkey AND ps_partkey = l_partkey "
        "AND p_partkey = l_partkey AND o_orderkey = l_orderkey AND s_nationkey = n_nationkey "
        "AND p_name LIKE '%green%') AS profit GROUP BY nation, o_year ORDER BY nation, o_year DESC",
    ),
    (
        "Q10",
        "统计 1993 年第四季度退货（l_returnflag='R'）的客户，营收按明细行计算，按营收降序取前 20，"
        "输出客户号、姓名、营收、账户余额、国家、地址、电话、备注。",
        "SELECT c_custkey, c_name, SUM(l_extendedprice * (1 - l_discount)) AS revenue, c_acctbal, n_name, "
        "c_address, c_phone, c_comment FROM customer, orders, lineitem, nation "
        "WHERE c_custkey = o_custkey AND l_orderkey = o_orderkey AND o_orderdate >= DATE '1993-10-01' "
        "AND o_orderdate < DATE '1994-01-01' AND l_returnflag = 'R' AND c_nationkey = n_nationkey "
        "GROUP BY c_custkey, c_name, c_acctbal, c_phone, n_name, c_address, c_comment "
        "ORDER BY revenue DESC LIMIT 20",
    ),
    (
        "Q11",
        "统计德国供应商的零件库存价值（供应成本×可用量之和），超过德国总量的万分之一，按价值降序。",
        "SELECT ps_partkey, SUM(ps_supplycost * ps_availqty) AS value FROM partsupp, supplier, nation "
        "WHERE ps_suppkey = s_suppkey AND s_nationkey = n_nationkey AND n_name = 'GERMANY' "
        "GROUP BY ps_partkey HAVING SUM(ps_supplycost * ps_availqty) > ("
        "SELECT SUM(ps_supplycost * ps_availqty) * 0.0001 FROM partsupp, supplier, nation "
        "WHERE ps_suppkey = s_suppkey AND s_nationkey = n_nationkey AND n_name = 'GERMANY') "
        "ORDER BY value DESC",
    ),
    (
        "Q12",
        "统计 1994 年收货的 MAIL/SHIP 发货方式中，高优先级与低优先级订单行数，按发货方式分组升序。",
        "SELECT l_shipmode, "
        "SUM(CASE WHEN o_orderpriority = '1-URGENT' OR o_orderpriority = '2-HIGH' THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN o_orderpriority <> '1-URGENT' AND o_orderpriority <> '2-HIGH' THEN 1 ELSE 0 END) "
        "FROM orders, lineitem WHERE o_orderkey = l_orderkey AND l_shipmode IN ('MAIL', 'SHIP') "
        "AND l_commitdate < l_receiptdate AND l_shipdate < l_commitdate "
        "AND l_receiptdate >= DATE '1994-01-01' AND l_receiptdate < DATE '1995-01-01' "
        "GROUP BY l_shipmode ORDER BY l_shipmode",
    ),
    (
        "Q13",
        "统计每个客户的订单数（不含备注含 special%requests% 的订单），按订单数分组统计客户数，按客户数降序、订单数降序。",
        "SELECT c_count, COUNT(*) AS custdist FROM ("
        "SELECT c_custkey, COUNT(o_orderkey) AS c_count FROM customer "
        "LEFT OUTER JOIN orders ON c_custkey = o_custkey AND o_comment NOT LIKE '%special%requests%' "
        "GROUP BY c_custkey) AS c_orders GROUP BY c_count ORDER BY custdist DESC, c_count DESC",
    ),
    (
        "Q14",
        "统计 1995 年 9 月促销零件（类型以 PROMO 开头）的营收占全部营收的百分比。",
        "SELECT 100.00 * SUM(CASE WHEN p_type LIKE 'PROMO%' THEN l_extendedprice * (1 - l_discount) ELSE 0 END) "
        "/ SUM(l_extendedprice * (1 - l_discount)) FROM lineitem, part "
        "WHERE l_partkey = p_partkey AND l_shipdate >= DATE '1995-09-01' AND l_shipdate < DATE '1995-10-01'",
    ),
    (
        "Q15",
        "统计 1996 年 1-3 月营收最高的供应商，输出供应商号、名称、地址、电话、总营收。",
        "WITH revenue AS (SELECT l_suppkey AS supplier_no, SUM(l_extendedprice * (1 - l_discount)) AS total_revenue "
        "FROM lineitem WHERE l_shipdate >= DATE '1996-01-01' AND l_shipdate < DATE '1996-04-01' "
        "GROUP BY l_suppkey) SELECT s_suppkey, s_name, s_address, s_phone, total_revenue FROM supplier, revenue "
        "WHERE s_suppkey = supplier_no AND total_revenue = (SELECT MAX(total_revenue) FROM revenue) ORDER BY s_suppkey",
    ),
    (
        "Q16",
        "统计零件品牌、类型、尺寸组合中，不满足特定品牌/类型/尺寸的供应商数量（去重），按数量降序、品牌/类型/尺寸升序。",
        "SELECT p_brand, p_type, p_size, COUNT(DISTINCT ps_suppkey) AS supplier_cnt FROM partsupp, part "
        "WHERE p_partkey = ps_partkey AND p_brand <> 'Brand#45' AND p_type NOT LIKE 'MEDIUM POLISHED%' "
        "AND p_size IN (49, 14, 23, 45, 19, 3, 36, 9) AND ps_suppkey NOT IN ("
        "SELECT s_suppkey FROM supplier WHERE s_comment LIKE '%Customer%Complaints%') "
        "GROUP BY p_brand, p_type, p_size ORDER BY supplier_cnt DESC, p_brand, p_type, p_size",
    ),
    (
        "Q17",
        "统计品牌 Brand#23、容器 MED BOX 的零件，明细数量低于同零件平均数量 20% 的平均年营收。",
        "SELECT SUM(l_extendedprice) / 7.0 FROM lineitem, part "
        "WHERE p_partkey = l_partkey AND p_brand = 'Brand#23' AND p_container = 'MED BOX' "
        "AND l_quantity < (SELECT 0.2 * AVG(l_quantity) FROM lineitem WHERE l_partkey = p_partkey)",
    ),
    (
        "Q18",
        "统计单笔订单明细数量和大于 300 的大客户订单，输出客户名、客户号、订单号、下单日期、订单总价、明细数量和，"
        "按订单总价降序、下单日期升序取前 100。",
        "SELECT c_name, c_custkey, o_orderkey, o_orderdate, o_totalprice, SUM(l_quantity) "
        "FROM customer, orders, lineitem WHERE o_orderkey IN ("
        "SELECT l_orderkey FROM lineitem GROUP BY l_orderkey HAVING SUM(l_quantity) > 300) "
        "AND c_custkey = o_custkey AND o_orderkey = l_orderkey "
        "GROUP BY c_name, c_custkey, o_orderkey, o_orderdate, o_totalprice "
        "ORDER BY o_totalprice DESC, o_orderdate LIMIT 100",
    ),
    (
        "Q19",
        "统计满足三组品牌/容器/数量/尺寸组合的明细营收合计（折后营收）。",
        "SELECT SUM(l_extendedprice * (1 - l_discount)) FROM lineitem, part WHERE p_partkey = l_partkey AND ("
        "(p_brand = 'Brand#12' AND p_container IN ('SM CASE', 'SM BOX', 'SM PACK', 'SM PKG') "
        "AND l_quantity >= 1 AND l_quantity <= 11 AND p_size BETWEEN 1 AND 5 "
        "AND l_shipmode IN ('AIR', 'AIR REG') AND l_shipinstruct = 'DELIVER IN PERSON') "
        "OR (p_brand = 'Brand#23' AND p_container IN ('MED BAG', 'MED BOX', 'MED PKG', 'MED PACK') "
        "AND l_quantity >= 10 AND l_quantity <= 20 AND p_size BETWEEN 1 AND 10 "
        "AND l_shipmode IN ('AIR', 'AIR REG') AND l_shipinstruct = 'DELIVER IN PERSON') "
        "OR (p_brand = 'Brand#34' AND p_container IN ('LG CASE', 'LG BOX', 'LG PACK', 'LG PKG') "
        "AND l_quantity >= 20 AND l_quantity <= 30 AND p_size BETWEEN 1 AND 15 "
        "AND l_shipmode IN ('AIR', 'AIR REG') AND l_shipinstruct = 'DELIVER IN PERSON'))",
    ),
    (
        "Q20",
        "统计加拿大供应商中，供应零件名含 forest、且供应量超过该零件该供应商 1994 年发货量一半的供应商名称和地址。",
        "SELECT s_name, s_address FROM supplier, nation WHERE s_suppkey IN ("
        "SELECT ps_suppkey FROM partsupp WHERE ps_partkey IN ("
        "SELECT p_partkey FROM part WHERE p_name LIKE 'forest%') AND ps_availqty > ("
        "SELECT 0.5 * SUM(l_quantity) FROM lineitem WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey "
        "AND l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1995-01-01')) "
        "AND s_nationkey = n_nationkey AND n_name = 'CANADA' ORDER BY s_name",
    ),
    (
        "Q21",
        "统计沙特阿拉伯供应商中，存在其他供应商延迟、但自身按时交付的订单，按供应商名分组计数，取前 100。",
        "SELECT s_name, COUNT(*) AS numwait FROM supplier, lineitem l1, orders, nation "
        "WHERE s_suppkey = l1.l_suppkey AND o_orderkey = l1.l_orderkey AND o_orderstatus = 'F' "
        "AND l1.l_receiptdate > l1.l_commitdate AND EXISTS ("
        "SELECT 1 FROM lineitem l2 WHERE l2.l_orderkey = l1.l_orderkey AND l2.l_suppkey <> l1.l_suppkey) "
        "AND NOT EXISTS (SELECT 1 FROM lineitem l3 WHERE l3.l_orderkey = l1.l_orderkey "
        "AND l3.l_suppkey <> l1.l_suppkey AND l3.l_receiptdate > l3.l_commitdate) "
        "AND s_nationkey = n_nationkey AND n_name = 'SAUDI ARABIA' "
        "GROUP BY s_name ORDER BY numwait DESC, s_name LIMIT 100",
    ),
    (
        "Q22",
        "统计指定国家代码（13/31/23/29/30/18/17）中，账户余额高于均值的客户，按国家代码分组计数和余额合计，按代码升序。",
        "SELECT cntrycode, COUNT(*) AS numcust, SUM(c_acctbal) AS totacctbal FROM ("
        "SELECT SUBSTRING(c_phone, 1, 2) AS cntrycode, c_acctbal FROM customer "
        "WHERE SUBSTRING(c_phone, 1, 2) IN ('13', '31', '23', '29', '30', '18', '17') "
        "AND c_acctbal > (SELECT AVG(c_acctbal) FROM customer WHERE c_acctbal > 0.00 "
        "AND SUBSTRING(c_phone, 1, 2) IN ('13', '31', '23', '29', '30', '18', '17')) "
        "AND NOT EXISTS (SELECT 1 FROM orders WHERE o_custkey = c_custkey)) AS custsale "
        "GROUP BY cntrycode ORDER BY cntrycode",
    ),
]


def _norm(rows) -> list:
    return sorted(tuple(str(x) for x in r) for r in rows)


def _matches(agent_rows, gold_rows) -> bool:
    a = _norm(agent_rows)
    g = _norm(gold_rows)
    if a == g:
        return True
    if not g or not a:
        return not g and not a
    ng, na = len(g[0]), len(a[0])
    if na < ng or na > 12:
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
