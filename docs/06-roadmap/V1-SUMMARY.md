# V1 阶段结项（V1-SUMMARY）

> 编号：06-roadmap/V1-SUMMARY · 日期：2026-11-26 · 状态：V1 收尾（V2 待规划）

## 一、V1 达成了什么

**一个能对话、会澄清、越用越懂、可评测、可打包的「数据分析 Agent」桌面应用。**

| 维度 | 状态 |
|---|---|
| **15 环节** | ①召回 ②澄清 ③规划 ④探查 ⑤生成 ⑥执行 ⑦闸门 ⑧自纠 ⑨交付 ⑩诊断 ⑪沉淀 ⑫复盘 ⑬打分 ⑭评测+trace ⑮会话上下文——**全部实现** |
| **代码分层** | 6 层成型（交互 web/ / 编排 orchestration/ / 核心 agent/ / 工具 tools/ / 模型 models/ / 持久化 db+okf） |
| **测试** | 60+ 单测，全绿 |
| **评测** | L1 自制 3/3、L2 手工 5/5、**Spider dev 前 50 题执行准确率 74%** |
| **复盘打分** | transcript 持久化 + LLM 五维加权打分 + 最弱维度→改进工单 |
| **交付形态** | CLI（ask/chat/review/eval/eval-spider）/ Web 三栏 UI（SSE 流式）/ pywebview 桌面窗口 / Tauri 壳 + NSIS 安装包 / **PyInstaller 绿色 ZIP（解压即用，不装 Python）** |

## 二、架构（环节 × 分层 双维）

- **垂直：15 环节**（业务流水线，回答"agent 做什么"）——见 `docs/02-design/MODULE_DESIGN.md`。
- **水平：6 层**（代码组织，回答"代码放哪"）——见 `docs/02-design/ARCHITECTURE.md`。

## 三、关键决策（ADR 0001-0007）

| ADR | 决策 |
|---|---|
| 0001 | 记录架构决策（ADR 制度） |
| 0002 | Python + langchain-core + 自写循环（不用 LangGraph） |
| 0003 | 桌面形态：Tauri v2 + Python sidecar（备选 pywebview） |
| 0004 | 数据来源组合 + 两层评测（L1 自制 + L2 公开 benchmark） |
| 0005 | 补充会话状态 + 上下文管理到设计（⑮） |
| 0006 | 借鉴通用 agent 分层：工具注册表 + 模型抽象（不照搬 6 层） |
| 0007 | Web 壳先行（FastAPI + SSE 流式），Tauri 打包后置 |

## 四、打包与部署

- **安装包**：Tauri NSIS `daagent_0.1.0_x64-setup.exe`（1.44 MB，装 Tauri 壳，需系统 Python）。
- **绿色版**：`scripts/build_green.ps1` → `dist/daagent-standalone-win64.zip`（**解压即用，不装 Python**；PyInstaller 独立 server + Tauri 壳）。
  - **打包规则**：排除 eval 依赖（datasets/pandas/pyarrow/huggingface_hub）；**不内置 .env**（用户自备 key 放 `daagent-server\.env`）。
- **CI/CD**：`.github/workflows/build.yml`（test → package → upload artifact）。

## 五、V1 诚实边界（哪些没做/没做好）

1. **评测**：Spider 只有 50 题（2 个库）；L2 手工集只有 5 题；复盘打分的"判别力校准/稳定性"未验证。
2. **前端**：三栏 UI 是"功能可用"级，交互复杂度、状态管理、错误兜底远未打磨（用户已明确要整改）。
3. **记忆**：用户画像（OKF users/）未实现；上下文压缩只是 helper，未接入 chat 循环。
4. **打包**：绿色版 102.9MB 偏大（瘦身空间）；Tauri 壳的自动更新未接。
5. **数据**：只有三表示例库，没有真实业务库；L1 只能验"自洽"，验不了"真实口径"。

## 六、V2 方向（宽度 × 深度）

V2 不再堆环节，转向两个维度：

- **宽度**：更多数据源（真实业务库 / 多 schema）、更多领域场景、更高的表/概念覆盖率；前端交互广度（多会话、多工作区、多产物类型）。
- **深度**：更深的分析能力（多步规划、归因、趋势/对比）、更完善的交付（图表、报告、可回放 trace）、更严谨的评测（扩大 benchmark、判别力校准）。

> V2 具体拆解由用户主导，本文档只记录 V1 的收尾状态与方向锚点。
