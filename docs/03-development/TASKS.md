# 任务清单（TASKS）

> 编号：03-development/TASKS · 版本 v0.9 · 2026-11-26

## 已完成

- [x] 借鉴研究（`RESEARCH_NOTES.md`）
- [x] 设计文档（`docs/02-design/`：TECH_STACK / PRINCIPLES / ARCHITECTURE / MODULE_DESIGN / DATABASE）
- [x] 文档体系（`docs/README.md` + ADR 0001~0004 + glossary / references / open-questions）
- [x] 工程初始化（Python 骨架 + uv 依赖 + smoke + pytest）
- [x] 精简 PRD（`docs/01-requirements/PRD.md`：功能优先级 + 验收标准）
- [x] 最小闭环（V0.1）：⑤生成 SQL → ⑥执行 → ⑨交付（接 DeepSeek，跑通）
- [x] 交付闸门 + 自纠环（V0.2/V0.3）：值域守卫 + 关系守卫 + 核对 SQL 真值 + 自纠 ≤2 轮 + 如实披露
- [x] OKF 知识库 + 守卫声明从 OKF 加载 + 候选全集 DISTINCT（V0.4）
- [x] 语义层（V0.5）：①召回 + ⑪沉淀（写入守卫）+ ②轻量语义映射（澄清多轮留到交互 UI）
- [x] ReAct 工具调用循环（V0.6）：LLM 自主调 5 工具（查口径/列表/看结构/执行/记口径），pipeline → agent
- [x] 多表 + 探查 + 规划（V0.6）：三表示例库 + 动态 list_tables/describe_table + 多表 JOIN
- [x] 业务诊断（V0.7a）：结论→依据→建议→影响（诊断型按需，纯取数不打扰）
- [x] 评测 L1（V0.8a）：自制业务口径集 + 打分器（数字命中/来源标注/首句先答）+ 评测只读闸门，3/3 通过
- [x] 澄清多轮 + 会话状态（V0.7b）：ask_user 反问确认口径 + chat 模式 + 追问续前文
- [x] trace 基础版（V0.8b）：span 计时（每环节耗时，可观测的最小可用形态）
- [x] 评测 L2（V0.8c）：5 道手工 SQL 题（计数/去重/多表），5/5 通过
- [x] trace 完整版 + 会话持久化 + 上下文压缩（V0.8）：token 统计 / SQLite chat 表 / compact 摘要
- [x] 评测 L2 真实 Spider 子集（V0.8d）：下载 xlangai/spider 前 50 题，执行准确率 74%（四招修复后：主外键+查值+约束输出+自检，从 54% 提到 74%）
- [x] 借鉴通用 agent 分层（V0.8e）：工具注册表 tools/ + 模型抽象 models/ + 编排层 orchestration/（ADR-0006）
- [x] 评测报告（EVAL_REPORT.md）：L1/L2/Spider 三层结果 + 方法论 + 诚实边界
- [x] Web 壳（V0.9a）：FastAPI + 三栏 UI（导航/对话/产物面板），连 agent 核心
- [x] Web 流式（V0.9b）：SSE 工具调用卡片 + 思考过程实时推（run_react 加 on_event）
- [x] 复盘打分最小版（V0.8f）：transcript 持久化（jsonl）+ 确定性打分（4 维）+ review 命令

## 进行中 / 待规划

- [ ] 复盘⑫⑬ 完整版（LLM 五维打分 + 用-查-改-用闭环）
- [ ] Tauri 打包（V0.9c：Rust 壳 + sidecar + 自动更新，需装 Rust）
- [ ] 多 Agent 编排（V2）
