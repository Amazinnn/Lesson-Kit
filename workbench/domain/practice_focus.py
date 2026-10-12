"""Pure focus rules for a practice-page Agent turn."""

import re


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
    "这题", "这道题", "这一题", "本题", "当前题",
)
_NEGATION_PREFIXES = ("不是", "并不是")
_NEGATORS = _NEGATION_PREFIXES + ("不要", "不需要", "不用", "不必", "不想", "别", "不")
_REFERENCE_OPERATIONS = (
    "解释", "讨论", "讲", "说", "看", "提", "聊", "管", "问", "分析", "复习",
)
_NEGATED_OPERATION = (
    rf"(?:{'|'.join(_NEGATORS)})\s*(?:(?:再|在)\s*)?"
    rf"(?:{'|'.join(_REFERENCE_OPERATIONS)})"
)
_REJECTION_BEFORE = re.compile(
    rf"(?:{'|'.join(_NEGATION_PREFIXES)}|{_NEGATED_OPERATION}"
    rf"(?:\s*一下)?)\s*$"
)
_REJECTION_AFTER = re.compile(rf"^\s*{_NEGATED_OPERATION}")


def _rejects_relative_reference(text, references):
    for reference in references:
        start = text.find(reference)
        while start >= 0:
            before = text[:start]
            after = text[start + len(reference):]
            if _REJECTION_BEFORE.search(before) or _REJECTION_AFTER.match(after):
                return True
            start = text.find(reference, start + len(reference))
    return False


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
    if _rejects_relative_reference(
        text, _PREVIOUS_PROBLEM_REFERENCES + _RECENT_PROBLEM_REFERENCES
    ):
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
