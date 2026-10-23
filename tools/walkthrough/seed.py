"""Seed the isolated workspace copy — records, sessions and an all-correct plan.

Specification: ``openspec/changes/workbench-visual-language-v2/design-notes/
walkthrough-harness.md`` §3.4 (the seed), §7.5.3 (3.4-6 / 3.7-2) and the
risk register **R-26** ("造数据只在隔离副本里做") / **X-9** ("执行器不得为了
让「98+ 条记录」的性能项可测而向**真实池**灌数据").

Why this module exists
----------------------
Three criteria were stuck at *PENDING* because the walkthrough had almost no
data to look at:

* **3.7-2** — the criterion needs a list of **98+ records**; the pool held
  three ``problem_attempts`` rows.
* **3.4-6** — the criterion needs the session list to be long enough that
  "is it scrollable or silently cropped?" is a question with an answer.
* **M-3** — the criterion needs a round that reaches the **milestone tier**,
  which (decisions.md A-29) happens on "本轮全对" or "章节首次完成".

The data therefore has to be *made* — but only inside the isolated copy.
This module is that maker.

What it seeds
-------------
============================  =====================================================
``problem_attempts``          ``--records N`` rows over the copy's own problems
``feedback_events``           one self-rating per seeded attempt (linked by id)
``.lessonkit/jobs/conv-*/``   ``--sessions N`` AI conversations (the session list)
``plan.json``                 the **all-correct plan**: gradable problems with
                              the option ids that make the round all-correct
============================  =====================================================

The plan is what lets the frames (M-3) and the sound probe (3.3-1) drive a
round in which **every item is graded correct** — the only way to reach the
milestone tier without inventing a proxy metric (A-29).

Isolation (the hard part)
-------------------------
The seed writes to a **pool copy** inside a scratch workspace.  Three
assertions run before the first byte is written and none of them is a
warning:

* **S-1** the target pool is not the real pool (different file *and* inode);
* **S-2** the target pool lives inside the workspace directory it belongs to;
* **S-3** the workspace directory is not inside the repository's ``pool/``.

The real pool's ``sha256`` / ``size`` / ``mtime`` are recorded **before and
after** the seed and both are written into the summary, so the report can
show that the real pool did not move.

Determinism
-----------
Both sides of a walkthrough must receive *the same* seed, otherwise the
persistence diff (G-2/G-3/G-6) compares two different databases.  Every row
is therefore derived from the copy's own content with a fixed order and
fixed timestamps — nothing is read from the clock.

Usage::

    python tools/walkthrough/seed.py \
        --workspace tmp/wt-run-8/scratch-after/ws-walk \
        --out tmp/wt-run-8/evidence/after/seed \
        --records 120 --sessions 120

Red lines (§8.3): this module writes to the isolated copy only, never to the
real pool, and it never touches product code.
"""

import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path

#: The repo root is derived from this file, never from the cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]

#: The three kinds of gradable item the plan asks for, in the order the
#: plan lists them.  ``multiple_choice`` comes first on purpose: it is the
#: only kind whose answer is submitted through ``#paper-item-submit``, which
#: is the gesture the product arms the answer cue with (workbench.js
#: ``ancestorWithId(target, "paper-item-submit")``).
PLAN_KINDS = ("multiple_choice", "single_choice", "yes_no")

#: The objective kinds that carry an answer key (the product's own list,
#: ``workbench/domain/micro_quiz.py``).  A keyless item cannot be graded, so
#: it never belongs in an all-correct round.
GRADABLE_KINDS = ("multiple_choice", "single_choice", "yes_no")

#: The options of a 判断题, in the order the page renders them.
YES_NO_OPTIONS = ("是", "否")

#: The self-rating values used for the seeded feedback events.
RATINGS = (3, 4, 5, 4, 3)

#: The statuses a seeded attempt may carry (``problem_attempts.status`` is a
#: CHECK constraint, so only these five are legal).
SEED_STATUSES = ("answered", "wrong", "answered", "stuck", "answered")


class SeedIsolationError(RuntimeError):
    """Raised when a seed would touch anything but the isolated copy."""


# ─────────────────────────────────────────────────────────────────────────
# the isolation assertions
# ─────────────────────────────────────────────────────────────────────────


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_file(path):
    """``sha256`` + ``size`` + ``mtime`` of one file (``None`` if missing)."""
    path = Path(path)
    if not path.exists():
        return None
    stat = path.stat()
    return {"sha256": sha256_file(path), "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns}


def assert_isolated(workspace, pool, real_pool=None):
    """S-1 / S-2 / S-3 — the seed may only write into the isolated copy.

    Any failure raises; nothing here is ever downgraded to a warning.
    """
    workspace = Path(workspace).resolve()
    pool = Path(pool).resolve()
    if not pool.is_file():
        raise SeedIsolationError(f"the pool to seed does not exist: {pool}")
    if not workspace.is_dir():
        raise SeedIsolationError(f"the workspace to seed does not exist: {workspace}")

    # S-1 — the copy is not the real pool.
    if real_pool is not None:
        real_pool = Path(real_pool).resolve()
        if real_pool.is_file():
            if os.path.samefile(pool, real_pool):
                raise SeedIsolationError(
                    f"the pool to seed is the real pool ({pool}) — the seed "
                    "would write the user's data")
            if pool.stat().st_ino == real_pool.stat().st_ino:
                raise SeedIsolationError(
                    f"the pool to seed shares the inode of the real pool ({pool})")

    # S-2 — the pool lives inside the workspace it belongs to.
    if not pool.is_relative_to(workspace):
        raise SeedIsolationError(
            f"the pool to seed ({pool}) is outside its workspace ({workspace})")

    # S-3 — the workspace is not inside the repository's pool directory.
    repo_pool = (REPO_ROOT / "pool").resolve()
    if workspace.is_relative_to(repo_pool) or pool.is_relative_to(repo_pool):
        raise SeedIsolationError(
            f"the workspace to seed ({workspace}) lives inside the real pool "
            f"directory ({repo_pool})")
    return {"workspace": str(workspace), "pool": str(pool)}


# ─────────────────────────────────────────────────────────────────────────
# the pool seeds
# ─────────────────────────────────────────────────────────────────────────


def _connect(pool):
    connection = sqlite3.connect(str(pool), timeout=30.0)
    connection.row_factory = sqlite3.Row
    return connection


def _problems(connection):
    """The copy's own problems, in a fixed order."""
    rows = connection.execute(
        "SELECT problem_id, display_title, micro_quiz FROM problems "
        "WHERE deleted_at IS NULL ORDER BY problem_id").fetchall()
    return [dict(row) for row in rows]


def _timestamp(index):
    """A fixed timestamp per seeded row — the clock is never read.

    The two sides of a walkthrough are seeded at different moments; a
    wall-clock timestamp would make the two copies differ (and the
    persistence diff G-2 would compare two different databases).
    """
    day = 1 + (index % 28)
    hour = index % 24
    minute = (index * 7) % 60
    return f"2026-03-{day:02d} {hour:02d}:{minute:02d}:00"


def seed_attempts(connection, problems, count):
    """Write ``count`` attempts (and one self-rating each) into the copy."""
    if not problems:
        raise SeedIsolationError("the pool copy holds no problem to seed records with")
    inserted = []
    for index in range(count):
        problem = problems[index % len(problems)]
        status = SEED_STATUSES[index % len(SEED_STATUSES)]
        verdict = 1 if status == "answered" else (0 if status == "wrong" else None)
        answer_text = "6500" if verdict == 1 else "650"
        cursor = connection.execute(
            "INSERT INTO problem_attempts "
            "(problem_id, status, note, answer_text, verdict, choices, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (problem["problem_id"], status, None, answer_text, verdict, None,
             _timestamp(index)))
        attempt_id = cursor.lastrowid
        inserted.append({"attempt_id": attempt_id,
                         "problem_id": problem["problem_id"],
                         "status": status, "verdict": verdict})
        connection.execute(
            "INSERT INTO feedback_events "
            "(item_type, item_id, rating, note, created_at, attempt_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("problem", problem["problem_id"],
             RATINGS[index % len(RATINGS)], None, _timestamp(index), attempt_id))
    connection.commit()
    return inserted


def build_plan(connection, kinds=PLAN_KINDS):
    """The **all-correct plan**: gradable problems and the right options.

    A problem qualifies when its ``micro_quiz`` carries an answer key — the
    product grades an answer only then (``practice_submission.grade_answer``
    → ``micro_quiz.has_answer_key``).  For every requested kind the first
    problem (in ``problem_id`` order) is taken, so the plan is the same on
    both sides of a walkthrough.
    """
    found = {}
    for problem in _problems(connection):
        raw = problem.get("micro_quiz")
        if not raw:
            continue
        try:
            quiz = json.loads(raw)
        except (TypeError, ValueError):
            continue
        kind = quiz.get("quiz_type")
        if kind not in GRADABLE_KINDS or kind in found:
            continue
        answer_key = quiz.get("answer_key")
        if kind == "multiple_choice":
            if not isinstance(answer_key, list) or not answer_key:
                continue
            option_ids = [str(item) for item in answer_key]
        else:
            if not isinstance(answer_key, str) or not answer_key.strip():
                continue
            option_ids = [answer_key]
        if kind == "yes_no":
            options = list(YES_NO_OPTIONS)
        else:
            options = [str(item) for item in (quiz.get("options") or [])]
        if not set(option_ids) <= set(options):
            continue
        found[kind] = {
            "problem_id": problem["problem_id"],
            "quiz_type": kind,
            "answer_key": answer_key,
            "option_ids": option_ids,
            "options": options,
            "multiple": kind == "multiple_choice",
        }
    plan = {"kinds": list(kinds),
            "items": [found[kind] for kind in kinds if kind in found],
            "missing": [kind for kind in kinds if kind not in found]}
    return plan


# ─────────────────────────────────────────────────────────────────────────
# the workspace seeds
# ─────────────────────────────────────────────────────────────────────────


def seed_sessions(workspace, count):
    """Write ``count`` AI conversations into the workspace's jobs directory.

    The session list of the right column is fed by
    ``<workspace>/.lessonkit/jobs/conv-*/conversation.json``
    (``workbench/bridge/conversations.py::list_sessions``).  The records are
    the same shape the product writes, with fixed timestamps so the two
    sides of a walkthrough receive identical lists.
    """
    jobs_dir = Path(workspace) / ".lessonkit" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for index in range(1, count + 1):
        conversation_id = f"conv-{index:03d}"
        folder = jobs_dir / conversation_id
        folder.mkdir(parents=True, exist_ok=True)
        stamp = _timestamp(index)
        record = {
            "conversation_id": conversation_id,
            "provider": "agent",
            "model": "seed",
            "model_entry": None,
            "model_args": [],
            "title": f"走查种子对话 {index:03d}",
            "title_source": "user",
            "provider_session_id": None,
            "status": "idle",
            "current_turn_id": None,
            "queue_paused": False,
            "queue_order": [],
            "created_at": stamp,
            "updated_at": stamp,
        }
        (folder / "conversation.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(conversation_id)
    return written


# ─────────────────────────────────────────────────────────────────────────
# the entry point of the seeding
# ─────────────────────────────────────────────────────────────────────────


def seed_workspace(workspace, pool, out, records=0, sessions=0,
                   real_pool=None, plan=True):
    """Seed one isolated workspace and write the summary into ``out``.

    Returns the summary dictionary (also written to ``<out>/summary.json``).
    """
    workspace = Path(workspace).resolve()
    pool = Path(pool).resolve()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    isolation = assert_isolated(workspace, pool, real_pool)
    real_before = snapshot_file(real_pool) if real_pool else None

    connection = _connect(pool)
    try:
        problems = _problems(connection)
        attempts = seed_attempts(connection, problems, records) if records else []
        plan_data = build_plan(connection) if plan else {"kinds": [], "items": [],
                                                         "missing": list(PLAN_KINDS)}
    finally:
        connection.close()

    conversations = seed_sessions(workspace, sessions) if sessions else []

    (out / "plan.json").write_text(
        json.dumps(plan_data, ensure_ascii=False, indent=2), encoding="utf-8")
    real_after = snapshot_file(real_pool) if real_pool else None

    summary = {
        "workspace": str(workspace),
        "pool": str(pool),
        "realPool": str(Path(real_pool).resolve()) if real_pool else None,
        "realPoolBefore": real_before,
        "realPoolAfter": real_after,
        "realPoolUnchanged": (real_before == real_after) if real_before else None,
        "poolBefore": snapshot_file(pool),
        "poolAfter": snapshot_file(pool),
        "records": len(attempts),
        "sessions": len(conversations),
        "sessionIds": conversations[:3] + (["…"] if len(conversations) > 3 else []),
        "plan": plan_data,
        "allCorrectRound": {
            "planned": bool(plan_data["items"]),
            "problemIds": [item["problem_id"] for item in plan_data["items"]],
            "missing": plan_data["missing"],
        },
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Seed an isolated workspace copy: records, sessions, "
                    "all-correct plan.  The real pool is never written.")
    parser.add_argument("--workspace", required=True,
                        help="the isolated workspace directory (e.g. <scratch>/ws-walk)")
    parser.add_argument("--pool", default=None,
                        help="the pool copy to seed (default: <workspace>/pool/<course>.db)")
    parser.add_argument("--course", default="dmath")
    parser.add_argument("--out", required=True, help="where the summary is written")
    parser.add_argument("--records", type=int, default=0,
                        help="how many attempt records to seed")
    parser.add_argument("--sessions", type=int, default=0,
                        help="how many AI conversations to seed")
    parser.add_argument("--real-pool", default=None,
                        help="the pool that must not change (default: <repo>/pool/<course>.db)")
    parser.add_argument("--no-plan", action="store_true",
                        help="do not write the all-correct plan")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).resolve()
    pool = Path(args.pool) if args.pool else workspace / "pool" / f"{args.course}.db"
    real_pool = Path(args.real_pool) if args.real_pool else \
        REPO_ROOT / "pool" / f"{args.course}.db"

    summary = seed_workspace(workspace, pool, args.out,
                             records=args.records, sessions=args.sessions,
                             real_pool=real_pool, plan=not args.no_plan)
    print(json.dumps({
        "workspace": summary["workspace"],
        "pool": summary["pool"],
        "records": summary["records"],
        "sessions": summary["sessions"],
        "allCorrectRound": summary["allCorrectRound"],
        "realPoolUnchanged": summary["realPoolUnchanged"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
