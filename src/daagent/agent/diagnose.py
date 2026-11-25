"""⑩ 业务诊断：结论 → 依据 → 建议 → 影响（按需，纯取数问题不诊断）。"""

from daagent.prompts import load_prompt


def _diagnose(llm, question: str, answer: str) -> str:
    resp = llm.invoke(
        [
            ("system", load_prompt("diagnose")),
            ("human", f"问题：{question}\n答案：{answer}"),
        ]
    )
    return resp.content.strip()


def _append_diagnosis(answer: str, diagnosis: str) -> str:
    """把诊断附到答案后（「无需诊断」或空则原样返回）。"""
    if diagnosis and "无需诊断" not in diagnosis:
        return f"{answer}\n\n{diagnosis}"
    return answer
