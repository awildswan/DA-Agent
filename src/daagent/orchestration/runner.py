"""编排入口：run()（一次性问答）+ chat()（交互多轮）。应用层 ② 的顶层流程。"""

from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from daagent.agent.diagnose import _append_diagnosis, _diagnose
from daagent.db.chat import ChatStore
from daagent.db.sample import sample_db
from daagent.delivery_check.declarations import DEFAULT_GUARDS_CONTENT, build_declarations
from daagent.models import build_llm
from daagent.okf.store import OkfStore
from daagent.orchestration.deliver import _check, _deliver_round, _fmt_answer, _truths
from daagent.prompts import load_prompt
from daagent.tools import build_tools
from daagent.tracing.tracer import Trace


def run(question: str, okf_root: str | None = None) -> str:
    llm = build_llm()
    con = sample_db()
    okf = OkfStore(Path(okf_root) if okf_root else Path("data/okf"))
    if okf.read("guards", "orders") is None:
        okf.write("guards", "orders", DEFAULT_GUARDS_CONTENT)
    declarations = build_declarations(okf, con)
    tools, tools_by_name = build_tools(okf, con, interactive=False)
    llm_with_tools = llm.bind_tools(tools)
    truths = _truths(con, declarations)

    trace = Trace()
    stats = {"tokens": 0, "llm_calls": 0}
    messages = [SystemMessage(load_prompt("react")), HumanMessage(question)]
    with trace.span("ReAct+闸门+自纠"):
        structured, reds = _deliver_round(llm_with_tools, messages, tools_by_name, lambda st: _check(st, declarations, truths), stats=stats)
    answer = structured.get("answer", "（结论解析失败）")
    with trace.span("业务诊断"):
        answer = _append_diagnosis(answer, _diagnose(llm, question, answer))
    trace.tokens = stats["tokens"]
    trace.llm_calls = stats["llm_calls"]
    return _fmt_answer(answer, reds) + f"\n\n[trace] {trace.summary()}"


def chat() -> None:
    """交互式多轮对话：支持澄清（ask_user）+ 会话状态（追问引用前文）。"""
    llm = build_llm()
    con = sample_db()
    okf = OkfStore(Path("data/okf"))
    if okf.read("guards", "orders") is None:
        okf.write("guards", "orders", DEFAULT_GUARDS_CONTENT)
    declarations = build_declarations(okf, con)
    tools, tools_by_name = build_tools(okf, con, interactive=True)
    llm_with_tools = llm.bind_tools(tools)
    truths = _truths(con, declarations)
    check = lambda st: _check(st, declarations, truths)

    messages = [SystemMessage(load_prompt("react"))]
    store = ChatStore()
    history = store.load("default", limit=20)
    if history:
        review = "；".join(f"{r}: {c[:40]}" for r, c in history[-6:])
        messages.append(("system", f"[上次会话回顾] {review}"))
    print("数据分析 Agent（多轮对话，支持澄清）。输入 exit 退出。\n")
    while True:
        q = input("你: ").strip()
        if not q:
            continue
        if q.lower() in ("exit", "quit"):
            break
        store.save("default", "user", q)
        messages.append(HumanMessage(q))
        trace = Trace()
        stats = {"tokens": 0, "llm_calls": 0}
        with trace.span("ReAct+闸门+自纠"):
            structured, reds = _deliver_round(llm_with_tools, messages, tools_by_name, check, stats=stats)
        answer = structured.get("answer", "（结论解析失败）")
        with trace.span("业务诊断"):
            answer = _append_diagnosis(answer, _diagnose(llm, q, answer))
        trace.tokens = stats["tokens"]
        trace.llm_calls = stats["llm_calls"]
        store.save("default", "agent", answer)
        print(f"\nAgent: {_fmt_answer(answer, reds)}\n[trace] {trace.summary()}\n")
