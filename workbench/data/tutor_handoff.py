"""A readable handoff an external Tutor can use without a native session.

The text is derived from facts the course already holds: goals, the learning
files, the current or parked Paper position, the unanswered items and every
recorded attempt with its original answer. It is a projection written into the
exchange package — never a second copy of the data — so a Tutor edits the
declared learning files and the normal receive path carries that back.
"""

import json
from pathlib import Path

FILE_NAME = "handoff.md"

HEADER = """# 课程交接（Tutor 可读）

这是从课程事实投影出来的只读交接，不是新的数据源。**不要在这里改写答案**：
需要回写的内容放进 `.lessonkit/learning/*.md`，随课程文件一起交换即可。
"""


def build(pool):
    """Deterministic Markdown for one course; identical facts give identical text."""
    connection = pool.connect()
    lines = [HEADER, ""]
    lines += _course(pool)
    lines += _goals(pool.root)
    lines += _resources(pool)
    lines += _position(connection)
    lines += _attempts(connection)
    return "\n".join(lines).rstrip() + "\n"


def write(pool, destination):
    """Write the handoff beside the package (never into the workspace)."""
    target = Path(destination) / FILE_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build(pool), encoding="utf-8")
    return target


def _course(pool):
    return ["## 课程", "", f"- 课程标识：`{pool.course}`",
            f"- 章节：`{pool.chapter or '（全课程）'}`", ""]


def _goals(root):
    path = Path(root) / ".lessonkit/goals.json"
    if not path.is_file():
        return ["## 目标", "", "（本课程尚未记录目标）", ""]
    try:
        goals = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["## 目标", "", "（目标文件无法读取，按原样报告）", ""]
    lines = ["## 目标", ""]
    for goal in goals if isinstance(goals, list) else []:
        if not isinstance(goal, dict):
            continue
        title = goal.get("title") or goal.get("goal_id") or "未命名目标"
        detail = goal.get("detail") or goal.get("description") or ""
        status = goal.get("status") or ""
        lines.append(f"- {title}" + (f"（{status}）" if status else ""))
        if detail:
            lines.append(f"  - {detail}")
    if len(lines) == 2:
        lines.append("（本课程尚未记录目标）")
    lines.append("")
    return lines


def _resources(pool):
    root = Path(pool.root)
    lines = ["## 资料与学习文件", ""]
    learning = root / ".lessonkit/learning"
    files = sorted(path.relative_to(root).as_posix()
                   for path in learning.rglob("*") if path.is_file()) if learning.is_dir() else []
    if files:
        lines += [f"- 学习文件：`{name}`" for name in files]
    else:
        lines.append("- 学习文件：（无）")
    papers = sorted((root / ".lessonkit/practice-sets").glob("*.json"))
    for path in papers:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            lines.append(f"- 试卷：`{path.name}`（无法读取）")
            continue
        title = record.get("title") if isinstance(record, dict) else None
        lines.append(f"- 试卷：`{path.stem}` {title or ''}".rstrip())
    if not papers:
        lines.append("- 试卷：（无）")
    lines.append("")
    return lines


def _has(connection, table):
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _position(connection):
    """Where teaching stopped: the active run or the parked checkpoint."""
    if not _has(connection, "active_practice") and not _has(connection, "paper_state"):
        return ["## 教学续接位置", "", "（本池没有保存执行状态的表）", ""]
    record = None
    active = connection.execute("SELECT * FROM active_practice LIMIT 1").fetchone()         if _has(connection, "active_practice") else None
    if active is not None:
        record = dict(active)
        record["items"] = [dict(row) for row in connection.execute(
            "SELECT * FROM active_practice_items ORDER BY position")]
        record["mode"] = "当前进行中"
    elif _has(connection, "paper_state"):
        parked = connection.execute(
            "SELECT paper_id, generation, checkpoint_json FROM paper_state "
            "WHERE checkpoint_json IS NOT NULL LIMIT 1").fetchone()
        if parked is not None:
            record = json.loads(parked["checkpoint_json"])
            record["mode"] = "已暂停"
            record["paper_id"] = parked["paper_id"]
    if record is None:
        return ["## 教学续接位置", "", "（没有未完成的 Paper）", ""]
    items = record.get("items") or []
    cursor = record.get("cursor") or 0
    paper = record.get("source_ref") or record.get("paper_id") or "（未命名）"
    lines = ["## 教学续接位置", "",
             f"- 状态：{record['mode']}",
             f"- 试卷：`{paper}`" + (f"（{record.get('source_label')}）"
                                  if record.get("source_label") else ""),
             f"- 位置：第 {cursor + 1} 题 / 共 {len(items)} 题",
             f"- 揭晓时机：{record.get('reveal_timing') or '未记录'}", ""]
    lines += ["## 参考答案披露事实", ""]
    revealed = []
    for item in items:
        draft = item.get("draft")
        if draft is None:
            draft = json.loads(item.get("draft_json") or "{}")
        if draft.get("reference_viewed"):
            revealed.append(f"- `{item['item_id']}`（已查看参考答案）")
        for part_id, part in (draft.get("parts") or {}).items():
            if part.get("reference_viewed"):
                revealed.append(f"- `{item['item_id']}` / `{part_id}`（已查看参考答案）")
    lines += revealed or ["（没有已记录的披露事实）"]
    lines.append("")
    pending = [item for item in items if item.get("state") == "pending"]
    lines += ["## 未答项", ""]
    if pending:
        for item in pending:
            lines.append(f"- 第 {item['position'] + 1} 题 `{item['item_id']}`"
                         + ("（已标不会）" if item.get("state") == "stuck" else ""))
    else:
        lines.append("（无）")
    lines.append("")
    return lines


def _attempts(connection):
    if not _has(connection, "problem_attempts"):
        return ["## 已记录的作答（原文保持不动）", "", "（本池没有作答记录表）", ""]
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(problem_attempts)")}
    wanted = [name for name in ("id", "problem_id", "status", "note", "answer_text",
                                "verdict", "choices", "created_at") if name in columns]
    rows = connection.execute(
        "SELECT " + ", ".join(f'"{name}"' for name in wanted)
        + " FROM problem_attempts ORDER BY id").fetchall()
    rows = [{name: row[name] if name in wanted else None for name in
             ("id", "problem_id", "status", "note", "answer_text", "verdict", "choices",
              "created_at")} for row in rows]
    lines = ["## 已记录的作答（原文保持不动）", ""]
    if not rows:
        lines += ["（无）", ""]
        return lines
    for row in rows:
        lines.append(f"### 尝试 {row['id']}｜题目 `{row['problem_id']}`")
        lines.append("")
        lines.append(f"- 记录状态：{row['status']}")
        if row["verdict"] is not None:
            lines.append(f"- 客观判定：{'对' if row['verdict'] else '错'}")
        if row["choices"]:
            lines.append(f"- 所选选项：{row['choices']}")
        if row["answer_text"]:
            lines += ["- 原始作答：", "", "```", row["answer_text"], "```"]
        if row["note"]:
            lines.append(f"- 备注：{row['note']}")
        if row["created_at"]:
            lines.append(f"- 时间：{row['created_at']}")
        lines.append("")
    return lines
