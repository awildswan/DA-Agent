# 部署与打包（DEPLOYMENT）

> 编号：05-deployment/DEPLOYMENT · 版本 v0.1 · 2026-11-22 · 状态：Draft
> 开发 / 部署阶段填具体步骤；此处先记决策骨架（见 ADR-0003）。

## 形态

- 桌面应用：**Web 壳先行**（FastAPI + 静态三栏前端，V0.9a/b 已做，见 ADR-0007）；Tauri v2 打包（Python 核心作 sidecar，V0.9c），自动更新（`tauri-plugin-updater`）。
- 开发运行：`uv run python -m daagent web` → 打开 http://127.0.0.1:8000。

## 待部署时填

- 打包命令、签名密钥管理、更新清单（`updates/latest.json`）、只读账号配置、环境变量清单。
