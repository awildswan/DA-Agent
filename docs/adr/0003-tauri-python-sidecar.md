# 0003. 桌面形态：Tauri v2 + Python sidecar

- **状态**：Accepted
- **日期**：2026-11-22

## 背景

交付形态定为桌面应用（最后打包）。核心是 Python，但桌面壳有多种选法。

## 决策

- **壳** = Tauri v2 + webview 前端；Python 核心作 **sidecar 进程**，经本地 stdio / socket IPC 通信。
- **核心 / 壳分离**：核心无头可驱动（评测无头跑器复用，对齐 daw 的 Emitter 抽象）。

## 后果

- 正面：打包小、自动更新（`tauri-plugin-updater`）、贴近 daw。
- 代价：引入 Rust 壳 + sidecar IPC（三语言）。
- 备选：pywebview + PyInstaller（单语言更轻、打包大、无自动更新）——嫌复杂度可降级，核心不变。
