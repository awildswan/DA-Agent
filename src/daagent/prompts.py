"""加载 prompt 模板（静态 prompt 与代码分离，便于版本管理 + 字节稳定）。"""

from pathlib import Path

_DIR = Path(__file__).parent / "prompts"

_FALLBACKS = {
    "sql": "你是数据分析助手。根据数据库 schema 把用户问题转成只读 SQL（仅 SELECT），只输出 SQL。",
    "conclude": '你是数据分析助手。输出 JSON：{"answer": "...", "numbers": {}, "entities": []}。',
    "correct": "你是数据分析助手。修正结论，输出同格式 JSON。",
    "concept": '你是数据分析助手。输出 JSON：{"concept": "名", "definition": "口径"}，无则 {"concept": null}。',
}


def load_prompt(name: str) -> str:
    p = _DIR / f"{name}.txt"
    return p.read_text(encoding="utf-8").strip() if p.exists() else _FALLBACKS[name]
