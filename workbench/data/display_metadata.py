"""Validate and apply tracked problem display metadata."""

import json
import re


def normalize(text):
    return " ".join(re.sub(r"<[^>]+>", "", text or "").split())


def validate(rows):
    errors = []
    for row in rows:
        problem_id = row.get("problem_id", "<missing>")
        title = " ".join((row.get("display_title") or "").split())
        topic = " ".join((row.get("topic_label") or "").split())
        summary = " ".join((row.get("display_summary") or "").split())
        length = len(normalize(row.get("problem_text")))
        if not title:
            errors.append(f"{problem_id}: display title is required")
        if not topic:
            errors.append(f"{problem_id}: topic label is required")
        if summary and length <= 300:
            errors.append(f"{problem_id}: summary is only allowed above 300 characters")
        if not summary and length > 300:
            errors.append(f"{problem_id}: summary is required above 300 characters")
        if "…" in summary or "..." in summary:
            errors.append(f"{problem_id}: summary must not contain an ellipsis")
        if len(summary) > 48:
            errors.append(f"{problem_id}: summary exceeds 48 characters")
    return errors


def apply(conn, manifest_path):
    rows = json.loads(manifest_path.read_text(encoding="utf-8-sig"))["problems"]
    problem_texts = dict(conn.execute("SELECT problem_id, problem_text FROM problems"))
    manifest_ids = [row.get("problem_id") for row in rows]
    if len(manifest_ids) != len(set(manifest_ids)):
        raise ValueError("manifest problem ids must be unique")
    if set(manifest_ids) != set(problem_texts):
        raise ValueError("manifest must cover every pool problem")
    rows = [dict(row, problem_text=problem_texts[row["problem_id"]]) for row in rows]
    errors = validate(rows)
    if errors:
        raise ValueError("\n".join(errors))
    conn.executemany(
        "UPDATE problems SET display_title=?, topic_label=?, display_summary=? "
        "WHERE problem_id=?",
        [
            (
                row.get("display_title"), row.get("topic_label"),
                row.get("display_summary"), row["problem_id"],
            )
            for row in rows
        ],
    )
    conn.commit()
    return len(rows)
