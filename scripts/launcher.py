"""PyInstaller 入口：启动桌面窗口（FastAPI + pywebview）。"""

import multiprocessing

from daagent.web.desktop import desktop

if __name__ == "__main__":
    multiprocessing.freeze_support()
    desktop()
