"""wb — the workbench super CLI. Data-only commands, no teaching semantics."""

import argparse
import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from workbench import registry
from workbench import ingest
from workbench.bridge import runner
from workbench.data import pool as pool_mod
from workbench.data import content
from workbench.data import mastery as mastery_data
from workbench.data import queries
from workbench.domain import feedback, learning_state, pull, schedule as schedule_rules, weak
from workbench.domain import mastery as mastery_rules


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


def _json_input(path):
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8-sig")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def _pipeline_script(name):
    path = Path(__file__).resolve().parents[2] / "pipeline" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"workbench_{name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


def _write_temp_json(folder, name, value):
    path = Path(folder) / name
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def _candidate_payload(row):
    return {
        "candidate_id": row["candidate_id"],
        "kp_ids": row["kp_ids"],
        "problem_text": row["problem_text"],
        "options": row.get("options_json"),
        "correct_option_id": row.get("correct_option_id"),
        "solution": row.get("solution"),
        "problem_type": row.get("problem_type"),
        "interaction_type": row.get("interaction_type"),
        "generation_purpose": row.get("generation_purpose"),
        "origin_kind": row.get("origin_kind"),
        "source_kind": row.get("source_kind"),
        "source_evidence": row.get("source_evidence_json"),
    }


def _insert_candidate(pool, workspace, data, candidate_id=None):
    candidate_id = candidate_id or content.next_id(pool, "candidate")
    payload = dict(data)
    payload["candidate_id"] = candidate_id
    manifest = {
        "metadata": {
            "course": workspace.get("active_course", ""),
            "chapter": workspace.get("active_chapter", ""),
        },
        "candidates": [payload],
    }
    with tempfile.TemporaryDirectory() as folder:
        path = _write_temp_json(folder, "candidate.json", manifest)
        inserted, _skipped, errors = _pipeline_script("insert-candidates").insert_candidates(
            pool.db_path, path, upsert=candidate_id is not None and content.get(pool, "candidate", candidate_id) is not None,
        )
    if errors or inserted != 1:
        raise ValueError("; ".join(errors) or "candidate was not inserted")
    metadata = {
        field: data[field]
        for field in ("display_title", "topic_label", "display_summary")
        if field in data
    }
    if metadata:
        content.update(pool, "candidate", candidate_id, metadata)
    return content.get(pool, "candidate", candidate_id)


def _update_candidate(pool, workspace, candidate_id, changes):
    current = content.get(pool, "candidate", candidate_id)
    if current is None:
        raise KeyError(candidate_id)
    payload = _candidate_payload(current)
    payload.update(changes)
    return _insert_candidate(pool, workspace, payload, candidate_id=candidate_id)


def _gate_candidate(pool, candidate_id, audit_path):
    passed, failed, errors = _pipeline_script("gate-candidates").gate_candidates(
        pool.db_path, audit_path, [candidate_id]
    )
    if errors or failed or passed != 1:
        raise ValueError("; ".join(errors) or "candidate gate failed")
    return content.get(pool, "candidate", candidate_id)


def _promote_candidate(pool, candidate_id):
    expected_id = content.next_id(pool, "problem")
    imported, _warnings, errors = _pipeline_script("import-candidates").import_candidates(
        pool.db_path, [candidate_id]
    )
    if errors or len(imported) != 1:
        raise ValueError("; ".join(errors) or "candidate was not promoted")
    if imported[0] != expected_id:
        raise ValueError(f"candidate promotion allocated {imported[0]}, expected {expected_id}")
    return {"candidate_id": candidate_id, "problem_id": imported[0], "action": "promoted"}


def cmd_data(args):
    workspace = _workspace(args.name)
    pool = _pool(workspace)
    try:
        if args.action == "get":
            result = content.get(pool, args.entity, args.target)
        elif args.action == "list":
            result = content.list_items(pool, args.entity)
        elif args.action == "search":
            result = content.search(pool, args.entity, args.target)
        elif args.action == "history":
            result = content.history(pool, args.entity, args.target)
        elif args.action == "create":
            data = _json_input(args.input)
            result = (
                _insert_candidate(pool, workspace, data)
                if args.entity == "candidate"
                else content.create(pool, args.entity, data)
            )
        elif args.action == "update":
            data = _json_input(args.input)
            result = (
                _update_candidate(pool, workspace, args.target, data)
                if args.entity == "candidate"
                else content.update(pool, args.entity, args.target, data)
            )
        elif args.action == "delete":
            content.delete(pool, args.entity, args.target)
            result = {"entity": args.entity, "id": args.target, "action": "deleted"}
        elif args.action == "state":
            if args.entity not in ("kp", "problem"):
                raise ValueError("state is supported only for kp and problem")
            if content.get(pool, args.entity, args.target) is None:
                raise KeyError(args.target)
            schedule = learning_state.apply(pool, args.entity, args.target, args.value)
            result = {
                "entity": args.entity, "id": args.target, "state": args.value,
                "due_at": schedule["due_at"],
            }
        elif args.action == "gate":
            if args.entity != "candidate":
                raise ValueError("gate is supported only for candidate")
            result = _gate_candidate(pool, args.target, args.input)
        else:
            if args.entity != "candidate":
                raise ValueError("promote is supported only for candidate")
            result = _promote_candidate(pool, args.target)
        if result is None:
            raise KeyError(args.target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        pool.close()


def cmd_guard(args):
    workspace = _workspace(_resolve_name(args))
    cmd = [sys.executable, "lessonkit.py", "guard", args.gate,
           "--course", workspace.get("active_course", ""),
           "--chapter", workspace.get("active_chapter", "")]
    if args.apply:
        cmd.append("--apply")
    return subprocess.call(cmd, cwd=workspace["path"])


def cmd_ingest(args):
    workspace = _workspace(args.name)
    db_path = Path(workspace["path"]) / workspace["db"]
    try:
        if args.action == "prepare":
            output = Path(args.output) / "task.json"
            result = ingest.prepare(args.operation, args.input, output)
        elif args.action == "run":
            task = Path(args.target)
            output = Path(args.output) if args.output else task / "result.json"
            result = ingest.run(
                task / "task.json" if task.is_dir() else task,
                output, args.provider, workspace["path"],
            )
        elif args.action == "gate":
            if args.entity != "problem":
                raise ValueError("formal gate currently supports problem artifacts")
            output = Path(args.output)
            result = ingest.gate(db_path, args.solutions, args.audit, output)
        elif args.action == "apply":
            if args.entity != "problem":
                raise ValueError("formal apply currently supports problem artifacts")
            output = Path(args.input)
            result = ingest.apply(db_path, output, args.backup)
        elif args.action == "render":
            output = Path(args.output)
            result = ingest.render(args.input, output)
        else:
            output = Path(args.output) / "recipe.json"
            result = ingest.recipe(
                args.recipe, db_path, args.input, args.output,
                apply_changes=args.apply, backup_path=args.backup,
            )
        print(json.dumps({"artifact": str(output), "result": result}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, sqlite3.Error, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2


def cmd_experiment(args):
    workspace = _workspace(args.name)
    pool = _pool(workspace)
    try:
        result = mastery_rules.evaluate(mastery_data.snapshot(pool.connect()), date.today())
    finally:
        pool.close()
    if args.entity == "problem":
        result["knowledge_points"] = []
    elif args.entity == "kp":
        result["problems"] = []
    if args.id:
        key = "knowledge_points" if args.entity == "kp" else "problems"
        result[key] = [item for item in result[key] if item["id"] == args.id]
        if not result[key]:
            print(json.dumps({"error": f"unknown {args.entity}: {args.id}"}, ensure_ascii=False))
            return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for item in result["knowledge_points"] + result["problems"]:
            print(f"{item['entity']} {item['id']} {item['category']}  {item['explanation']}")
            for reason in item["reasons"]:
                print(f"  {reason['date'] or '-'}  {reason['evidence']}")
    return 0


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

    p = sub.add_parser("data", help="read or explicitly mutate workspace content as JSON")
    p.add_argument("name")
    p.add_argument(
        "action",
        choices=["get", "list", "search", "history", "create", "update", "delete", "state", "gate", "promote"],
    )
    p.add_argument("entity", choices=["kp", "problem", "candidate", "relation"])
    p.add_argument("target", nargs="?")
    p.add_argument("value", nargs="?", choices=["needs_work", "review", "mastered"])
    p.add_argument("--input")
    p.set_defaults(func=cmd_data)

    p = sub.add_parser("guard", help="run a workspace guard")
    p.add_argument("name", nargs="?")
    p.add_argument("gate", choices=["extract-chapter", "extract-problems", "problem-set"])
    p.add_argument("--apply", action="store_true")
    p.set_defaults(func=cmd_guard)

    p = sub.add_parser("ingest", help="prepare, run, gate, and apply UTF-8 content artifacts")
    p.add_argument("name")
    ingest_sub = p.add_subparsers(dest="action", required=True)

    action = ingest_sub.add_parser("prepare")
    action.add_argument("operation", choices=["problem-solutions", "problem-audit"])
    action.add_argument("--input", required=True)
    action.add_argument("--output", required=True)
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("run")
    action.add_argument("target")
    action.add_argument("--provider", required=True, choices=["codex", "claude"])
    action.add_argument("--output")
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("gate")
    action.add_argument("entity", choices=["kp", "problem", "candidate", "relation"])
    action.add_argument("--solutions", required=True)
    action.add_argument("--audit", required=True)
    action.add_argument("--output", required=True)
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("apply")
    action.add_argument("entity", choices=["kp", "problem", "candidate", "relation"])
    action.add_argument("--input", required=True)
    action.add_argument("--backup")
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("render")
    action.add_argument("target", choices=["guide", "problem-set", "graph"])
    action.add_argument("--input", required=True)
    action.add_argument("--output", required=True)
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("recipe")
    action.add_argument("recipe", choices=["knowledge", "problems", "candidates", "views"])
    action.add_argument("--input", required=True)
    action.add_argument("--output", required=True)
    action.add_argument("--apply", action="store_true")
    action.add_argument("--backup")
    action.set_defaults(func=cmd_ingest)

    p = sub.add_parser("experiment", help="run a read-only experimental evaluator")
    p.add_argument("name")
    p.add_argument("experiment", choices=["mastery"])
    p.add_argument("--entity", choices=["all", "kp", "problem"], default="all")
    p.add_argument("--id")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_experiment)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
