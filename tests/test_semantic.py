"""语义层（召回 / 沉淀）+ 解析 离线单测——只测纯函数，不调 LLM。"""

from daagent.okf.recall import _recall_concepts, _valid_concept
from daagent.okf.store import OkfStore
from daagent.parsing import _parse_concept_json, _parse_conclusion_json


def test_recall_concepts_reads_okf(tmp_path):
    okf = OkfStore(tmp_path / "okf")
    okf.write("concepts", "有效订单", "有效订单 = status='paid'（已支付）")
    okf.write("guards", "orders", "# orders\n\n## 允许\nregion = 华东")  # 非 concepts，应被忽略
    text = _recall_concepts(okf)
    assert "有效订单 = status='paid'" in text
    assert "guards" not in text


def test_recall_concepts_empty_when_no_concepts(tmp_path):
    okf = OkfStore(tmp_path / "okf")
    okf.write("guards", "orders", "x")
    assert _recall_concepts(okf) == ""


def test_parse_concept_json_plain():
    assert _parse_concept_json('{"concept": "有效订单", "definition": "status=paid"}') == {
        "concept": "有效订单",
        "definition": "status=paid",
    }


def test_parse_concept_json_fenced():
    text = '```json\n{"concept": "有效订单", "definition": "status=paid"}\n```'
    assert _parse_concept_json(text) == {"concept": "有效订单", "definition": "status=paid"}


def test_parse_concept_json_null():
    assert _parse_concept_json('{"concept": null}') is None


def test_parse_concept_json_invalid():
    assert _parse_concept_json("这不是 JSON") is None


def test_valid_concept_rejects_tautology():
    assert _valid_concept("有效订单", "有效订单 = 未展开说明") is False  # 自指
    assert _valid_concept("有效订单", "status='paid'（已支付）") is True


def test_valid_concept_rejects_vague():
    assert _valid_concept("有效订单", "未给出具体定义") is False
    assert _valid_concept("有效订单", "") is False


def test_parse_conclusion_json():
    s = _parse_conclusion_json(
        '{"answer": "6 单", "numbers": {"有效订单": 6}, "entities": ["华东"]}'
    )
    assert s["answer"] == "6 单"
    assert s["numbers"] == {"有效订单": 6}
    assert s["entities"] == ["华东"]


def test_parse_conclusion_json_fallback_on_garbage():
    s = _parse_conclusion_json("这不是 JSON")
    assert s["answer"] == "（结论解析失败）"
