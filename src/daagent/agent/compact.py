"""上下文压缩（⑮）：超长历史把前半部分总结成一条摘要。"""

from daagent.prompts import load_prompt


def _fmt(m) -> str:
    role = getattr(m, "type", None) or type(m).__name__
    content = getattr(m, "content", "") or ""
    return f"{role}: {content}"


def compact(messages, llm, keep_last: int = 6):
    """超长历史压缩：保留 system + 最近 keep_last 条，其余总结成一条摘要。"""
    if len(messages) <= keep_last + 4:
        return messages
    old = messages[1:-keep_last]
    text = "\n".join(_fmt(m) for m in old)
    summary = llm.invoke(
        [
            ("system", load_prompt("compact")),
            ("human", text),
        ]
    ).content
    return [messages[0], ("system", f"[历史摘要] {summary}")] + messages[-keep_last:]
