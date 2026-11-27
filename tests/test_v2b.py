"""V2.0b-3 单测：板块级 upsert + 表登记。"""

import pytest

from daagent.db.datasource import sample_source
from daagent.db.registry import TableRegistry
from daagent.okf.store import OkfStore


def test_upsert_block_replaces_and_preserves(tmp_path):
    okf = OkfStore(tmp_path / "okf", git=False)
    okf.write("guards", "orders", "## 允许\nregion = A、B\n\n## 关系\n总 = A、B")
    okf.upsert_block("guards", "orders", "允许", "region = A")
    content = okf.read("guards", "orders")
    assert "region = A" in content
    assert "## 关系" in content  # 其他块保留
    assert "B" not in content.split("## 关系")[0]  # 旧允许被替换


def test_upsert_block_appends_new(tmp_path):
    okf = OkfStore(tmp_path / "okf", git=False)
    okf.write("guards", "orders", "## 允许\nregion = A")
    okf.upsert_block("guards", "orders", "核对", "SELECT 1")
    content = okf.read("guards", "orders")
    assert "## 核对" in content and "SELECT 1" in content


def test_upsert_block_rejects_frontmatter(tmp_path):
    okf = OkfStore(tmp_path / "okf", git=False)
    with pytest.raises(ValueError):
        okf.upsert_block("guards", "orders", "允许", "---\ntitle: x\n---")


def test_table_registry_scans():
    r = TableRegistry(sample_source())
    assert any(e.table == "orders" for e in r.entries)
    assert "orders" in r.summary()
