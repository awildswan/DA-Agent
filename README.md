# daagent — 数据分析 Agent

> 大白话问数，带出处、带口径、带建议，越用越懂。

**定位**：一个数据分析 Agent——你像问同事一样用大白话问业务数据，它自己找表、写 SQL、算数字，把结果连同「怎么来的、意味着什么」一起给你，且只读、越用越懂。

**当前进度**：**V1 收尾**——15 环节全实现、60+ 测试、Spider 公开 benchmark 执行准确率 74%、桌面绿色版（解压即用）。详见 [`docs/06-roadmap/V1-SUMMARY.md`](docs/06-roadmap/V1-SUMMARY.md)。

**文档入口**：

- 用户视角：`docs/01-requirements/PROJECT_OVERVIEW.md`
- 设计文档：`docs/02-design/`（技术栈 / 原则 / 架构 / 模块 / 数据）
- 文档体系：`docs/README.md`
- 架构决策：`docs/adr/`（0001~0007）
- 术语表：`docs/glossary.md`
- V1 结项与 V2 方向：`docs/06-roadmap/V1-SUMMARY.md`

**运行方式**：

```bash
uv sync
uv run python -m daagent ask "有效订单有多少"   # 单次问答
uv run python -m daagent chat                  # 交互多轮（支持澄清）
uv run python -m daagent web                   # 浏览器 UI → http://127.0.0.1:8000
uv run python -m daagent desktop               # 原生桌面窗口（WebView2）
uv run python -m daagent eval                  # L1 + L2 评测
uv run python -m daagent eval-spider           # Spider benchmark 子集
uv run python -m daagent review                # 复盘打分
```

**技术栈**：Python + langchain-core（自写循环）+ DeepSeek；桌面壳 Tauri v2 + WebView2（Rust，备选 pywebview）；绿色版 PyInstaller 独立 sidecar。

**状态**：V1 收尾，活文档随迭代更新。
