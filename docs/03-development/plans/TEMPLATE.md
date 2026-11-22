# Plan NNN: <结果句>

> **执行者须知**：逐步执行，每个 Verify 跑一遍并与预期比对；触发 STOP 就停下报告；完成后更新 `plans/README.md` 状态。

> **漂移检查（先跑）**：`git diff --stat <计划时 sha>..HEAD -- <本计划涉及路径>`，若与「当前状态」不符，STOP。

## 状态

- 里程碑：M?
- 规模：S | M | L
- 风险：LOW | MEDIUM | HIGH
- 依赖：plan NNN / open question Q?
- 计划于：`<sha>`，YYYY-MM-DD

## 为什么做

<一段：用户可见结果 + 对应 DESIGN / ADR 哪一节。>

## 当前状态

<现状，带路径。>

## 范围

**在范围内**：- ...

**不在范围内**：- ...

## 步骤

### Step 1: <标题>

<做什么、改哪些文件、对应 spec 哪节。>

**Verify:** `<命令>` → <预期结果>

## 测试计划

<单测 + E2E 场景。>

## 完成标准

- [ ] ...
- [ ] DESIGN / ADR / TASKS 同步更新
- [ ] `plans/README.md` 状态更新

## STOP 条件

- spec 事实有误 → 记 `docs/open-questions.md`
- 步骤需改协议 / 契约但计划没写
- 校验失败两次

## 维护备注

<后来者须知：捷径、后续工作。>
