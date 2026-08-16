"""Server-rendered pages: DSH-styled three-column shell."""

import html
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


def shell(workspace, workspaces, weak_items, middle_html, active_nav):
    course = workspace.get("active_course") or ""
    chapter = workspace.get("active_chapter") or ""
    meta = f"<span class='meta'>{html.escape(workspace['name'])}"
    if course and chapter:
        meta += f" · {html.escape(course)} / {html.escape(chapter)}"
    meta += "</span>"
    topbar = (
        "<header id='topbar'>"
        "<span class='brand'>lesson-kit</span>"
        f"{meta}"
        "</header>"
    )
    left = _left_column(workspace, workspaces, weak_items, active_nav)
    ai = _ai_column(workspace["name"])
    body = (
        topbar
        + f"<div id='layout' data-workspace='{workspace['name']}'>"
        + f"<aside id='left-column'>{left}</aside>"
        + f"<main id='middle'>{middle_html}</main>"
        + f"<aside id='ai-column'>{ai}</aside>"
        + "</div>"
        + "<script src='/static/workbench.js'></script>"
    )
    return _base(f"workbench {workspace['name']}", body)


def practice_page(workspace, workspaces, weak_items):
    middle = (
        "<h1>练习</h1>"
        "<div id='start-area'>"
        "<button id='start-practice' class='primary'>开始练习（弱项优先）</button>"
        "</div>"
        "<div id='stream'></div>"
        "<div id='composer' class='hidden'>"
        "<div id='composer-row'>"
        "<textarea id='answer-box' rows='3' placeholder='作答（开放题）'></textarea>"
        "<button id='answer-submit' class='primary'>提交作答</button>"
        "</div>"
        "<div id='composer-actions' class='hidden'>"
        "<button id='show-answer' class='primary'>看答案</button>"
        "<button id='no-time' class='ghost'>没时间批改</button>"
        "</div>"
        "<button id='goto-session-end' class='outline hidden'>去会话末统一自评</button>"
        "</div>"
    )
    return shell(workspace, workspaces, weak_items, middle, "practice")


def kps_page(workspace, workspaces, weak_items, pool):
    prefix = f"{workspace.get('active_course', '')}-{workspace.get('active_chapter', '')}"
    ranked = weak.score_all(
        pool.kps(prefix), pool.signals(), pool.schedule_rows(),
        pool.relations(), set(), __import__("datetime").date.today(),
    )
    items = "".join(
        f"<li><a href='/w/{workspace['name']}/kp/{item['kp_id']}'>{html.escape(item['kp_id'])}</a>"
        f"<span class='score'> {item['score']}</span>"
        f"<span class='reasons'> {html.escape('; '.join(item['reasons']))}</span></li>"
        for item in ranked
    )
    middle = f"<h1>知识点</h1><ul>{items or '<li>无</li>'}</ul>"
    return shell(workspace, workspaces, weak_items, middle, "kps")


def kp_page(workspace, workspaces, weak_items, pool, kp_id):
    detail = queries.kp_detail(pool, kp_id)
    kp = detail["kp"]
    if kp is None:
        return shell(workspace, workspaces, weak_items, "<h1>未知知识点</h1>", "kps")
    signals_html = "".join(
        f"<li>{html.escape(s['signal_type'])} — {html.escape(s['weight'])}"
        f"{'（×' + str(s['evidence_count']) + '）' if s.get('evidence_count', 1) >= 2 else ''}"
        f"<span class='reasons'> {html.escape(s.get('note') or '')}</span></li>"
        for s in detail["signals"]
    )
    problems_html = "".join(
        f"<li>{html.escape(p['problem_id'])}"
        f"<span class='reasons'> {html.escape(p['problem_text'][:60])}</span></li>"
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
    return shell(workspace, workspaces, weak_items, middle, "kps")


def graph_page(workspace, workspaces, weak_items, has_artifact):
    if has_artifact:
        middle = (
            "<div style='display:flex;flex-direction:column;"
            "height:calc(100vh - 130px)'>"
            "<h1>知识图谱</h1>"
            f"<iframe src='/api/w/{workspace['name']}/graph' title='知识图谱' "
            "style='flex:1;width:100%;border:1px solid var(--dsw-border-l2);"
            "border-radius:12px'></iframe>"
            "</div>"
        )
    else:
        course = workspace.get("active_course", "")
        chapter = workspace.get("active_chapter", "")
        middle = (
            "<h1>知识图谱</h1>"
            "<div class='card'><p>图谱尚未生成。</p>"
            "<p>生成命令（在仓库根目录运行）：</p>"
            "<pre>python pool/scripts/render-graph-html.py --db pool/{course}.db "
            "--course {course} --chapter {chapter} --course-name \"课程名\" "
            "--out output/{course}/{chapter}</pre>"
            "<p>生成后刷新本页即可。</p></div>"
        ).format(course=course, chapter=chapter)
    return shell(workspace, workspaces, weak_items, middle, "graph")


def session_end_page(workspace, workspaces, weak_items):
    middle = (
        "<h1>会话末统一自评</h1>"
        "<div id='pending-ratings'></div>"
        "<div id='session-end-actions'>"
        "<button id='practice-similar' class='primary'>再练同类（弱项组）</button>"
        "<button id='skip-all' class='ghost'>跳过全部</button>"
        "</div>"
    )
    return shell(workspace, workspaces, weak_items, middle, "session-end")


def _left_column(workspace, workspaces, weak_items, active_nav):
    options = "".join(
        f"<option value='{ws['name']}' {'selected' if ws['name'] == workspace['name'] else ''}>"
        f"{html.escape(ws['name'])}</option>"
        for ws in workspaces
    )
    nav_items = [
        ("practice", "练习"),
        ("kps", "知识点"),
        ("graph", "知识图谱"),
    ]
    nav = "".join(
        f"<div class='nav-item {'active' if key == active_nav else ''}'>"
        f"<a href='/w/{workspace['name']}/{key if key != 'kps' else 'kps'}'>{label}</a></div>"
        for key, label in nav_items
    )
    weak_html = "".join(
        f"<div class='weak-item'><a href='/w/{workspace['name']}/kp/{item['kp_id']}'>"
        f"<span class='id'>{html.escape(item['kp_id'])}</span></a>"
        f"<span class='score'>{item['score']}</span>"
        f"<span class='reasons' title='{html.escape('; '.join(item['reasons']))}'>"
        f"{html.escape('; '.join(item['reasons']))}</span></div>"
        for item in weak_items
    )
    return (
        "<h2>工作区</h2>"
        f"<select id='workspace-select'>{options}</select>"
        f"<h2>导航</h2>{nav}"
        "<h2>弱项（按信号排序）</h2>"
        f"<div class='weak-list'>{weak_html or '<p class=\"score\">暂无信号</p>'}</div>"
    )


def _ai_column(workspace_name):
    return (
        "<h2>AI 教师</h2>"
        f"<div id='ai-context' data-workspace='{workspace_name}'>上下文：无</div>"
        "<div id='ai-actions'>"
        "<button id='ai-explain' class='primary sm'>讲解</button>"
        "<button id='ai-diagnose' class='outline sm'>诊断</button>"
        "<button id='ai-new' class='ghost sm'>新会话</button>"
        "</div>"
        "<div id='ai-messages'></div>"
        "<div id='ai-input-row'>"
        "<input id='ai-input' placeholder='附加说明（可选）'>"
        "<button id='ai-send' class='primary sm'>发送</button>"
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
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title>"
        "<link rel='stylesheet' href='/static/workbench.css'>"
        "<link rel='stylesheet' href='/static/katex/katex.min.css'>"
        "<script src='/static/katex/katex.min.js'></script>"
        f"</head><body>{body}</body></html>"
    )
