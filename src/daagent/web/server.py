"""Web 壳：FastAPI 服务，把 agent 核心暴露成 HTTP API（三栏 UI 的后端）。"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from daagent.db.chat import ChatStore
from daagent.orchestration import run_structured

app = FastAPI(title="数据分析 Agent")


class ChatRequest(BaseModel):
    question: str
    model: str | None = None


@app.post("/api/chat")
def chat(req: ChatRequest):
    r = run_structured(req.question, model=req.model)
    store = ChatStore()
    store.save("web", "user", req.question)
    store.save("web", "agent", r["answer"])
    return r


@app.get("/api/sessions")
def sessions():
    store = ChatStore()
    return {"messages": [{"role": r, "content": c} for r, c in store.load("web", limit=50)]}


@app.get("/api/tools")
def tools():
    return {
        "tools": ["search_knowledge", "list_tables", "describe_table", "execute_query", "record_concept"]
    }


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
