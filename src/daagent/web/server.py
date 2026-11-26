"""Web 壳：FastAPI 服务，把 agent 核心暴露成 HTTP API（三栏 UI 的后端）。"""

import json
import queue
import threading
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from daagent.db.chat import ChatStore
from daagent.orchestration import run_structured

app = FastAPI(title="数据分析 Agent")


class ChatRequest(BaseModel):
    question: str
    model: str | None = None
    session_id: str | None = None


@app.post("/api/chat")
def chat(req: ChatRequest):
    r = run_structured(req.question, model=req.model)
    store = ChatStore()
    sid = req.session_id or f"session-{int(time.time() * 1000)}"
    store.save(sid, "user", req.question)
    store.save(sid, "agent", r["answer"])
    return {**r, "session_id": sid}


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    """SSE 流式：Thought → 工具调用事件 → 最终答案。"""
    q = queue.Queue()
    sid = req.session_id or f"session-{int(time.time() * 1000)}"

    def worker():
        try:
            r = run_structured(req.question, model=req.model, on_event=lambda e: q.put(e))
            store = ChatStore()
            store.save(sid, "user", req.question)
            store.save(sid, "agent", r["answer"])
            q.put({"type": "done", "session_id": sid, **r})
        except Exception as e:  # noqa: BLE001
            q.put({"type": "error", "message": str(e)})

    threading.Thread(target=worker, daemon=True).start()

    def gen():
        while True:
            e = q.get()
            yield f"data: {json.dumps(e, ensure_ascii=False)}\n\n"
            if e["type"] in ("done", "error"):
                break

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/sessions")
def sessions():
    return {"sessions": ChatStore().list_sessions()}


@app.get("/api/sessions/{sid}")
def session_messages(sid: str):
    return {"messages": [{"role": r, "content": c} for r, c in ChatStore().load(sid, limit=200)]}


@app.get("/api/tools")
def tools():
    return {
        "tools": ["search_knowledge", "record_concept", "list_tables", "describe_table", "execute_query"]
    }


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
