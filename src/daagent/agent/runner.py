"""agent runner：ReAct 工具调用循环 + 交付闸门 + 自纠环 + 业务诊断。

run()：一次性问答（无澄清，用于评测）。
chat()：交互式多轮对话（有 ask_user 澄清 + 会话状态）。
"""

from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from daagent.agent.diagnose import _append_diagnosis, _diagnose
from daagent.agent.react import run_react
from daagent.config import get_settings
from daagent.db.query import _format_result
from daagent.db.sample import list_tables as db_list_tables, sample_db, schema_for_table
from daagent.delivery_check.declarations import DEFAULT_GUARDS_CONTENT, build_declarations
from daagent.delivery_check.guards import RedFlag, run_guards, truth_check
from daagent.okf.recall import _recall_concepts, _valid_concept
from daagent.okf.store import OkfStore
from daagent.parsing import _parse_conclusion_json
from daagent.prompts import load_prompt
from daagent.skills.sql import _guard
from daagent.tracing.tracer import Trace


def _make_tools(okf, con, interactive: bool = False):
    """构建工具集。interactive=True 时加 ask_user（澄清）。"""

    @tool
    def search_knowledge(query: str) -> str:
        """搜索已确认的业务口径。"""
        return _recall_concepts(okf) or "（知识库暂无已确认口径）"

    @tool
    def list_tables() -> str:
        """列出可用表。"""
        return "、".join(db_list_tables())

    @tool
    def describe_table(table: str) -> str:
        """返回指定表的 schema。"""
        return schema_for_table(table)

    @tool
    def execute_query(sql: str) -> str:
        """执行一条只读 SQL，返回结果行。"""
        _guard(sql)
        con.execute(sql)
        return _format_result(con, con.fetchall())

    @tool
    def record_concept(name: str, definition: str) -> str:
        """记录一个业务口径（概念 = 取数定义）。"""
        if not _valid_concept(name, definition):
            return "未记录（定义无效：空/自指/空泛）"
        okf.write("concepts", name, f"{name} = {definition}")
        return f"已记录：{name} = {definition}"

    tools = [search_knowledge, list_tables, describe_table, execute_query, record_concept]

    if interactive:

        @tool
        def ask_user(question: str) -> str:
            """业务口径或需求有歧义时，反问用户确认，返回用户的回答。"""
            return input(f"（需要你确认）{question}\n你: ")

        tools.append(ask_user)

    return tools, {t.name: t for t in tools}


def _truths(con, declarations):
    ts = []
    for t in declarations.truth_checks:
        con.execute(t.sql)
        ts.append((t.label, float(con.fetchone()[0] or 0), t.tolerance))
    return ts


def _check(structured: dict, declarations, truths) -> list[RedFlag]:
    reds = run_guards(structured, declarations)
    numbers = structured.get("numbers", {}) or {}
    for label, tv, tol in truths:
        f = truth_check(numbers, label, tv, tol)
        if f:
            reds.append(f)
    return reds


def _deliver_round(llm_with_tools, messages, tools_by_name, check, max_rounds: int = 2):
    """一轮：ReAct → 闸门 → 自纠。返回 (structured, reds)。"""
    text = run_react(llm_with_tools, messages, tools_by_name)
    structured = _parse_conclusion_json(text)
    for _ in range(max_rounds):
        reds = check(structured)
        if not reds:
            break
        messages.append(
            HumanMessage(
                "上一版结论被交付闸门拦下：" + "；".join(r.message for r in reds) + "。请修正后重新输出 JSON。"
            )
        )
        text = run_react(llm_with_tools, messages, tools_by_name)
        structured = _parse_conclusion_json(text)
    return structured, reds


def _build_llm():
    s = get_settings()
    return ChatOpenAI(
        model=s.deepseek_model,
        api_key=s.openai_api_key,
        base_url=s.openai_api_base,
        temperature=0,
    )


def _fmt_answer(answer: str, reds: list[RedFlag]) -> str:
    if reds:
        return answer + "\n⚠️ 自纠后仍有 " + "；".join(r.message for r in reds) + "（请人工复核）"
    return answer


def run(question: str, okf_root: str | None = None) -> str:
    llm = _build_llm()
    con = sample_db()
    okf = OkfStore(Path(okf_root) if okf_root else Path("data/okf"))
    if okf.read("guards", "orders") is None:
        okf.write("guards", "orders", DEFAULT_GUARDS_CONTENT)
    declarations = build_declarations(okf, con)
    tools, tools_by_name = _make_tools(okf, con, interactive=False)
    llm_with_tools = llm.bind_tools(tools)
    truths = _truths(con, declarations)

    trace = Trace()
    messages = [SystemMessage(load_prompt("react")), HumanMessage(question)]
    with trace.span("ReAct+闸门+自纠"):
        structured, reds = _deliver_round(llm_with_tools, messages, tools_by_name, lambda st: _check(st, declarations, truths))
    answer = structured.get("answer", "（结论解析失败）")
    with trace.span("业务诊断"):
        answer = _append_diagnosis(answer, _diagnose(llm, question, answer))
    return _fmt_answer(answer, reds) + f"\n\n[trace] {trace.summary()}"


def chat() -> None:
    """交互式多轮对话：支持澄清（ask_user）+ 会话状态（追问引用前文）。"""
    llm = _build_llm()
    con = sample_db()
    okf = OkfStore(Path("data/okf"))
    if okf.read("guards", "orders") is None:
        okf.write("guards", "orders", DEFAULT_GUARDS_CONTENT)
    declarations = build_declarations(okf, con)
    tools, tools_by_name = _make_tools(okf, con, interactive=True)
    llm_with_tools = llm.bind_tools(tools)
    truths = _truths(con, declarations)
    check = lambda st: _check(st, declarations, truths)

    messages = [SystemMessage(load_prompt("react"))]
    print("数据分析 Agent（多轮对话，支持澄清）。输入 exit 退出。\n")
    while True:
        q = input("你: ").strip()
        if not q:
            continue
        if q.lower() in ("exit", "quit"):
            break
        messages.append(HumanMessage(q))
        trace = Trace()
        with trace.span("ReAct+闸门+自纠"):
            structured, reds = _deliver_round(llm_with_tools, messages, tools_by_name, check)
        answer = structured.get("answer", "（结论解析失败）")
        with trace.span("业务诊断"):
            answer = _append_diagnosis(answer, _diagnose(llm, q, answer))
        print(f"\nAgent: {_fmt_answer(answer, reds)}\n[trace] {trace.summary()}\n")
