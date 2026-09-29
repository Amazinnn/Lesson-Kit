"""Shared validation for safe problem markup and learner-facing labels."""

import re


LABEL_FIELD_LIMITS = {
    "topic_label": 40,
    "display_title": 80,
    "display_summary": 200,
}
ALLOWED_TAG = re.compile(r"</?(sup|sub)>")


def validate_markup(text):
    if not isinstance(text, str):
        return ["is not text"]
    if "\ufffd" in text:
        return ["has suspicious formula damage"]
    errors = []
    stack = []
    index = 0
    while index < len(text):
        start = text.find("<", index)
        if start < 0:
            break
        match = ALLOWED_TAG.match(text, start)
        if match is None:
            tail = text[start:]
            complete_tag = re.match(
                r"</?[A-Za-z][A-Za-z0-9]*(?:\s+[^<>]*)?\s*/?>", tail)
            unterminated_tag = (
                (start == 0 or text[start - 1].isspace())
                and re.match(r"</?[A-Za-z][A-Za-z0-9]*(?:\s+[^<>]*)?\s*$", tail)
            )
            if complete_tag or unterminated_tag:
                errors.append("has unknown or unterminated HTML")
            index = start + 1
            continue
        tag = match.group(1)
        closing = text.startswith("</", start)
        if closing:
            if not stack or stack[-1][0] != tag:
                errors.append("has unbalanced sup/sub")
            else:
                _, content_start, opening_start = stack.pop()
                if not text[content_start:start].strip():
                    errors.append("has empty sup/sub")
                left = _word_left(text, opening_start)
                right = _word_right(text, match.end())
                if left and right and (
                    len(left) + len(right) > 2
                    or (left.islower() and right.islower())
                ):
                    errors.append("sup/sub splits an ordinary word")
        else:
            stack.append((tag, match.end(), start))
        index = match.end()
    if stack:
        errors.append("has unbalanced sup/sub")
    return errors


def validate_label(field, value):
    limit = LABEL_FIELD_LIMITS.get(field)
    if limit is None:
        return [f"unknown label field: {field}"]
    if not isinstance(value, str) or not value.strip():
        return [f"{field} must be a non-empty string"]
    errors = []
    if len(value) > limit:
        errors.append(f"{field} exceeds {limit} characters")
    errors.extend(f"{field} {reason}" for reason in validate_markup(value))
    return errors


def _word_left(text, index):
    match = re.search(r"[A-Za-z]+$", text[:index])
    return match.group(0) if match else ""


def _word_right(text, index):
    match = re.match(r"[A-Za-z]+", text[index:])
    return match.group(0) if match else ""
