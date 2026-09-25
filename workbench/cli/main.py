"""lesson-kit — the workbench super CLI. Data-only commands, no teaching semantics."""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

from workbench import registry
from workbench import ingest
from workbench.bridge import conversation_providers
from workbench.data import pool as pool_mod
from workbench.data import content
from workbench.data import difficulty as difficulty_data
from workbench.data import mastery as mastery_data
from workbench.data import queries
from workbench.domain import difficulty as difficulty_rules
from workbench.domain import feedback, learning_state, pull, schedule as schedule_rules, weak
from workbench.domain import mastery as mastery_rules


def _workspace(name):
    """An unknown name is a readable refusal, never a stack trace for the Agent."""
    try:
        return registry.get_workspace(name)
    except KeyError:
        names = ", ".join(w["name"] for w in registry.list_workspaces())
        sys.exit(
            f"unknown workspace: {name}\n"
            f"registered workspaces: {names or 'none'}"
        )


def _pool(workspace):
    root = Path(workspace["path"])
    return pool_mod.Pool(
        root=root,
        db_path=root / workspace["db"],
        course=workspace.get("active_course", ""),
        chapter=workspace.get("active_chapter", ""),
    )


def _resolve_name(args):
    """The workspace a command works on — never guessed when several are registered."""
    name = getattr(args, "name", None)
    if name:
        return name
    workspaces = registry.list_workspaces()
    if not workspaces:
        sys.exit("no workspaces registered — run: lesson-kit init <path>")
    if len(workspaces) == 1:
        return workspaces[0]["name"]
    names = ", ".join(w["name"] for w in workspaces)
    command = getattr(args, "command", "data")
    sys.exit(
        f"several workspaces registered ({names}) — name one:\n"
        f"  lesson-kit {command} {workspaces[0]['name']} …"
    )


COURSE_SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")


def _slug_from_name(name):
    """Course slug for an ASCII folder name; None when it cannot be derived."""
    if not name.isascii():
        return None
    candidate = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return candidate if COURSE_SLUG.fullmatch(candidate) else None


def _require_slug(value, kind="course"):
    """Reject a course or chapter that would poison every content id.

    Both go into ids and paths (the chapter also into the `course-chapter` query
    prefix and the graph artifact name), so a free-form value is never stored.
    """
    if COURSE_SLUG.fullmatch(value):
        return value
    example = ("lesson-kit init --course uphy2" if kind == "course"
               else "lesson-kit use uphy2 ch06")
    raise SystemExit(
        f"{kind} {value!r} is not a valid identifier — it goes into every content "
        f"id and path of this workspace, so it must be lowercase ASCII (letters, "
        f"digits, dashes).\nExample: {example}"
    )


def _optional_slug(value, kind):
    """Empty means "no chapter" (the whole course); anything else must be an identifier."""
    return _require_slug(value, kind) if value else ""


def _next_course_code(folder):
    """Sequential short code (c01, c02, …) for a folder name that yields no slug."""
    used = {w.get("active_course", "") for w in registry.list_workspaces()}
    pool_dir = folder / "pool"
    if pool_dir.is_dir():
        used |= {db.stem for db in pool_dir.glob("*.db")}
    numbers = [
        int(match.group(1)) for name in used
        if (match := re.fullmatch(r"c(\d+)", name or ""))
    ]
    return f"c{max(numbers, default=0) + 1:02d}"


def _init_course(args, folder):
    """Explicit --course, else an existing pool's name, else a folder-name slug,
    else an automatically allocated sequential code."""
    if args.course:
        return _require_slug(args.course)
    pool = registry.find_pool(folder)
    if pool:
        return Path(pool).stem
    return _slug_from_name(folder.name) or _next_course_code(folder)


def cmd_init(args):
    folder = Path(args.path).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    try:
        course = _init_course(args, folder)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if not registry.looks_like_workspace(folder):
        _bootstrap_workspace(folder, course=course)
    chapter = _optional_slug(args.chapter, "chapter")
    try:
        workspace = registry.register(str(folder), name=args.name,
                                      course=course, chapter=chapter)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"registered workspace: {workspace['name']} -> {workspace['path']}")


def _bootstrap_workspace(folder, course):
    """Create a pool database and the .lessonkit skeleton in a fresh folder."""
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "pipeline" / "scripts" / "create-tables.py"
    try:
        subprocess.run(
            [sys.executable, str(script), "--db", f"pool/{course}.db"],
            cwd=str(folder), check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"creating the pool database failed (exit {exc.returncode})")
    for name in ("figures", "explain", "jobs"):
        (folder / ".lessonkit" / name).mkdir(parents=True, exist_ok=True)


def cmd_use(args):
    if args.workspace:
        name = args.workspace
    else:
        workspaces = registry.list_workspaces()
        if len(workspaces) == 1:
            name = workspaces[0]["name"]
        else:
            raise SystemExit("multiple workspaces registered — pass --workspace <name>")
    chapter = _optional_slug(args.chapter, "chapter")
    registry.update_active(name, _require_slug(args.course), chapter)
    print(f"workspace {name}: active course/chapter -> "
          f"{args.course}/{chapter or '<全课程>'}")
    print(f"workbench at http://127.0.0.1:3081/w/{name}/")


def cmd_ls(args):
    rows = []
    for workspace in registry.list_workspaces():
        pool = _pool(workspace)
        try:
            stats = queries.hub_stats(pool)
        except Exception:
            stats = {"kps": "?", "problems": "?", "due": "?", "signals": "?"}
        finally:
            pool.close()
        rows.append({
            "name": workspace["name"], "path": workspace["path"],
            "course": workspace.get("active_course", ""),
            "chapter": workspace.get("active_chapter", ""), **stats,
        })
        if not args.json:
            print(f"{workspace['name']:<12} {workspace['path']} "
                  f"kp={stats['kps']} problems={stats['problems']} "
                  f"signals={stats['signals']} due={stats['due']}")
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


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
    ranked = ranked[: args.limit]
    if args.json:
        print(json.dumps(ranked, ensure_ascii=False, indent=2))
        return 0
    for item in ranked:
        print(f"{item['kp_id']:<24} {item['score']:<8} {'; '.join(item['reasons'])}")
    return 0


def cmd_due(args):
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        items = queries.due_list(pool)
    finally:
        pool.close()
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return 0
    for item in items:
        print(f"{item['due_at']}  {item['item_type']} {item['item_id']}  {item['label']}")
    return 0


def cmd_pull(args):
    """Compose a practice set from the pool, or reuse a manifest, and optionally
    check / save / print it. `--input` and the selection flags are alternatives:
    one composes, the other re-runs what a previous composition recorded."""
    from workbench.data import content as content_data
    from workbench.data import practice_sets

    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        selection = _selection_given(args)
        if args.input and selection:
            raise ValueError(
                "--input re-runs a saved manifest; pass either --input or the "
                "selection flags, not both"
            )
        if args.input:
            plan = practice_sets.read(args.input)
            _, problems = practice_sets.resolve(pool, plan)
        else:
            if args.exam_year:
                reason = content_data.exam_year_column_error(pool)
                if reason:
                    raise ValueError(reason)
            plan, problems = _compose_plan(pool, args, workspace)
            if not problems and (args.plan or args.print_dir or args.check):
                raise ValueError(
                    "the selection is empty — nothing to write or check; widen the "
                    "conditions, or run it without --plan/--print/--check to see the "
                    "empty result and its shortage"
                )

        if args.check:
            result = practice_sets.check(pool, plan)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["valid"] else 2
        result = {"count": len(problems), "shortage": plan.get("shortage", [])}
        if args.plan:
            result["plan"] = str(practice_sets.write(args.plan, plan))
        if args.print_dir:
            rendered = practice_sets.render(pool, plan)
            result["printed"] = [
                str(path) for path in _write_sheets(rendered, args, problems)
            ]
            result["preview"] = rendered["preview"]
        if not (args.plan or args.print_dir):
            result.update(_pull_payload(plan, problems, args))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        pool.close()


def _selection_given(args):
    return bool(
        args.kp or args.problem or args.exclude or args.include
        or args.weak or args.due or args.wrong
        or args.source_kind or args.origin_kind or args.source_group
        or args.exam_year or args.difficulty_min is not None
        or args.difficulty_max is not None or args.difficulty_strategy
        or any(getattr(args, name + "_min") is not None
               or getattr(args, name + "_max") is not None
               for name in difficulty_rules.DIMENSIONS)
    )


def _compose_plan(pool, args, workspace):
    from workbench.data import practice_sets

    kp_ids = args.kp or [row["kp_id"] for row in pool.kps(pool.scope_prefix())]
    result = pull.select(
        pool, kp_ids, n=args.n, mode=args.mode,
        source_kind=args.source_kind, origin_kind=args.origin_kind,
        source_group=args.source_group, exclude_ids=set(args.exclude),
        include_ids=set(args.include),
        exam_year=args.exam_year, explicit_ids=set(args.problem),
        drivers=[name for name in pull.DRIVERS if getattr(args, name)],
        difficulty_min=args.difficulty_min, difficulty_max=args.difficulty_max,
        difficulty_dimensions={
            name: (getattr(args, name + "_min"), getattr(args, name + "_max"))
            for name in difficulty_rules.DIMENSIONS
            if getattr(args, name + "_min") is not None
            or getattr(args, name + "_max") is not None
        },
        difficulty_strategy=args.difficulty_strategy,
        with_reasons=True,
        # Coverage-first before the cap: a set composed across chapters must not
        # return one chapter just because its problems cover more knowledge points.
        coverage=True,
    )
    problems = result["problems"]
    title = args.title or _practice_title(workspace, problems)
    plan = practice_sets.build(title, result["problems"], _pull_request(args, workspace))
    plan["course"] = workspace.get("active_course", "")
    plan["shortage"] = result["shortage"]
    return plan, problems


def _pull_payload(plan, problems, args):
    """The selection itself: full rows by default, ids behind --ids, plus the reasons."""
    return {
        "problems": [p["problem_id"] for p in problems] if args.ids else problems,
        "shortage": plan.get("shortage", []),
    }


def _write_sheets(rendered, args, problems):
    """Two files per set: the student sheet and its aligned solutions."""
    directory = Path(args.print_dir)
    base = args.base or _base_name(problems)
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for suffix, text in (("problem-set", rendered["practice_set"]),
                         ("solutions", rendered["solutions"])):
        path = directory / f"{base}-{suffix}.md"
        path.write_text(text, encoding="utf-8")
        paths.append(path)
    return paths


def _selected_chapters(problems):
    """The chapter segments of the selected problems, so a set names itself."""
    chapters = set()
    for problem in problems:
        parts = str(problem["problem_id"]).split("-")
        if len(parts) >= 3 and parts[-2] in ("prob", "mq") and parts[-1].isdigit():
            chapters.add("-".join(parts[1:-2]))
    return sorted(chapters)


def _base_name(problems):
    chapters = _selected_chapters(problems)
    if len(chapters) == 1:
        return chapters[0]
    return "all"


def _practice_title(workspace, problems):
    course = workspace.get("active_course", "")
    chapters = _selected_chapters(problems)
    if not chapters:
        return f"{course} 练习"
    return f"{course} {'/'.join(chapters)} 练习"


def _pull_request(args, workspace):
    """The inputs a manifest needs to reproduce this selection."""
    return {
        "course": workspace.get("active_course", ""),
        "chapter": workspace.get("active_chapter", ""),
        "kp": list(args.kp),
        "problem": list(args.problem),
        "drivers": [name for name in pull.DRIVERS if getattr(args, name)],
        "source_kind": args.source_kind,
        "origin_kind": args.origin_kind,
        "source_group": args.source_group,
        "exam_year": args.exam_year,
        "n": args.n,
        "mode": args.mode,
    }


def cmd_practice(args):
    from workbench.data import attempts as attempts_data
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        recorded = attempts_data.record_result(
            pool, args.problem, args.result, note=args.note,
            answer_text=args.answer_text,
        )
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        pool.close()
    if not recorded["recorded"]:
        print(f"recorded {args.problem}: {args.result} (no learning record)")
        return 0
    print(f"recorded {args.problem}: {args.result}; due {recorded['due_at']}")
    return 0


def cmd_feedback(args):
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        lookup = {"kp": pool.kp, "problem": pool.problem, "card": pool.card}[args.item]
        item = lookup(args.id)
        if item is None:
            print(json.dumps({"error": f"unknown {args.item}: {args.id}"}, ensure_ascii=False))
            return 2
        direction = args.direction or ""
        if args.item == "card" and direction not in {"", *item["directions"]}:
            print(json.dumps({"error": "direction is not available for this card"},
                             ensure_ascii=False))
            return 2
        if args.rating is None and not (args.note and args.note.strip()):
            print(json.dumps({"error": "rating or note is required"}, ensure_ascii=False))
            return 2
        changes = feedback.apply(pool, args.item, args.id, rating=args.rating,
                                 note=args.note, direction=direction)
    finally:
        pool.close()
    for change in changes:
        print(change)
    return 0


def cmd_schedule(args):
    workspace = _workspace(_resolve_name(args))
    pool = _pool(workspace)
    try:
        row = pool.schedule_get(args.item, args.id)
    finally:
        pool.close()
    print(json.dumps(row, ensure_ascii=False, indent=2) if row else "no schedule")


def cmd_goals(args):
    from workbench.data import goals as goals_mod
    workspace = _workspace(_resolve_name(args))
    root = workspace["path"]
    if args.action == "add":
        if not args.title:
            raise SystemExit("goals add requires --title")
        goal = goals_mod.create_goal(root, {
            "title": args.title,
            "kind": args.kind or "stage",
            "start_date": args.start_date or "",
            "deadline": args.deadline or "",
            "description": args.description or "",
        })
    elif args.action == "update":
        if not args.goal_id:
            raise SystemExit("goals update requires a goal id")
        values = {k: v for k, v in {
            "title": args.title, "kind": args.kind,
            "start_date": args.start_date, "deadline": args.deadline,
            "description": args.description,
        }.items() if v is not None}
        goal = goals_mod.update_goal(root, args.goal_id, values)
    elif args.action == "rm":
        if not args.goal_id:
            raise SystemExit("goals rm requires a goal id")
        goal = goals_mod.delete_goal(root, args.goal_id)
    else:
        print(json.dumps(goals_mod.list_goals(root), ensure_ascii=False, indent=2))
        return
    goals_mod.invalidate_plan(workspace)
    print(json.dumps(goal, ensure_ascii=False, indent=2))


def cmd_bridge(args):
    if args.action == "list":
        return _bridge_list()
    if not args.provider or not args.command:
        raise SystemExit("bridge add requires <provider> and --command")
    registry.add_bridge(args.provider, args.command, args=args.args,
                        model=args.model, timeout_s=args.timeout,
                        tool_timeout_s=args.tool_timeout)
    print(f"bridge provider configured: {args.provider}")
    for provider in conversation_providers.discover():
        if provider["name"] == args.provider:
            print(f"  silence budget={provider['timeout_s']}s "
                  f"tool budget={provider['tool_timeout_s']}s")


def _bridge_list():
    configured = registry.load_bridges().get("providers", {})
    found = conversation_providers.discover()
    if not found:
        print("no supported Agent CLI found on PATH or in bridge config")
    for provider in found:
        source = "config" if provider["name"] in configured else "path"
        command = provider["command"]
        marker = "" if Path(command).is_file() else " (missing)"
        model = provider.get("model") or "-"
        print(f"{provider['name']}: {command}{marker} [{source}] model={model} "
              f"silence={provider['timeout_s']}s tool={provider['tool_timeout_s']}s")
    for name in conversation_providers.SUPPORTED:
        if name not in {provider["name"] for provider in found}:
            print(f"{name}: not found")
    return 0


def _json_input(path):
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8-sig")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def cmd_attempts(args):
    from workbench.data import attempts as attempts_data
    from workbench import registry
    try:
        workspace = _workspace(args.name)
    except KeyError as exc:
        print(json.dumps({"error": str(exc).strip("'\"")}, ensure_ascii=False))
        return 2
    if args.action in ("sources",):
        return _attempt_sources(args, workspace)
    pool = _pool(workspace)
    try:
        if args.action == "list":
            result = attempts_data.list_attempts(pool, args.problem)
        elif args.action == "get":
            result = attempts_data.get_attempt(pool, int(args.attempt_id))
        elif args.action == "check":
            result = attempts_data.check(pool, _json_input(args.input))
        elif args.action == "apply":
            result = attempts_data.apply(pool, _json_input(args.input))
        else:
            result = attempts_data.correct(
                pool, int(args.attempt_id), _json_input(args.input))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except attempts_data.ManifestError as exc:
        error = {"error": str(exc)}
        if exc.items:
            error["errors"] = exc.items
        print(json.dumps(error, ensure_ascii=False, indent=2))
        return 2
    except (ValueError, KeyError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        pool.close()


def _attempt_sources(args, workspace):
    """Answer-image discovery is a read source list, not an image store."""
    try:
        if args.source_action == "add":
            result = registry.add_answer_source(workspace["name"], args.path)
        elif args.source_action == "remove":
            result = registry.remove_answer_source(workspace["name"], args.path)
        else:
            result = {"workspace": workspace["name"],
                      "paths": registry.answer_sources(workspace["name"])}
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stdout)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


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
            result = content.create(pool, args.entity, data)
        elif args.action == "update":
            data = _json_input(args.input)
            result = content.update(pool, args.entity, args.target, data)
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
        if result is None:
            raise KeyError(args.target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        pool.close()


def cmd_difficulty(args):
    workspace = _workspace(args.name)
    pool = _pool(workspace)
    try:
        manifest = _json_input(args.input)
        result = (difficulty_data.check(pool, manifest) if args.action == "check"
                  else difficulty_data.apply(pool, manifest))
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
        if args.action == "batches":
            output = None
            result = {"batches": ingest.list_batches(db_path)}
        elif args.action == "prepare":
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
            result = ingest.gate(
                db_path, args.solutions, args.audit, output,
                args.content_patch, args.content_audit,
            )
        elif args.action == "apply":
            if args.entity != "problem":
                raise ValueError("formal apply currently supports problem artifacts")
            output = Path(args.input)
            result = ingest.apply(db_path, output, args.backup)
        elif args.action == "rollback":
            result = ingest.rollback_batch(db_path, args.batch, args.backup)
            output = Path(result["backup_path"])
        elif args.action == "migrate-figures":
            output = None
            result = ingest.migrate_legacy_figures(
                db_path, workspace["path"], apply_changes=args.apply,
                backup_path=args.backup)
        elif args.action == "render":
            output = Path(args.output)
            result = ingest.render(args.input, output)
        else:
            output = Path(args.output) / "recipe.json"
            result = ingest.recipe(
                args.recipe, db_path, args.input, args.output,
                apply_changes=args.apply, backup_path=args.backup,
            )
        print(json.dumps({"artifact": str(output) if output is not None else None,
                          "result": result}, ensure_ascii=False, indent=2))
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


def cmd_daemon(args):
    from workbench.cli import service
    try:
        if args.action == "start":
            result = service.start(port=args.port)
            if result["already_running"]:
                print(f"workbench already running: pid {result['pid']} "
                      f"http://127.0.0.1:{result['port']}/")
                return 0
            print(f"workbench started: pid {result['pid']} "
                  f"http://127.0.0.1:{result['port']}/ (log: {result['log']})")
            return 0
        if args.action == "stop":
            result = service.stop()
            if not result["was_running"]:
                print("workbench is not running")
                return 0
            print(f"workbench stopped: pid {result['pid']} (log: {result['log']})")
            return 0
        result = service.status()
    except RuntimeError as exc:
        print(f"workbench: {exc}", file=sys.stderr)
        return 2
    if not result["running"]:
        print("workbench is not running")
        return 0
    print(f"workbench running: pid {result['pid']} "
          f"http://127.0.0.1:{result['port']}/ since {result.get('started_at')}")
    return 0


def cmd_dashboard(args):
    import webbrowser

    from workbench.cli import service
    try:
        result = service.start(port=args.port)
    except RuntimeError as exc:
        print(f"workbench: {exc}", file=sys.stderr)
        return 2
    if result["already_running"]:
        print(f"workbench already running: pid {result['pid']}")
    else:
        print(f"workbench started: pid {result['pid']} (log: {result['log']})")
    name = args.name
    if not name:
        workspaces = registry.list_workspaces()
        name = workspaces[0]["name"] if len(workspaces) == 1 else None
    url = service.workbench_url(args.port, name)
    print(f"opening {url}")
    webbrowser.open(url)
    return 0


def cmd_doctor(args):
    from workbench.cli import doctor
    checks = doctor.run_checks()
    for line in doctor.format_report(checks):
        print(line)
    if doctor.all_passed(checks):
        print("all checks passed")
        return 0
    print("problems found (nothing was changed)", file=sys.stderr)
    return 2


def build_parser(prog="lesson-kit"):
    parser = argparse.ArgumentParser(prog=prog,
                                     description="lesson-kit workbench CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="register a folder; create the pool and skeleton first if it is not a workspace yet")
    p.add_argument("path", nargs="?", default=".",
                   help="folder to register (default: the current directory)")
    p.add_argument("--name", help="workspace name (default: the folder name)")
    p.add_argument("--course",
                   help="course identifier, lowercase ASCII (default: the pool "
                        "database name, else a slug of the folder name, else the "
                        "next free short code)")
    p.add_argument("--chapter")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("use", help="switch the active course and chapter of a workspace")
    p.add_argument("course")
    p.add_argument("chapter", help="chapter identifier, or \"\" for the whole course")
    p.add_argument("--workspace")
    p.set_defaults(func=cmd_use)

    p = sub.add_parser("ls", help="list workspaces with stats")
    p.add_argument("--json", action="store_true", help="print the workspaces as JSON")
    p.set_defaults(func=cmd_ls)

    p = sub.add_parser("open", help="print the workspace URL")
    p.add_argument("name", nargs="?")
    p.add_argument("--port", type=int, default=3081)
    p.set_defaults(func=cmd_open)

    p = sub.add_parser("serve", help="start the web workbench in the foreground")
    p.add_argument("--port", type=int, default=3081)
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("daemon", help="run the web workbench in the background")
    daemon_sub = p.add_subparsers(dest="action", required=True)

    action = daemon_sub.add_parser("start")
    action.add_argument("--port", type=int, default=3081)
    action.set_defaults(func=cmd_daemon)

    action = daemon_sub.add_parser("stop")
    action.set_defaults(func=cmd_daemon)

    action = daemon_sub.add_parser("status")
    action.set_defaults(func=cmd_daemon)

    p = sub.add_parser("dashboard", help="ensure the workbench runs and open it")
    p.add_argument("name", nargs="?")
    p.add_argument("--port", type=int, default=3081)
    p.set_defaults(func=cmd_dashboard)

    p = sub.add_parser("doctor", help="check registry, databases, providers, and service (read-only)")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("weak", help="weak knowledge points, ordered")
    p.add_argument("name", nargs="?")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true", help="print the ranked list as JSON")
    p.set_defaults(func=cmd_weak)

    p = sub.add_parser("due", help="due items (background reminders)")
    p.add_argument("name", nargs="?")
    p.add_argument("--json", action="store_true", help="print the due list as JSON")
    p.set_defaults(func=cmd_due)

    p = sub.add_parser(
        "pull",
        help="compose a practice set: scope, named problems, filters, learner evidence")
    p.add_argument("name", nargs="?")
    p.add_argument("--kp", action="append", default=[],
                   help="knowledge point to select from (repeatable; default: the chapter lens)")
    p.add_argument("--problem", action="append", default=[],
                   help="named problem to add to the set (repeatable; never filtered or capped away)")
    p.add_argument("--weak", action="store_true",
                   help="add problems of the knowledge points carrying weakness evidence")
    p.add_argument("--due", action="store_true", help="add problems whose review is due")
    p.add_argument("--wrong", action="store_true",
                   help="add problems recorded as wrong or stuck")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--mode", choices=["weak", "random", "all", "exam", "micro", "yes_no"],
                   default="weak")
    p.add_argument("--source-kind")
    p.add_argument("--origin-kind", choices=[
        "source_problem", "adapted_problem", "generated_grounded",
    ])
    p.add_argument("--source-group", choices=[
        "textbook", "exam", "ai_generated", "other",
    ])
    p.add_argument("--exam-year",
                   help="source examination year; matched as a prefix (2023 finds 2023-2024秋冬)")
    p.add_argument("--difficulty-min", type=float)
    p.add_argument("--difficulty-max", type=float)
    for dimension in difficulty_rules.DIMENSIONS:
        p.add_argument("--" + dimension.replace("_", "-") + "-min", type=int)
        p.add_argument("--" + dimension.replace("_", "-") + "-max", type=int)
    p.add_argument("--difficulty-strategy", choices=["balanced"])
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("--include", action="append", default=[],
                   help="restrict the result to these problems inside the scope")
    p.add_argument("--ids", action="store_true",
                   help="print problem ids only (the historical shape)")
    p.add_argument("--check", action="store_true",
                   help="validate the manifest and preview the print, writing nothing")
    p.add_argument("--input", help="re-run a saved practice manifest (file, or - for stdin)")
    p.add_argument("--plan", help="write the practice manifest to this file")
    p.add_argument("--print", dest="print_dir", metavar="DIR",
                   help="write <base>-problem-set.md and <base>-solutions.md into DIR")
    p.add_argument("--base", help="base file name for --print (default: the chapter)")
    p.add_argument("--title", help="title of the printed practice set")
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
    p.add_argument("--item", required=True, choices=["kp", "problem", "card"])
    p.add_argument("--id", required=True)
    p.add_argument("--rating", type=int, choices=[1, 2, 3, 4, 5])
    p.add_argument("--note")
    p.add_argument("--direction", help="card practice direction (default: forward)")
    p.set_defaults(func=cmd_feedback)

    p = sub.add_parser("schedule", help="show schedule state for an item")
    p.add_argument("name", nargs="?")
    p.add_argument("--item", required=True, choices=["kp", "problem"])
    p.add_argument("--id", required=True)
    p.set_defaults(func=cmd_schedule)

    p = sub.add_parser("goals", help="manage goals (list/add/update/rm)")
    p.add_argument("name", nargs="?")
    p.add_argument("action", nargs="?", choices=["list", "add", "update", "rm"], default="list")
    p.add_argument("goal_id", nargs="?")
    p.add_argument("--title")
    p.add_argument("--kind", choices=["stage", "long_term"])
    p.add_argument("--start-date")
    p.add_argument("--deadline")
    p.add_argument("--description")
    p.set_defaults(func=cmd_goals)

    p = sub.add_parser("bridge", help="configure or list bridge providers")
    p.add_argument("action", choices=["add", "list"])
    p.add_argument("provider", nargs="?")
    p.add_argument("--command")
    p.add_argument("--model")
    p.add_argument("--args", action="append", default=[])
    p.add_argument("--timeout", type=int, default=300,
                   help="seconds of silence before a turn is declared stuck")
    p.add_argument("--tool-timeout", type=int,
                   help="seconds of silence allowed while a command or tool runs")
    p.set_defaults(func=cmd_bridge)

    p = sub.add_parser(
        "attempts",
        help="read, check, record, and correct Agent-transcribed problem attempts")
    p.add_argument("name")
    attempts_sub = p.add_subparsers(dest="action", required=True)

    action = attempts_sub.add_parser("list", help="attempts of one problem")
    action.add_argument("--problem", required=True, help="problem id")
    action.set_defaults(func=cmd_attempts)

    action = attempts_sub.add_parser("get", help="one attempt with its recording")
    action.add_argument("attempt_id")
    action.set_defaults(func=cmd_attempts)

    manifest_help = ("JSON file (or - for stdin): {\"request_id\": \"<caller-stable id>\","
                     " \"items\": [{\"problem_id\": \"…\", \"answer_text\": \"…\","
                     " \"note\": \"…\", \"rating\": 1-5 (optional)}]}")
    for action_name, help_text in (
        ("check", "validate a manifest and preview its effects, writing nothing"),
        ("apply", "record every attempt of a manifest atomically"),
    ):
        action = attempts_sub.add_parser(action_name, help=help_text)
        action.add_argument("--input", required=True, help=manifest_help)
        action.set_defaults(func=cmd_attempts)

    action = attempts_sub.add_parser(
        "correct", help="replace one Agent-recorded attempt and its rating")
    action.add_argument("attempt_id")
    action.add_argument(
        "--input", required=True,
        help="JSON file (or - for stdin): {\"request_id\": \"<new id>\","
             " \"answer_text\": \"…\", \"note\": \"…\", \"rating\": 1-5 (optional)}")
    action.set_defaults(func=cmd_attempts)

    action = attempts_sub.add_parser(
        "sources", help="answer-image directories the Agent may read (no copies)")
    action.set_defaults(func=cmd_attempts)
    sources_sub = action.add_subparsers(dest="source_action", required=True)
    for source_action in ("add", "remove"):
        source = sources_sub.add_parser(source_action)
        source.add_argument("--path", required=True,
                            help="directory that holds the learner's answer images")
        source.set_defaults(func=cmd_attempts)
    sources_sub.add_parser("list").set_defaults(func=cmd_attempts)

    p = sub.add_parser("data", help="read or explicitly mutate workspace content as JSON")
    p.add_argument("name")
    p.add_argument(
        "action",
        choices=["get", "list", "search", "history", "create", "update", "delete", "state"],
    )
    p.add_argument("entity", choices=["kp", "problem", "relation"])
    p.add_argument("target", nargs="?")
    p.add_argument("value", nargs="?", choices=["needs_work", "review", "mastered"])
    p.add_argument("--input")
    p.set_defaults(func=cmd_data)

    p = sub.add_parser("difficulty", help="check or apply objective problem ratings")
    p.add_argument("name")
    difficulty_sub = p.add_subparsers(dest="action", required=True)
    for action_name in ("check", "apply"):
        action = difficulty_sub.add_parser(action_name)
        action.add_argument("--input", required=True)
        action.set_defaults(func=cmd_difficulty)

    p = sub.add_parser("guard", help="run a workspace guard")
    p.add_argument("name", nargs="?")
    p.add_argument("gate", choices=["extract-chapter", "extract-problems", "problem-set"])
    p.add_argument("--apply", action="store_true")
    p.set_defaults(func=cmd_guard)

    p = sub.add_parser("ingest", help="prepare, run, gate, and apply UTF-8 content artifacts")
    p.add_argument("name")
    ingest_sub = p.add_subparsers(dest="action", required=True)

    action = ingest_sub.add_parser("batches")
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("prepare")
    action.add_argument("operation", choices=["problem-solutions", "problem-audit"])
    action.add_argument("--input", required=True)
    action.add_argument("--output", required=True)
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("run")
    action.add_argument("target")
    action.add_argument("--provider", required=True,
                        choices=list(conversation_providers.SUPPORTED))
    action.add_argument("--output")
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("gate")
    action.add_argument("entity", choices=["problem"])
    action.add_argument("--solutions", required=True)
    action.add_argument("--audit", required=True)
    action.add_argument("--content-patch")
    action.add_argument("--content-audit")
    action.add_argument("--output", required=True)
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("apply")
    action.add_argument("entity", choices=["problem"])
    action.add_argument("--input", required=True)
    action.add_argument("--backup")
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("rollback")
    action.add_argument("--batch", required=True)
    action.add_argument("--backup")
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("migrate-figures",
                                   help="plan (default) or apply (--apply) the migration of embedded source images")
    action.add_argument("--apply", action="store_true")
    action.add_argument("--backup")
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("render")
    action.add_argument("--input", required=True)
    action.add_argument("--output", required=True)
    action.set_defaults(func=cmd_ingest)

    action = ingest_sub.add_parser("recipe")
    action.add_argument("recipe",
                        choices=["knowledge", "problems", "views", "micro-quiz", "flash-card", "figures"])
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


def command_names(parser=None):
    """Every top-level command this CLI exposes (the surface audit reads this)."""
    parser = parser or build_parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return sorted(action.choices)
    return []


def _run(argv, prog):
    args = build_parser(prog).parse_args(argv)
    return args.func(args) or 0


def main(argv=None):
    """Module-form entry point (`python -m workbench.cli.main`)."""
    return _run(argv, "lesson-kit")


def lesson_kit_main(argv=None):
    """Entry point for the `lesson-kit` command."""
    return _run(argv, "lesson-kit")


if __name__ == "__main__":
    sys.exit(main())
