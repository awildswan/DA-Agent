"""生成 TPC-H 数据到 data/tpch（parquet + load.sql），供本地开发/测试。

这些文件在 .gitignore 里（data/tpch/*.parquet），不会被 git 追踪/推送。
用法：uv run python scripts/gen_tpch.py [sf]   （默认 sf=0.01）
"""

import sys
from pathlib import Path

import duckdb

OUT = Path("data/tpch")
TABLES = ["customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"]


def main(sf: float = 0.01) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL tpch")
    con.execute("LOAD tpch")
    con.execute(f"CALL dbgen(sf={sf})")
    lines = []
    for t in TABLES:
        dest = OUT / f"{t}.parquet"
        con.execute(f"COPY {t} TO '{dest}' (FORMAT 'parquet')")
        size_mb = dest.stat().st_size / 1e6
        print(f"  {t}.parquet  {size_mb:.1f} MB")
        lines.append(f"COPY {t} FROM 'data/tpch/{t}.parquet' (FORMAT 'parquet');")
    (OUT / "load.sql").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"TPC-H sf={sf} 完成：{len(TABLES)} 表 → {OUT}")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 0.01)
