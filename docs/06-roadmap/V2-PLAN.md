# V2 计划（V2-PLAN）

> 编号：06-roadmap/V2-PLAN · 日期：2026-11-26 · 状态：计划（待用户确认起点后执行）

## 一、对材料的判断（成立 / 过时）

**成立（已核代码证据）**：

| 问题 | 证据 |
|---|---|
| db 层薄、连不了真实库 | `db/query.py` 6 行、`db/meta.py` 8 行、`db/sample.py` 73 行（7 条硬编码） |
| OKF 只整文件读写 | `okf/store.py` 68 行，无板块级 `upsert_block` |
| 打分器子串误判 | `evals/scorer.py` 用 `str(n) in answer`（1000 ⊂ 10000） |
| 工具异常被吞 | `agent/react.py` `except Exception` 吞成字符串 |
| 无时区固定 | 全仓无 `SET TimeZone` |
| 工具窄 | 仅 5 个（+ask_user），数据库类仅 3 个 |

**过时（V1 收尾 / 前端整改已补）**：

- README「尚未开始编码」→ 已改 V1 收尾。
- TEST_REPORT 空 → 已填（60 单测 + L1/L2/Spider 74%）。
- 「前端 49 行 demo」→ 已三栏 UI（会话切换 / 深度思考 / 折叠 trace / 会话菜单）。
- 「没有流式输出」→ 已 SSE 流式。
- 「973 行 / 58 测试」→ 1228 行 / 60 测试。

**结论**：材料的「地基优先」方向正确；「完成度极低」偏重——15 环节都实现了，但**真实数据能力为零**，这才是命门。

## 二、V2 分层计划

### V2.0 地基：真实数据 + 可靠性（P0，先做）

| 项 | 动作 | 验收 |
|---|---|---|
| TPC-H 数据集 | DuckDB `tpch` 扩展 `dbgen(sf=0.01)`（8 表，lineitem 6 万行）替代 7 行示例 | 能查真实星型数据、多表 JOIN |
| db 层 | 连接管理 + `SET TimeZone` + 多表 schema 探查 | 同 SQL 两次同数 |
| 工具 P0 | `sample_data`（看样例）+ `list_connections`（数据源列表） | 取数前能看真实样例 |
| fail-loud | react.py 工具异常结构化（错误类型 + 消息） | 失败有错误类型 |
| 知识库 | store.py 板块级 upsert（frontmatter 拒写 / 同名标题剥壳 / 空白归一化） | 误用不损坏知识库 |
| 打分 | scorer 精确匹配 + 容差；session_score 加确定性基线 | 不误判、可复现 |

### V2.1 度量：TPC-H 22 查询评测（P1）

- 22 标准查询 → 金牌 = DuckDB 直查真值（防 ETL 漂移）。
- 确定性打分作为基线（LLM 打分只作语义辅助）。

### V2.2 宽度：工具 + 可视化（P1/P2）

- `render_chart`（出图）。
- `create_view`（视图固化）。
- `search`（联网搜索）。

### V2.3 产品打磨（P2）

- 导出（CSV / 图片）。
- 多工作区 / 多会话。
- 前端宽度（图表、产物面板）。

## 三、不做 / 后置

- MCP 插件（P3）。
- 多 Agent 编排（V2 后期）。
- 真沙箱（先做超时 / 行数帽，进程隔离后置）。
