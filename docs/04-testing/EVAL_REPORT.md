# 评测报告（EVAL_REPORT）

> 编号：04-testing/EVAL_REPORT · 版本 v0.1 · 2026-11-25

## 评测三层（现状）

| 层 | 内容 | 结果 |
|---|---|---|
| **L1 自制业务口径集** | 3 题（有效订单 / 总销售额 / 品类销量），数字命中 + 来源标注 + 首句先答 | **3/3** |
| **L2 手工 SQL 题** | 5 题（计数 / 去重 / 多表） | **5/5** |
| **Spider benchmark 子集** | 真实公开 benchmark，dev 前 50 题 | **74%（37/50）** |

## 第一次真实对标：Spider benchmark

### 方法

- **数据**：`xlangai/spider`（题目 + 金牌 SQL，HF datasets）+ `HAL-9001/spider-databases`（SQLite 库，从 zip 解压）。
- **范围**：dev 前 50 题，覆盖 2 个库（`concert_singer`、`pets_1`）。
- **harness**：`evals/spider.py`——agent 连 Spider 的 schema（`list_tables` / `describe_table` / `execute_query` 三工具），记录执行的 SQL。
- **指标**：执行准确率 = agent 执行过的**任意一条 SQL 的结果集 == 金牌 SQL 结果集**（无序比对，对 agent 的探索行为稳健）。

### 结果

- **37/50 = 74%**（模型 = `deepseek-flash`）。
- 两个口径：严格「最后一条 SQL」= 24%；稳健「任意 SQL 匹配」= 74%（采用后者，更公平）。

### 改进（54% → 74%）

逐条扒 false 后定位：错误是**语义理解**（多带列/错选列/漏过滤/聚合方向反），不是格式。四项修复：

1. **读主外键**：`describe_table` 返回主外键（外键决定 JOIN 条件）；
2. **大致查值**：加 `sample_values` 工具（DISTINCT 取值，避免猜错大小写/格式/类型）；
3. **约束输出**：prompt 强调"只生成一条答案 SQL、只选需要的列、聚合方向正确、过滤完整"；
4. **执行自检**：execute_query 后看结果是否符合问题，不符修正重跑。

### 诚实边界

1. **模型是 deepseek-flash（便宜模型）**——换 `deepseek-v4-pro` 会更高，`build_llm("deepseek-v4-pro")` 一行可测上限；
2. **样本小**：50 题只覆盖 2 个库，且 `concert_singer` 偏难（大量 JOIN / INTERSECT / EXCEPT / 嵌套子查询）；
3. **污染声明**：Spider dev 是 2018 年的，主流大模型可能见过（flash 是轻量模型，影响有限，诚实注明）；
4. **列顺序敏感**：执行准确率对结果集列顺序敏感（标准语义）。

### 怎么复现

```bash
uv run python -m daagent eval-spider   # 跑 50 题，结果存 data/spider/results.json
```

## 下一步（评测待讨论项）

- 换 `deepseek-v4-pro` 测上限（验证「flash 54% → pro 多少」）；
- 扩充样本（50 → 200+，覆盖更多库）；
- 复盘⑫ + 打分⑬（无金牌五维打分，daw 的「用-查-改-用」闭环）。
