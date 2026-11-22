# 技术栈（TECH_STACK）

> 编号：02-design/TECH_STACK · 版本 v0.1 · 2026-11-22 · 状态：Draft
> 决策记录见 [ADR-0002](../adr/0002-python-langchain-core-custom-loop.md)、[ADR-0003](../adr/0003-tauri-python-sidecar.md)。

## 选型

| 层 | 选型 | 理由 |
|---|---|---|
| 语言 | Python（后端 / 核心） | 胜负手在 Python 生态：`sqlglot` / `SQLAlchemy` / `DuckDB` / `pandas` / `sentence-transformers` |
| 模型 / 工具 / MCP 抽象 | `langchain-core` + `langchain-openai`（配 DeepSeek 兼容端点，或 `langchain-deepseek`）+ `langchain-mcp-adapters` | DeepSeek 主模型（OpenAI 兼容 API）；多 provider 作后续扩展 |
| **循环 / 编排** | **自写（显式状态机）** | 循环就是产品：交付闸门 / 自纠环 / 知识写回是领域逻辑，框架给不了 |

## 明确不用

- **LangGraph**：graph / checkpoint 对我们是过度抽象。daw 的自纠是「in-context 续跑」不是「checkpoint 恢复」；状态真相是 OKF 知识库 + 会话，不是 graph state；要审计就 SQLite 落一条（comet 的 State⊥Process 做法）。将来真要**多 Agent 编排**再上不迟。
- **完整 LangChain 高级 agent**：链式 / AgentExecutor 那套抽象会和自写闸门打架，只取 `langchain-core` 原语。
- **Pi**：TS + coding-agent 动作空间，双重不匹配。

## 备选与边界

- **备选**：`pydantic-ai`（类型化工具 / 结果更现代）作为可替换项；暂不选是「贴近 comet + MCP 成熟度」优先。
- **DSH 定位**：DSH 仅为本项目开发时使用的 coding 工具，**不是目标平台 / 底座**。
- **主模型**：DeepSeek（OpenAI 兼容 API，`langchain-openai` 配 base_url 或 `langchain-deepseek`）；多 provider 作后续扩展。
