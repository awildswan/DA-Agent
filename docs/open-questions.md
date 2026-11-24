# 待验证项（Open Questions）

> 编号：open-questions · 版本 v0.1 · 2026-11-22 · 状态：Draft
> 记录尚未拍板或待实测验证的问题。定案后移到 ADR / 对应设计文档 / TASKS，并在此划掉。

| # | 问题 | 状态 | 影响 |
|---|---|---|---|
| 1 | 桌面壳 Tauri v2（引入 Rust）vs pywebview（单语言）：若嫌 Rust 复杂度，可降级 pywebview（核心不变） | 待验证 | ARCHITECTURE.md |
| 2 | 多 Agent 编排是否 V2 引入 LangGraph | 留 V2 | ADR-0002 |
| 3 | 无真实业务库 → L1 只能验证「自洽」，验不了「真实口径对错」 | 已知边界 | TEST_PLAN.md |
| 4 | `pydantic-ai` 作为 langchain-core 的可替换项，何时评估迁移 | 备选 | ADR-0002 |
| 5 | 交付闸门「宁漏不误」的误报 / 漏报率阈值，需真实数据调参 | 待实测 | MODULE_DESIGN.md ⑦ |
| 6 | `queryRowLimit` / 超时 / 并发的默认值，需实测定 | 待实测 | MODULE_DESIGN.md ⑥ |
| 7 | 商业模型 / 价值链锚点如何量化沉淀（原则⑥ 轻量版的具体形态） | 待细化 | MODULE_DESIGN.md ⑩ |
| 8 | 上下文压缩的阈值与摘要方式（何时压、压到多细） | 待实测 | MODULE_DESIGN.md ⑮ |
| 9 | 多轮澄清的交互形态（CLI 交互 vs 桌面 UI） | 待定 | MODULE_DESIGN.md ⑮ |
