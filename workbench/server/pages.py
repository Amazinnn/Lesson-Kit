"""Server-rendered pages: three-column shell (minimal utilitarian)."""

import html
import json
import re

from workbench.data import queries
from workbench.domain import weak


def hub_page(workspaces):
    cards = []
    for ws in workspaces:
        stats = ws.get("stats", {})
        cards.append(
            f"<div class='card'><h2><a href='/w/{ws['name']}/practice'>{html.escape(ws['name'])}</a></h2>"
            f"<p>kp={stats.get('kps')} problems={stats.get('problems')} "
            f"signals={stats.get('signals')} due={stats.get('due')}</p></div>"
        )
    return _base("lesson-kit", f"<h1>Workbenches</h1>{''.join(cards)}")


def shell(workspace, workspaces, weak_items, middle_html):
    """Three-column page: left selector, middle page area, right AI column."""
    left = _left_column(workspace, workspaces, weak_items)
    ai = _ai_column(workspace["name"])
    body = (
        f"<div id='layout' data-workspace='{workspace['name']}'>"
        f"<aside id='left-column'>{left}</aside>"
        f"<main id='middle'>{middle_html}</main>"
        f"<aside id='ai-column'>{ai}</aside>"
        "</div>"
        "<script src='/static/workbench.js'></script>"
    )
    return _base(f"workbench {workspace['name']}", body)


def practice_page(workspace, workspaces, weak_items):
    middle = (
        "<h1>练习</h1>"
        "<div id='practice-controls'>"
        "<button id='start-practice' class='primary'>开始练习（弱项优先）</button>"
        "<a href='session-end'>会话末统一自评</a>"
        "</div>"
        "<div id='problem-card' class='card hidden'></div>"
    )
    return shell(workspace, workspaces, weak_items, middle)


def session_end_page(workspace, workspaces, weak_items):
    middle = (
        "<h1>会话末统一自评</h1>"
        "<div id='pending-ratings'></div>"
        "<div id='session-end-actions'>"
        "<button id='practice-similar' class='primary'>再练同类（弱项组）</button>"
        "<button id='skip-all'>跳过全部</button>"
        "</div>"
    )
    return shell(workspace, workspaces, weak_items, middle)


def kp_page(workspace, workspaces, weak_items, pool, kp_id):
    detail = queries.kp_detail(pool, kp_id)
    kp = detail["kp"]
    if kp is None:
        return shell(workspace, workspaces, weak_items, "<h1>未知知识点</h1>")
    signals_html = "".join(
        f"<li>{html.escape(s['signal_type'])} — {html.escape(s['weight'])}"
        f"{'（×' + str(s['evidence_count']) + '）' if s.get('evidence_count', 1) >= 2 else ''}"
        f"<span class='reasons'>{html.escape(s.get('note') or '')}</span></li>"
        for s in detail["signals"]
    )
    problems_html = "".join(
        f"<li><a href='/w/{workspace['name']}/kp/{kp_id}'>{html.escape(p['problem_id'])}</a>"
        f"<span class='reasons'>{html.escape(p['problem_text'][:60])}</span></li>"
        for p in detail["problems"]
    )
    schedule = detail["schedule"]
    schedule_html = (
        f"state={schedule['state']} reps={schedule['repetitions']} "
        f"ease={schedule['ease']:.2f} due={schedule.get('due_at') or '—'}"
        if schedule else "未排期"
    )
    middle = (
        f"<h1>{html.escape(kp['knowledge_item'])}</h1>"
        f"<div class='card'>{_render_markdown(kp.get('body') or '', workspace['name'], kp_id)}</div>"
        f"<h2>信号</h2><ul>{signals_html or '<li>无</li>'}</ul>"
        f"<h2>关联题目</h2><ul>{problems_html or '<li>无</li>'}</ul>"
        f"<h2>调度</h2><p>{schedule_html}</p>"
        f"<script>window.wbKpId='{kp_id}';</script>"
    )
    return shell(workspace, workspaces, weak_items, middle)


def _left_column(workspace, workspaces, weak_items):
    options = "".join(
        f"<option value='{ws['name']}' {'selected' if ws['name'] == workspace['name'] else ''}>"
        f"{html.escape(ws['name'])}</option>"
        for ws in workspaces
    )
    weak_html = "".join(
        f"<li><a href='/w/{workspace['name']}/kp/{item['kp_id']}'>{html.escape(item['kp_id'])}</a>"
        f"<span class='score'> {item['score']}</span>"
        f"<span class='reasons'> {html.escape('; '.join(item['reasons']))}</span></li>"
        for item in weak_items
    )
    return (
        "<h2>工作区</h2>"
        f"<select id='workspace-select'>{options}</select>"
        "<nav>"
        f"<a href='/w/{workspace['name']}/practice'>练习</a> · "
        f"<a href='/w/{workspace['name']}/session-end'>会话末</a>"
        "</nav>"
        "<h2>弱项（按信号排序）</h2>"
        f"<ul>{weak_html or '<li>暂无信号</li>'}</ul>"
    )


def _ai_column(workspace_name):
    return (
        "<h2>AI 教师</h2>"
        f"<div id='ai-context' data-workspace='{workspace_name}'>上下文：无</div>"
        "<div id='ai-actions'>"
        "<button id='ai-explain'>讲解</button>"
        "<button id='ai-diagnose'>诊断</button>"
        "<button id='ai-new'>新会话</button>"
        "</div>"
        "<div id='ai-messages'></div>"
        "<div id='ai-input-row'>"
        "<input id='ai-input' placeholder='提问（绑定当前题时作为讲解/诊断输入）'>"
        "<button id='ai-send'>发送</button>"
        "</div>"
    )


_MATH_RE = re.compile(r"\$([^$\n]+)\$|^\$\$([\s\S]+?)\$\$", re.MULTILINE)


def _render_markdown(text, workspace_name, kp_id):
    """Minimal Markdown renderer: math, wiki links, images, headings, lists."""
    if not text:
        return ""
    out = []
    in_list = False
    for line in text.splitlines():
        if line.startswith("### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h4>{_rich(line[4:], workspace_name)}</h4>")
        elif line.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{_rich(line[3:], workspace_name)}</h3>")
        elif line.startswith("# "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h2>{_rich(line[2:], workspace_name)}</h2>")
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_rich(line[2:], workspace_name)}</li>")
        elif line.strip() == "":
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<p></p>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<p>{_rich(line, workspace_name)}</p>")
    if in_list:
        out.append("</ul>")
    return "".join(out)


def _rich(text, workspace_name):
    """Escape first, then inject math/wiki/image markup (order matters)."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = _MATH_RE.sub(_math_replace, text)
    text = _wiki_replace(text, workspace_name)
    text = _image_replace(text, workspace_name)
    return text


def _math_replace(match):
    expr = match.group(1) or match.group(2)
    return f"<span class='math'>{html.escape(expr)}</span>"


def _wiki_replace(line, workspace_name):
    def repl(match):
        kp_id = match.group(1)
        return f"<a href='/w/{workspace_name}/kp/{kp_id}'>{html.escape(kp_id)}</a>"
    return re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", repl, line)


def _image_replace(line, workspace_name):
    def repl(match):
        alt, path = match.group(1), match.group(2)
        return (f"<img alt='{html.escape(alt)}' "
                f"src='/api/w/{workspace_name}/figures/{path.lstrip('/')}'>")
    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, line)


def _base(title, body):
    return (
        "<!doctype html><html lang='zh'><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>"
        "<link rel='stylesheet' href='/static/workbench.css'>"
        "<link rel='stylesheet' href='/static/katex/katex.min.css'>"
        "<script defer src='/static/katex/katex.min.js'></script>"
        f"</head><body>{body}</body></html>"
    )
