"""守卫声明：允许值域 + 关系 + 核对 SQL 真值。

完整声明格式随 OKF 知识库在 V0.4 引入，届时声明从知识库（git）加载，不再硬编码。
"""

from daagent.delivery_check.guards import (
    Declarations,
    RelationshipDecl,
    TruthDecl,
    ValueDomain,
)

DEFAULT_DECLARATIONS = Declarations(
    value_domains=[
        ValueDomain(
            category="region",
            allowed=["华东", "华南", "华北"],
            universe=["华东", "华南", "华北", "华中"],  # 华中 = 数据里埋的脏值陷阱
        )
    ],
    relationships=[
        RelationshipDecl(
            total_label="总销售额",
            part_labels=["华东", "华南", "华北", "华中"],
            tolerance=0.02,
        )
    ],
    truth_checks=[
        TruthDecl(label="总销售额", sql="SELECT SUM(amount) FROM orders", tolerance=0.01),
    ],
)
