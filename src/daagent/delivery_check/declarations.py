"""守卫声明（V0.2）：允许值域。

完整声明格式（允许 / 禁止 / 关系 / 核对）随 OKF 知识库在 V0.3 引入，届时声明从知识库加载。
"""

from daagent.delivery_check.guards import Declarations, ValueDomain

DEFAULT_DECLARATIONS = Declarations(
    value_domains=[
        ValueDomain(
            category="region",
            allowed=["华东区", "华南区", "华北区"],
            universe=["华东区", "华南区", "华北区", "华中区"],  # 华中区=数据里埋的脏值陷阱
        )
    ]
)
