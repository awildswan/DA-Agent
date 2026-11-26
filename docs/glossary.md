# 术语表（Glossary）

> 编号：glossary · 版本 v0.1 · 2026-11-22 · 状态：Draft
> 统一口径 / 指标 / 维度命名。新增术语先查这里；同名不同义必须显式定义（对齐 daw「每个事实只有一个 owner」）。

## 业务口径类

| 术语 | 定义 | 说明 |
|---|---|---|
| 口径 | 一个指标的计算规则（统计对象 + 时间范围 + 过滤条件 + 去重方式） | 同一指标换口径结果不同 |
| 有效单 / 有效成交 | 剔除测试单、取消单、0 元单后的成交 | 默认报有效口径（原则③） |
| 业务叫法 vs 物理表名 | 用户说的「业绩」 vs 库里 `dw_gmv_order` | 交付时两段式都给 |
| 语义映射 | 口头表达 → 业务模型 → 数据表达（表 / 字段 / 筛选） | agent 本职（原则②） |

## 架构类

| 术语 | 定义 |
|---|---|
| OKF | 工作区知识库（业务知识：concepts / tables / selections / playbooks / users / 守卫声明），git 版本化 |
| table_registry | 技术元数据（access_mode / table_type / status / connection），存 SQLite |
| catalog vs pushdown | 两种访问模式：普通表走 catalog 视图，外表走 `postgres_query` 下推 |
| 交付闸门 | 交付前机械对账：值域守卫 + 关系守卫 + 核对 SQL 直查真值 |
| 值域守卫 | 结论实体 ∉ 声明允许值域 → 红灯 |
| 关系守卫 | 大数关系超容差且无解释 → 红灯 |
| 核对 SQL | 自纠前直查真值，把幻觉变「机械不可能」 |
| 自纠环 | 红灯 → in-context 续跑自纠 → 复检，≤2 轮 |
| 修正优先于并存 | 新结论推翻旧结论时改写，禁止新旧并存 |
| fail-loud | 外部副作用必须检查结果，失败进日志可归因 |
| 金牌复标 | 评测金牌用直查 SQL 复标，钉在新鲜值上（防 ETL 漂移） |
| firstRow 指纹 | 执行结果首行指纹，用于引擎级不确定性对账 |

## 记忆与上下文类

| 术语 | 定义 |
|---|---|
| 会话记忆（短期记忆） | 同一会话内临时保留的对话历史与中间状态；跨会话才沉淀 OKF |
| 上下文压缩 | 长会话超窗口时，把旧轮次总结成大纲而非逐字保留 |
| 上下文窗口 | LLM 单次可处理的 token 上限 |
| 多轮状态机 | 需用户回应的点（澄清 / 确认 / 纠正）做成显式状态：反问 → 等确认 → 继续 |

## 评测类

| 术语 | 定义 |
|---|---|
| L1 自制业务口径集 | 数字命中 / 来源标注 / 首句先答 / 口径正确 / 闸门红灯（对齐 daw） |
| L2 Spider / BIRD 子集 | SQL 生成 / 执行准确率回归（附诚实污染声明） |
| A/B 对照 | 闸门开 / 关、有口径 / 无口径、自纠开 / 关的对照实验 |

## 工程 / 打包类

| 术语 | 定义 |
|---|---|
| ReAct | LLM 自主决定调工具的循环（Thought / Action / Observation） |
| 工具注册表 | `tools/` 按域分组 + `build_tools()` 组装，工具插拔 |
| 模型抽象 | `models/build_llm(model=...)`，主 / 快模型可切换 |
| transcript | 一轮会话的完整记录（问题 + 工具调用 + 答案 + token + trace），供复盘打分 |
| 会话切换 | 前端多会话（session_id）切换与加载 |
| SSE | Server-Sent Events，流式推送工具调用事件（Thought/Action/Observation） |
| 绿色版 | 解压即用、不装 Python（PyInstaller sidecar + Tauri 壳，ZIP） |
| sidecar | 主程序旁的独立进程（Tauri 壳 → `daagent-server.exe`） |
| 复盘⑫ / 打分⑬ | 读 transcript 找问题 / LLM 五维加权打分 → 最弱维度 = 改进工单 |
| 深度思考 | 模型的思考模式开关（runner 在 prompt 追加"先分析再行动"指令） |
| 会话置顶 / 重命名 / 删除 | 会话管理操作（sessions 表：pinned / title） |
| 数据源解绑 | agent 不绑定单数据集，连哪个库用哪个（运行时 schema 发现） |
| TPC-H | 工业标准测试数据集（8 表星型模型，DuckDB 内置 `tpch` 扩展可生成） |
