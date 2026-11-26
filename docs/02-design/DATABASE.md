# 数据模型与数据来源（DATABASE）

> 编号：02-design/DATABASE · 版本 v0.1 · 2026-11-22 · 状态：Draft
> 评测标准三层见 [TEST_PLAN.md](../04-testing/TEST_PLAN.md)。

## 数据模型

### 分层：技术元数据 vs 业务知识（核心）

| 层 | 载体 | 内容 | 版本化 |
|---|---|---|---|
| 技术元数据 | SQLite `table_registry` | access_mode / table_type / status / connection | 否 |
| 业务知识 | OKF（git） | concepts / tables / selections / playbooks / users / 守卫声明 | 是 |

### 核心表（SQLite）

- **db_connections（数据源）**：connection_name、db_type、db_product、db_mode、credentials（加密）、…
- **table_registry（表元数据）**：id、workspace_path、connection_name、local_name、remote_schema、remote_table、db_type、db_product、db_mode、table_type（native / foreign）、access_mode（catalog / pushdown）、status、unavailable_reason、last_explored
- **chat（会话 / 消息元数据）**：session_id、task_id、role、content（原文）、tool_calls（json）、turn_usage、created_at；完整 transcript 另存 jsonl（`payload` 字段存结构化 SqlResult）
- **trace / span（可观测）**：trace_id、span_id、parent_span_id、环节、输入 / 输出摘要、tokens、cost、耗时、firstRow 指纹
- **eval_cases / eval_runs（评测）**：case_id、question、gold_sql、gold_result、notes（金牌复标）、run_id、model、passed、score

### OKF 知识块（git 版本化，文件即条目）

每个工作区一份 git 仓库，按类别分文件：

- `concepts/`：业务概念与口径映射；
- `tables/`：表卡（字段释义 + **守卫声明**：`允许 <列>: 值1…` / `禁止: …` / `关系: …` / `核对:SELECT…`）；
- `selections/`：选表经验（「按问题找表」地图）；
- `playbooks/`：任务协议（适用问题 + 数据源 + 交付结构 + 验证清单）；
- `users/`：用户画像（角色 / 观点 / 偏好 / 口径基准 / 已拍板决策 / 纠错记录）。

### 关键取舍

- 技术元数据放 SQLite（结构化枚举 / 查询），业务知识放 git（可回溯 / 对账 / diff 审计）——职责分离。
- trace 双表（trace + span）字段对齐 OTel，便于日后导出。
- 评测集业务数字不进开源仓库（放 `~/.daw/evals/cases/` 之外），金牌复标 SQL 钉在直查新鲜值。

### 实际实现（V1，简化于设计）

| 设计 | 实际实现 | 说明 |
|---|---|---|
| chat（含 tool_calls / turn_usage） | `db/chat.py` 的 chat 表（session_id / role / content） | 会话元数据简化，够用 |
| 完整 transcript 另存 jsonl | `tracing/transcript.py` → `data/transcripts.jsonl` | 含问题 + 工具调用事件 + 答案 + tokens + trace |
| trace / span 双表 | `tracing/tracer.py` 内存 span（不落库） | 每环节耗时 + tokens 出在答案末尾 |
| table_registry | 未实现（`db/sample.py` 硬编码三表） | V2 接真实多表时补 |

## 数据来源（已定：组合）

> 参考结论：daw（唯一同域）用**真实业务库 + 自建口径集**，不用任何公共 NL2SQL benchmark；comet 用**三层评测**（L1 自制集 + L2 C-MTEB + L3 HotpotQA）。据此定案「组合」：

1. **demo 数据**：Northwind / AdventureWorks（真实业务结构）+ 一层合成的「业务口径 + 陷阱」（模拟 daw 真实数据里的坑：时区漂移、同秒重复单、部门 ≠ 战区）。
2. **eval 分两层**：
   - **L1 自制业务口径集（重点，对齐 daw）**：数字命中 / 来源表标注 / 首句先答 / 口径正确 / 交付闸门红灯拦截——测「业务口径 + 交付形态」，这才是取数 Agent 真正的难点；
   - **L2 Spider / BIRD 子集（SQL 准确率回归）**：测 SQL 生成 / 执行准确率，附「诚实污染声明」。
3. **诚实污染声明**（借 comet）：公共 benchmark 只作系统设计对比，不作绝对水平断言。
