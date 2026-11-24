"""V0.1 runner 的离线单测（不调 LLM）。"""

import pytest

from daagent.db.sample import sample_db
from daagent.parsing import _extract_sql
from daagent.skills.sql import _guard


def test_extract_sql_plain():
    assert _extract_sql("SELECT 1") == "SELECT 1"


def test_extract_sql_fenced():
    assert _extract_sql("```sql\nSELECT 1\n```") == "SELECT 1"


def test_guard_blocks_dangerous():
    with pytest.raises(ValueError):
        _guard("DROP TABLE orders")
    with pytest.raises(ValueError):
        _guard("DELETE FROM orders")
    with pytest.raises(ValueError):
        _guard("UPDATE orders SET x = 1")


def test_guard_allows_is_deleted_column():
    # 词边界：is_deleted 列名不误伤
    _guard("SELECT * FROM orders WHERE is_deleted = 0")


def test_guard_ignores_literal_keyword():
    # 字符串字面量里的 DELETE 不误伤（先抹字面量）
    _guard("SELECT * FROM t WHERE note = 'user pressed DELETE'")


def test_sample_db():
    con = sample_db()
    assert con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 7
