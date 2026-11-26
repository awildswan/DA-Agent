# 文档体系（Documentation System）

> 本文档定义项目文档的结构、命名规则、统一模板与维护约定。遵循 `DLC.md`（五类文档 + 最少文档集），融合 AgentHerd 的 ADR 纪律。
> 版本 v1.0 · 2026-11-21 · 状态：Draft

## 一、结构总览

```
daagent/
├── README.md                     # 项目入口（定位 / 架构图 / 快速开始 / 进度）
├── RESEARCH_NOTES.md             # 借鉴研究笔记（Step 0 产物）
├── DLC.md                        # 规范（方法论，保留）
└── docs/
    ├── README.md                 # 本文档：文档体系总览 + 维护指南
    ├── adr/                      # 架构决策记录（ADR）
    │   ├── README.md             # ADR 索引 + 格式
    │   └── NNNN-<slug>.md
    ├── 01-requirements/          # 需求：要做什么
    │   ├── PROJECT_OVERVIEW.md
    │   └── PRD.md
    ├── 02-design/                # 设计（技术栈 / 原则 / 架构 / 模块 / 数据）
    │   ├── TECH_STACK.md
    │   ├── ARCHITECTURE.md
    │   ├── DATABASE.md
    │   └── MODULE_DESIGN.md
    ├── 03-development/           # 开发过程
    │   ├── DEVELOPMENT.md
    │   ├── CODING_STANDARDS.md
    │   └── TASKS.md
    ├── 04-testing/               # 测试
    │   ├── TEST_PLAN.md
    │   └── TEST_REPORT.md
    ├── 05-deployment/            # 部署
    │   └── DEPLOYMENT.md
    ├── 06-roadmap/               # 路线图与阶段结项
    │   └── V1-SUMMARY.md
    ├── prompts/                  # AI：prompt 版本管理
    │   └── README.md
    └── evaluations/              # AI：评测集设计
        └── README.md
```

## 二、每类装什么

| 目录 | 内容 | 何时写 |
|---|---|---|
| `adr/` | 技术决策及原因（编号 + 状态） | 每个重大决策 |
| `01-requirements/` | 项目概览 + 产品需求（PRD） | 设计阶段 |
| `02-design/` | 技术栈 / 原则 / 架构 / 模块 / 数据（设计主文档） | 设计稳定后 |
| `03-development/` | 开发环境 / 代码规范 / 任务清单 | 初始化时起步 |
| `04-testing/` | 测试策略 + 报告 | 测试前 / 后 |
| `05-deployment/` | 部署与打包 | 上线准备 |
| `06-roadmap/` | 路线图 / 阶段结项（V1 总结 + V2 方向） | 阶段收尾时 |
| `prompts/` | prompt 版本 + 变更记录 | 迭代期 |
| `evaluations/` | 评测集设计（三层标准） | 迭代期 |

## 三、统一文档头（DLC 规范）

每份正式文档开头必带：

| 字段 | 值 |
|---|---|
| 文档名称 / 编号 | … |
| 版本 / 日期 | v0.1 / YYYY-MM-DD |
| 作者 / 状态 | … / Draft · Review · Approved |
| 变更记录 | … |

## 四、最少文档集（V0 起步，DLC 原则）

1. `README.md`（初稿：定位 + 一句话目标 + 进度）
2. `docs/adr/`（ADR-0001 + 已定决策）
3. `docs/03-development/TASKS.md`（任务清单）
4. `.env.example`（环境变量模板）

## 五、维护约定

- **单一 owner**：每个事实只在一处权威定义，其余引用（对齐 daw「每个事实只有一个 owner」）。
- **设计统一在 `docs/02-design/`**：技术栈 / 原则 / 架构 / 模块 / 数据各自独立成文，单一 owner。
- **ADR 只记已定决策**：满足「难以逆转 / 脱离上下文令人意外 / 存在真实取舍」之一才进 ADR；约束与范围记进 `02-design` / `01-requirements`。
- **文档随迭代更新**：接口 / 表结构 / 任务状态改动时同步对应文档（对齐 DLC 更新同步表）。
