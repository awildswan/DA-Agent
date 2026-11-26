# 系统架构（ARCHITECTURE）

> 编号：02-design/ARCHITECTURE · 版本 v0.1 · 2026-11-22 · 状态：Draft

## 定位

**一句话**：一个**数据分析 Agent**——像你我一样「规划 → 拆解 → 多步调用工具 → 机械校验 → 自纠 → 交付 → 沉淀 → 越用越懂」；数据库与 SQL 是它的核心工具，不是它的全部。

**它不是**：单跳 NL2SQL 翻译器（问一句 → 翻一条 SQL → 回一个数）；也不是聊天 / 知识库 bot。

**它为什么特殊（决定一切设计）**：

1. 答案是「算」出来的，不是「生成」出来的——错一个 JOIN 全错，用户拿去做决策；
2. 用户只说业务语言（"定金""有效单"），不知道表 / 字段 / 口径——**语义映射是 agent 本职**；
3. 数据口径是宪法——同一问题换表换写法必须同一答案（**唯一真相**）；
4. 会**越用越懂**——口径 / 字段释义 / 排障必须沉淀、可回溯、**修正优先于并存**。

## 核心循环（15 环节全景）

```
① 召回知识    search OKF：口径 / 语义 / 守卫声明 / 排障，新会话自动继承
② 语义映射    先给业务理解 + 口径让用户确认 / 纠正，确认即沉淀
③ 规划/拆解  多步问题拆子查询（对比 / 同比环比 / 多表对账 / 趋势+归因）
④ 穷尽探查   命名族扫描 → register / describe / sample；is_*/status_* 标记；权限 ≠ 不存在
⑤ 生成 SQL   方言 / 下推抽象（catalog vs pushdown）；静态 / 动态 prompt 分离
⑥ 执行       只读守卫（禁词词边界 / 裸引远端拦截 / 超时 / 行数上限）
⑦ 交付闸门   值域守卫 + 关系守卫 + 核对 SQL 直查真值 → 红灯
⑧ 自纠环     红灯 → in-context 续跑自纠（带接地纪律） → 复检，≤2 轮
⑨ 交付       先答所问 + 出处 + 业务结构；残留未消除则如实披露
⑩ 业务诊断   结果意味着什么 → 是否值得采取措施 → 建议 + 影响评估（标注依据）
⑪ 沉淀       修正优先于并存；git 版本化 + ±行数回执
⑫ [离线]复盘 review_transcript 找问题 → 配测试修复 → 再用验证
⑬ [离线]打分 五维 session_score → 最弱维度 = 下一个改进工单
⑭ 生产四要素 Eval / Trace / Deploy / Security 贯穿全程
⑮ 会话与上下文 会话记忆 / 上下文压缩 / 多轮状态 贯穿全程
```

**生产四要素如何贯穿**：

- **Eval**：⑪⑫ 离线评测 + 评测只读闸门 + 金牌复标 SQL（钉在直查新鲜值上）；
- **Trace**：①~⑨ 每环节打 span（OTel 风格），出错了逐帧回放定位；
- **Deploy**：Docker + 只读账号 + 超时 / LIMIT / 并发控制 + 模型失败降级转人工；
- **Security**：⑥ 只读守卫 + 行级权限 + 敏感列脱敏 + prompt injection 作为已知风险写明。

> 逐环节详细设计见 [MODULE_DESIGN.md](MODULE_DESIGN.md)。

## 架构决策

- **形态**：本地优先桌面应用（数据全在本机，无云端依赖），最终打包成可分发安装包。
- **核心 / 壳分离**：核心是**无头 Python**（可脱离 UI 独立跑评测），壳是桌面 webview——即 daw「Emitter 事件出口抽象 → 无头跑器」思路的顶层化。
- **桌面壳**：Web 壳先行（FastAPI + 静态三栏前端，V0.9a/b 已做）；Tauri v2 只是打包层（V0.9c，把 web 静态资源包进 Rust 壳 + Python sidecar）——见 ADR-0007。
- **备选**：pywebview + PyInstaller（单语言更轻，但打包更大、无自动更新）——记入 ADR 取舍。

## 模块划分（C4 Level 2）

```
┌────────────────────────── 桌面应用 ──────────────────────────┐
│  壳（Tauri v2）                                              │
│   ├─ 前端 webview：聊天 UI / 工作区 / 设置 / 图表(ECharts)    │
│   └─ Rust 壳：窗口 / 更新器(tauri-plugin-updater) / 品牌      │
│        ▲ invoke / event（IPC：stdio / 本地 socket）           │
│  Python 核心（sidecar，无头可驱动）                           │
│   ├─ orchestration（run/chat 编排 + 交付闸门/自纠）           │
│   ├─ agent（ReAct 循环 / 诊断 / 上下文压缩）                  │
│   ├─ tools（工具注册表：知识/数据库/用户交互，插拔）          │
│   ├─ models（模型抽象：主/快模型可切换）                      │
│   ├─ web（FastAPI + 三栏前端 + SSE 流式）                     │
│   ├─ skills（SQL 守卫：禁词/字面量抹除）                      │
│   ├─ delivery_check（值域 / 关系 / 核对 SQL 真值）            │
│   ├─ okf（知识库：写入守卫 / 版本化 / 体检）                  │
│   ├─ eval（无头跑器 + 打分器 + 评测集）/ trace（span 双表）   │
│   └─ db（连接抽象：SQLite 元数据 + DuckDB 查询）              │
│        │                                                     │
│  SQLite（元数据）  DuckDB in-memory（查询/视图）  OKF（git）  │
│        │                                                     │
│  外部：DeepSeek（主模型）· 数据源（见 DATABASE.md）           │
└──────────────────────────────────────────────────────────────┘
```

## 数据流（一次取数的端到端）

用户消息 → 壳 UI → HTTP/SSE → web server → orchestration：① 召回 OKF → ② 语义映射（可能反问用户）→ ③ 规划 → ④ 探查 schema → ⑤ 生成 SQL（langchain-core）→ ⑥ 执行（DuckDB / 下推）→ ⑦ delivery_check → ⑧ 自纠（≤2 轮）→ ⑨ 交付 → ⑩ 业务诊断 → ⑪ 沉淀 OKF（git commit）→ 回传 UI（SSE 流式推工具调用事件）+ trace span 落库。

## 关键取舍

- **核心 / 壳分离为什么是必须**：评测需要无头跑器（eval 不能依赖 UI），复现需要可无头驱动；壳只是 view 层，核心才是产品。
- **Tauri vs pywebview**：Tauri 打包小、有自动更新、贴近 daw；代价是引入 Rust 壳 + sidecar IPC。pywebview 单语言但 PyInstaller 打包大、无自动更新。V1 选 Tauri；嫌复杂度可降级 pywebview（核心不变）。
- **DuckDB 双角色**：既是「本地验证 SQL」的执行引擎（评测 / 试跑），又是「查询会话」的 in-memory 引擎——与 daw 一致。
