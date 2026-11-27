"""编排入口：run()（一次性问答）+ chat()（交互多轮）。应用层 ② 的顶层流程。"""

from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from daagent.agent.diagnose import _append_diagnosis, _diagnose
from daagent.db.chat import ChatStore
from daagent.db.datasource import get_datasource
from daagent.delivery_check.declarations import DEFAULT_GUARDS_CONTENT, build_declarations
from daagent.models import build_llm
from daagent.okf.store import OkfStore
from daagent.orchestration.deliver import _check, _deliver_round, _fmt_answer, _truths
from daagent.prompts import load_prompt
from daagent.tools import build_tools
from daagent.tracing.tracer import Trace
from daagent.tracing.transcript import TranscriptStore


def run(question: str, okf_root: str | None = None) -> str:
    """返回格式化答案（含 trace 行），供 CLI。"""
    r = run_structured(question, okf_root)
    return f"{r['answer']}\n\n[trace] {r['trace']}"


def run_structured(
    question: str,
    okf_root: str | None = None,
    model: str | None = None,
    on_event=None,
    deep_thinking: bool = False,
) -> dict:
    """返回结构化结果 {answer, trace, tokens, llm_calls}，供 web/eval。on_event 用于流式。"""
    events = []

    def emit(e):
        events.append(e)
        if on_event:
            on_event(e)

    llm = build_llm(model=model)
    ds = get_datasource()
    con = ds.con
    okf = OkfStore(Path(okf_root) if okf_root else Path("data/okf"))
    if okf.read("guards", "orders") is None:
        okf.write("guards", "orders", DEFAULT_GUARDS_CONTENT)
    declarations = build_declarations(okf, con)
    tools, tools_by_name = build_tools(okf, ds, interactive=False)
    llm_with_tools = llm.bind_tools(tools)
    truths = _truths(con, declarations)

    system_prompt = load_prompt("react")
    if deep_thinking:
        system_prompt += (
            "\n\n【深度思考】先仔细分析问题（拆解子问题、考虑边界与口径歧义），"
            "再决定调用哪些工具，最后再给答案。"
        )

    trace = Trace()
    stats = {"tokens": 0, "llm_calls": 0}
    messages = [SystemMessage(system_prompt), HumanMessage(question)]
    with trace.span("ReAct+闸门+自纠"):
        structured, reds = _deliver_round(llm_with_tools, messages, tools_by_name, lambda st: _check(st, declarations, truths), stats=stats, on_event=emit)
    answer = structured.get("answer", "（结论解析失败）")
    with trace.span("业务诊断"):
        answer = _append_diagnosis(answer, _diagnose(llm, question, answer))
    trace.tokens = stats["tokens"]
    trace.llm_calls = stats["llm_calls"]
    result = {
        "answer": _fmt_answer(answer, reds),
        "trace": trace.summary(),
        "tokens": trace.tokens,
        "llm_calls": trace.llm_calls,
    }
    # 持久化 transcript（供复盘⑫ / 打分⑬）
    TranscriptStore().save(
        {
            "question": question,
            "model": model,
            "events": events,
            "answer": result["answer"],
            "tokens": result["tokens"],
            "llm_calls": result["llm_calls"],
            "trace": result["trace"],
        }
    )
    return result


def chat() -> None:
    """交互式多轮对话：支持澄清（ask_user）+ 会话状态（追问引用前文）。"""
    llm = build_llm()
    ds = get_datasource()
    con = ds.con
    okf = OkfStore(Path("data/okf"))
    if okf.read("guards", "orders") is None:
        okf.write("guards", "orders", DEFAULT_GUARDS_CONTENT)
    declarations = build_declarations(okf, con)
    tools, tools_by_name = build_tools(okf, ds, interactive=True)
    llm_with_tools = llm.bind_tools(tools)
    truths = _truths(con, declarations)
    check = lambda st: _check(st, declarations, truths)

    messages = [SystemMessage(load_prompt("react"))]
    store = ChatStore()
    history = store.load("default", limit=20)
    if history:
        review = "；".join(f"{r}: {c[:40]}" for r, c, _ in history[-6:])
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
