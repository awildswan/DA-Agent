# 开发环境与流程（DEVELOPMENT）

> 编号：03-development/DEVELOPMENT · 版本 v0.3 · 2026-11-26

## 环境要求

- Python 3.12+（本仓库用 3.12 验证）
- [uv](https://docs.astral.sh/uv/)（依赖管理）
- 可选（打包用）：Node.js 22（Tauri CLI）、Rust（Tauri 壳）、PyInstaller

## 快速开始

```bash
uv sync                          # 建 .venv + 装依赖
uv run python -m daagent         # smoke：验证环境（不调 LLM），打印 SMOKE OK
uv run python -m daagent ask "有效订单有多少"   # 单次问答
uv run python -m daagent chat                    # 交互多轮
uv run python -m daagent web                     # 浏览器 UI（http://127.0.0.1:8000）
uv run python -m daagent desktop                 # 原生桌面窗口
uv run pytest                    # 跑测试
uv run ruff check                # lint
```

## 主模型（DeepSeek）

复制 `.env.example` 为 `.env`，填入真实 key：

- `OPENAI_API_KEY` = 你的 DeepSeek key
- `OPENAI_API_BASE` = `https://api.deepseek.com`
- `DEEPSEEK_MODEL` = `deepseek-flash`（或 `deepseek-v4-pro`）

## 目录结构

```
src/daagent/          # 包（核心无头可跑）
├── __main__.py       # CLI：smoke / ask / chat / web / desktop / eval / eval-spider / review
├── config.py         # pydantic-settings（冻结感知 .env）
├── orchestration/    # 编排：run/chat + 交付闸门/自纠
├── agent/            # 核心：ReAct 循环 / 诊断 / 上下文压缩
├── tools/            # 工具注册表（知识/数据库/用户交互，插拔）
├── models/           # 模型抽象（主/快模型可切换）
├── web/              # FastAPI + 三栏前端 + SSE 流式
├── db/               # 示例库 / 会话持久化 / 查询
├── okf/              # 知识库（git 版本化）
├── delivery_check/   # 值域 / 关系 / 核对 SQL 真值
├── skills/           # SQL 守卫
├── tracing/          # trace / transcript
└── evals/            # L1/L2 评测 + 复盘打分 + Spider
tests/                # pytest
docs/                 # 文档体系
scripts/              # 打包脚本（build_green.ps1 / server_entry.py / launcher.py）
src-tauri/            # Tauri 桌面壳（Rust）
```

## 本机注意

- 若 C 盘空间不足（uv 缓存默认在 C 盘），把缓存指到 D 盘（PowerShell）：
  `$env:UV_CACHE_DIR = "D:\vsgaia\.uv-cache"`
- 数据全本地：SQLite（会话）+ DuckDB（查询）+ OKF（git）；凭据走 `.env`，不进仓库。
- 打包脚本见 `scripts/build_green.ps1`（绿色版）与 `docs/05-deployment/DEPLOYMENT.md`。
