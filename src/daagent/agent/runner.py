"""agent runner：ReAct 工具调用循环 + 交付闸门 + 自纠环。

LLM 有工具集（查口径/列表/看结构/执行 SQL/记口径），自己决定调用顺序；最终输出结构化 JSON 结论，
交付闸门检查，红灯则 in-context 自纠（≤2 轮）。
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


def run(question: str) -> str:
    s = get_settings()
    llm = ChatOpenAI(
        model=s.deepseek_model,
        api_key=s.openai_api_key,
        base_url=s.openai_api_base,
        temperature=0,
    )
    con = sample_db()
    okf = OkfStore(Path("data/okf"))
    if okf.read("guards", "orders") is None:
        okf.write("guards", "orders", DEFAULT_GUARDS_CONTENT)
    declarations = build_declarations(okf, con)

    # —— 工具（LLM 可主动调用）——
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
            return f"未记录（定义无效：空/自指/空泛）"
        okf.write("concepts", name, f"{name} = {definition}")
        return f"已记录：{name} = {definition}"

    tools = [search_knowledge, list_tables, describe_table, execute_query, record_concept]
    tools_by_name = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    # 核对 SQL 真值（直查，进自纠做接地）
    truths = []
    for t in declarations.truth_checks:
        con.execute(t.sql)
        truths.append((t.label, float(con.fetchone()[0] or 0), t.tolerance))

    def check(structured: dict) -> list[RedFlag]:
        reds = run_guards(structured, declarations)
        numbers = structured.get("numbers", {}) or {}
        for label, tv, tol in truths:
            f = truth_check(numbers, label, tv, tol)
            if f:
                reds.append(f)
        return reds

    # —— ReAct 循环 + 闸门/自纠（≤2 轮）——
    messages = [SystemMessage(load_prompt("react")), HumanMessage(question)]
    text = run_react(llm_with_tools, messages, tools_by_name)
    structured = _parse_conclusion_json(text)

    for _ in range(2):
        reds = check(structured)
        if not reds:
            break
        messages.append(
            HumanMessage(
                "上一版结论被交付闸门拦下："
                + "；".join(r.message for r in reds)
                + "。请修正后重新输出 JSON。"
            )
        )
        text = run_react(llm_with_tools, messages, tools_by_name)
        structured = _parse_conclusion_json(text)

    answer = structured.get("answer", "（结论解析失败）")

    # ⑩ 业务诊断（按需：纯取数问题不打扰）
    answer = _append_diagnosis(answer, _diagnose(llm, question, answer))

    if reds:
        tail = "⚠️ 自纠后仍有 " + "；".join(r.message for r in reds) + "（请人工复核）"
    else:
        tail = ""

    return f"{answer}\n{tail}".strip()
