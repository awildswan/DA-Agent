"""模型层：LLM 构建抽象，主/快模型可切换。"""

from langchain_openai import ChatOpenAI

from daagent.config import get_settings


def build_llm(model: str | None = None, temperature: float = 0.0):
    """构建 LLM。model 为空时用 config 主模型；传 'deepseek-v4-pro' 等可切换。"""
    s = get_settings()
    return ChatOpenAI(
        model=model or s.deepseek_model,
        api_key=s.openai_api_key,
        base_url=s.openai_api_base,
        temperature=temperature,
    )
