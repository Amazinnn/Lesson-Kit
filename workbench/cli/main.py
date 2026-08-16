"""wb — the workbench super CLI. Data-only commands, no teaching semantics."""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from workbench import registry
from workbench.bridge import runner
from workbench.data import pool as pool_mod
from workbench.data import queries
from workbench.domain import feedback, pull, schedule as schedule_rules, weak


RESULT_PROGRESS = {"correct": "reviewing", "wrong": "wrong", "stuck": "stuck"}


def _workspace(name):
    return registry.get_workspace(name)


def _pool(workspace):
    root = Path(workspace["path"])
    return pool_mod.Pool(
        root=root,
        db_path=root / workspace["db"],
        course=workspace.get("active_course", ""),
        chapter=workspace.get("active_chapter", ""),
    )


def _resolve_name(args):
    name = getattr(args, "name", None)
    if name:
        return name
    workspaces = registry.list_workspaces()
    if not workspaces:
        sys.exit("no workspaces registered — run: wb init <path>")
    return workspaces[0]["name"]


def cmd_init(args):
    workspace = registry.register(args.path, name=args.name,
                                  course=args.course or "", chapter=args.chapter or "")
    print(f"registered workspace: {workspace['name']} -> {workspace['path']}")


def cmd_ls(args):
    for workspace in registry.list_workspaces():
        pool = _pool(workspace)
        try:
            stats = queries.hub_stats(pool)
        except Exception:
            stats = {"kps": "?", "problems": "?", "due": "?", "signals": "?"}
        finally:
            pool.close()
        print(f"{workspace['name']:<12} {workspace['path']} "
              f"kp={stats['kps']} problems={stats['problems']} "
              f"signals={stats['signals']} due={stats['due']}")


def cmd_weak(args):
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        prefix = f"{workspace.get('active_course', '')}-{workspace.get('active_chapter', '')}"
        ranked = weak.score_all(
            pool.kps(prefix), pool.signals(), pool.schedule_rows(),
            pool.relations(), set(), date.today(),
        )
    finally:
        pool.close()
    for item in ranked[: args.limit]:
        print(f"{item['kp_id']:<24} {item['score']:<8} {'; '.join(item['reasons'])}")


def cmd_due(args):
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        items = queries.due_list(pool)
    finally:
        pool.close()
    for item in items:
        print(f"{item['due_at']}  {item['item_type']} {item['item_id']}  {item['label']}")


def cmd_pull(args):
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        result = pull.select(
            pool, args.kp, n=args.n, mode=args.mode,
            source_kind=args.source_kind, exclude_ids=set(args.exclude),
        )
    finally:
        pool.close()
    print(json.dumps({
        "problems": [p["problem_id"] for p in result["problems"]],
        "candidates": [c["candidate_id"] for c in result["candidates"]],
        "shortage": result["shortage"],
    }, ensure_ascii=False, indent=2))


def cmd_practice(args):
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        pool.insert_attempt(args.problem, args.result, args.note, args.answer_text)
        status = RESULT_PROGRESS.get(args.result)
        if status:
            pool.upsert_problem_progress(args.problem, status, args.note)
        state = pool.schedule_get("problem", args.problem) or schedule_rules.default_state(
            "problem", args.problem
        )
        next_state = schedule_rules.after_result(state, args.result, date.today())
        pool.schedule_upsert(next_state)
    finally:
        pool.close()
    print(f"recorded {args.problem}: {args.result}; due {next_state['due_at']}")


def cmd_feedback(args):
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        changes = feedback.apply(pool, args.item, args.id,
                                 rating=args.rating, note=args.note)
    finally:
        pool.close()
    for change in changes:
        print(change)


def cmd_schedule(args):
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        row = pool.schedule_get(args.item, args.id)
    finally:
        pool.close()
    print(json.dumps(row, ensure_ascii=False, indent=2) if row else "no schedule")


def cmd_ai(args):
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        if args.action == "status":
            job = pool_mod_jobs_status(pool, args.target)
            print(f"{args.target}: {job.get('state')}"
                  + (f" ({job.get('error')})" if job.get("error") else ""))
            return
        job_id = runner.run_ai_task(
            pool, Path(workspace["path"]), args.action, args.target,
            provider_name=args.provider, note=args.note,
            user_answer=args.user_answer, stuck_step=args.stuck_step,
        )
        status = pool_mod_jobs_status(pool, job_id)
        print(f"{job_id}: {status.get('state')}"
              + (f" ({status.get('error')})" if status.get("error") else ""))
    finally:
        pool.close()


def pool_mod_jobs_status(pool, job_id):
    from workbench.bridge import jobs
    return jobs.status(pool.jobs_dir(), job_id)


def cmd_bridge(args):
    registry.add_bridge(args.provider, args.command, args=args.args,
                        timeout_s=args.timeout)
    print(f"bridge provider configured: {args.provider}")


def cmd_guard(args):
    workspace = _workspace(_resolve_name(args))
    cmd = [sys.executable, "lessonkit.py", "guard", args.gate,
           "--course", workspace.get("active_course", ""),
           "--chapter", workspace.get("active_chapter", "")]
    if args.apply:
        cmd.append("--apply")
    return subprocess.call(cmd, cwd=workspace["path"])


def cmd_open(args):
    port = args.port
    print(f"workbench at http://127.0.0.1:{port}/w/{_resolve_name(args)}/")


def cmd_serve(args):
    from workbench.server import app
    app.serve(port=args.port)


def build_parser():
    parser = argparse.ArgumentParser(prog="wb",
                                     description="lesson-kit workbench CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="register a folder as a workspace")
    p.add_argument("path")
    p.add_argument("--name")
    p.add_argument("--course")
    p.add_argument("--chapter")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("ls", help="list workspaces with stats")
    p.set_defaults(func=cmd_ls)

    p = sub.add_parser("open", help="print the workspace URL")
    p.add_argument("name", nargs="?")
    p.add_argument("--port", type=int, default=3081)
    p.set_defaults(func=cmd_open)

    p = sub.add_parser("serve", help="start the web workbench")
    p.add_argument("--port", type=int, default=3081)
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("weak", help="weak knowledge points, ordered")
    p.add_argument("name", nargs="?")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_weak)

    p = sub.add_parser("due", help="due items (background reminders)")
    p.add_argument("name", nargs="?")
    p.set_defaults(func=cmd_due)

    p = sub.add_parser("pull", help="pull problems for knowledge points")
    p.add_argument("name", nargs="?")
    p.add_argument("--kp", action="append", default=[])
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--mode", choices=["weak", "random", "all"], default="weak")
    p.add_argument("--source-kind")
    p.add_argument("--exclude", action="append", default=[])
    p.set_defaults(func=cmd_pull)

    p = sub.add_parser("practice", help="record a problem result")
    p.add_argument("name", nargs="?")
    p.add_argument("--problem", required=True)
    p.add_argument("--result", required=True,
                   choices=["correct", "wrong", "stuck", "skip"])
    p.add_argument("--note")
    p.add_argument("--answer-text")
    p.set_defaults(func=cmd_practice)

    p = sub.add_parser("feedback", help="record feedback (rating and/or note)")
    p.add_argument("name", nargs="?")
    p.add_argument("--item", required=True, choices=["kp", "problem"])
    p.add_argument("--id", required=True)
    p.add_argument("--rating", type=int, choices=[1, 2, 3, 4, 5])
    p.add_argument("--note")
    p.set_defaults(func=cmd_feedback)

    p = sub.add_parser("schedule", help="show schedule state for an item")
    p.add_argument("name", nargs="?")
    p.add_argument("--item", required=True, choices=["kp", "problem"])
    p.add_argument("--id", required=True)
    p.set_defaults(func=cmd_schedule)

    p = sub.add_parser("ai", help="AI teacher tasks via the bridge")
    p.add_argument("name", nargs="?")
    p.add_argument("action", choices=["explain", "diagnose", "status"])
    p.add_argument("target", nargs="?", help="problem id, or job id for status")
    p.add_argument("--provider")
    p.add_argument("--note")
    p.add_argument("--user-answer")
    p.add_argument("--stuck-step")
    p.set_defaults(func=cmd_ai)

    p = sub.add_parser("bridge", help="configure bridge providers")
    p.add_argument("action", choices=["add"])
    p.add_argument("provider")
    p.add_argument("--command", required=True)
    p.add_argument("--args", action="append", default=[])
    p.add_argument("--timeout", type=int, default=300)
    p.set_defaults(func=cmd_bridge)

    p = sub.add_parser("guard", help="run a workspace guard")
    p.add_argument("name", nargs="?")
    p.add_argument("gate", choices=["extract-chapter", "extract-problems", "problem-set"])
    p.add_argument("--apply", action="store_true")
    p.set_defaults(func=cmd_guard)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
