"""ReAct 循环离线单测（mock LLM，不调真实模型）。"""

from langchain_core.messages import AIMessage

from daagent.agent.react import run_react


class _FakeTool:
    def __init__(self, name, result):
        self._name = name
        self._result = result

    def invoke(self, args):
        return self._result


class _FakeLLM:
    """第一次返回 tool_call，第二次返回最终答案。"""

    def __init__(self):
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        if self.calls == 1:
            return AIMessage(
                content="",
                tool_calls=[{"name": "execute_query", "args": {"sql": "SELECT 1"}, "id": "c1"}],
            )
        return AIMessage(content='{"answer": "1"}', tool_calls=[])


def test_run_react_calls_tool_then_final_answer():
    llm = _FakeLLM()
    tools = {"execute_query": _FakeTool("execute_query", "1")}
    text = run_react(llm, [], tools)
    assert text == '{"answer": "1"}'
    assert llm.calls == 2


def test_run_react_unknown_tool_does_not_crash():
    llm = _FakeLLM()
    tools = {}  # 工具不存在 → 给"未知工具"，继续循环
    text = run_react(llm, [], tools)
    assert llm.calls == 2  # 第二轮给最终答案
