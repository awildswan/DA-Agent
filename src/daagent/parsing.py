"""解析 LLM 输出：SQL 围栏 / JSON（结构化结论 / 概念）。"""

import json
import re


def _extract_sql(text: str) -> str:
    """从 LLM 输出里取 SQL：剥掉 ```sql 围栏与行尾分号。"""
    text = text.strip()
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
    return text.strip().rstrip(";").strip()


def _parse_json(text: str) -> dict | None:
    """解析 LLM 输出的 JSON（剥掉 ```json 围栏）。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _parse_conclusion_json(text: str) -> dict:
    """解析结构化结论，失败时给兜底（不 crash）。"""
    data = _parse_json(text)
    if not isinstance(data, dict) or not data.get("answer"):
        return {"answer": "（结论解析失败）", "numbers": {}, "entities": []}
    return {
        "answer": str(data["answer"]),
        "numbers": data.get("numbers") or {},
        "entities": data.get("entities") or [],
    }


def _parse_concept_json(text: str) -> dict | None:
    data = _parse_json(text)
    if isinstance(data, dict) and data.get("concept"):
        return {"concept": data["concept"], "definition": data.get("definition", "")}
    return None
