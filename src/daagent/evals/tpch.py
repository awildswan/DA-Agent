"""TPC-H 22 查询评测：题目从 JSON 读，结果落 data/tpch/results.json，跑 N 次取均值。"""

import json
import os
import tempfile
import time
from pathlib import Path

from daagent.db.datasource import get_datasource
from daagent.orchestration.runner import run_structured

_QUERIES_FILE = Path(__file__).parent / "data" / "tpch_queries.json"
_RESULTS_FILE = Path("data/tpch/results.json")


def load_queries() -> list[dict]:
    """从 JSON 读 22 题（不写死在代码里）。"""
    return json.loads(_QUERIES_FILE.read_text(encoding="utf-8"))


def _norm(rows) -> list:
    """顺序无关结果集。"""
    return sorted(tuple(str(x) for x in r) for r in rows)


def _matches(agent_rows, gold_rows) -> bool:
    """允许 agent 多列：完全一致，或 agent 存在与 gold 列数相同的投影能对上。"""
    a = _norm(agent_rows)
    g = _norm(gold_rows)
    if a == g:
        return True
    if not g or not a:
        return not g and not a
    ng, na = len(g[0]), len(a[0])
    if na < ng or na > 12:
        return False
    from itertools import combinations

    return any(
        sorted(tuple(str(r[c]) for c in cols) for r in a) == g
        for cols in combinations(range(na), ng)
    )


def _safe_exec(con, sql):
    try:
        return con.execute(sql).fetchall()
    except Exception:  # noqa: BLE001
        return None


def run_tpch(runs: int = 1, limit: int | None = None) -> dict:
    os.environ["DAAGENT_DATASOURCE"] = "tpch"
    ds = get_datasource()
    con = ds.con
    okf_root = tempfile.mkdtemp(prefix="tpch_okf_")
    queries = load_queries()
    if limit:
        queries = queries[:limit]
    details = []
    total_correct = 0
    total_runs = 0
    t0_all = time.time()

    for item in queries:
        qid, nl, sql = item["id"], item["nl"], item["sql"]
        try:
            gold = _norm(con.execute(sql).fetchall())
        except Exception as e:  # noqa: BLE001
            details.append({"id": qid, "error": str(e)})
            print(f"{qid}: 金牌 SQL 失败 {e}")
            continue
        correct_count = 0
        agent_sqls: list[str] = []
        for _ in range(runs):
            executed: list[str] = []

            def on_event(e):
                if e.get("type") == "tool_call" and e.get("name") == "execute_query":
                    s = (e.get("args") or {}).get("sql", "")
                    if s:
                        executed.append(s)

            try:
                run_structured(nl, okf_root=okf_root, on_event=on_event)
            except Exception:  # noqa: BLE001
                pass
            hit = False
            for s in executed:
                rows = _safe_exec(con, s)
                if rows is not None and _matches(rows, gold):
                    hit = True
                    break
            correct_count += hit
            agent_sqls.extend(executed)
        total_correct += correct_count
        total_runs += runs
        details.append(
            {
                "id": qid,
                "correct": correct_count,
                "runs": runs,
                "gold_sql": sql,
                "gold_rows": len(gold),
                "agent_sqls": agent_sqls[-8:],
            }
        )
        status = "✅" if correct_count == runs else ("⚠️" if correct_count else "❌")
        print(f"{qid}: {status} {correct_count}/{runs}  ({time.time() - t0_all:.0f}s elapsed)")

    accuracy = round(total_correct / total_runs, 3) if total_runs else 0
    payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "runs_per_query": runs,
        "accuracy": accuracy,
        "total_correct": total_correct,
        "total_runs": total_runs,
        "elapsed_s": round(time.time() - t0_all, 1),
        "details": details,
    }
    _RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n执行准确率：{total_correct}/{total_runs} = {accuracy:.0%}")
    print(f"结果已存：{_RESULTS_FILE}")
    return payload
