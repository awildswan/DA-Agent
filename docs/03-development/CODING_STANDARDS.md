# 代码规范（CODING_STANDARDS）

> 编号：03-development/CODING_STANDARDS · 版本 v0.1 · 2026-11-22 · 状态：Draft
> 约定草案（项目初始化时细化）。核心是「把设计里的纪律编码成可执行规则」。

## 语言与工具

- Python 3.12+；uv 管依赖；ruff（lint + format）；pytest（测试）；sqlglot（SQL 解析）。

## 分层（对应 ARCHITECTURE.md 模块划分）

- `agent runner` / `skills` / `delivery_check` / `okf` / `eval` / `trace` / `db` 各自独立，核心最小。

## Prompt 纪律（对齐 daw）

- **静态 / 动态分离**：system prompt 字节稳定，每轮变化走 `<runtime_context>`。
- **每个事实只有一个 owner**：规则一处权威定义，其余一行引用。
- **守卫解析器测试用例必须来自真实翻车原文**（多行 / CTE / 中文过滤值），不测理想单行。

## SQL 只读纪律

- 禁词**词边界**匹配（`is_deleted` 不误伤），先抹字符串字面量；**宁误拦不漏放**。
- 评测只读闸门：`eval-` 任务写工具全拒。

## 测试纪律

- 每个守卫配 fail-loud 测试；改动 prompt 引用的工具名 / 类别枚举触发测试失败。
- 确定性测试：无 API key 时跳过 LLM 相关用例。
