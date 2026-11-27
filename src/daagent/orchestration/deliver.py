"""交付编排：闸门 + 自纠环 + 答案格式化（应用层 ② 的交付状态机）。"""

from langchain_core.messages import HumanMessage

from daagent.agent.react import run_react
from daagent.delivery_check.guards import RedFlag, run_guards, truth_check
from daagent.parsing import _parse_conclusion_json


def _truths(con, declarations):
    ts = []
    for t in declarations.truth_checks:
        try:
            con.execute(t.sql)
            ts.append((t.label, float(con.fetchone()[0] or 0), t.tolerance))
        except Exception:  # noqa: BLE001  # 该真值 SQL 不适用于当前数据源，跳过
            pass
    return ts


def _check(structured: dict, declarations, truths) -> list[RedFlag]:
    reds = run_guards(structured, declarations)
    numbers = structured.get("numbers", {}) or {}
    for label, tv, tol in truths:
        f = truth_check(numbers, label, tv, tol)
        if f:
            reds.append(f)
    return reds


def _deliver_round(llm_with_tools, messages, tools_by_name, check, max_rounds: int = 2, stats: dict | None = None, on_event=None):
    """一轮：ReAct → 闸门 → 自纠。返回 (structured, reds)。"""
    text = run_react(llm_with_tools, messages, tools_by_name, stats=stats, on_event=on_event)
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
        text = run_react(llm_with_tools, messages, tools_by_name, stats=stats, on_event=on_event)
        structured = _parse_conclusion_json(text)
    return structured, reds


def _fmt_answer(answer: str, reds: list[RedFlag]) -> str:
    if reds:
        return answer + "\n⚠️ 自纠后仍有 " + "；".join(r.message for r in reds) + "（请人工复核）"
    return answer
