"""表登记：记录当前数据源有哪些表（列 + 行数），换数据源 / 连远程靠它。"""

from dataclasses import dataclass


@dataclass
class TableEntry:
    table: str
    columns: list[str]
    row_count: int


class TableRegistry:
    def __init__(self, ds):
        self.ds = ds
        self.entries = self._scan()

    def _scan(self) -> list[TableEntry]:
        entries = []
        for t in self.ds.list_tables():
            try:
                cols = [r[0] for r in self.ds.con.execute(f"DESCRIBE {t}").fetchall()]
                n = int(self.ds.con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
            except Exception:  # noqa: BLE001
                cols, n = [], 0
            entries.append(TableEntry(t, cols, n))
        return entries

    def summary(self) -> str:
        lines = [f"数据源：{self.ds.name}（{len(self.entries)} 张表）"]
        for e in self.entries:
            lines.append(f"- {e.table}（{len(e.columns)} 列，{e.row_count} 行）")
        return "\n".join(lines)
