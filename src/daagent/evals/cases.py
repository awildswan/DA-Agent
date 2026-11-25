"""L1 自制业务口径集：问题 → 金牌（数字 + 来源表）。"""

from dataclasses import dataclass


@dataclass
class Case:
    id: str
    question: str
    gold_numbers: list[float]  # 答案必须含这些数字
    source_table: str  # 答案应提及这个来源表


CASES = [
    Case("c1", "有效订单有多少", [6], "orders"),
    Case("c2", "总销售额是多少", [950], "orders"),
    Case("c3", "每个品类卖了多少件", [6, 1], "order_items"),
]

# L2：SQL 准确率（SQL 型题目：计数 / 去重 / 多表，gold 数字明确）
SQL_CASES = [
    Case("s1", "products 表里有多少个商品", [3], "products"),
    Case("s2", "order_items 表里有多少行明细", [6], "order_items"),
    Case("s3", "有多少个不同的品类", [2], "products"),
    Case("s4", "orders 表里一共有多少笔订单", [7], "orders"),
    Case("s5", "数码类商品卖了多少件", [6], "order_items"),
]
