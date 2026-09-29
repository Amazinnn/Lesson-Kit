"""Server-side HTML for the records surface."""

import html


def content(workspace_name, overview):
    rows = []
    for record in overview["records"]:
        verdict = record.get("verdict")
        if verdict is None:
            badge, verdict_class = "未判定", "record-verdict-open"
        elif verdict:
            badge, verdict_class = "对", "record-verdict-ok"
        else:
            badge, verdict_class = "错", "record-verdict-bad"
        rating = record.get("rating")
        title = html.escape(record.get("title") or "未命名题目")
        answer = html.escape((record.get("answer_text") or "").strip())
        note = html.escape(
            (record.get("feedback_note") or record.get("note") or "").strip())
        link = f"/w/{workspace_name}/practice?problem={record['problem_id']}"
        stars = ""
        if isinstance(rating, int) and 1 <= rating <= 5:
            stars = (
                f"<span class='record-rating'>{'★' * rating}"
                f"{'☆' * (5 - rating)}</span>"
            )
        rows.append(
            "<article class='record-row card'>"
            f"<header><a class='record-title' href='{link}'>{title}</a>"
            f"<span class='record-verdict {verdict_class}'>{badge}</span>"
            + stars
            + "<time class='record-time'>"
            + html.escape(str(record.get("created_at") or ""))
            + "</time></header>"
            + (f"<p class='record-answer'>{answer}</p>" if answer else "")
            + (f"<p class='record-note muted'>{note}</p>" if note else "")
            + "</article>"
        )
    if not rows:
        rows.append("<p class='muted'>还没有做题记录——去练习页答第一题吧。</p>")
    return (
        "<div class='page-content'><section class='support-section'>"
        + "".join(rows)
        + "</section></div>"
    )
