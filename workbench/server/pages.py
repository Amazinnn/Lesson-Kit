"""Server-rendered pages: DSH-styled three-column shell."""

import html
import json
import re
from datetime import date

from workbench.data import queries


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
          page_type=None, object_id=None, kp_titles=None):
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
        + f"<aside id='left-column'>{left}<div id='left-resizer' class='column-resizer' role='separator' aria-label='调整左栏宽度' title='拖动调整左栏宽度'></div></aside>"
        + f"<main id='middle'>{_practice_scope_tray(kp_titles)}{middle_html}</main>"
        + f"<aside id='ai-column'>{ai}<div id='right-resizer' class='column-resizer' role='separator' aria-label='调整右栏宽度' title='拖动调整右栏宽度'></div></aside>"
        + "</div>"
        + ("<script src='/static/graph-physics.js'></script>" if graph_mode else "")
        + "<script src='/static/practice-deck.js'></script>"
        + "<script src='/static/workbench.js'></script>"
    )
    return _base(f"workbench {workspace['name']}", body)


def _practice_scope_tray(kp_titles=None):
    names_json = html.escape(json.dumps(kp_titles or {}, ensure_ascii=False))
    return (
        "<div class='scope-tray-anchor'><aside id='scope-tray' class='scope-tray' "
        "aria-label='练习范围托盘' data-kp-names='" + names_json + "'>"
        "<button id='scope-tray-toggle' class='outline sm scope-tray-trigger' type='button' "
        "aria-controls='scope-tray-panel' aria-expanded='false' aria-label='展开练习范围'>"
        "练习范围 <span id='scope-tray-trigger-count'>0</span></button>"
        "<section id='scope-tray-panel' class='scope-tray-panel hidden'>"
        "<header class='scope-tray-header'><div><span class='side-label'>练习范围</span>"
        "<strong id='scope-tray-count'>已选 0 个</strong></div>"
        "<button id='scope-tray-collapse' class='ghost sm icon-only' type='button' "
        "aria-label='收起练习范围' title='收起'>−</button></header>"
        "<ol id='scope-tray-list' class='scope-tray-list' aria-label='已选知识点'></ol>"
        "<p id='scope-tray-empty' class='muted scope-tray-empty'>还没有选择知识点。</p>"
        "<button id='scope-tray-practice' class='primary scope-tray-practice' "
        "type='button' disabled>练习这些知识点</button>"
        "</section></aside></div>"
    )


def _page_header(context, title, summary="", actions=""):
    summary_html = f"<p class='page-summary'>{summary}</p>" if summary else ""
    actions_html = f"<div class='page-header-actions'>{actions}</div>" if actions else ""
    return (
        "<header class='page-header'>"
        f"<p class='context-line'>{context}</p>"
        f"<div class='page-title-row'><div><h1>{title}</h1>{summary_html}</div>{actions_html}</div>"
        "</header>"
    )


def practice_page(workspace, workspaces, weak_items, plan=None, suggestions=None,
                  kp_titles=None):
    """Render practice: staged selection list + on-demand suggestions + time view."""
    plan = plan or {"goals": [], "queue": [], "totals": {}}
    middle = (
        _page_header("学习 / 明确范围", "练习", "先选定要练的知识点，再选择一种练习模式。")
        + "<div class='page-content practice-content'>"
        + "<div class='practice-columns' id='practice-columns'>"
        + "<div class='practice-main'>"
        + _daily_plan(plan)
        + _staged_practice_html(workspace["name"], suggestions or [], kp_titles or {})
        + "<section id='start-area' class='practice-intro'><p class='section-kicker'>本轮练习</p>"
        "<h2>选择一种练习模式</h2>"
        "<p id='practice-scope-summary'>当前范围由知识点视图明确选择；本轮不会自动扩展范围。</p>"
        "<fieldset class='practice-mode-choice'><legend>练习模式（必选其一）</legend>"
        "<label><input id='practice-mode-exam' type='radio' name='practice-mode' value='exam'> 综合题</label>"
        "<label><input id='practice-mode-micro' type='radio' name='practice-mode' value='micro'> 小测</label>"
        "<label><input id='practice-mode-yes_no' type='radio' name='practice-mode' value='yes_no'> 判断</label>"
        "<label><input id='practice-mode-flash_card' type='radio' name='practice-mode' value='flash_card'> 闪卡</label></fieldset>"
        "<fieldset id='flash-direction-choice' class='flash-direction-choice hidden'><legend>闪卡方向</legend>"
        "<label><input id='flash-direction-mixed' type='radio' name='flash-direction' value='mixed' checked> 混合</label>"
        "<label><input id='flash-direction-forward' type='radio' name='flash-direction' value='forward'> 正向</label>"
        "<label><input id='flash-direction-reverse' type='radio' name='flash-direction' value='reverse'> 反向</label>"
        "<p>单向卡始终按正面提问。</p></fieldset>"
        "<fieldset class='practice-rating-choice'><legend>自评时机（必选其一）</legend>"
        "<label><input id='practice-rating-immediate' type='radio' name='practice-rating-mode' value='immediate'> 每题作答后自评</label>"
        "<label><input id='practice-rating-batch' type='radio' name='practice-rating-mode' value='batch'> 完成后统一自评</label></fieldset>"
        "<button id='start-practice' class='primary' disabled>开始本轮练习</button></section>"
        + "</div>"
        + "<aside class='practice-time'>" + time_view_html() + "</aside>"
        + "</div>"
        + "<section class='practice-flow' aria-label='练习过程'><p id='practice-error' class='inline-error hidden' aria-live='polite'></p>"
        "<button id='retry-practice' class='outline sm hidden' type='button'>重试</button><div id='stream' class='practice-card-area'></div>"
        "<div id='composer' class='practice-answer-card hidden'><div id='composer-row'><textarea id='answer-box' rows='3' placeholder='写下你的作答'></textarea>"
        "<button id='answer-submit' class='primary'>提交作答</button></div><div id='composer-actions' class='hidden'>"
        "<button id='show-answer' class='outline'>查看解析</button>"
        "<button id='card-direction-switch' class='ghost hidden' type='button' aria-label='交换闪卡提问方向' title='交换提问方向'>⇄</button>"
        "<span id='card-nav' class='hidden'><button id='card-prev' class='ghost' type='button'>上一张</button>"
        "<button id='card-next' class='ghost' type='button'>下一张</button></span></div><div id='feedback-area' class='feedback-card hidden'>"
        "<label class='visually-hidden' for='rating-input'>自评分（1–5）</label>"
        "<input id='rating-input' type='number' min='1' max='5' step='1' inputmode='numeric' placeholder='自评 1–5'>"
        "<label class='visually-hidden' for='feedback-note'>卡点或心得（可选）</label>"
        "<div class='feedback-note-row'><textarea id='feedback-note' rows='1' placeholder='卡点或心得（可选）'></textarea>"
        "<button id='save-rating' class='primary sm'>记录并下一题</button></div></div></div></section>"
        "<div id='session-end-entry' class='session-end-entry hidden'><span>本题未提交的内容只保留在当前会话。</span><div>"
        "<button id='no-time' class='ghost'>跳到下一道题目</button><button id='goto-session-end' class='outline'>提前结束本次练习</button></div></div></div>"
    )
    return shell(
        workspace, workspaces, weak_items, middle, "practice",
        page_type="practice", kp_titles=kp_titles,
    )


def _daily_plan(plan):
    goals = plan.get("goals") or []
    goal_cards = "".join(
        "<article class='goal-card card' data-goal-id='" + html.escape(str(goal.get("id") or "")) + "'"
        + " data-goal-title='" + html.escape(goal.get("title") or "") + "'"
        + " data-goal-kind='" + html.escape(str(goal.get("kind") or "stage")) + "'"
        + " data-goal-start-date='" + html.escape(str(goal.get("start_date") or "")) + "'"
        + " data-goal-deadline='" + html.escape(str(goal.get("deadline") or "")) + "'"
        + " data-goal-description='" + html.escape(str(goal.get("description") or "")) + "'>"
        + "<h3>" + html.escape(goal.get("title") or "未命名目标") + "</h3>"
        + ("<p class='goal-progress'>覆盖进度：" + html.escape(str(goal.get("coverage_progress", goal.get("progress", "暂无")))) + "</p>" if goal.get("coverage_progress", goal.get("progress")) is not None else "")
        + ("<p class='plan-deadline'>" + html.escape(str(goal.get("start_date"))) + " → "
           + html.escape(str(goal["deadline"])) + "</p>" if goal.get("start_date") and goal.get("deadline")
           else ("<p class='plan-deadline'>截止 " + html.escape(str(goal["deadline"])) + "</p>" if goal.get("deadline") else ""))
        + ("<details><summary>查看说明与范围</summary><p>" + html.escape(str(goal.get("description") or goal.get("scope") or "")) + "</p></details>" if goal.get("description") or goal.get("scope") else "")
        + "<div class='goal-card-actions'><button type='button' class='ghost sm goal-edit' data-goal-edit>编辑</button>"
        + "<button type='button' class='ghost sm goal-delete' data-goal-delete>删除</button></div>"
        + "</article>"
        for goal in goals
    ) or "<p class='muted'>暂无已设置的长期或阶段目标。</p>"
    return (
        "<section id='daily-plan' class='daily-plan' aria-label='学习安排'>"
        "<section id='goal-cards' class='goal-cards' aria-label='长期与阶段目标'><h3>长期与阶段目标</h3>" + goal_cards + "</section>"
        "<details class='goal-editor'><summary id='goal-editor-summary'>添加目标</summary><form id='goal-form'>"
        "<input type='hidden' id='goal-id' value=''>"
        "<label for='goal-title'>目标名称</label><input id='goal-title' name='title' required>"
        "<label for='goal-kind'>目标类型</label><select id='goal-kind' name='kind'><option value='stage'>阶段目标</option><option value='long_term'>长期目标</option></select>"
        "<label for='goal-start-date'>开始日期</label><input id='goal-start-date' name='start_date' type='date'>"
        "<label for='goal-deadline'>截止日期</label><input id='goal-deadline' name='deadline' type='date'>"
        "<label for='goal-description'>说明</label><textarea id='goal-description' name='description' rows='3'></textarea>"
        "<div class='goal-form-actions'><button class='primary sm' type='submit' id='goal-submit'>保存目标</button>"
        "<button type='button' class='outline sm hidden' id='goal-cancel'>取消编辑</button></div>"
        "<p id='goal-form-status' class='inline-error' aria-live='polite'></p>"
        "<div class='goal-assist'>"
        "<label for='goal-nl'>说不清字段？一句话让 Agent 帮你填</label>"
        "<textarea id='goal-nl' rows='2' placeholder='例如：期末前掌握第六章计数，重点补鸽巢和组合'></textarea>"
        "<button type='button' class='outline sm' id='goal-assist-send'>让 Agent 填</button>"
        "</div>"
        "</form></details></section>"
    )


SUGGESTION_LIMIT = 20


def suggestion_rows(plan_queue, due_items, problem_kps=None, kp_titles=None, today=None):
    """KP-level on-demand suggestions: plan queue ∪ due rows, one phrase each.

    Pure mapping for the practice page's suggestion entry: overdue and
    due-today rows come first (earliest due date first), plan-only items
    follow; every knowledge point appears at most once with at most one
    human-readable phrase (due phrases win over plan phrases).
    """
    today = today or date.today()
    problem_kps = problem_kps or {}
    kp_titles = kp_titles or {}
    rows = []
    seen = set()

    def add(kp_id, title, phrase):
        if not kp_id or kp_id in seen:
            return
        seen.add(kp_id)
        rows.append({"kp_id": kp_id, "title": title or kp_id, "reason": phrase})

    def due_days(item):
        try:
            return (date.fromisoformat(str(item.get("due_at") or "")[:10]) - today).days
        except ValueError:
            return 0

    due_sorted = sorted(
        (item for item in (due_items or []) if due_days(item) <= 0),
        key=lambda item: (str(item.get("due_at") or ""), str(item.get("item_id") or "")),
    )
    for item in due_sorted:
        days = due_days(item)
        phrase = f"拖了 {abs(days)} 天" if days < 0 else "今天到期"
        if item.get("item_type") == "kp":
            add(item.get("item_id"),
                kp_titles.get(item.get("item_id")) or item.get("label"), phrase)
        else:
            for kp_id in problem_kps.get(item.get("item_id"), []):
                add(kp_id, kp_titles.get(kp_id), phrase)
    for item in plan_queue or []:
        phrase = item.get("reason") or "覆盖仍低"
        for kp_id in item.get("kp_ids") or []:
            add(kp_id, kp_titles.get(kp_id) or item.get("title"), phrase)
    return rows


def _staged_practice_html(workspace_name, suggestions, kp_titles=None):
    kp_titles = kp_titles or {}
    names_json = html.escape(json.dumps(kp_titles, ensure_ascii=False))
    total = len(suggestions)
    rows = "".join(
        "<li class='suggestion-row' data-kp-id='" + html.escape(row["kp_id"]) + "'>"
        "<span class='suggestion-title'>" + html.escape(row["title"]) + "</span>"
        "<span class='suggestion-reason'>" + html.escape(row["reason"]) + "</span>"
        "<button class='outline sm suggestion-join' type='button' data-kp-id='"
        + html.escape(row["kp_id"]) + "'>加入</button></li>"
        for row in suggestions[:SUGGESTION_LIMIT]
    )
    more = total - SUGGESTION_LIMIT
    more_html = (
        f"<p id='suggestions-more' class='muted'>还有 {more} 条。</p>"
        if more > 0 else ""
    )
    return (
        "<section id='staged-practice' class='staged-practice' aria-label='准备练习'>"
        "<div class='section-heading'><div><p class='section-kicker'>准备练习</p>"
        "<h2>今天要练的</h2></div></div>"
        "<ol id='staged-list' class='staged-list' aria-label='已选定的知识点' "
        f"data-kp-names='{names_json}'></ol>"
        "<p id='staged-empty' class='muted staged-empty'>还没选定要练的知识点——"
        f"<a href='/w/{html.escape(workspace_name)}/kps'>去知识点页挑一个</a>。</p>"
        "<div class='suggestion-entry'>"
        "<button id='suggestions-toggle' class='outline sm' type='button' "
        "aria-expanded='false' data-total='" + str(total) + "'>"
        "＋ 加今天要练的" + (f"（{total}）" if total else "") + "</button>"
        "<div id='suggestions' class='suggestions hidden'>"
        "<ol id='suggestion-list' class='suggestion-list'>" + rows + "</ol>"
        + more_html
        + "<p id='suggestions-empty' class='muted hidden'>今天没有建议。</p>"
        "<button id='recalculate-plan' class='ghost sm' type='button'>重新安排</button>"
        "</div></div></section>"
    )


def kp_page(workspace, workspaces, weak_items, pool, kp_id, kp_titles=None):
    detail = queries.kp_detail(pool, kp_id)
    kp = detail["kp"]
    if kp is None:
        return shell(
            workspace, workspaces, weak_items, "<h1>未知知识点</h1>", "kps",
            page_type="kp", object_id=kp_id, kp_titles=kp_titles,
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
    empty_problems = '<p class="muted">—</p>'
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
        f"{problems_html or empty_problems}"
        "</section></div>"
    )
    return shell(
        workspace, workspaces, weak_items, middle, "kps",
        page_type="kp", object_id=kp_id, kp_titles=kp_titles,
    )


def kps_page(workspace, workspaces, weak_items, pool, kp_titles=None):
    prefix = f"{workspace.get('active_course', '')}-{workspace.get('active_chapter', '')}"
    source_kps = pool.kps(prefix)
    problem_counts = {kp["kp_id"]: 0 for kp in source_kps}
    for problem in pool.problems_all():
        for kp_id in problem.get("kp_ids", []):
            if kp_id in problem_counts:
                problem_counts[kp_id] += 1
    states = {row["item_id"]: row["state"] for row in pool.current_states()
              if row["item_type"] == "kp"}
    state_labels = {"needs_work": "重点练习", "review": "可以复习"}
    items = "".join(
        "<li class='knowledge-row' data-kp-order='" + str(index) + "' data-kp-title='" + html.escape(item.get("knowledge_item") or "")
        + "' data-kp-problem-count='" + str(problem_counts.get(item["kp_id"], 0))
        + "' data-kp-state='" + html.escape(states.get(item["kp_id"], "unmarked"))
        + "' data-kp-importance='" + html.escape(item.get("importance") or "supplementary") + "'>"
        "<label><input type='checkbox' data-kp-selection data-kp-id='" + html.escape(item["kp_id"]) + "'> "
        "<a href='/w/" + html.escape(workspace["name"]) + "/kp/" + html.escape(item["kp_id"]) + "'>" + html.escape(item["knowledge_item"]) + "</a>"
        "<span class='knowledge-meta'>" + str(problem_counts.get(item["kp_id"], 0)) + " 题"
        + (" · " + state_labels[states[item["kp_id"]]] if states.get(item["kp_id"]) in state_labels else "")
        + "</span></label></li>"
        for index, item in enumerate(source_kps)
    )
    empty_items = '<li class="muted">暂无知识点</li>'
    middle = (_page_header("学习 / 当前章节", "知识点", "明确选择本轮练习范围；阅读和导航不会改变选择。")
        + "<div class='page-content'><div class='knowledge-sort-bar'><label for='knowledge-sort'>排序</label><select id='knowledge-sort'>"
        + "<option value='source' selected>课程顺序</option><option value='title'>名称</option>"
        + "<option value='problem_count'>题目数量</option><option value='state'>学习状态</option>"
        + "<option value='importance'>重要性</option></select>"
        + "<button id='knowledge-sort-direction' class='ghost sm' type='button' aria-label='切换排序方向' title='切换排序方向'>↑</button></div>"
        + "<section class='support-section knowledge-index'><div class='section-heading'><div><p class='section-kicker'>当前排序</p><h2>本章知识点</h2></div></div>"
        + f"<ul id='knowledge-list' class='knowledge-list'>{items or empty_items}</ul></section></div>")
    return shell(
        workspace, workspaces, weak_items, middle, "kps",
        page_type="kps", kp_titles=kp_titles,
    )


def graph_page(workspace, workspaces, weak_items, has_artifact, kp_titles=None):
    middle = (_page_header("知识网络 / 当前章节", "知识图谱", "勾选知识点后，可将同一范围交给练习。")
        + "<div class='page-content graph-content'><section class='graph-panel' aria-label='知识图谱'><div class='graph-toolbar'>"
        "<label class='visually-hidden' for='graph-search'>搜索知识点</label><input id='graph-search' placeholder='搜索知识点'>"
        "<label for='graph-projection'>视图</label><select id='graph-projection' aria-describedby='graph-projection-hint' title='按已有指标调整图谱形态'>"
        "<option value='structure' selected>关系结构</option><option value='problem_count'>题目数量</option>"
        "<option value='importance'>重要性</option><option value='state'>学习状态</option></select>"
        "<span id='graph-projection-hint' class='graph-projection-hint'>关系决定位置 · 大小表示题量</span>"
        "<details id='graph-state-filter' class='graph-filter-menu'><summary id='graph-filter-summary'>筛选状态</summary>"
        "<fieldset><legend>显示哪些学习状态</legend>"
        "<label><input id='graph-filter-needs_work' type='checkbox' value='needs_work'>重点练习</label>"
        "<label><input id='graph-filter-review' type='checkbox' value='review'>可以复习</label>"
        "<label><input id='graph-filter-mastered' type='checkbox' value='mastered'>已掌握</label>"
        "<label><input id='graph-filter-null' type='checkbox' value='null'>未标记</label>"
        "<button id='graph-filter-clear' class='ghost sm' type='button' disabled>清除筛选</button>"
        "</fieldset></details>"
        "<label class='graph-gravity-label' for='graph-gravity'>聚拢</label><input id='graph-gravity' type='range' min='0' max='100' value='30' aria-label='调整图谱聚拢程度' title='调整图谱聚拢程度'>"
        "<div class='graph-zoom' aria-label='缩放'><button id='graph-zoom-out' class='ghost sm' title='缩小'>−</button><button id='graph-zoom-in' class='ghost sm' title='放大'>＋</button><button id='graph-fit' class='outline sm'>适应画布</button></div>"
        "</div><div id='graph-canvas' data-kp-selection-surface tabindex='0' aria-label='知识图谱画布'></div></section></div>")
    return shell(
        workspace, workspaces, weak_items, middle, "graph", graph_mode=True,
        page_type="graph", kp_titles=kp_titles,
    )


def session_end_page(workspace, workspaces, weak_items, kp_titles=None):
    middle = (
        _page_header(
            "练习 / 收束本轮", "会话末统一自评",
            "只补充尚未评分的题目与闪卡；已写入的记录不会重复出现。",
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
                 page_type="session-end", kp_titles=kp_titles)


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
    actionable = [
        item for item in weak_items
        if item.get("score", 0) > 0.2 or item.get("reasons")
    ]
    weak_html = "".join(
        f"<div class='weak-item'><a href='/w/{workspace['name']}/kp/{item['kp_id']}'>"
        f"<span class='weak-title'>{html.escape(item['knowledge_item'])}</span>"
        "</a></div>"
        for item in actionable
    )
    rail_label = "优先回看" if actionable else "本章知识点"
    empty = "暂无明确薄弱证据" if not actionable else "暂无提醒"
    empty_weak = '<p class="score">' + empty + "</p>"
    return (
        "<section class='side-section workspace-switcher'>"
        "<p class='side-label'>工作区</p>"
        f"<select id='workspace-select' aria-label='切换工作区'>{options}</select>"
        "</section>"
        "<nav class='side-section primary-nav' aria-label='工作台导航'>"
        "<p class='side-label'>页面</p>"
        f"{nav}</nav>"
        "<section class='side-section weak-section'>"
        f"<div class='side-heading'><p class='side-label'>{rail_label}</p></div>"
        f"<div class='weak-list'>{weak_html or empty_weak}</div>"
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


def time_view_html():
    return (
        "<section id='time-view' class='card time-view hidden' aria-label='时间安排'>"
        "<div class='section-heading'><div><p class='section-kicker'>实验视图</p>"
        "<h2>时间安排</h2></div>"
        "<button id='workload-prefill' class='outline sm hidden' type='button'>让 Agent 看看</button>"
        "</div>"
        "<div id='calendar-grid' class='calendar-grid'></div>"
        "<div id='workload-bars' class='workload-bars'></div>"
        "<p id='time-view-empty' class='muted hidden'>最近没有安排在日历上。</p>"
        "</section>"
    )
