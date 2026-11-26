# 部署与打包（DEPLOYMENT）

> 编号：05-deployment/DEPLOYMENT · 版本 v0.1 · 2026-11-22 · 状态：Draft
> 开发 / 部署阶段填具体步骤；此处先记决策骨架（见 ADR-0003）。

## 形态

- 桌面应用：**Web 壳先行**（FastAPI + 静态三栏前端，V0.9a/b）+ **pywebview 原生窗口**（V0.9c，WebView2，Windows 10/11 自带）；Tauri v2 打包（需 Rust + MSVC）与 PyInstaller 打 exe 是后续打包步骤（见 ADR-0003 / ADR-0007）。
- 运行方式：
  - `uv run python -m daagent web` → 浏览器打开 http://127.0.0.1:8000；
  - `uv run python -m daagent desktop` → 原生桌面窗口。

## Tauri 桌面壳（V0.9d）

- Rust 工具链装在工作区（`.cargo` / `.rustup`，不入库，`CARGO_HOME`/`RUSTUP_HOME` 指向工作区）。
- 编译：`cd src-tauri && cargo build --release` → `src-tauri/target/release/daagent-desktop.exe`（5.9 MB）。
- 安装包：`npx @tauri-apps/cli build --bundles nsis` → `src-tauri/target/release/bundle/nsis/daagent_0.1.0_x64-setup.exe`（1.44 MB）。
- 注意：该 exe 是"薄壳"，需本机 Python + daagent 包（启动时 spawn `python -m daagent web`）；真正 standalone 需 PyInstaller 打 sidecar。

## 待部署时填

- 打包命令、签名密钥管理、更新清单（`updates/latest.json`）、只读账号配置、环境变量清单。
