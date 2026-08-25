"""Server-rendered pages: DSH-styled three-column shell."""

import html
import re
from datetime import date

from workbench.data import queries
from workbench.domain import weak


def hub_page(workspaces):
    cards = []
    for ws in workspaces:
        stats = ws.get("stats", {})
        cards.append(
            f"<a class='workspace-card' href='/w/{ws['name']}/practice'>"
            f"<span class='context-line'>学习工作区</span>"
            f"<h2>{html.escape(ws['name'])}</h2>"
            f"<p>{stats.get('kps')} 个知识点 · {stats.get('problems')} 道题 · "
            f"{stats.get('due')} 项待复习</p></a>"
        )
    body = (
        "<main class='hub-page'>"
        "<header class='page-header'>"
        "<p class='context-line'>lesson-kit</p>"
        "<h1>学习工作台</h1>"
        "<p class='page-summary'>选择一个工作区，从最需要回看的地方继续。</p>"
        "</header>"
        f"<section class='workspace-grid' aria-label='工作区列表'>{''.join(cards)}</section>"
        "</main>"
    )
    return _base("lesson-kit 工作台", body)


def shell(workspace, workspaces, weak_items, middle_html, active_nav, graph_mode=False):
    course = workspace.get("active_course") or ""
    chapter = workspace.get("active_chapter") or ""
    meta = f"<span class='meta'>{html.escape(workspace['name'])}"
    if course and chapter:
        meta += f" · {html.escape(course)} / {html.escape(chapter)}"
    meta += "</span>"
    topbar = (
        "<header id='topbar'>"
        "<a class='brand' href='/'>lesson-kit</a>"
        "<span class='topbar-separator'>/</span>"
        f"{meta}"
        "</header>"
    )
    left = _left_column(workspace, workspaces, weak_items, active_nav)
    ai = _ai_column(workspace["name"], graph_mode)
    body = (
        topbar
        + f"<div id='layout' data-workspace='{workspace['name']}'>"
        + f"<aside id='left-column'>{left}</aside>"
        + f"<main id='middle'>{middle_html}</main>"
        + f"<aside id='ai-column'>{ai}</aside>"
        + "</div>"
        + ("<script src='/static/graph-physics.js'></script>" if graph_mode else "")
        + "<script src='/static/workbench.js'></script>"
    )
    return _base(f"workbench {workspace['name']}", body)


def _page_header(context, title, summary="", actions=""):
    summary_html = f"<p class='page-summary'>{summary}</p>" if summary else ""
    actions_html = f"<div class='page-header-actions'>{actions}</div>" if actions else ""
    return (
        "<header class='page-header'>"
        f"<p class='context-line'>{context}</p>"
        f"<div class='page-title-row'><div><h1>{title}</h1>{summary_html}</div>{actions_html}</div>"
        "</header>"
    )


def practice_page(workspace, workspaces, weak_items):
    middle = (
        _page_header(
            "学习 / 弱项优先", "练习",
            "从最需要回看的知识点开始，按自己的节奏完成这一轮。",
        )
        + "<div class='page-content practice-content'>"
        "<section id='start-area' class='practice-intro'>"
        "<p class='section-kicker'>本轮练习</p>"
        "<h2>先选定自评方式</h2>"
        "<p>本轮会持续练习薄弱项相关题；跳题和草稿不会留下学习记录。</p>"
        "<fieldset class='practice-mode-choice'><legend>本轮自评方式（必选）</legend>"
        "<label><input id='practice-mode-immediate' type='radio' name='practice-mode' "
        "value='immediate'> 每题作答后自评</label>"
        "<label><input id='practice-mode-batch' type='radio' name='practice-mode' "
        "value='batch'> 完成后统一自评</label></fieldset>"
        "<button id='start-practice' class='primary' disabled>开始本轮练习</button>"
        "</section>"
        "<section class='practice-flow' aria-label='练习过程'>"
        "<div id='stream' class='practice-card-area'></div>"
        "<div id='composer' class='practice-answer-card hidden'>"
        "<div id='composer-row'>"
        "<textarea id='answer-box' rows='3' placeholder='写下你的作答'></textarea>"
        "<button id='answer-submit' class='primary'>提交作答</button>"
        "</div>"
        "<div id='composer-actions' class='hidden'>"
        "<button id='show-answer' class='outline'>查看解析</button>"
        "</div>"
        "<div id='feedback-area' class='feedback-card hidden'>"
        "<label for='rating-input'>自评分（1–5）</label>"
        "<input id='rating-input' type='number' min='1' max='5' step='1' inputmode='numeric' "
        "placeholder='输入 1–5'>"
        "<textarea id='feedback-note' rows='2' placeholder='可选备注'></textarea>"
        "<button id='save-rating' class='primary'>保存并下一题</button>"
        "</div>"
        "</div>"
        "</section>"
        "<div id='session-end-entry' class='session-end-entry hidden'>"
        "<span>本题未提交的内容只保留在当前会话。</span>"
        "<div><button id='no-time' class='ghost'>跳到下一道题目</button>"
        "<button id='goto-session-end' class='outline'>提前结束本次练习</button></div>"
        "</div>"
        "</div>"
    )
    return shell(workspace, workspaces, weak_items, middle, "practice")


def kps_page(workspace, workspaces, weak_items, pool):
    prefix = f"{workspace.get('active_course', '')}-{workspace.get('active_chapter', '')}"
    ranked = weak.score_all(
        pool.kps(prefix), pool.signals(), pool.schedule_rows(),
        pool.relations(), set(), date.today(),
    )
    items = "".join(
        f"<li><a href='/w/{workspace['name']}/kp/{item['kp_id']}'>{html.escape(item['knowledge_item'])}</a>"
        f"<span class='item-id'>{html.escape(item['kp_id'])}</span>"
        f"<span class='score'> {item['score']}</span>"
        f"<span class='reasons'> {html.escape('; '.join(item['reasons']))}</span></li>"
        for item in ranked
    )
    middle = (
        _page_header(
            "学习 / 当前章节", "知识点",
            "按薄弱程度浏览本章内容，随时进入具体知识点回看。",
        )
        + "<div class='page-content'>"
        "<section class='support-section knowledge-index'>"
        "<div class='section-heading'><div>"
        "<p class='section-kicker'>当前排序</p><h2>本章知识点</h2>"
        "</div><p>分数越高，越值得优先回看。</p></div>"
        f"<ul class='knowledge-list'>{items or '<li class="muted">暂无知识点</li>'}</ul>"
        "</section></div>"
    )
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
    problems_html = _linked_problems(detail["problems"])
    schedule = detail["schedule"]
    schedule_html = (
        f"state={schedule['state']} reps={schedule['repetitions']} "
        f"ease={schedule['ease']:.2f} due={schedule.get('due_at') or '—'}"
        if schedule else "未排期"
    )
    middle = (
        _page_header(
            "知识点 / 当前章节", html.escape(kp["knowledge_item"]),
            "先读正文；需要时再查看掌握线索、关联题和复习安排。",
        )
        + "<div class='page-content'>"
        f"<article class='knowledge-body card'>{_render_markdown(kp.get('body') or '', workspace['name'], kp_id)}</article>"
        "<section class='support-section evidence-section'>"
        "<div class='section-heading'><div>"
        "<p class='section-kicker'>辅助信息</p><h2>掌握线索</h2>"
        "</div><p>这些记录只说明下一次该从哪里继续。</p></div>"
        "<div class='support-grid'>"
        f"<section class='detail-block'><h3>信号</h3><ul>{signals_html or '<li class=\"muted\">—</li>'}</ul></section>"
        f"<section class='detail-block'><h3>调度</h3><p>{schedule_html}</p></section>"
        "</div></section>"
        "<section class='support-section linked-problems'>"
        "<div class='section-heading'><div>"
        "<p class='section-kicker'>练习入口</p><h2>关联题目</h2>"
        "</div></div>"
        f"{problems_html or '<p class=\"muted\">—</p>'}"
        "</section></div>"
    )
    return shell(workspace, workspaces, weak_items, middle, "kps")


def graph_page(workspace, workspaces, weak_items, has_artifact):
    middle = (
        _page_header(
            "知识网络 / 当前章节", "知识图谱",
            "搜索、筛选或聚焦一个知识点，查看它与当前学习状态的联系。",
        )
        + "<div class='page-content graph-content'>"
        "<section class='graph-panel' aria-label='知识图谱'>"
        "<div class='graph-toolbar'>"
        "<label class='visually-hidden' for='graph-search'>搜索知识点</label>"
        "<input id='graph-search' placeholder='搜索知识点'>"
        "<label class='visually-hidden' for='graph-state-filter'>按状态筛选</label>"
        "<select id='graph-state-filter'><option value=''>全部状态</option>"
        "<option value='needs_work'>待攻克</option><option value='review'>待复习</option>"
        "<option value='mastered'>已掌握</option></select>"
        "<div class='graph-zoom' aria-label='缩放'>"
        "<button id='graph-zoom-out' class='ghost sm' title='缩小'>−</button>"
        "<button id='graph-zoom-in' class='ghost sm' title='放大'>＋</button>"
        "<button id='graph-fit' class='outline sm'>适应画布</button></div>"
        "</div><div id='graph-canvas' tabindex='0' aria-label='知识图谱画布'></div>"
        "</section></div>"
    )
    return shell(workspace, workspaces, weak_items, middle, "graph", graph_mode=True)


def session_end_page(workspace, workspaces, weak_items):
    middle = (
        _page_header(
            "练习 / 收束本轮", "会话末统一自评",
            "只补充尚未评分的题目；已写入的记录不会重复出现。",
        )
        + "<div class='page-content'>"
        "<section class='support-section pending-section'>"
        "<div class='section-heading'><div>"
        "<p class='section-kicker'>待补充</p><h2>尚未评分的题目</h2>"
        "</div><p>逐题输入 1–5 分；点击保存前不会写入学习记录。</p></div>"
        "<div id='pending-ratings'></div></section>"
        "<section id='session-end-actions' class='next-step'>"
        "<div><p class='section-kicker'>下一步</p><h2>继续打磨弱项</h2>"
        "<p>重新开始时再次选择自评方式。</p></div>"
        "<div class='next-step-actions'>"
        "<button id='practice-similar' class='primary'>再练同类</button>"
        "</div></section></div>"
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
        f"<a href='/w/{workspace['name']}/{key}'>{label}</a></div>"
        for key, label in nav_items
    )
    weak_html = "".join(
        f"<div class='weak-item'><a href='/w/{workspace['name']}/kp/{item['kp_id']}'>"
        f"<span class='weak-title'>{html.escape(item['knowledge_item'])}</span>"
        f"<span class='id'>{html.escape(item['kp_id'])}</span></a>"
        f"<span class='score'>{item['score']}</span>"
        f"<span class='reasons' title='{html.escape('; '.join(item['reasons']))}'>"
        f"{html.escape('; '.join(item['reasons']))}</span></div>"
        for item in weak_items
    )
    return (
        "<section class='side-section workspace-switcher'>"
        "<p class='side-label'>工作区</p>"
        f"<select id='workspace-select' aria-label='切换工作区'>{options}</select>"
        "</section>"
        "<nav class='side-section primary-nav' aria-label='工作台导航'>"
        "<p class='side-label'>页面</p>"
        f"{nav}</nav>"
        "<section class='side-section weak-section'>"
        "<div class='side-heading'><p class='side-label'>当前薄弱项</p>"
        "<span>按信号排序</span></div>"
        f"<div class='weak-list'>{weak_html or '<p class=\"score\">暂无信号</p>'}</div>"
        "</section>"
    )


def _linked_problems(problems):
    groups = {}
    for problem in problems:
        topic = problem.get("topic_label") or "未分类"
        groups.setdefault(topic, []).append(problem)
    return "".join(
        "<details class='problem-topic' open>"
        f"<summary>{html.escape(topic)}</summary><ul>"
        + "".join(
            "<li class='linked-problem'>"
            f"<span class='problem-title'>{html.escape(_problem_title(problem))}</span>"
            + (
                f"<span class='problem-summary'>{html.escape(_problem_summary(problem))}</span>"
                if _problem_summary(problem) else ""
            )
            + "<details class='linked-problem-detail'><summary>查看完整题干</summary>"
            f"<p>{html.escape(_problem_text(problem))}</p></details>"
            + "</li>"
            for problem in items
        )
        + "</ul></details>"
        for topic, items in groups.items()
    )


def _problem_title(problem):
    title = problem.get("display_title")
    if title:
        return title
    text = " ".join((problem.get("problem_text") or "").split())
    return text[:24] or problem["problem_id"]


def _problem_summary(problem):
    text = _problem_text(problem)
    summary = " ".join((problem.get("display_summary") or "").split())
    if len(text) <= 300 or not summary or len(summary) > 48:
        return ""
    if "…" in summary or "..." in summary:
        return ""
    return summary


def _problem_text(problem):
    text = re.sub(r"<[^>]+>", "", problem.get("problem_text") or "")
    return " ".join(text.split())


def _ai_column(workspace_name, graph_mode=False):
    teacher = (
        "<section class='ai-identity'>"
        "<div id='ai-head'><div><p class='side-label'>外部 Agent</p><h2>AI 教师</h2></div>"
        "<button id='ai-collapse' class='ghost sm' title='折叠/展开'>‹</button></div>"
        "<div id='ai-context'>上下文：无</div></section>"
        "<section id='ai-actions' class='ai-actions' aria-label='AI 操作'>"
        "<button id='ai-explain' class='primary sm'>讲解</button>"
        "<button id='ai-diagnose' class='outline sm'>诊断</button>"
        "<button id='ai-new' class='ghost sm'>新会话</button>"
        "</section>"
        "<section class='ai-conversation'><p class='side-label'>对话</p>"
        "<div id='ai-messages'></div></section>"
        "<div id='ai-input-row' class='ai-input-row'>"
        "<input id='ai-input' placeholder='附加说明（可选）'>"
        "<button id='ai-send' class='primary sm'>发送</button>"
        "</div>"
    )
    if not graph_mode:
        return teacher
    return (
        "<div id='right-tabs' role='tablist' aria-label='图谱侧栏'>"
        "<button id='graph-detail-tab' class='right-tab active' role='tab' "
        "aria-selected='true'>知识点详情</button>"
        "<button id='ai-teacher-tab' class='right-tab' role='tab' "
        "aria-selected='false'>AI 教师</button></div>"
        "<section id='graph-detail-panel' role='tabpanel'>"
        "<p class='side-label'>知识点详情</p><h2>选择一个节点</h2>"
        "<p class='muted'>图谱会读取当前工作区；点击节点查看正文、学习状态与可编辑内容。</p>"
        "</section>"
        "<div id='ai-teacher-panel' class='hidden' role='tabpanel'>"
        f"{teacher}</div>"
    )


_MATH_RE = re.compile(r"\$\$([\s\S]+?)\$\$|\$([^$\n]+)\$", re.MULTILINE)


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
    if match.group(1) is not None:
        return f"<span class='math display'>{html.escape(expr)}</span>"
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
