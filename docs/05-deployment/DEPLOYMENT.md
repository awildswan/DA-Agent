# 部署与打包（DEPLOYMENT）

> 编号：05-deployment/DEPLOYMENT · 版本 v0.1 · 2026-11-22 · 状态：Draft
> 开发 / 部署阶段填具体步骤；此处先记决策骨架（见 ADR-0003）。

## 形态

- 桌面应用：**Web 壳先行**（FastAPI + 静态三栏前端，V0.9a/b）+ **pywebview 原生窗口**（V0.9c，WebView2，Windows 10/11 自带）；Tauri v2 打包（需 Rust + MSVC）与 PyInstaller 打 exe 是后续打包步骤（见 ADR-0003 / ADR-0007）。
- 运行方式：
  - `uv run python -m daagent web` → 浏览器打开 http://127.0.0.1:8000；
  - `uv run python -m daagent desktop` → 原生桌面窗口。

## 待部署时填

- 打包命令、签名密钥管理、更新清单（`updates/latest.json`）、只读账号配置、环境变量清单。
