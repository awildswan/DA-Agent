# 0002. Python + langchain-core 底座 + 自写循环

- **状态**：Accepted
- **日期**：2026-11-21

## 背景

本 Agent 的核心是「取数 + 数据分析」，难点在 SQL 精确性、schema 检索、业务口径层、交付闸门、评测。底座有两条路线：用重编排框架（LangGraph / 完整 LangChain agent / Pi），或薄抽象 + 自写循环。

## 决策

- **语言**：Python（后端 / 核心）——SQL 侧生态（`sqlglot` / `SQLAlchemy` / `DuckDB` / `pandas` / `sentence-transformers`）是胜负手，TS 无对等。
- **模型 / 工具 / MCP 抽象**：`langchain-core` + `langchain-openai`（配 DeepSeek 兼容端点，或 `langchain-deepseek`）+ `langchain-mcp-adapters`。
- **循环 / 编排**：**自写显式状态机**，不用 LangGraph、不用完整 LangChain 高级 agent、不用 Pi。
- **主模型**：DeepSeek（OpenAI 兼容 API，用户唯一可用 key）；多 provider 作为后续扩展。

## 后果

- 正面：循环可控（交付闸门 / 自纠环 / 知识写回是领域逻辑，框架给不了）；与 comet（langchain-core 自写 Verifier-Loop）、daw（rig-core 自写 runner）同构。
- 代价：自写循环要自己维护状态机 / 重试 / 持久化；将来多 Agent 编排需再评估 LangGraph。
- 备选：`pydantic-ai`（类型化更现代）记为可替换项；如需更强类型化再迁移。
