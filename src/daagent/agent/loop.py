"""⑦ 交付闸门 → ⑧ 自纠环（≤ max_rounds 轮）。"""


def _deliver(conclude, correct, check, question, result, max_rounds: int = 2):
    """conclude/correct/check 可注入（便于测试）。

    conclude/correct 返回结构化结论 dict；check 返回 RedFlag 列表。
    """
    structured = conclude(question, result)
    reds = check(structured)
    for _ in range(max_rounds):
        if not reds:
            break
        structured = correct(question, result, reds)
        reds = check(structured)
    return structured, reds
