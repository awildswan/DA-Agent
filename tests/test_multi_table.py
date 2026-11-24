"""多表 + 探查 离线单测。"""

from daagent.db.sample import list_tables, sample_db, schema_for_table


def test_multiple_tables():
    assert list_tables() == ["order_items", "orders", "products"]


def test_schema_for_table():
    assert "orders" in schema_for_table("orders")
    assert "未知表" in schema_for_table("nonexistent")


def test_join_query():
    con = sample_db()
    rows = con.execute(
        """
        SELECT p.category, SUM(oi.quantity) AS qty
        FROM order_items oi JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.category
        """
    ).fetchall()
    assert dict(rows) == {"数码": 6, "家居": 1}
