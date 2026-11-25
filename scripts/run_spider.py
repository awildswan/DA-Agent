"""跑 Spider 子集评测并存结果文件（供 CLI 与离线分析复用）。"""

import json

from daagent.evals.spider import run_spider_eval

r = run_spider_eval(50)
n = sum(x["matched"] for x in r)
print(f"SUMMARY {n}/{len(r)} = {n / len(r):.0%}")
json.dump(r, open("data/spider/results.json", "w"), ensure_ascii=False, indent=1)
print("saved data/spider/results.json")
