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
