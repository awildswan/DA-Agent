# 任务清单（TASKS）

> 编号：03-development/TASKS · 版本 v0.4 · 2026-11-24

## 已完成

- [x] 借鉴研究（`RESEARCH_NOTES.md`）
- [x] 设计文档（`docs/02-design/`：TECH_STACK / PRINCIPLES / ARCHITECTURE / MODULE_DESIGN / DATABASE）
- [x] 文档体系（`docs/README.md` + ADR 0001~0004 + glossary / references / open-questions）
- [x] 工程初始化（Python 骨架 + uv 依赖 + smoke + pytest）
- [x] 精简 PRD（`docs/01-requirements/PRD.md`：功能优先级 + 验收标准）
- [x] 最小闭环（V0.1）：⑤生成 SQL → ⑥执行 → ⑨交付（接 DeepSeek，跑通）
- [x] 交付闸门 + 自纠环（V0.2/V0.3）：值域守卫 + 关系守卫 + 核对 SQL 真值 + 自纠 ≤2 轮 + 如实披露
- [x] OKF 知识库 + 守卫声明从 OKF 加载 + 候选全集 DISTINCT（V0.4）

## 进行中 / 待规划

- [ ] 核心取数链路（④穷尽探查 → ⑤生成 → ⑥执行）
- [ ] 语义层（①②⑪：召回 / 语义映射 / 沉淀，接 OKF）
- [ ] 业务诊断（⑩）
- [ ] 评测（L1 + L2）+ trace（⑫⑬⑭）
- [ ] 桌面壳 + 打包
- [ ] 多 Agent 编排（V2）
