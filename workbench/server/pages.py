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


def shell(workspace, workspaces, weak_items, middle_html, active_nav, graph_mode=False,
          page_type=None, object_id=None):
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
        "<div class='mobile-drawer-controls'>"
        "<button id='mobile-nav-toggle' class='ghost sm icon-only' type='button' "
        "aria-controls='left-column' aria-expanded='false' aria-label='打开导航' title='打开导航'>☰</button>"
        "<button id='mobile-ai-toggle' class='ghost sm icon-only' type='button' "
        "aria-controls='ai-column' aria-expanded='false' aria-label='打开对话' title='打开对话'>◌</button>"
        "</div>"
        "</header>"
    )
    left = _left_column(workspace, workspaces, weak_items, active_nav)
    page_type = page_type or active_nav
    object_attributes = (
        f" data-object-type='{page_type}' data-object-id='{html.escape(object_id)}'"
        if object_id else ""
    )
    ai = _ai_column(workspace["name"], graph_mode, page_type)
    body = (
        topbar
        + f"<div id='layout' data-workspace='{workspace['name']}' "
        f"data-page='{page_type}'{object_attributes}>"
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
        "<p id='practice-error' class='inline-error hidden' aria-live='polite'></p>"
        "<button id='retry-practice' class='outline sm hidden' type='button'>重试</button>"
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
    return shell(workspace, workspaces, weak_items, middle, "practice", page_type="practice")


def kps_page(workspace, workspaces, weak_items, pool):
    prefix = f"{workspace.get('active_course', '')}-{workspace.get('active_chapter', '')}"
    ranked = weak.score_all(
        pool.kps(prefix), pool.signals(), pool.schedule_rows(),
        pool.relations(), set(), date.today(),
    )
    items = "".join(
        f"<li><a href='/w/{workspace['name']}/kp/{item['kp_id']}'>{html.escape(item['knowledge_item'])}</a>"
        "</li>"
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
    return shell(workspace, workspaces, weak_items, middle, "kps", page_type="kps")


def kp_page(workspace, workspaces, weak_items, pool, kp_id):
    detail = queries.kp_detail(pool, kp_id)
    kp = detail["kp"]
    if kp is None:
        return shell(
            workspace, workspaces, weak_items, "<h1>未知知识点</h1>", "kps",
            page_type="kp", object_id=kp_id,
        )
    problems_html = _linked_problems(detail["problems"], workspace["name"], kp_id)
    schedule = detail["schedule"]
    reminder = "重点练习" if detail["signals"] else (
        "可以复习" if schedule and schedule.get("due_at")
        and schedule["due_at"] <= date.today().isoformat() else ""
    )
    reminder_html = f"<p class='action-reminder'>{reminder}</p>" if reminder else ""
    practice_action = (
        f"<a id='practice-kp' class='primary kp-practice-action' "
        f"data-practice-kp-id='{html.escape(kp_id)}' "
        f"href='/w/{workspace['name']}/practice?kp={html.escape(kp_id)}'>练习此知识点</a>"
    )
    middle = (
        _page_header(
            "知识点 / 当前章节", html.escape(kp["knowledge_item"]),
            "先读正文，再按需要继续练习相关题目。", practice_action,
        )
        + "<div class='page-content'>"
        f"<article class='knowledge-body card'>{_render_markdown(kp.get('body') or '', workspace['name'], kp_id)}</article>"
        + reminder_html
        + "<section class='support-section linked-problems'>"
        "<div class='section-heading'><div>"
        "<p class='section-kicker'>练习入口</p><h2>关联题目</h2>"
        "</div></div>"
        f"{problems_html or '<p class=\"muted\">—</p>'}"
        "</section></div>"
    )
    return shell(
        workspace, workspaces, weak_items, middle, "kps",
        page_type="kp", object_id=kp_id,
    )


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
         "<label class='graph-gravity-label' for='graph-gravity'>聚拢</label>"
         "<input id='graph-gravity' type='range' min='0' max='100' value='30' "
         "aria-label='调整图谱聚拢程度' title='调整图谱聚拢程度'>"
         "<div class='graph-zoom' aria-label='缩放'>"
        "<button id='graph-zoom-out' class='ghost sm' title='缩小'>−</button>"
        "<button id='graph-zoom-in' class='ghost sm' title='放大'>＋</button>"
        "<button id='graph-fit' class='outline sm'>适应画布</button></div>"
        "</div><div id='graph-canvas' tabindex='0' aria-label='知识图谱画布'></div>"
        "</section></div>"
    )
    return shell(workspace, workspaces, weak_items, middle, "graph", graph_mode=True,
                 page_type="graph")


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
    return shell(workspace, workspaces, weak_items, middle, "session-end",
                 page_type="session-end")


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
        "</a></div>"
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
        "<div class='side-heading'><p class='side-label'>优先回看</p></div>"
        f"<div class='weak-list'>{weak_html or '<p class=\"score\">暂无提醒</p>'}</div>"
        "</section>"
    )


def _linked_problems(problems, workspace_name, kp_id):
    groups = {}
    for problem in problems:
        topic = problem.get("topic_label") or "未分类"
        groups.setdefault(topic, []).append(problem)
    return "".join(
        "<details class='problem-topic'>"
        f"<summary>{html.escape(topic)}</summary><ul>"
        + "".join(
            "<li class='linked-problem'>"
            f"<span class='problem-title'>{html.escape(_problem_title(problem))}</span>"
            + f"<div class='linked-problem-text rich-text'>{_render_markdown(problem.get('problem_text') or '', workspace_name, kp_id)}</div>"
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
    return "未命名题目"


def _problem_summary(problem):
    text = _problem_text(problem)
    summary = " ".join((problem.get("display_summary") or "").split())
    if len(text) <= 500 or not summary or len(summary) > 48:
        return ""
    if "…" in summary or "..." in summary:
        return ""
    return summary


def _problem_text(problem):
    text = re.sub(r"<[^>]+>", "", problem.get("problem_text") or "")
    return " ".join(text.split())


def _ai_column(workspace_name, graph_mode=False, page_type=""):
    teacher = (
        "<section id='ai-session-controls' aria-label='对话'>"
        "<div id='ai-session-list-view'>"
        "<div class='ai-session-list-head'><p class='side-label'>对话</p>"
        "<button id='ai-new-session' class='outline sm'>新建</button></div>"
        "<div id='ai-session-list' role='list' aria-label='历史对话'></div>"
        "<p id='ai-session-empty' class='muted'>还没有对话。</p>"
        "</div>"
        "<div id='ai-provider-picker' class='hidden' aria-label='选择 Agent'>"
        "<p class='side-label'>选择 Agent</p>"
        "<p class='muted'>创建后将固定使用所选 Agent。</p>"
        "<div id='ai-provider-options' class='ai-provider-options'></div>"
        "</div></section>"
        "<section id='ai-chat-view' class='hidden' aria-label='当前对话'>"
        "<div id='ai-chat-head'>"
        "<button id='ai-session-back' class='ghost sm icon-only' title='返回对话列表' "
        "aria-label='返回对话列表'>‹</button>"
        "</div>"
        "<section class='ai-conversation'><div id='ai-messages'></div>"
        "<p id='ai-status' class='muted' aria-live='polite'></p></section>"
        "<div id='ai-input-row' class='ai-input-row'>"
        "<textarea id='ai-input' rows='2' placeholder='输入问题'></textarea>"
        "<div class='ai-send-actions'><button id='ai-stop' class='outline sm hidden'>停止</button>"
        "<button id='ai-send' class='primary sm' disabled>发送</button></div>"
        "</div></section>"
    )
    if not graph_mode:
        return teacher
    return (
        "<div id='right-tabs' role='tablist' aria-label='图谱侧栏'>"
        "<button id='graph-detail-tab' class='right-tab active' role='tab' "
        "aria-selected='true'>学习看板</button>"
        "<button id='ai-teacher-tab' class='right-tab' role='tab' "
        "aria-selected='false'>对话</button></div>"
        "<section id='graph-detail-panel' role='tabpanel'>"
        "<p class='side-label'>学习看板</p><h2>选择一个节点</h2>"
        "<p class='muted'>点击图中的知识点，查看掌握状态、关联题数与关系强度。</p>"
        "<a id='graph-open-kp' class='graph-dashboard-link hidden' href='#'>打开知识点</a>"
        "</section>"
        "<div id='ai-teacher-panel' class='hidden' role='tabpanel'>"
        f"{teacher}</div>"
    )


_MATH_RE = re.compile(r"\$\$([\s\S]+?)\$\$|\$([^$\n]+)\$", re.MULTILINE)


def _render_markdown(text, workspace_name, kp_id):
    """Render the same small safe Markdown subset used by the browser."""
    if not text:
        return ""
    out, paragraph, list_tag = [], [], None
    in_code, code_lang, code_lines = False, "", []

    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            out.append(f"<p>{'<br>'.join(_rich(line, workspace_name) for line in paragraph)}</p>")
            paragraph = []

    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        fence = re.match(r"^\s*```\s*([\w-]*)\s*$", line)
        if fence:
            flush_paragraph()
            close_list()
            if in_code:
                out.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                code_lang = ""
            in_code = not in_code
            code_lang = fence.group(1) if in_code else ""
            continue
        if in_code:
            code_lines.append(line)
            continue
        heading = re.match(r"^\s*(#{1,3})\s+(.+?)\s*#*\s*$", line)
        if heading:
            flush_paragraph(); close_list()
            level = len(heading.group(1)) + 1
            out.append(f"<h{level}>{_rich(heading.group(2), workspace_name)}</h{level}>")
            continue
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        unordered = re.match(r"^\s*[-*+]\s+(.+)$", line)
        if ordered or unordered:
            flush_paragraph()
            wanted = "ol" if ordered else "ul"
            if list_tag and list_tag != wanted:
                close_list()
            if not list_tag:
                list_tag = wanted
                out.append(f"<{list_tag}>")
            out.append(f"<li>{_rich((ordered or unordered).group(1), workspace_name)}</li>")
            continue
        if line.startswith(">"):
            flush_paragraph(); close_list()
            out.append(f"<blockquote>{_rich(line[1:].lstrip(), workspace_name)}</blockquote>")
            continue
        if not line.strip():
            flush_paragraph(); close_list()
            continue
        close_list()
        paragraph.append(line)
    flush_paragraph(); close_list()
    if in_code:
        out.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    return "".join(out)


def _rich(text, workspace_name):
    """Escape first, then inject math/wiki/image markup (order matters)."""
    tokens = []

    def preserve_script(match):
        tokens.append(
            f"<{match.group(1)}>{html.escape(match.group(2))}</{match.group(1)}>"
        )
        return f"\x00{len(tokens) - 1}\x00"

    text = re.sub(r"<(sup|sub)>([^<>]+)</\1>", preserve_script, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = _MATH_RE.sub(_math_replace, text)
    text = _wiki_replace(text, workspace_name)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        lambda match: (
            f"<a href='{html.escape(match.group(2), quote=True)}' "
            f"target='_blank' rel='noopener noreferrer'>{match.group(1)}</a>"
        ),
        text,
    )
    text = _image_replace(text, workspace_name)
    return re.sub(r"\x00(\d+)\x00", lambda match: tokens[int(match.group(1))], text)


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
