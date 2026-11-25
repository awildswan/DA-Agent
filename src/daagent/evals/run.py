"""评测运行器：跑 L1 集 + 打分 + 报告。

评测只读闸门（简化版）：用临时 OKF 目录，评测不污染真实 data/okf 知识库。
"""

import tempfile

from daagent.orchestration import run
from daagent.evals.cases import CASES, SQL_CASES
from daagent.evals.scorer import score


def run_eval(cases=None) -> list[dict]:
    cases = cases or CASES
    okf_root = tempfile.mkdtemp(prefix="daagent_eval_")
    results = []
    for case in cases:
        answer = run(case.question, okf_root=okf_root)
        checks = score(answer, case)
        results.append({"id": case.id, "question": case.question, **checks, "answer": answer})
    return results


def print_report(results: list[dict], label: str = "L1") -> None:
    passed = sum(1 for r in results if r["passed"])
    print(f"{label} 评测：{passed}/{len(results)} 通过\n")
    for r in results:
        mark = "✅" if r["passed"] else "❌"
        fails = [k for k in ("数字命中", "来源标注", "首句先答") if not r[k]]
        print(f"{mark} {r['id']}「{r['question']}」" + (f"  未过：{fails}" if fails else ""))
        if not r["passed"]:
            print(f"   答：{r['answer'][:120]}")
