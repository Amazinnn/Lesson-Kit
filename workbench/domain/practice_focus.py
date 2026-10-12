"""Pure focus rules for a practice-page Agent turn."""


_PREVIOUS_PROBLEM_REFERENCES = (
    "上一题", "上一道题", "上题", "前一题", "前一道题",
    "前面那题", "前面那道题", "刚才那题", "刚才那道题",
    "刚刚那题", "刚刚那道题",
)
_RECENT_PROBLEM_REFERENCES = (
    "前几题", "前几道题", "前面几题", "前面几道题",
    "刚才几题", "刚才几道题", "刚刚几题", "刚刚几道题",
    "最近几题", "最近几道题",
)
_COMPETING_CURRENT_REFERENCES = (
    "这题", "这道题", "本题", "当前题",
)
_NEGATED_RELATIVE_REFERENCES = (
    "不是上一题", "不是上一道题", "不是上题", "不是前一题", "不是前一道题",
    "不要解释上一题", "不要解释上一道题", "不要讨论上一题", "不要讲上一题",
    "不解释上一题", "不讨论上一题", "不讲上一题",
    "别解释上一题", "别讨论上一题", "别讲上一题",
    "前几题不用管", "前几道题不用管", "前面几题不用管", "前面几道题不用管",
    "最近几题不用管", "最近几道题不用管",
)


def resolve(message, visible_problem_id, previous_problem_ids):
    """Return a managed page default or one unambiguous relative focus."""
    if not isinstance(visible_problem_id, str) or not visible_problem_id:
        return None

    text = message if isinstance(message, str) else ""
    previous_ids = [
        problem_id for problem_id in previous_problem_ids
        if isinstance(problem_id, str) and problem_id
    ]
    asks_previous = any(phrase in text for phrase in _PREVIOUS_PROBLEM_REFERENCES)
    asks_recent = any(phrase in text for phrase in _RECENT_PROBLEM_REFERENCES)
    page_focus = {
        "type": "problem",
        "problem_ids": [visible_problem_id],
        "basis": "page_anchor",
    }

    if asks_previous == asks_recent:
        return page_focus
    if any(phrase in text for phrase in _COMPETING_CURRENT_REFERENCES):
        return page_focus
    if any(phrase in text for phrase in _NEGATED_RELATIVE_REFERENCES):
        return page_focus
    selected_ids = previous_ids if asks_recent else previous_ids[-1:]
    if not selected_ids:
        return page_focus
    return {
        "type": "problem",
        "problem_ids": selected_ids,
        "basis": "user_recent_reference" if asks_recent
        else "user_previous_reference",
    }
