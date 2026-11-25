# 任务清单（TASKS）

> 编号：03-development/TASKS · 版本 v0.6 · 2026-11-24

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

## 进行中 / 待规划

- [ ] 评测 L2（Spider/BIRD 子集）+ trace（⑫⑬⑭）
- [ ] 桌面壳 + 打包
- [ ] 多 Agent 编排（V2）
