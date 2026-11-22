# 开发环境与流程（DEVELOPMENT）

> 编号：03-development/DEVELOPMENT · 版本 v0.2 · 2026-11-22 · 状态：Draft

## 环境要求

- Python 3.12+（本仓库用 3.12 验证）
- [uv](https://docs.astral.sh/uv/)（依赖管理）

## 快速开始

```bash
uv sync                    # 建 .venv + 装依赖
uv run python -m daagent   # smoke：验证环境（不调 LLM），打印 SMOKE OK
uv run python -m daagent ask "华东区11月订单量"   # V0.1：问一句 → 生成 SQL → 执行 → 返回
uv run pytest              # 跑测试
uv run ruff check          # lint
```

## 主模型（DeepSeek）

复制 `.env.example` 为 `.env`，填入真实 key：

- `OPENAI_API_KEY` = 你的 DeepSeek key
- `OPENAI_API_BASE` = `https://api.deepseek.com`
- `DEEPSEEK_MODEL` = `deepseek-chat`

## 目录结构

```
daagent/          # 包（核心无头可跑）
├── __main__.py   # smoke 入口
├── config.py     # pydantic-settings
├── runner.py     # 14 环节循环（骨架）
├── skills/ delivery_check/ okf/ evals/ tracing/ db/   # 模块（骨架）
tests/            # pytest
docs/             # 文档体系
```

## 本机注意

- 若 C 盘空间不足（uv 缓存默认在 C 盘），把缓存指到 D 盘（PowerShell）：
  `$env:UV_CACHE_DIR = "D:\vsgaia\.uv-cache"`
- 数据全本地：SQLite（元数据）+ DuckDB（查询）+ OKF（git）；凭据走 `.env`，不进仓库。
