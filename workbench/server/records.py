"""Server-side HTML for the records surface."""

import html
import math


VIEWS = {"overview", "runs", "attempts", "wrong"}

# 仪表盘卡的迷你图高（layout-spec §5.6「迷你图高 28」）
_MINI_HEIGHT = 28

# 14 天负荷柱：与时间视图共用 `.workload-bars` 一族类名（CSS 已落）
_BAR_MAX_PX = 132        # 柱高上限（与时间视图同一档）
_BAR_STAGGER_MS = 24     # 逐柱错峰（decisions.md「负荷柱逐柱错峰 24ms」）

# 作答日历的**五档**强度（spec「The calendar levels are fixed and legible」）：
# 档 0 = 0 次 · 档 1 = 1 次 · 档 2 = 2–3 次 · 档 3 = 4–7 次 · 档 4 = ≥8 次。
# 每档 = (档号, 下界, 上界)；上界为 None 表示无上界。
# **唯一真源**：格子分档（`_calendar_level`）与页面图例文案（`_activity_legend`）都取这里。
_CALENDAR_LEVELS = (
    (0, 0, 0),
    (1, 1, 1),
    (2, 2, 3),
    (3, 4, 7),
    (4, 8, None),
)

# 作答日历格子的**高度**：fill 之外的第二重编码
# （spec「The activity calendar is compact and decodable」—— 强度由 fill 与 height 共同编码）。
# 高度**只由当天的次数**决定 ⇒ 不新增任何统计口径；
# 同一档内次数越多格子越高（单调），跨档也不低于低档；零负荷日仍占位（基线位置不塌）。
_CALENDAR_MAX_COUNT = 8      # 高度封顶对应的次数（= 最高档下界，不另设刻度）
_CALENDAR_CELL_MIN_PX = 4    # 零负荷日的占位高度
_CALENDAR_CELL_MAX_PX = 28   # 最高档的格子高度
_CALENDAR_ROW_PX = 30        # 日历行高（每行等高 ⇒ 行内共享一条基线）
_CALENDAR_ROWS = 7           # 日历的行数 = 星期数（一列 = 一周，与 CSS 的
                             # `grid-template-rows: repeat(7, 30px)` 同值）
_CALENDAR_STAGGER_MS = 24    # 日历扩散的逐柱错峰（motion-spec §2.1 第 19 项：
                             # 「逐柱错峰 24ms」—— 柱 = 列，一列一起动）


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


def _wrong_reason(record):
    """错因摘要：只说现成字段已经记下的事实（判定 / 作答状态），不发明新口径。"""
    reasons = []
    verdict = record.get("verdict")
    if verdict is not None and not verdict:
        reasons.append("判定为错")
    status = record.get("status")
    if status == "stuck":
        reasons.append("不会")
    elif status == "wrong":
        reasons.append("标记为错")
    return " · ".join(reasons)


def _attempt_rows(workspace_name, records, wrong=False):
    """作答明细 = 圆角小卡流（12px、不描边、靠留白 + `--elev-1` 分隔）。

    六项字段一个不少：题目 + 评语 + 摘录（题目下第二、三行）· 判定（结构块 +
    几何符号 + 文字三通道）· 自评（彩色圆点 + 星级形状，零文字标签）·
    时间（卡片右上角，次级墨）。

    错题视图用同一族卡片，但**视觉重一档**（`--elev-2`）并补一行错因摘要。
    """
    rows = []
    for record in records:
        verdict = record.get("verdict")
        if verdict is None:
            badge, verdict_class = "未判定", "record-verdict-open"
        elif verdict:
            badge, verdict_class = "对", "record-verdict-ok"
        else:
            badge, verdict_class = "错", "record-verdict-bad"
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
        reason = _wrong_reason(record) if wrong else ""
        if wrong:
            card = ("<article class='record-row card record-wrong' "
                    "style='box-shadow:var(--elev-2)'>")
        else:
            card = "<article class='record-row card record-attempt'>"
        summary = ""
        if reason or note:
            summary = (
                "<p class='record-note'>"
                + (f"<strong>{html.escape(reason)}</strong>" if reason else "")
                + (f" {note}" if (reason and note) else note)
                + "</p>"
            )
        rows.append(
            card
            + f"<header><a class='record-title' href='{link}'>{title}</a>"
            f"<span class='record-verdict {verdict_class}'>{badge}</span>"
            + _rating_marks(rating)
            + "<time class='record-time'>"
            + html.escape(str(record.get("created_at") or ""))
            + "</time></header>"
            + summary
            + (f"<p class='record-answer'>{answer}</p>" if answer else "")
            + "</article>"
        )
    return "".join(rows) or "<p class='muted'>暂无记录</p>"


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
    return "".join(items) or "<p class='muted'>暂无练习轮次</p>"


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
            "最近判定 —" if accuracy is None else (
                f"最近判定 {latest.get('correct') or 0}/"
                f"{latest.get('judged') or 0}"),
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
                    "判定 —"
                    if run_accuracy is None
                    else f"判定正确 {run.get('correct') or 0}/{run.get('judged') or 0}"
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
        cards.append(
            "<article class='record-run card'>"
            f"<h3>{html.escape(item.get('source_label') or '未命名试卷')}{'（试卷已删除）' if item.get('source_deleted') else ''}</h3>"
            f"<p class='muted'>{html.escape(' · '.join(meta))}</p>"
            "<ul>"
            + "".join(history)
            + "</ul></article>"
        )
    return (
        "<section class='support-section'><div class='section-heading'><div>"
        "<h2>多次练习</h2></div>"
        + "".join(cards)
        + "</section>"
    )


def _verdict_ring(correct, judged):
    """判定分布的迷你环：对（中性墨）与错（红）各占一段，弧长 = 占比。

    整圈 = 已判定的作答数，所以墨色弧的占比就是卡片上的判定占比；
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


def _sparkline(values):
    """迷你趋势线：每天一个点 —— 画的就是**每天的作答次数**（`_trend` 的 attempts）。

    完整数值在下方「最近 14 天」柱图里逐日标出，所以这层是装饰
    （`aria-hidden`），不重复读一遍。
    """
    if not values:
        return ""
    top = max(values)
    if top <= 0:
        return ""
    width, height = 100, _MINI_HEIGHT
    span = width / (len(values) - 1) if len(values) > 1 else width
    points = " ".join(
        f"{index * span:.2f},{height - 1 - value / top * (height - 2):.2f}"
        for index, value in enumerate(values)
    )
    return (
        f"<svg class='record-spark' width='100%' height='{height}' "
        f"viewBox='0 0 {width} {height}' preserveAspectRatio='none' "
        "aria-hidden='true' focusable='false' "
        f"style='display:block;width:100%;height:{height}px'>"
        f"<polyline points='{points}' fill='none' style='stroke:var(--role-blue)' "
        "stroke-width='1.5' stroke-linejoin='round' stroke-linecap='round' "
        "vector-effect='non-scaling-stroke'/>"
        "</svg>"
    )


def _run_blocks(runs, limit=12):
    """已完成练习轮次的迷你图：最近若干轮，每轮一块。

    实心 = 已完成、空心 = 未完成 —— 几何冗余通道，不靠颜色单独承载状态。
    """
    if not runs:
        return ""
    blocks = []
    for run in runs[:limit]:
        done = run.get("status") == "completed"
        style = (
            "width:8px;height:8px;border-radius:2px;background:var(--role-blue)"
            if done else
            "width:8px;height:8px;border-radius:2px;background:transparent;"
            "box-shadow:inset 0 0 0 1.5px var(--ink-faint)"
        )
        blocks.append(f"<div class='record-spark-block' style='{style}'></div>")
    return (
        "<div class='record-spark' style='display:flex;gap:4px;align-items:center'>"
        + "".join(blocks)
        + "</div>"
    )


def _summary_cards(summary, runs, trend, ratings):
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
        ("客观题判定", "—" if accuracy is None else (
            f"{int(summary.get('correct') or 0)}/{int(summary.get('judged') or 0)}")),
        ("平均自评", "—" if average is None else f"{average:.1f} / 5"),
    ]
    minis = [
        _sparkline([int(day.get("attempts") or 0) for day in trend]),
        _run_blocks(runs),
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

    类名走 `.record-verdict-dist*` 一族（判定是三态语义，自评是星级语义，两族分开；
    `.record-rating-*` 留给 `_rating_chart` 的自评分布）。
    条形颜色由**状态类**给（`--ok` / `--bad` / `--open`），不再内联覆盖。
    """
    attempts = int(summary.get("attempts") or 0)
    judged = int(summary.get("judged") or 0)
    correct = int(summary.get("correct") or 0)
    rows = [
        ("对", correct, "record-verdict-dist-fill--ok"),
        ("错", max(judged - correct, 0), "record-verdict-dist-fill--bad"),
        ("未判定", max(attempts - judged, 0), "record-verdict-dist-fill--open"),
    ]
    items = []
    for label, count, fill_class in rows:
        width = count / attempts * 100 if attempts else 0
        items.append(
            "<div class='record-verdict-dist-row'>"
            f"<span class='record-verdict-dist-label'>{label}</span>"
            "<div class='record-verdict-dist-track'>"
            f"<span class='record-verdict-dist-fill {fill_class}' "
            f"style='width:{width:.1f}%'></span></div>"
            f"<strong class='record-verdict-dist-count'>{count}</strong></div>"
        )
    return (
        "<div class='record-verdict-dist' aria-label='判定分布'>"
        + "".join(items)
        + "</div>"
    )


def _trend_chart(trend):
    """最近 14 天的作答量 = 负荷柱（与时间视图共用 `.workload-bars` 一族类名）。

    · **共享基线**：`.workload-bars` 的下边框就是基线；零负荷日不画柱，
      但保留在基线上的位置（不错位占位）。
    · **峰值日**按形态（平顶方块）+ 颜色（黄，`.bar-col.peak`）区分。
    · **重日**（当天作答数 ≥ 非零日均的 2 倍）加几何冗余标记
      （`.bar-heavy-flag` 红点），不靠一堆解释文字。
    · 每根柱的**精确数值**标在各自柱上方（`.bar-value`）。
    · **逐柱错峰 24ms** 生长（`animation-delay`），只动 transform / opacity；
      柱的静态样式就是终态 ⇒ 动效偏好关或系统 reduced-motion 生效时，
      柱直接落最终高度，数值 / 峰值标记 / 重日标记同时就位。
    """
    counts = [int(day.get("attempts") or 0) for day in trend]
    maximum = max(counts, default=0)
    if maximum == 0:
        return "<p class='muted'>最近 14 天暂无作答</p>"
    nonzero = [count for count in counts if count > 0]
    average = sum(nonzero) / len(nonzero) if nonzero else 0
    heavy_threshold = average * 2
    peak_index = counts.index(maximum)
    columns = []
    for index, day in enumerate(trend):
        count = counts[index]
        date = str(day.get("date") or "")
        height = round(count / maximum * _BAR_MAX_PX)
        state = " peak" if index == peak_index else ""
        heavy = count > 0 and count >= heavy_threshold
        if heavy:
            state += " heavy"
        bar = ""
        if count:
            # 峰值日 = 平顶方块（形态）＋ 黄（颜色，由 `.bar-col.peak` 给）
            form = "border-radius:0;" if index == peak_index else ""
            bar = (
                f"<span class='bar-value' style='bottom:{height + 5}px'>{count}</span>"
                f"<div class='bar-fill' style='height:{height}px;{form}"
                f"animation-delay:{index * _BAR_STAGGER_MS}ms'></div>"
            )
        flag = (
            f"<span class='bar-heavy-flag' style='bottom:{max(height - 3, 0)}px' "
            "aria-hidden='true'></span>"
            if heavy else ""
        )
        columns.append(
            f"<div class='bar-col{state}' role='listitem' data-bar-date='{date}' "
            f"aria-label='{date}，{count} 次作答"
            + ("，峰值" if index == peak_index else "")
            + ("，偏重" if heavy else "")
            + "'>"
            f"<div class='bar-plot'>{bar}{flag}</div>"
            f"<span class='bar-date'>{html.escape(date[5:])}</span>"
            "</div>"
        )
    return (
        "<div class='workload-chart-scroll'>"
        "<div class='workload-bars' role='list' aria-label='最近 14 天作答量'>"
        + "".join(columns)
        + "</div></div>"
    )


def _calendar_level(attempts):
    """按当天的**作答次数**定档 —— 五档的唯一判定入口。

    阈值全部取自 `_CALENDAR_LEVELS`（0 / 1 / 2–3 / 4–7 / ≥8），
    不再有行内三元表达式。
    """
    for level, low, high in _CALENDAR_LEVELS:
        if attempts < low:
            continue
        if high is None or attempts <= high:
            return level
    return _CALENDAR_LEVELS[-1][0]


def _calendar_height(attempts):
    """当天的格子高度（px）—— fill 之外的第二重编码。

    高度**只由次数决定**：次数越多越高（同一档内单调，跨档也不低于低档），
    到最高档封顶（不另设刻度）；零负荷日留一小截占位，基线位置不塌。
    """
    capped = min(attempts, _CALENDAR_MAX_COUNT)
    span = _CALENDAR_CELL_MAX_PX - _CALENDAR_CELL_MIN_PX
    return round(_CALENDAR_CELL_MIN_PX + span * capped / _CALENDAR_MAX_COUNT)


def _calendar_range(low, high):
    """档位区间文案（0 / 1 / 2–3 / 4–7 / ≥8）—— 与分档同一份口径。"""
    if high is None:
        return f"≥{low}"
    if low == high:
        return str(low)
    return f"{low}–{high}"


def _activity_legend():
    """档位图例：五个色块 + 区间刻度（服务端渲染，不引新资源）。

    解码由**图例本身**承担（少字原则）：不写解释句，
    「0 / 1 / 2–3 / 4–7 / ≥8」五个刻度就是格子的档位口径。
    色块沿用 `.level-N` 那一族填色 ⇒ 与格子的颜色一一对应。
    """
    items = "".join(
        "<span class='lk-legend__item'>"
        f"<span class='lk-legend__swatch level-{level}' aria-hidden='true'></span>"
        f"<span class='lk-legend__range'>{_calendar_range(low, high)}</span>"
        "</span>"
        for level, low, high in _CALENDAR_LEVELS
    )
    return (
        "<div class='lk-legend' aria-label='图例：当天作答次数'>"
        "<span class='lk-legend__title'>当天作答次数</span>"
        + items
        + "</div>"
    )


def _activity_calendar(activity):
    if not activity or not any(day.get("attempts") for day in activity):
        return "<p class='muted'>最近 12 周暂无作答</p>"
    labels = "".join(
        f"<span class='record-activity-weekday'>{label}</span>"
        for label in ("一", "二", "三", "四", "五", "六", "日")
    )
    cells = []
    for index, day in enumerate(activity):
        # 错峰的单位是**列**（一周一列）：网格按列流（CSS 的
        # `grid-auto-flow: column`，7 行 = 7 个星期）⇒ 第 `index` 个格子
        # 落在第 `index // 7` 列 ⇒ 同一列的格子**一起动**
        # （motion-spec §2.1 第 19 项「逐柱错峰 24ms」，与 `.bar-fill` 同一套做法）。
        delay = (index // _CALENDAR_ROWS) * _CALENDAR_STAGGER_MS
        if day.get("future"):
            cells.append(
                "<span class='record-activity-day future' aria-hidden='true'"
                f" style='animation-delay:{delay}ms'></span>")
            continue
        attempts = int(day.get("attempts") or 0)
        level = _calendar_level(attempts)
        date_text = str(day.get("date") or "")
        cells.append(
            f"<span class='record-activity-day level-{level}' "
            # 高度是第二重编码：`align-self:end` 让格子贴着行底（共享基线），
            # `aspect-ratio:auto` 解掉旧的正方形比例（高度由次数给）。
            f"style='align-self:end;aspect-ratio:auto;"
            f"height:{_calendar_height(attempts)}px;"
            f"animation-delay:{delay}ms' "
            f"title='{html.escape(date_text)} · {attempts} 次作答' "
            f"aria-label='{html.escape(date_text)}，{attempts} 次作答'></span>"
        )
    return (
        # 行高写死 ⇒ 每行等高、行内共享一条基线（高度编码才读得出量级）。
        "<div class='record-activity' aria-label='最近 12 周作答日历' "
        f"style='grid-auto-rows:{_CALENDAR_ROW_PX}px'>"
        + labels + "".join(cells) + "</div>"
        + _activity_legend()
    )


def _rating_chart(ratings):
    maximum = max((item.get("count", 0) for item in ratings), default=0)
    if maximum == 0:
        return "<p class='muted'>暂无带自评的作答</p>"
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
            # R-54（copy-table 定稿）：`按单题过滤` —— 去掉"正在"与句号，
            # 作为状态标签而非叙述句（copy-table §2.8 R-54）。
            "<p class='record-filter-note'>按单题过滤"
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
            "<h2>练习轮次</h2></div>"
            + _runs(active, runs)
            + "</section>"
        )
    elif view == "attempts":
        body = (
            "<section class='support-section'><div class='section-heading'><div>"
            "<h2>逐题记录</h2></div>"
            f"<p>{len(records)} 条</p></div>"
            + _attempt_rows(workspace_name, records)
            + "</section>"
        )
    elif view == "wrong":
        body = (
            "<section class='support-section'><div class='section-heading'><div>"
            "<h2>错题</h2></div>"
            f"<p>{len(filtered)} 条客观判错或卡住的记录。</p></div>"
            + _attempt_rows(workspace_name, filtered, wrong=True)
            + "</section>"
        )
    else:
        summary = overview.get("summary") or {}
        body = (
            _summary_cards(summary, runs, overview.get("trend") or [],
                           overview.get("ratings") or [])
            + "<section class='card record-chart-card record-activity-card'>"
            "<div class='section-heading'><div><p class='section-kicker'>最近 12 周</p>"
            "<h2>作答日历</h2></div></div>"
            + _activity_calendar(overview.get("activity") or [])
            + "</section>"
            + "<section class='card record-chart-card'>"
            "<div class='section-heading'><div><p class='section-kicker'>最近 14 天</p>"
            "<h2>作答量</h2></div></div>"
            + _trend_chart(overview.get("trend") or [])
            + "</section>"
            + "<section class='record-dashboard-grid'>"
            "<article class='card record-chart-card'><div class='section-heading'><div>"
            "<p class='section-kicker'>判定</p><h2>判定分布</h2></div></div>"
            + _verdict_distribution(summary)
            + "</article>"
            "<article class='card record-chart-card'><div class='section-heading'><div>"
            "<p class='section-kicker'>自评</p><h2>1–5 分分布</h2></div></div>"
            + _rating_chart(overview.get("ratings") or [])
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
