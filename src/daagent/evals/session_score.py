"""会话打分（⑬ 最小版：确定性检查，无金牌）。"""

import re

from daagent.tracing.transcript import TranscriptStore


def score_session(record: dict) -> dict:
    """确定性打分：交付形态 / 首句先答 / 知识行为 / 验证倾向。"""
    answer = record.get("answer", "")
    tool_names = [e["name"] for e in record.get("events", []) if e["type"] == "tool_call"]
    first_line = answer.split("\n")[0]
    return {
        "交付形态（来源标注）": any(t in answer for t in ("orders", "products", "order_items", "来源")),
        "首句先答数字": bool(re.search(r"\d", first_line)),
        "知识行为（召回/沉淀）": bool({"search_knowledge", "record_concept"} & set(tool_names)),
        "验证倾向（真查了数据）": "execute_query" in tool_names,
    }


def review() -> None:
    """复盘报告：读 transcripts，逐条打分 + 汇总。"""
    records = TranscriptStore().load()
    if not records:
        print("暂无 transcript（先跑几次问答，如 `python -m daagent ask \"有效订单有多少\"`）")
        return
    print(f"共 {len(records)} 条会话\n")
    total = 0
    for i, r in enumerate(records, 1):
        s = score_session(r)
        n_pass = sum(1 for v in s.values() if v)
        total += n_pass
        print(f"#{i} 「{r['question']}」 tokens={r.get('tokens')} LLM={r.get('llm_calls')} 次 → {n_pass}/4")
        for k, v in s.items():
            print(f"   {'✅' if v else '❌'} {k}")
    print(f"\n平均：{total / len(records):.1f}/4 维度")
