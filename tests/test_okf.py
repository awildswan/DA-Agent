"""OKF 知识库离线单测（写入守卫 / 修正优先于并存 / 读取 / 列表）。"""

import pytest

from daagent.okf.store import OkfStore


def test_write_and_read(tmp_path):
    okf = OkfStore(tmp_path / "okf")
    okf.write("guards", "orders", "# orders\n\n## 允许\nregion = 华东、华南、华北")
    assert okf.read("guards", "orders").startswith("# orders")


def test_write_rejects_empty(tmp_path):
    okf = OkfStore(tmp_path / "okf")
    with pytest.raises(ValueError):
        okf.write("guards", "orders", "   ")


def test_write_overwrites_same_name(tmp_path):
    # 修正优先于并存：同名覆盖，绝不新旧并存
    okf = OkfStore(tmp_path / "okf")
    okf.write("concepts", "有效单", "旧口径")
    okf.write("concepts", "有效单", "新口径")
    assert okf.read("concepts", "有效单") == "新口径"


def test_list_blocks(tmp_path):
    okf = OkfStore(tmp_path / "okf")
    okf.write("guards", "orders", "x")
    okf.write("concepts", "有效单", "y")
    blocks = okf.list_blocks()
    assert ("guards", "orders") in blocks
    assert ("concepts", "有效单") in blocks
