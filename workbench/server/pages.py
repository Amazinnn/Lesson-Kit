"""Minimal server-rendered pages (shell upper layer, evolves freely)."""

import html


def hub_page(workspaces):
    cards = []
    for ws in workspaces:
        stats = ws.get("stats", {})
        cards.append(
            f"<div class='card'><h2><a href='/w/{ws['name']}/'>{html.escape(ws['name'])}</a></h2>"
            f"<p>kp={stats.get('kps')} problems={stats.get('problems')} "
            f"signals={stats.get('signals')} due={stats.get('due')}</p></div>"
        )
    return _page("lesson-kit workbench", f"<h1>Workbenches</h1>{''.join(cards)}")


def workspace_page(workspace, weak_items, due_items):
    weak_html = "".join(
        f"<li>{html.escape(item['kp_id'])} "
        f"<span class='score'>{item['score']}</span>"
        f"<span class='reasons'>{html.escape('; '.join(item['reasons']))}</span></li>"
        for item in weak_items
    )
    due_html = "".join(
        f"<li>{item['due_at']} {html.escape(item['label'])}</li>"
        for item in due_items
    )
    body = (
        f"<h1>{html.escape(workspace['name'])}</h1>"
        f"<h2>Weak knowledge points</h2><ul>{weak_html}</ul>"
        f"<h2>Due reminders</h2><ul>{due_html or '<li>nothing due</li>'}</ul>"
        f"<h2>Views</h2>"
        f"<ul><li><a href='/api/w/{workspace['name']}/weak'>weak (json)</a></li>"
        f"<li><a href='/api/w/{workspace['name']}/due'>due (json)</a></li></ul>"
    )
    return _page(f"workspace {workspace['name']}", body)


def _page(title, body):
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>"
        "<style>body{font-family:sans-serif;max-width:60em;margin:2em auto}"
        ".card{border:1px solid #ccc;padding:1em;margin:1em 0}"
        ".reasons{color:#888;font-size:0.85em}</style>"
        f"</head><body>{body}</body></html>"
    )
