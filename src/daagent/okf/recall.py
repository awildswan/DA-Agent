"""OKF 召回 + 概念写入守卫（①召回 / ⑪沉淀的读写逻辑）。"""

from daagent.okf.store import OkfStore

_VAGUE = ("未展开", "具体定义", "未给出", "该口径")


def _recall_concepts(okf: OkfStore) -> str:
    """① 召回：读 OKF concepts，返回「已知业务口径」文本（无则空串）。"""
    concepts = [
        okf.read(cat, name) for cat, name in okf.list_blocks() if cat == "concepts"
    ]
    concepts = [c for c in concepts if c]
    if not concepts:
        return ""
    return "已知业务口径（之前确认过的，请沿用）：\n" + "\n".join(f"- {c}" for c in concepts)


def _valid_concept(concept: str, definition: str) -> bool:
    """写入守卫：拒写空定义 / 自指（同义反复）/ 空泛定义。"""
    if not concept or not definition:
        return False
    if concept in definition:
        return False
    return not any(v in definition for v in _VAGUE)
