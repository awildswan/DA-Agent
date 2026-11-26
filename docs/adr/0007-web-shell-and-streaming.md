# 0007. Web 壳先行（FastAPI + SSE 流式），Tauri 打包后置

- **状态**：Accepted
- **日期**：2026-11-26

## 背景

V0.9 桌面壳按 ADR-0003 是 Tauri v2 + Python sidecar。但 Tauri 要 Rust 工具链 + Node 构建，一次到位太重；且核心/壳分离本就要求"壳只是 view 层"。

## 决策

1. **先做 Web 壳**：FastAPI + 静态三栏前端（导航 / 对话 / 产物面板），核心仍是无头 Python——壳是 FastAPI 服务的 webview；
2. **流式用 SSE**：`run_react` 加 `on_event` → `/api/chat/stream` → 前端渲染工具调用卡片（思考过程 + 工具结果实时推）；
3. **Tauri 打包后置**（V0.9c）：把 web 静态资源包进 Rust 壳 + Python sidecar，前端代码可复用。

## 后果

- 正面：不依赖 Rust 就打通"对话框 + 工作控制台"，流式可视化 agent 的工具调用。
- 代价：Tauri 打包仍是待办；Web 壳与 Tauri 壳共用静态前端资源。
