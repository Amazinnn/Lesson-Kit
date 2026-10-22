"""Server-side HTML for the records surface."""

import html
import math


VIEWS = {"overview", "runs", "attempts", "wrong"}

# 仪表盘卡的迷你图高（layout-spec §5.6「迷你图高 28」）
_MINI_HEIGHT = 28


def _verdict_mark(kind):
    """判定的几何符号（§3.6 冗余状态通道：勾 / 叉 / 空心环）。

    「对」的勾形由 CSS 侧 `.record-verdict-ok::before/::after` 画（墨色 2px 双段），
    这里只补 CSS 侧尚未画的两种：错 = 红叉、未判定 = 淡墨空心环。
    """
    if kind == "bad":
        return (
            "<svg class='record-verdict-mark' width='9' height='9' viewBox='0 0 10 10' "
            "aria-hidden='true' focusable='false' "
            "style='vertical-align:-1px;margin-right:4px'>"
            "<path d='M1.6 1.6 L8.4 8.4 M8.4 1.6 L1.6 8.4' fill='none' "
            "style='stroke:var(--role-red-ink);stroke-width:2;stroke-linecap:round'/>"
            "</svg>"
        )
    return (
        "<svg class='record-verdict-mark' width='9' height='9' viewBox='0 0 10 10' "
        "aria-hidden='true' focusable='false' "
        "style='vertical-align:-1px;margin-right:4px'>"
        "<circle cx='5' cy='5' r='3.2' fill='none' "
        "style='stroke:var(--ink-muted);stroke-width:1.6'/>"
        "</svg>"
    )


def _rating_marks(rating):
    """自评 = 彩色圆点 + 星级形状（零文字标签）。"""
    if not isinstance(rating, int) or not 1 <= rating <= 5:
        return ""
    return (
        "<span class='record-rating'>"
        "<svg class='record-rating-dot' width='8' height='8' viewBox='0 0 8 8' "
        "aria-hidden='true' focusable='false' "
        "style='vertical-align:-1px;margin-right:4px'>"
        "<circle cx='4' cy='4' r='4' style='fill:var(--role-yellow)'/></svg>"
        f"{'★' * rating}{'☆' * (5 - rating)}"
        "</span>"
    )


def _attempt_rows(workspace_name, records):
    """作答明细 = 圆角小卡流（12px、不描边、靠留白 + `--elev-1` 分隔）。

    六项字段一个不少：题目 + 评语 + 摘录（题目下第二、三行）· 判定（结构块 +
    几何符号 + 文字三通道）· 自评（彩色圆点 + 星级形状，零文字标签）·
    时间（卡片右上角，次级墨）。
    """
    rows = []
    for record in records:
        verdict = record.get("verdict")
        if verdict is None:
            badge, verdict_class = "未判定", "record-verdict-open"
            # 「对」的勾形在 CSS 侧；其余两态的几何符号在这里补上。
            mark = _verdict_mark("open")
        elif verdict:
            badge, verdict_class = "对", "record-verdict-ok"
            mark = ""
        else:
            badge, verdict_class = "错", "record-verdict-bad"
            mark = _verdict_mark("bad")
        rating = record.get("rating")
        title = html.escape(record.get("title") or "未命名题目")
        if record.get('deleted_content'):
            title += '（题目已删除）'
        answer = html.escape((record.get("answer_text") or "").strip())
        note = html.escape(
            (record.get("feedback_note") or record.get("note") or "").strip())
        link = (
            f"/w/{html.escape(workspace_name, quote=True)}/practice"
            f"?problem={html.escape(record['problem_id'], quote=True)}"
        )
        rows.append(
            "<article class='record-row card record-attempt' style='border:0'>"
            f"<header><a class='record-title' href='{link}'>{title}</a>"
            f"<span class='record-verdict {verdict_class}'>{mark}{badge}</span>"
            + _rating_marks(rating)
            + "<time class='record-time'>"
            + html.escape(str(record.get("created_at") or ""))
            + "</time></header>"
            + (f"<p class='record-note muted'>{note}</p>" if note else "")
            + (f"<p class='record-answer'>{answer}</p>" if answer else "")
            + "</article>"
        )
    return "".join(rows) or "<p class='muted'>这里还没有记录。</p>"


def _run_card(run):
    status = run.get("status")
    if status == "active":
        state = "进行中"
    elif status == "completed":
        state = "已完成"
    else:
        state = "已结束"
    kind = {
        "paper": "试卷",
        "practice_set": "试卷",
        "agent": "Agent",
        "quick": "练习",
    }.get(run.get("source_kind"), "练习")
    mode = {
        "exam": "综合题",
        "micro": "小测",
        "yes_no": "判断",
        "flash_card": "闪卡",
    }.get(run.get("practice_mode"), run.get("practice_mode") or "练习")
    rating_mode = {
        "immediate": "逐题自评",
        "batch": "统一自评",
        "off": "关闭自评",
    }.get(run.get("rating_mode"), "")
    progress = run.get("progress") or {}
    completed = int(progress.get("completed") or 0)
    total = int(progress.get("total") or 0)
    stuck = int(progress.get("stuck") or 0)
    label = html.escape(run.get("source_label") or "临时练习")
    if run.get('source_deleted'):
        label += '（试卷已删除）'
    when = run.get("finished_at") or run.get("started_at") or ""
    meta = " · ".join(filter(None, [
        kind, mode, rating_mode, f"{completed}/{total} 项",
        f"{stuck} 个不会" if stuck else "",
    ]))
    replay = ""
    if run.get("run_id") is not None:
        replay = (
            "<div class='record-run-actions'>"
            + (f"<button type='button' data-run-view='{int(run['run_id'])}'>查看本次答卷</button>"
               if run.get("status") == "completed" else "")
            +
            f"<button type='button' data-run-replay='{int(run['run_id'])}'>再做一次</button>"
            "</div>"
        )
    return (
        "<article class='record-run card'>"
        "<header><div>"
        f"<p class='section-kicker'>{html.escape(state)}</p>"
        f"<h3>{label}</h3></div>"
        f"<time>{html.escape(str(when))}</time></header>"
        f"<p class='muted'>{html.escape(meta)}</p>"
        "<div class='record-run-progress' aria-label='完成进度'>"
        f"<span style='width:{(completed / total * 100) if total else 0:.1f}%'></span>"
        "</div>" + replay + "</article>"
    )


def _runs(active, runs, limit=None):
    items = []
    if active:
        items.append(_run_card(active))
    selected = runs[:limit] if limit else runs
    items.extend(_run_card(run) for run in selected)
    return "".join(items) or "<p class='muted'>还没有完整的练习轮次记录。</p>"


def _practice_set_history(practice_sets):
    if not practice_sets:
        return ""
    cards = []
    for item in practice_sets:
        runs = item.get("runs") or []
        latest = runs[0] if runs else {}
        accuracy = latest.get("accuracy")
        rating = latest.get("average_rating")
        meta = [
            f"已完成 {item.get('count') or 0} 次",
            "最近正确率 —" if accuracy is None else f"最近正确率 {accuracy * 100:.0f}%",
            "最近自评 —" if rating is None else f"最近自评 {rating:.1f} / 5",
            f"最近不会 {latest.get('stuck') or 0} 个",
        ]
        history = []
        for run in runs[:8]:
            run_accuracy = run.get("accuracy")
            run_rating = run.get("average_rating")
            history.append(
                "<li>"
                f"<time>{html.escape(str(run.get('finished_at') or ''))}</time>"
                " · "
                + (
                    "正确 —"
                    if run_accuracy is None
                    else f"正确 {run.get('correct') or 0}/{run.get('judged') or 0}"
                )
                + " · "
                + (
                    "自评 —"
                    if run_rating is None
                    else f"自评 {run_rating:.1f} / 5"
                )
                + f" · 不会 {run.get('stuck') or 0} 个"
                + "</li>"
            )
        changed = (
            "<p class='record-filter-note'>这张试卷的题目或顺序曾变化；"
            "下面按每次实际内容分别显示，不合并成一条趋势。</p>"
            if item.get("content_changed") else ""
        )
        cards.append(
            "<article class='record-run card'>"
            f"<h3>{html.escape(item.get('source_label') or '未命名试卷')}{'（试卷已删除）' if item.get('source_deleted') else ''}</h3>"
            f"<p class='muted'>{html.escape(' · '.join(meta))}</p>"
            + changed
            + "<ul>"
            + "".join(history)
            + "</ul></article>"
        )
    return (
        "<section class='support-section'><div class='section-heading'><div>"
        "<p class='section-kicker'>同一试卷</p><h2>多次练习</h2></div>"
        "<p>只使用每次实际留下的作答、自评和不会记录。</p></div>"
        + "".join(cards)
        + "</section>"
    )


def _verdict_ring(correct, judged):
    """判定分布的迷你环：对（中性墨）与错（红）各占一段，弧长 = 占比。

    整圈 = 已判定的作答数，所以墨色弧的占比就是卡片上的正确率；
    「对 / 错 / 未判定」三档的完整分布在下方「判定分布」图里逐行标数。
    """
    if not judged:
        return ""
    size, radius, stroke = _MINI_HEIGHT, 9.0, 4.0
    center = size / 2
    circumference = 2 * math.pi * radius
    share = max(0.0, min(1.0, correct / judged))
    return (
        f"<svg class='record-ring' width='{size}' height='{size}' "
        f"viewBox='0 0 {size} {size}' aria-hidden='true' focusable='false' "
        "style='display:block'>"
        f"<circle cx='{center}' cy='{center}' r='{radius}' fill='none' "
        f"style='stroke:var(--role-red-ink);stroke-width:{stroke}'/>"
        f"<circle cx='{center}' cy='{center}' r='{radius}' fill='none' "
        f"stroke-dasharray='{share * circumference:.2f} {circumference:.2f}' "
        f"transform='rotate(-90 {center} {center})' "
        f"style='stroke:var(--ink-strong);stroke-width:{stroke}'/>"
        "</svg>"
    )


def _rating_spark(ratings):
    """平均自评的迷你图：1–5 分每档一根条（黄只承载面积，不承载文字）。"""
    counts = [int(item.get("count") or 0) for item in ratings]
    if not counts or max(counts) <= 0:
        return ""
    top = max(counts)
    bars = "".join(
        f"<div class='record-spark-bar' style='flex:1;height:{count / top * 100:.1f}%;"
        "background:var(--role-yellow)'></div>"
        for count in counts
    )
    return (
        "<div class='record-spark' style='display:flex;gap:4px;align-items:flex-end;"
        f"height:{_MINI_HEIGHT}px'>" + bars + "</div>"
    )


def _summary_cards(summary, runs, ratings):
    """统计区 = 仪表盘卡片（一主三辅，各带一个迷你图）。

    四个汇总数字的**取值与口径与改造前逐位相同**（spec delta「The summary
    figures keep their present values」）—— 这里只改呈现形态：
    卡片承载数字，迷你图承载分布。
    """
    accuracy = summary.get("accuracy")
    average = summary.get("average_rating")
    completed_runs = sum(run.get("status") == "completed" for run in runs)
    values = [
        ("作答次数", str(summary.get("attempts") or 0)),
        ("完成练习", str(completed_runs)),
        ("客观题正确率", "—" if accuracy is None else f"{accuracy * 100:.0f}%"),
        ("平均自评", "—" if average is None else f"{average:.1f} / 5"),
    ]
    minis = [
        None,  # 迷你趋势线（19.4 补：每天的作答次数）
        None,  # 已完成练习轮次（19.4 补）
        _verdict_ring(
            int(summary.get("correct") or 0), int(summary.get("judged") or 0)),
        _rating_spark(ratings),
    ]
    cards = []
    for index, (label, value) in enumerate(values):
        lead = index == 0
        classes = "record-summary card" + (" record-summary-lead" if lead else "")
        number = (
            "<strong style='font-size:30px;line-height:36px'>"
            if lead else "<strong>"
        ) + html.escape(value) + "</strong>"
        mini = minis[index]
        cards.append(
            f"<article class='{classes}'>"
            f"<span>{html.escape(label)}</span>"
            f"{number}"
            + (f"<div class='record-summary-mini' style='margin-top:8px'>{mini}</div>"
               if mini else "")
            + "</article>"
        )
    return (
        "<section class='record-summary-grid' aria-label='记录摘要'>"
        + "".join(cards)
        + "</section>"
    )


def _verdict_distribution(summary):
    """按判定分布：对 / 错 / 未判定 的作答数。

    数据源是现成读路径 `overview['summary']`（attempts / judged / correct），
    零新增查询、零写入。条长按「全部作答数」归一，三段之和即全部作答数。
    """
    attempts = int(summary.get("attempts") or 0)
    judged = int(summary.get("judged") or 0)
    correct = int(summary.get("correct") or 0)
    rows = [
        ("对", correct, "var(--ink-strong)"),
        ("错", max(judged - correct, 0), "var(--role-red-ink)"),
        ("未判定", max(attempts - judged, 0), "var(--ink-faint)"),
    ]
    items = []
    for label, count, color in rows:
        width = count / attempts * 100 if attempts else 0
        items.append(
            "<div class='record-rating-row'>"
            f"<span>{label}</span>"
            "<div class='record-rating-track'>"
            f"<span style='width:{width:.1f}%;background:{color}'></span></div>"
            f"<strong>{count}</strong></div>"
        )
    return (
        "<div class='record-rating-chart' aria-label='判定分布'>"
        + "".join(items)
        + "</div>"
    )


def _trend_chart(trend):
    maximum = max((day.get("attempts", 0) for day in trend), default=0)
    if maximum == 0:
        return "<p class='muted'>最近 14 天还没有作答。</p>"
    bars = []
    for day in trend:
        attempts = day.get("attempts", 0)
        height = (attempts / maximum * 100) if maximum else 0
        label = str(day.get("date") or "")[5:]
        bars.append(
            "<div class='record-day'>"
            "<div class='record-day-bar-wrap'>"
            f"<span class='record-day-value'>{attempts or ''}</span>"
            f"<span class='record-day-bar{' empty' if attempts == 0 else ''}' "
            f"style='height:{height:.1f}%'></span>"
            "</div>"
            f"<span class='record-day-label'>{html.escape(label)}</span>"
            "</div>"
        )
    return "<div class='record-trend' aria-label='最近 14 天作答量'>" + "".join(bars) + "</div>"


def _activity_calendar(activity):
    if not activity or not any(day.get("attempts") for day in activity):
        return "<p class='muted'>最近 12 周还没有作答。</p>"
    labels = "".join(
        f"<span class='record-activity-weekday'>{label}</span>"
        for label in ("一", "二", "三", "四", "五", "六", "日")
    )
    cells = []
    for day in activity:
        if day.get("future"):
            cells.append("<span class='record-activity-day future' aria-hidden='true'></span>")
            continue
        attempts = int(day.get("attempts") or 0)
        level = 0 if attempts == 0 else 1 if attempts == 1 else 2 if attempts <= 3 else 3 if attempts <= 7 else 4
        date_text = str(day.get("date") or "")
        cells.append(
            f"<span class='record-activity-day level-{level}' "
            f"title='{html.escape(date_text)} · {attempts} 次作答' "
            f"aria-label='{html.escape(date_text)}，{attempts} 次作答'></span>"
        )
    return (
        "<div class='record-activity' aria-label='最近 12 周作答日历'>"
        + labels + "".join(cells) + "</div>"
        "<p class='muted'>颜色只表示当天的作答次数。</p>"
    )


def _rating_chart(ratings):
    maximum = max((item.get("count", 0) for item in ratings), default=0)
    if maximum == 0:
        return "<p class='muted'>还没有带自评的作答。</p>"
    rows = []
    for item in ratings:
        count = item.get("count", 0)
        width = (count / maximum * 100) if maximum else 0
        rows.append(
            "<div class='record-rating-row'>"
            f"<span>{item['rating']} 分</span>"
            "<div class='record-rating-track'>"
            f"<span style='width:{width:.1f}%'></span></div>"
            f"<strong>{count}</strong></div>"
        )
    return "<div class='record-rating-chart' aria-label='自评分布'>" + "".join(rows) + "</div>"


def _tabs(workspace_name, active_view):
    base = f"/w/{html.escape(workspace_name, quote=True)}/records"
    items = [
        ("overview", "概览"),
        ("runs", "练习 / 试卷"),
        ("attempts", "作答明细"),
        ("wrong", "错题"),
    ]
    return (
        "<nav class='record-tabs' aria-label='记录视图'>"
        + "".join(
            f"<a class='record-tab{' active' if key == active_view else ''}' "
            f"href='{base}{'' if key == 'overview' else '?view=' + key}'>{label}</a>"
            for key, label in items
        )
        + "</nav>"
    )


def content(workspace_name, overview, view="overview", problem_id=None, limit=None):
    view = view if view in VIEWS else "overview"
    records = overview.get("records") or []
    runs = overview.get("runs") or []
    active = overview.get("active_run")

    def _needs_review(record):
        # sqlite returns verdict as 0/1, never bool — compare by value.
        verdict = record.get("verdict")
        return ((verdict is not None and not verdict)
                or record.get("status") in {"wrong", "stuck"})

    filtered = [record for record in records if _needs_review(record)]
    notice = ""
    if problem_id:
        notice = (
            "<p class='record-filter-note'>正在按单题过滤。"
            f"<a href='/w/{html.escape(workspace_name, quote=True)}/records'>查看全部记录</a></p>"
        )
    elif (limit and view in {"attempts", "wrong"}
            and len(records) >= limit):
        notice = (
            f"<p class='record-filter-note'>已载入最近 {limit} 条，"
            "更早的记录未显示。</p>"
        )

    if view == "runs":
        body = (
            _practice_set_history(overview.get("practice_sets") or [])
            + "<section class='support-section'><div class='section-heading'><div>"
            "<p class='section-kicker'>练习 / 试卷</p><h2>每一轮做了什么</h2></div>"
            "<p>完成或替换一轮练习后保留快照；试卷记录保留当时的试卷名称。</p></div>"
            + _runs(active, runs)
            + "</section>"
        )
    elif view == "attempts":
        body = (
            "<section class='support-section'><div class='section-heading'><div>"
            "<p class='section-kicker'>作答明细</p><h2>逐题记录</h2></div>"
            f"<p>{len(records)} 条已载入。</p></div>"
            + _attempt_rows(workspace_name, records)
            + "</section>"
        )
    elif view == "wrong":
        body = (
            "<section class='support-section'><div class='section-heading'><div>"
            "<p class='section-kicker'>错题</p><h2>需要回看的作答</h2></div>"
            f"<p>{len(filtered)} 条客观判错或卡住的记录。</p></div>"
            + _attempt_rows(workspace_name, filtered)
            + "</section>"
        )
    else:
        summary = overview.get("summary") or {}
        body = (
            _summary_cards(summary, runs, overview.get("ratings") or [])
            + "<section class='card record-chart-card record-activity-card'>"
            "<div class='section-heading'><div><p class='section-kicker'>最近 12 周</p>"
            "<h2>作答日历</h2></div></div>"
            + _activity_calendar(overview.get("activity") or [])
            + "</section>"
            + "<section class='record-dashboard-grid'>"
            "<article class='card record-chart-card'><div class='section-heading'><div>"
            "<p class='section-kicker'>最近 14 天</p><h2>作答量</h2></div></div>"
            + _trend_chart(overview.get("trend") or [])
            + "</article>"
            "<article class='card record-chart-card'><div class='section-heading'><div>"
            "<p class='section-kicker'>自评</p><h2>1–5 分分布</h2></div></div>"
            + _rating_chart(overview.get("ratings") or [])
            + "</article>"
            "<article class='card record-chart-card'><div class='section-heading'><div>"
            "<p class='section-kicker'>判定</p><h2>判定分布</h2></div></div>"
            + _verdict_distribution(summary)
            + "</article></section>"
            "<section class='support-section record-section'><div class='section-heading'><div>"
            "<p class='section-kicker'>最近练习</p><h2>练习 / 试卷</h2></div>"
            f"<a href='/w/{html.escape(workspace_name, quote=True)}/records?view=runs'>查看全部</a></div>"
            + _runs(active, runs, limit=5)
            + "</section>"
            "<section class='support-section record-section'><div class='section-heading'><div>"
            "<p class='section-kicker'>最近作答</p><h2>逐题明细</h2></div>"
            f"<a href='/w/{html.escape(workspace_name, quote=True)}/records?view=attempts'>查看全部</a></div>"
            + _attempt_rows(workspace_name, records[:8])
            + "</section>"
        )
    return (
        "<div class='page-content records-center'>"
        + _tabs(workspace_name, view)
        + notice
        + body
        + "</div>"
    )
