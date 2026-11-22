# 借鉴研究笔记（Step 0 产物）

> **用途**：项目初始化前的借鉴研究，喂给后续 **Step 1（把设计做完，现已拆入 `docs/02-design/`）** 与 **Step 2（文档体系）**。
> **来源**：四个参考项目 `comet` / `daw` / `pi` / `AgentHerd` + 书目《深入理解 AI Agent：原理与工程实践》。
> **状态**：Draft · 待用户审阅（下文「第 5 节」的开放问题需你拍板后，才进入 Step 1）。

---

## 0. 结论速览（TL;DR）

四项目各有一个「最值钱」的强项，正好互补：

| 项目 | 定位 | 最值钱的借鉴（设计/架构） | 最值钱的借鉴（文档体系） |
|---|---|---|---|
| **comet** | AI 知识库 + 记忆助手 | Verifier-Loop 自校验、可观测 Tracing、独立 Eval 模块 | 能力域分目录 + 单篇 9 节统一模板 |
| **daw** | **Text-to-SQL 数据智能体**（唯一同域） | 交付闸门（机械对账）、技术元数据 vs 业务口径分层、静态/动态 prompt 分离 | AGENTS.md「复盘日志 + 纪律清单」写法 |
| **pi** | coding-agent harness | 契约包/运行时包分离、Eval 隔离 AB、显式信任边界(SECURITY) | AGENTS.md 作为「AI 协作硬规则」 |
| **AgentHerd** | agent 管家（Herder + ACP） | fail-toward-human 分层决策、角色分离 | **spec/adr/plans 三层文档 + 可执行计划模板** |

收敛出的**候选借鉴清单**（是否采纳由 Step 1/2 逐一决策，本节只列结论）：

- **设计 5 条**：① SQL 自校验 = 机械验证 + 独立 verifier + 红灯人工兜底；② schema 检索 + 语义层 = 「技术元数据 / 业务口径」双层；③ Eval = 独立模块 + 隔离 AB + 只读闸门；④ Trace = OTel 风格每步打 span；⑤ 只读安全 = 显式信任边界 + 禁词守卫 + 白名单 + fail-closed。
- **文档 4 条**：① 三层文档 spec/adr/plans（What/Why/How）；② AGENTS.md 硬规则；③ 可执行计划模板；④ glossary + open-questions + references + ADR index。

---

## 1. 书目结论：《深入理解 AI Agent》

- **身份**：《深入理解 AI Agent：原理与工程实践》v2.0（2026-09），李博杰著，312 页，10 章。配套代码仓 `github.com/bojieli/ai-agent-book`（chapter1–10 按章组织）。
- **核心公式**：**Agent = LLM + 上下文 + 工具**（大脑 + 眼睛 + 手脚）。上下文=观察/历史/记忆/状态；工具=感知/执行/协作/安全。
- **最关键概念「Harness」**：模型与外部环境之间的**中介层**，负责循环（loop）、状态管理、权限、校验、边界。书里反复强调：**让 Agent 变好的不是换更强模型，而是把 Harness 做对**（loop engineering、权限、评测、灰度）。
- **与我们最相关的章节**：
  - 第 1 章（Agent 基础 / ReAct / Harness）→ 我们的主循环骨架；
  - 第 4 章（工具 / MCP / 安全）→ 数据源连接、只读工具设计；
  - 第 7 章（Agent 评估：难度分级 / LLM-as-Judge / 失败归因 / benchmark→系统改进）→ 直接对应「生产四要素」里的 Eval；
  - 第 9 章（系统级优化：版本化 → 验证 → 灰度 → 回归）→ 直接对应「改 prompt/模型要跑回归」的工程闭环；
  - 第 10 章（多 Agent 协作：分工 / 沟通 / 失败模式）→ 决定 V1 是否要编排多 Agent。
- **对设计的指导**：我们的「SQL 自校验、只读安全、Trace 可观测」**都属于 Harness 层**，不是模型能力；把它们当成一等架构组件来设计，而不是事后补。

---

## 2. 设计 / 架构借鉴（候选清单）

### 2.1 SQL 自校验闭环 —— 三条腿合成

- **comet 的 Verifier-Loop**（`api/app/core/agent/loop/`）：`Verify⊥Generate`（独立 LLM session 审稿，可跨模型家族）+ `Controller⊥Task`（通用状态机）+ `State⊥Process`（状态落库可中断恢复、有 audit trail）。
- **daw 的交付闸门**（`src-tauri/.../delivery_check.rs`、`tools/eval_pipeline.py`）：用**机械规则**对账——值域守卫、关系守卫、核对 SQL 直查真值，红灯触发「带接地纪律的自纠环」，而非依赖模型自觉。
- **AgentHerd 的 fail-toward-human**（`docs/spec/04-herder.md`、`docs/adr/0007`）：guard list → rules → Reviewer → 人，**任何不确定/超时/不可读输出一律 escalate，而不是 allow**。

> **落到 Text-to-SQL**：生成 SQL 后走「危险操作拦截 → 语法/`EXPLAIN` 机械验证 → 独立 verifier 审语义 → 小样本试跑对真值 → 红灯重生成/转人工」，状态全程落库可回放。

### 2.2 Schema 检索 + 语义层 —— 「技术元数据 / 业务口径」双层

- **daw**（`docs/table-metadata-spec.md`）：`table_registry`（技术元数据：access_mode / table_type / connection）与 **OKF**（业务知识：字段释义、关联关系、排障记录）**明确分工**；OKF 用 **git 版本化 + 类别化 + 写入守卫 +「修正优先于并存」**（`okf/model.rs`、`store.rs`）。
- **comet**：`core/memory/ontology.py` 用**受控词表**约束类型；`core/agent/tools/registry.py` 工具注册中心 + 白名单开关。
- **AgentHerd**：`docs/spec/glossary.md` 统一术语表。

> **落到 Text-to-SQL**：把「几百张表的 schema 检索」和「活跃用户等业务口径」拆成两层；口径可配置、可 git 审计；schema 按问题裁剪只取相关表/字段，不整库塞 prompt。

### 2.3 Eval 评测 —— 独立模块 + 隔离 AB + 只读闸门

- **comet**（`api/eval/`）：与生产解耦、独立模型配置、双输出（指标表 + 逐条明细）、gold 集可复现。
- **pi**（`packages/evals/README.md`）：Docker 隔离跑 `with_docs / without_docs` **AB 对比算 lift**，报告区分 lift/负收益/饱和/flaky。
- **daw**：评测四件套 + **只读闸门**（评测只能读、不能写库）。

> **落到 Text-to-SQL**：建「NL 问题 → 标准 SQL → 标准结果」gold 集（思路参考 Spider/BIRD），核心指标 = SQL 执行准确率 + 结果正确率；可做「有口径 vs 无口径」AB；每次改 prompt/模型跑回归防退化。

### 2.4 Trace 可观测 —— OTel 风格每步打 span

- **comet**（`core/agent/tracing/`）：OTel GenAI 规范的 trace/span **双表模型**，`ContextVar` 自动 parent 关联，`asyncio.Queue` 批量异步落库不阻塞主流程，按模型单价核算成本。

> **落到 Text-to-SQL**：NL→澄清→schema 检索→SQL 生成→自校验→执行→结果，每步一个 span；字段对齐 OTel 便于日后导出；顺带做 token/成本核算。

### 2.5 只读安全 —— 显式信任边界 + 禁词守卫 + fail-closed

- **pi**（`SECURITY.md`）：**显式写清信任边界与 out-of-scope**（含 prompt injection 属已知不可防护风险）。
- **daw**（`skill/data_analysis/mod.rs`）：**只读禁词守卫**（DDL/DML 拦截）+ SQL 错误分类器对症建议。
- **comet**：工具白名单 + 只读连接强制。
- **AgentHerd**：fail-closed（不确定就拒绝/上报）。

> **落到 Text-to-SQL**：只读账号兜底 + `DROP/DELETE/UPDATE/ALTER` 等直接拦截 + 行级权限 + 敏感列脱敏 + 超时/LIMIT/并发控制 + 把 prompt injection 作为「已知风险」写进 SECURITY。

### 2.6 架构分层 —— 核心最小 + 契约/运行时分离

- **pi**：契约包（`schema`/`telemetry`/协议）与运行时包分离，能力靠扩展点外扩而非 core 堆积。
- **comet**：`controller → service → repository → model` 严格分层，横切能力按子系统放 `core/`。
- **AgentHerd**：`protocol` 零依赖契约，改契约须同步 spec+client+测试。

> **落到 Text-to-SQL**：SQL 方言/连接器适配、schema 检索/embedding、语义层、Agent 编排、Eval、Trace 各自独立成模块，核心最小；数据源与口径通过注册/插件扩展。

---

## 3. 文档体系借鉴（候选清单）

### 3.1 三层文档 spec / adr / plans —— **最值得整套借鉴**（AgentHerd）

- **spec = What**（`docs/spec/00-baseline`…`09-agent-tools` + `glossary.md` + `open-questions.md`）；
- **adr = Why**（`docs/adr/0001…` + `README.md` 索引，含 Accepted/Superseded/Withdrawn 状态）；
- **plans = How**（`plans/NNN-*.md` 可执行计划 + `README.md` 状态表）。
- **流转**：需求 → open-questions/spec 草稿 → ADR → plan → 执行，代码 + spec + 测试 + plan 状态**同 commit 变更**。
- 这与 `DLC.md` 的「需求 → 架构 → 详细设计」**可融合**（见第 5 节问题 2）。

### 3.2 AGENTS.md 作为「AI 协作硬规则」

- **pi**（全篇）：代码质量红线（tagged union、禁 `any`、只在信任边界做运行时校验）、命令约定、Git 安全、依赖安全、末段「User Override」。
- **daw**（全篇）：另一种范式——「复盘日志 + 纪律清单」，用真实翻车案例沉淀规则（现象 → 根因 → 修复 → 教训）。
- **AgentHerd**：单一规则源 + exporter 导出到各 agent config，冲突以 AGENTS.md 为准。

> **落到本项目**：把「SQL 校验规则、口径唯一来源、禁止直接执行非只读 SQL、测试/自检命令」写成仓库内 AI 必读规范。

### 3.3 可执行计划模板（AgentHerd `plans/TEMPLATE.md`）

- 结构：**Drift check（先 git diff 防漂移）→ Status → Why → Current state → Scope → Commands → Steps（每步带 Verify）→ Test plan → Done criteria → STOP conditions → Maintenance notes**。
- 天然适配「AI 多轮开发」：每步可验证、有明确停止条件、状态永不删除只更新。

### 3.4 单篇文档统一模板（comet 9 节）

`能力定位 → 解决问题 → 架构/数据流(Mermaid) → 核心设计与实现 → 关键取舍表 → 踩坑 → 面试问答 → 相关概念 → 可优化方向`；重头是**取舍表 + 问答**。能力域目录 + 数字前缀编号 + 总览维护指南。

### 3.5 术语表 + 待验证项 + 借鉴台账 + ADR 索引（AgentHerd）

- `glossary.md`：统一口径/指标/维度命名（对我们尤其重要——「活跃用户」这类口径的歧义源头）。
- `open-questions.md`：追踪 Eval 待验证项。
- `references.md`：**借鉴台账**（借鉴了谁、license、借了什么）——本笔记正是它的雏形。
- `docs/adr/README.md`：ADR 索引表 + 状态标记。

### 3.6 README 三段式 + 双语镜像

- **comet**：根 README（定位/架构图/快速开始/FAQ/目录/约定）+ 子目录 README（模块职责 + 迁移记录）。
- **AgentHerd**：README 英源 + zh-CN 镜像，同 commit 同步。

---

## 4. 各项目一句话定位（备忘）

- **comet**：多用户 AI 知识库 + 记忆助手；Agent 工具编排、自校验 Loop、评测、可观测四条主线与我们高度同构。
- **daw**：开源数据智能体工作台（Tauri + Rust + SolidJS），**对话式 Text-to-SQL + RAG 知识沉淀**，是唯一同域参考；「越用越懂」被做成了机制（git 版本化知识库 + 守卫 + 交付闸门 + 复盘脚本）。
- **pi**：极简可扩展 coding-agent harness（TS monorepo）；把「给 AI 的规范 + 契约化分层 + 隔离评测 + 确定性 CI + 供应链硬化 + 显式安全边界」做成可复制模板。
- **AgentHerd**：本地 coding-agent 管家（飞书 + Herder + ACP 统一接入多个 agent）；**不是多 agent 互协作，而是「一主管 + 统一协议 + 分层审批」监督并行 agent**；文档体系与治理最成熟。

---

## 5. 待你决策的开放问题（进入 Step 1 前需拍板）

1. **技术栈**：`DLC.md` 通篇假设「Python + AI Agent + RAG」；但四个参考项目多为 TS/JS/Rust。Text-to-SQL 后端主体用 **Python**（贴合 DLC 与 LLM/RAG 生态）还是其它？前端/交付形态另议。
2. **文档体系选型**：采用 `DLC.md` 的 `docs/01-requirements…05-deployment` 五类目录，还是 **AgentHerd 的 spec/adr/plans 三层**，还是**融合**（如 `docs/spec + docs/adr + docs/plans + 能力域目录`）？我的倾向：融合，spec/adr/plans 管「设计决策与计划」，能力域目录管「功能实现细节」。
3. **借鉴深度**：上面候选清单里，哪些「整套照搬」（如三层文档、计划模板），哪些「只借思想」（如 Verifier-Loop、OKF 知识库）？需要你圈定优先级。
4. **V1 范围**：以**单 Agent（Text-to-SQL）**为主，还是把多 Agent 编排（书目第 10 章 / comet 05 / AgentHerd 的 Herder）也纳入 V1 设计？
5. **交付形态**：Web 应用（comet 式前后端分离）？CLI（pi 式）？桌面（daw 式）？这决定架构与文档里的部署章节。

---

*最后更新：待定 · 文档版本 v0.1（Draft）*
