# 0001. 用 ADR 记录架构决策

- **状态**：Accepted
- **日期**：2026-11-21

## 背景

本项目会持续做出影响架构的决策（技术栈、交付形态、评测标准等）。这些决策若不记录，几个月后没人知道「当时为什么这么选」（对齐 DLC「所有重要决策都要留痕」）。

## 决策

用轻量 ADR（Michael Nygard 风格，三段式）记录每个重大架构决策：

1. **编号**：`NNNN-<slug>.md`，四位递增；
2. **结构**：背景（Context）→ 决策（Decision）→ 后果（Consequences）；
3. **状态**：Accepted / Superseded / Withdrawn（不删除，只改状态，Git 保留历史）；
4. **索引**：`docs/adr/README.md` 维护编号 + 标题 + 状态表。

**准入门槛（ADR Gate）**：满足以下**之一**才记 ADR——① 难以逆转；② 脱离上下文会令人意外；③ 存在真实取舍。约束（如「只有 DeepSeek key」）与范围（如「多 Agent 留 V2」）记进 DESIGN / PRD，不占 ADR。

## 后果

- 正面：决策可追溯、可被后来者复核；`docs/adr/README.md` 是决策总览。
- 代价：每做一个大决策要写一段；三段式很短，成本低。
