# daagent — 数据分析 Agent

> 大白话问数，带出处、带口径、带建议，越用越懂。

**定位**：一个数据分析 Agent——你像问同事一样用大白话问业务数据，它自己找表、写 SQL、算数字，把结果连同「怎么来的、意味着什么」一起给你，且只读、越用越懂。

**当前进度**：设计完成（`docs/02-design/`），文档体系已搭；尚未开始编码。

**文档入口**：

- 用户视角：`docs/01-requirements/PROJECT_OVERVIEW.md`
- 设计文档：`docs/02-design/`（技术栈 / 原则 / 架构 / 模块 / 数据）
- 文档体系：`docs/README.md`
- 架构决策：`docs/adr/`
- 术语表：`docs/glossary.md`

**技术栈**：Python + langchain-core（自写循环）+ DeepSeek；桌面壳 Tauri v2。

**状态**：架构设计可行（≠ 实现后可靠），活文档随实现迭代。
