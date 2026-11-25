"""Spider harness 纯逻辑单测（不调 LLM）。"""

import sqlite3

from daagent.evals.spider import _execute, _norm


def test_norm_order_insensitive():
    assert _norm([(1, "a"), (2, "b")]) == _norm([(2, "b"), (1, "a")])


def test_execute_and_match(tmp_path):
    db = tmp_path / "t.sqlite"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE t (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO t VALUES (1, 'a'), (2, 'b')")
    conn.commit()
    conn.close()
    assert _execute(db, "SELECT * FROM t ORDER BY id") == [(1, "a"), (2, "b")]
    # 执行准确率：列顺序不同 = 不匹配（标准执行准确率语义）
    assert _norm(_execute(db, "SELECT id, name FROM t")) != _norm(_execute(db, "SELECT name, id FROM t"))
