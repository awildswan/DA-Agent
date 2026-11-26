# 测试报告（TEST_REPORT）

> 编号：04-testing/TEST_REPORT · 版本 v1.0 · 2026-11-26

## 单测

- `uv run pytest` → **60+ passed**（守卫 fail-loud / 解析 / OKF / 语义层 / ReAct / 多表 / 诊断 / 打分 / 工具注册表 / web 路由 / tracer / transcript）。
- 每条策略都配了"必踩"用例（禁词词边界、值域误报、写入守卫、执行准确率比对）。

## 评测（详见 [EVAL_REPORT.md](EVAL_REPORT.md)）

| 层 | 内容 | 结果 |
|---|---|---|
| L1 自制业务口径集 | 3 题（数字命中/来源/首句） | 3/3 |
| L2 手工 SQL 题 | 5 题（计数/去重/多表） | 5/5 |
| Spider benchmark 子集 | dev 前 50 题，执行准确率 | **74%（37/50）** |

## 复现

```bash
uv run pytest
uv run python -m daagent eval
uv run python -m daagent eval-spider
```

## 诚实边界

- 60+ 单测证明"已知规则被守住"，不证明"真实业务口径正确"（无真实业务库）。
- Spider 50 题只覆盖 2 库，样本小；模型是 deepseek-flash（换 v4-pro 可再提）。
