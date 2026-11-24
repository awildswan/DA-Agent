"""示例数据库：多表（orders / products / order_items），用于探查 + 多表规划。"""

import duckdb

_SCHEMAS = {
    "orders": (
        "表 orders（订单表）：\n"
        "- order_id INTEGER：订单 ID\n"
        "- region VARCHAR：区域（标准值：华东 / 华南 / 华北）\n"
        "- order_date DATE：下单日期\n"
        "- amount DECIMAL(10, 2)：金额（元）\n"
        "- status VARCHAR：状态（paid=已支付，cancelled=已取消）"
    ),
    "products": (
        "表 products（商品表）：\n"
        "- product_id INTEGER：商品 ID\n"
        "- name VARCHAR：商品名\n"
        "- category VARCHAR：品类"
    ),
    "order_items": (
        "表 order_items（订单明细表）：\n"
        "- order_id INTEGER：订单 ID（外键 → orders.order_id）\n"
        "- product_id INTEGER：商品 ID（外键 → products.product_id）\n"
        "- quantity INTEGER：数量"
    ),
}


def sample_db() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(
        """
        CREATE TABLE orders (
            order_id INTEGER, region VARCHAR, order_date DATE,
            amount DECIMAL(10, 2), status VARCHAR
        )
        """
    )
    con.execute(
        """
        INSERT INTO orders VALUES
        (1, '华东', DATE '2026-11-01', 100.00, 'paid'),
        (2, '华东', DATE '2026-11-15', 200.00, 'paid'),
        (3, '华东', DATE '2026-12-01', 150.00, 'paid'),
        (4, '华南', DATE '2026-11-10', 300.00, 'paid'),
        (5, '华南', DATE '2026-11-20', 50.00, 'cancelled'),
        (6, '华北', DATE '2026-11-05', 120.00, 'paid'),
        (7, '华中', DATE '2026-11-22', 80.00, 'paid')
        """
    )
    con.execute("CREATE TABLE products (product_id INTEGER, name VARCHAR, category VARCHAR)")
    con.execute(
        """
        INSERT INTO products VALUES
        (101, '手机', '数码'), (102, '笔记本', '数码'), (103, '水杯', '家居')
        """
    )
    con.execute("CREATE TABLE order_items (order_id INTEGER, product_id INTEGER, quantity INTEGER)")
    con.execute(
        """
        INSERT INTO order_items VALUES
        (1, 101, 1), (2, 102, 1), (3, 101, 2), (4, 103, 1), (6, 102, 1), (7, 101, 1)
        """
    )
    return con


def list_tables() -> list[str]:
    return sorted(_SCHEMAS.keys())


def schema_for_table(table: str) -> str:
    return _SCHEMAS.get(table, f"未知表 {table}（可用表：{list_tables()}）")
