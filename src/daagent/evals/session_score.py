"""会话打分：确定性五维基线（默认）+ LLM 语义辅助（可选）+ 复盘报告⑫。

基线必须确定性（同会话两次打分一致），LLM 打分只作语义辅助，不做基线。
"""

import re

from daagent.models import build_llm
from daagent.parsing import _parse_json
from daagent.prompts import load_prompt
from daagent.tracing.transcript import TranscriptStore

# 五维权重（对齐 MODULE_DESIGN ⑬）
_WEIGHTS = {"D1": 0.30, "D2": 0.15, "D3": 0.20, "D4": 0.10, "D5": 0.25}

_NEGATIVE = ("拿不准", "失败", "无法", "抱歉", "不知道")

_IMPROVEMENT_HINTS = {
    "D1": "强化 prompt「首句给数字 + 来源表 + 口径」纪律",
    "D2": "减少冗余探索（约束单条 SQL）、调 max_steps、修工具错误",
    "D3": "强化「先 search_knowledge 再取数、确认后 record_concept」",
    "D4": "强化「execute_query 后自检」",
    "D5": "检查是否漏接问题语义（过滤 / 聚合 / 列选）",
}


def score_session(record: dict) -> dict:
    """确定性打分（4 维布尔，快速版，供单测 + 快速检查）。"""
    answer = record.get("answer", "")
    tool_names = [e["name"] for e in record.get("events", []) if e["type"] == "tool_call"]
    first_line = answer.split("\n")[0]
    return {
        "交付形态（来源标注）": any(t in answer for t in ("orders", "products", "order_items", "来源")),
        "首句先答数字": bool(re.search(r"\d", first_line)),
        "知识行为（召回/沉淀）": bool({"search_knowledge", "record_concept"} & set(tool_names)),
        "验证倾向（真查了数据）": "execute_query" in tool_names,
    }


def score_session_det(record: dict) -> dict:
    """确定性五维打分基线（D1-D5，0-10，机械判定，可复现）。"""
    answer = record.get("answer", "")
    first_line = answer.split("\n")[0]
    events = record.get("events", [])
    tools = [e["name"] for e in events if e["type"] == "tool_call"]
    results = [e for e in events if e["type"] == "tool_result"]
    errors = sum(1 for e in results if "失败" in str(e.get("result", "")))
    llm_calls = record.get("llm_calls", 0) or 0

    has_number = bool(re.search(r"\d", first_line))
    has_source = any(t in answer for t in ("orders", "products", "order_items", "来源", "表"))
    has_concept = any(t in answer for t in ("口径", "定义", "指"))
    used_recall = "search_knowledge" in tools
    used_record = "record_concept" in tools
    used_query = "execute_query" in tools
    negative = any(n in answer for n in _NEGATIVE)

    scores = {
        "D1": (4 if has_number else 0) + (3 if has_source else 0) + (3 if has_concept else 0),
        "D2": max(0, 10 - errors * 3 - max(0, llm_calls - 6)),
        "D3": (5 if used_recall else 0) + (5 if used_record else 0),
        "D4": 10 if used_query else 0,
        "D5": 10 if (has_number and not negative) else 5,
    }
    scores["total"] = round(sum(scores[k] * _WEIGHTS[k] for k in _WEIGHTS), 1)
    return scores


def _fmt_record(record: dict) -> str:
    tools = "; ".join(e["name"] for e in record.get("events", []) if e["type"] == "tool_call")
    return (
        f"问题：{record.get('question')}\n"
        f"答案：{record.get('answer')}\n"
        f"工具调用：{tools}\n"
        f"tokens={record.get('tokens')} LLM 调用={record.get('llm_calls')} 次"
    )


def score_session_llm(llm, record: dict) -> dict:
    """LLM 五维打分（语义辅助，非基线）。"""
    resp = llm.invoke([("system", load_prompt("score")), ("human", _fmt_record(record))])
    d = _parse_json(resp.content) or {}
    scores = {k: float(d.get(k, 0)) for k in _WEIGHTS}
    scores["total"] = round(sum(scores[k] * w for k, w in _WEIGHTS.items()), 1)
    scores["理由"] = d.get("理由", "")
    return scores


def review(use_llm: bool = False) -> None:
    """复盘报告⑫：确定性五维基线（默认）+ 可选 LLM 语义分 + 最弱维度→改进工单。"""
    records = TranscriptStore().load()
    if not records:
        print("暂无 transcript（先跑几次问答，如 `python -m daagent ask \"有效订单有多少\"`）")
        return
    print(f"共 {len(records)} 条会话，确定性五维基线" + ("（附 LLM 辅助分）" if use_llm else "") + "\n")
    dims = {k: [] for k in _WEIGHTS}
    for i, r in enumerate(records, 1):
        s = score_session_det(r)
        for k in _WEIGHTS:
            dims[k].append(s[k])
        dim_str = " ".join(f"{k}={s[k]:.0f}" for k in _WEIGHTS)
        print(f"#{i} 「{r['question']}」 总分 {s['total']}/10  [{dim_str}]")
        if use_llm:
            ls = score_session_llm(build_llm(), r)
            print(f"   （LLM 辅助分 {ls['total']}/10）")
    avg = {k: sum(v) / len(v) for k, v in dims.items()}
    weakest = min(avg, key=avg.get)
    print(f"\n维度平均：{' '.join(f'{k}={avg[k]:.1f}' for k in _WEIGHTS)}")
    print(f"最弱维度：{weakest}（{avg[weakest]:.1f}/10）→ 改进工单：{_IMPROVEMENT_HINTS[weakest]}")
