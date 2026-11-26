"""会话打分（⑬ 完整版：LLM 五维加权 + 复盘报告⑫）。"""

import re

from daagent.models import build_llm
from daagent.parsing import _parse_json
from daagent.tracing.transcript import TranscriptStore

# 五维权重（对齐 MODULE_DESIGN ⑬）
_WEIGHTS = {"D1": 0.30, "D2": 0.15, "D3": 0.20, "D4": 0.10, "D5": 0.25}

_SCORE_PROMPT = """你是会话质量评审。给下面这轮会话的 agent 表现打分（每维 0-10 整数）：
- D1 交付形态：首句先答数字、有来源、口径清晰
- D2 效率稳定：token / 调用次数合理、无冗余探索
- D3 知识行为：是否正确召回 / 沉淀业务口径
- D4 验证倾向：是否真查数据、自检
- D5 用户验收：答案是否直接回答了用户的问题、可直接采用

只输出 JSON：{"D1": n, "D2": n, "D3": n, "D4": n, "D5": n, "理由": "一句话"}"""

_IMPROVEMENT_HINTS = {
    "D1": "强化 prompt「首句给数字 + 来源表」纪律",
    "D2": "减少冗余探索（约束单条 SQL）、调 max_steps",
    "D3": "强化「先 search_knowledge 再取数、确认后 record_concept」",
    "D4": "强化「execute_query 后自检」",
    "D5": "检查是否漏接问题语义（过滤 / 聚合 / 列选）",
}


def score_session(record: dict) -> dict:
    """确定性打分（4 维，快速版，供单测 + 快速检查）。"""
    answer = record.get("answer", "")
    tool_names = [e["name"] for e in record.get("events", []) if e["type"] == "tool_call"]
    first_line = answer.split("\n")[0]
    return {
        "交付形态（来源标注）": any(t in answer for t in ("orders", "products", "order_items", "来源")),
        "首句先答数字": bool(re.search(r"\d", first_line)),
        "知识行为（召回/沉淀）": bool({"search_knowledge", "record_concept"} & set(tool_names)),
        "验证倾向（真查了数据）": "execute_query" in tool_names,
    }


def _fmt_record(record: dict) -> str:
    tools = "; ".join(e["name"] for e in record.get("events", []) if e["type"] == "tool_call")
    return (
        f"问题：{record.get('question')}\n"
        f"答案：{record.get('answer')}\n"
        f"工具调用：{tools}\n"
        f"tokens={record.get('tokens')} LLM 调用={record.get('llm_calls')} 次"
    )


def score_session_llm(llm, record: dict) -> dict:
    """LLM 五维加权打分（完整版）。"""
    resp = llm.invoke([("system", _SCORE_PROMPT), ("human", _fmt_record(record))])
    d = _parse_json(resp.content) or {}
    scores = {k: float(d.get(k, 0)) for k in _WEIGHTS}
    scores["total"] = round(sum(scores[k] * w for k, w in _WEIGHTS.items()), 1)
    scores["理由"] = d.get("理由", "")
    return scores


def review() -> None:
    """复盘报告⑫：LLM 五维打分 + 维度平均 + 最弱维度 → 改进工单（用-查-改-用的「查」「改」）。"""
    records = TranscriptStore().load()
    if not records:
        print("暂无 transcript（先跑几次问答，如 `python -m daagent ask \"有效订单有多少\"`）")
        return
    llm = build_llm()
    print(f"共 {len(records)} 条会话，LLM 五维打分\n")
    dims = {k: [] for k in _WEIGHTS}
    for i, r in enumerate(records, 1):
        s = score_session_llm(llm, r)
        for k in _WEIGHTS:
            dims[k].append(s[k])
        dim_str = " ".join(f"{k}={s[k]:.0f}" for k in _WEIGHTS)
        print(f"#{i} 「{r['question']}」 总分 {s['total']}/10  [{dim_str}]")
        print(f"   理由：{s['理由']}")
    avg = {k: sum(v) / len(v) for k, v in dims.items()}
    weakest = min(avg, key=avg.get)
    print(f"\n维度平均：{' '.join(f'{k}={avg[k]:.1f}' for k in _WEIGHTS)}")
    print(f"最弱维度：{weakest}（{avg[weakest]:.1f}/10）→ 改进工单：{_IMPROVEMENT_HINTS[weakest]}")
