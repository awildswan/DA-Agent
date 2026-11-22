"""V0.2 示例数据库：orders 表（含一个脏值陷阱），用于跑通最小闭环 + 交付闸门。"""

import duckdb


def sample_db() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(
        """
        CREATE TABLE orders (
            order_id INTEGER,
            region VARCHAR,
            order_date DATE,
            amount DECIMAL(10, 2),
            status VARCHAR
        )
        """
    )
    con.execute(
        """
        INSERT INTO orders VALUES
        (1, '华东区', DATE '2026-11-01', 100.00, 'paid'),
        (2, '华东区', DATE '2026-11-15', 200.00, 'paid'),
        (3, '华东区', DATE '2026-12-01', 150.00, 'paid'),
        (4, '华南区', DATE '2026-11-10', 300.00, 'paid'),
        (5, '华南区', DATE '2026-11-20', 50.00, 'cancelled'),
        (6, '华北区', DATE '2026-11-05', 120.00, 'paid'),
        (7, '华中区', DATE '2026-11-22', 80.00, 'paid')
        """
    )
    return con


def schema_str() -> str:
    return (
        "表 orders（订单表）：\n"
        "- order_id INTEGER：订单 ID\n"
        "- region VARCHAR：区域（标准值：华东区 / 华南区 / 华北区）\n"
        "- order_date DATE：下单日期\n"
        "- amount DECIMAL(10, 2)：金额（元）\n"
        "- status VARCHAR：状态（paid=已支付，cancelled=已取消）\n"
        "说明：'订单量' 通常指订单数 COUNT(*)；'销售额' 指金额 SUM(amount)。"
    )
