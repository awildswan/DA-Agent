"""桌面窗口：FastAPI（后台线程）+ pywebview 原生 WebView2 窗口。"""

import threading

import uvicorn
import webview

from daagent.web.server import app


def desktop() -> None:
    """启动本地服务 + 打开原生桌面窗口（WebView2，Windows 10/11 自带）。"""

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

    threading.Thread(target=run_server, daemon=True).start()
    webview.create_window("数据分析 Agent", "http://127.0.0.1:8000", width=1280, height=820)
    webview.start()
