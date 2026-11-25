"""L1 打分器：数字命中 / 来源标注 / 首句先答（确定性检查，不调 LLM）。"""

import re


def score(answer: str, case) -> dict:
    first_line = answer.split("\n")[0] if answer else ""
    checks = {
        "数字命中": all(str(int(n)) in answer for n in case.gold_numbers),
        "来源标注": case.source_table in answer,
        "首句先答": bool(re.search(r"\d", first_line)),
    }
    checks["passed"] = all(checks.values())
    return checks
