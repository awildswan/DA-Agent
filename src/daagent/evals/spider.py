"""Spider benchmark 子集评测（执行准确率 execution accuracy）。

对齐用户方案 ②：
1. 加载 Spider dev 前 N 题（`xlangai/spider`）；
2. 按 db_id 下载对应 .sqlite（GitHub `taoyds/spider/database`）；
3. 对每题让 agent 连它的 schema 跑（list_tables / describe_table / execute_query），
   记录 agent 执行的所有 SQL；执行准确率 = agent 执行过的任意一条 SQL 结果集 == gold SQL 结果集。
"""

import sqlite3
import zipfile
from pathlib import Path

from huggingface_hub import hf_hub_download
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from daagent.agent.react import run_react
from daagent.config import get_settings
from daagent.parsing import _parse_conclusion_json
from daagent.prompts import load_prompt

DB_DIR = Path("data/spider")
SPIDER_DB_REPO = "HAL-9001/spider-databases"


def download_dbs(db_ids: list[str]) -> None:
    """从 spider_data.zip 解压所需数据库 .sqlite 文件（幂等）。"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = hf_hub_download(SPIDER_DB_REPO, "spider_data.zip", repo_type="dataset")
    with zipfile.ZipFile(zip_path) as zf:
        for db in db_ids:
            dest = DB_DIR / f"{db}.sqlite"
            if dest.exists():
                continue
            with zf.open(f"spider_data/database/{db}/{db}.sqlite") as src, open(dest, "wb") as out:
                out.write(src.read())


def _execute(db_path: Path, sql: str) -> list[tuple]:
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def _norm(rows: list[tuple]) -> list[tuple]:
    return sorted(tuple(r) for r in rows)


def _build_agent(db_path: Path, llm, sql_log: list):
    """构建连到 Spider 库的 agent（工具 + SQL 记录）。"""

    @tool
    def list_tables() -> str:
        """列出所有表。"""
        rows = _execute(db_path, "SELECT name FROM sqlite_master WHERE type='table'")
        return "、".join(r[0] for r in rows)

    @tool
    def describe_table(table: str) -> str:
        """返回指定表的列。"""
        rows = _execute(db_path, f"PRAGMA table_info({table})")
        return "\n".join(f"{r[1]} {r[2]}" for r in rows)

    @tool
    def execute_query(sql: str) -> str:
        """执行 SQL 返回结果。"""
        sql_log.append(sql)
        return str(_execute(db_path, sql))

    tools = [list_tables, describe_table, execute_query]
    return llm.bind_tools(tools), {t.name: t for t in tools}


def run_spider_eval(n: int = 50) -> list[dict]:
    from datasets import load_dataset

    ds = load_dataset("xlangai/spider", split="validation").select(range(n))
    db_ids = sorted(set(ds["db_id"]))
    download_dbs(db_ids)

    s = get_settings()
    llm = ChatOpenAI(
        model=s.deepseek_model, api_key=s.openai_api_key, base_url=s.openai_api_base, temperature=0
    )

    results = []
    for ex in ds:
        db_path = DB_DIR / f"{ex['db_id']}.sqlite"
        gold_rows = _execute(db_path, ex["query"])
        sql_log = []
        agent, tools_by_name = _build_agent(db_path, llm, sql_log)
        messages = [SystemMessage(load_prompt("spider")), HumanMessage(ex["question"])]
        text = run_react(agent, messages, tools_by_name)
        _parse_conclusion_json(text)
        # 执行准确率：agent 执行过的任意一条 SQL 结果集 == 金牌结果集（对探索性查询稳健）
        matched_sql = next((s for s in sql_log if _norm(_execute(db_path, s)) == _norm(gold_rows)), "")
        results.append(
            {
                "db_id": ex["db_id"],
                "question": ex["question"],
                "gold": ex["query"],
                "pred": matched_sql or (sql_log[-1] if sql_log else ""),
                "matched": bool(matched_sql),
            }
        )
    return results


def print_report(results: list[dict]) -> None:
    passed = sum(1 for r in results if r["matched"])
    print(f"Spider 子集执行准确率：{passed}/{len(results)} = {passed / len(results):.0%}\n")
    for r in results:
        mark = "✅" if r["matched"] else "❌"
        print(f"{mark} [{r['db_id']}] {r['question']}")
        if not r["matched"]:
            print(f"   gold: {r['gold']}")
            print(f"   pred: {r['pred']}")
