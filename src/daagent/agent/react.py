"""ReAct 工具调用循环：LLM 决定调工具 → 执行 → 观察 → 重复，直到产出最终答案。"""

from langchain_core.messages import ToolMessage


def _extract_tokens(resp) -> int:
    """从 AIMessage 提取 token 数（langchain usage_metadata 或 response_metadata 兜底）。"""
    um = getattr(resp, "usage_metadata", None)
    if um:
        return int(um.get("input_tokens", 0) or 0) + int(um.get("output_tokens", 0) or 0)
    ru = (getattr(resp, "response_metadata", None) or {}).get("token_usage", {})
    return int(ru.get("prompt_tokens", 0) or 0) + int(ru.get("completion_tokens", 0) or 0)


def run_react(llm_with_tools, messages, tools_by_name, max_steps: int = 8, stats: dict | None = None, on_event=None):
    """循环直到 LLM 不再返回 tool_calls（即给出最终答案），或达到最大步数。

    stats（可选）：累计 {"tokens": int, "llm_calls": int}。
    on_event（可选）：每步工具调用回调 {"type": "tool_call"/"tool_result", ...}。
    """
    for _ in range(max_steps):
        resp = llm_with_tools.invoke(messages)
        messages.append(resp)
        if stats is not None:
            stats["tokens"] = stats.get("tokens", 0) + _extract_tokens(resp)
            stats["llm_calls"] = stats.get("llm_calls", 0) + 1
        if on_event:
            content = getattr(resp, "content", "") or ""
            if content:
                on_event({"type": "thought", "content": content})
        tool_calls = getattr(resp, "tool_calls", None)
        if not tool_calls:
            return resp.content
        for tc in tool_calls:
            name = tc.get("name")
            args = tc.get("args", {})
            if on_event:
                on_event({"type": "tool_call", "name": name, "args": args})
            tool = tools_by_name.get(name)
            try:
                result = tool.invoke(args) if tool else f"未知工具 {name}"
            except Exception as e:  # noqa: BLE001
                result = f"工具 {name} 执行失败：{e}"
            if on_event:
                on_event({"type": "tool_result", "name": name, "result": str(result)})
            messages.append(ToolMessage(content=str(result), tool_call_id=tc.get("id")))
    return "（达到最大步数，未给出最终答案）"
