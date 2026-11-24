"""ReAct 工具调用循环：LLM 决定调工具 → 执行 → 观察 → 重复，直到产出最终答案。"""

from langchain_core.messages import ToolMessage


def run_react(llm_with_tools, messages, tools_by_name, max_steps: int = 8) -> str:
    """循环直到 LLM 不再返回 tool_calls（即给出最终答案），或达到最大步数。"""
    for _ in range(max_steps):
        resp = llm_with_tools.invoke(messages)
        messages.append(resp)
        tool_calls = getattr(resp, "tool_calls", None)
        if not tool_calls:
            return resp.content
        for tc in tool_calls:
            name = tc.get("name")
            args = tc.get("args", {})
            tool = tools_by_name.get(name)
            try:
                result = tool.invoke(args) if tool else f"未知工具 {name}"
            except Exception as e:  # noqa: BLE001
                result = f"工具 {name} 执行失败：{e}"
            messages.append(ToolMessage(content=str(result), tool_call_id=tc.get("id")))
    return "（达到最大步数，未给出最终答案）"
