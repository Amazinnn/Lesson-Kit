"""Resumable UTF-8 ingestion artifacts and formal-problem gates."""

import html
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
from pathlib import Path

from workbench.bridge import conversation_providers
from workbench.domain import cards as card_rules
from workbench.domain import micro_quiz as micro_quiz_rules


AUDIT_DIMENSIONS = (
    "source_consistency", "meaning", "formatting", "knowledge_point_mapping",
    "answer_correctness", "solution_completeness",
)
KP_AUDIT_DIMENSIONS = (
    "source_consistency", "meaning", "formatting", "relationship_mapping",
    "uniqueness", "completeness",
)
KP_FIELDS = (
    "kp_id", "knowledge_item", "source_location", "knowledge_type",
    "related_kp_ids", "importance", "learning_action", "body",
    "fragile", "graph_label",
)
KP_TYPES = {
    "concept-property", "method-modeling", "formula-calculation",
    "algorithm-process", "code-implementation", "system-timing",
    "lab-implementation", "memory-recall",
}
KP_IMPORTANCE = {"core", "supplementary", "optional"}
RECIPE_NAMES = {"knowledge", "problems", "views", "micro-quiz",
                "flash-card", "figures"}
MICRO_QUIZ_KIND = "micro-quiz-patch"
MICRO_QUIZ_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-mq-\d{3}$")
FLASH_CARD_KIND = "flash-card-patch"
FLASH_CARD_ID = re.compile(r"^[a-z0-9-]+-fc-\d{3}$")
FIGURE_PATCH_KIND = "figure-patch"
# One atomic bundle of new knowledge points, problems, cards, and source figures.
CONTENT_BUNDLE_KIND = "content-bundle"
PROBLEM_TYPES = {
    "calculation", "proof", "modeling", "explanation", "experiment",
    "design", "application", "counterexample", "other",
}
SOLUTION_ORIGINS = {"source", "generated"}
_BUNDLE_LISTS = ("knowledge_points", "problems", "flash_cards")
CHAPTER_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SOURCE_KINDS = {"textbook", "quiz", "midterm", "final", "makeup", "other"}
ORIGIN_KINDS = {"source_problem", "adapted_problem", "generated_grounded"}
FIGURE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "svg", "webp"}
_LEGACY_IMAGE_REF = re.compile(r"!\[[^\]]*\]\(images/([^)/\s]+)\)")
_TAG = re.compile(r"</?(sup|sub)>")
_CURRENT_RECOVERY_PROBLEMS = {
    f"dmath-ch06-prob-{index:03d}" for index in range(1, 304)
}
_CURRENT_RECOVERY_KPS = {
    "dmath-ch06-kp-029", "dmath-ch06-kp-030", "dmath-ch06-kp-031",
}
_CURRENT_RECOVERY_MAPPINGS = {
    "dmath-ch06-prob-067": ["dmath-ch06-kp-003", "dmath-ch06-kp-009", "dmath-ch06-kp-010"],
    "dmath-ch06-prob-156": ["dmath-ch06-kp-009", "dmath-ch06-kp-010", "dmath-ch06-kp-012", "dmath-ch06-kp-013"],
    "dmath-ch06-prob-189": ["dmath-ch06-kp-014", "dmath-ch06-kp-026"],
    "dmath-ch06-prob-190": ["dmath-ch06-kp-014", "dmath-ch06-kp-026"],
    "dmath-ch06-prob-280": ["dmath-ch06-kp-020"],
    "dmath-ch06-prob-281": ["dmath-ch06-kp-003", "dmath-ch06-kp-020"],
    "dmath-ch06-prob-294": ["dmath-ch06-kp-029"],
    "dmath-ch06-prob-295": ["dmath-ch06-kp-030"],
    "dmath-ch06-prob-297": ["dmath-ch06-kp-030"],
    "dmath-ch06-prob-300": ["dmath-ch06-kp-031"],
    "dmath-ch06-prob-301": ["dmath-ch06-kp-031"],
    "dmath-ch06-prob-302": ["dmath-ch06-kp-031"],
    "dmath-ch06-prob-303": ["dmath-ch06-kp-031"],
}


def read_artifact(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("artifact must be a JSON object")
    return data


def write_artifact(path, data):
    if not isinstance(data, dict):
        raise ValueError("artifact must be a JSON object")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def prepare(operation, input_path, output_path):
    """Create an explicit provider task; this operation never starts a provider."""
    source = read_artifact(input_path)
    records = source.get("items", source.get("problems"))
    if not isinstance(records, list):
        raise ValueError("prepare input requires an items list")
    items = []
    for record in records:
        problem = record.get("problem", record.get("problem_id")) if isinstance(record, dict) else None
        text = record.get("source", record.get("problem_text")) if isinstance(record, dict) else None
        if not isinstance(problem, str) or not isinstance(text, str):
            raise ValueError("prepare input requires problem_id and problem_text")
        item = {"source": text, "problem": problem}
        if operation == "problem-audit":
            solution = record.get("solution")
            if not isinstance(solution, str):
                raise ValueError("problem-audit input requires solution")
            item["solution"] = solution
        items.append(item)
    return write_artifact(output_path, {
        "kind": "ingest-task", "operation": operation, "items": items,
    })


def run(task_path, output_path, provider_name, workspace):
    """Run one PATH-native agent session, without registry fallback."""
    if provider_name not in conversation_providers.SUPPORTED:
        raise ValueError(
            "provider must be explicitly " + " or ".join(conversation_providers.SUPPORTED)
        )
    task = read_artifact(task_path)
    if task.get("kind") != "ingest-task":
        raise ValueError("run requires an ingest-task artifact")
    provider = conversation_providers.get(provider_name)
    command = conversation_providers.build_command(provider)
    prompt = json.dumps({
        "instruction": "Return one UTF-8 JSON artifact only.", "task": task,
    }, ensure_ascii=False)
    try:
        completed = subprocess.run(
            command, input=prompt, text=True, encoding="utf-8", capture_output=True,
            cwd=str(workspace), timeout=provider.get("timeout_s", 300), check=False,
            **conversation_providers.hidden_launch_kwargs(),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("provider timed out") from exc
    if completed.returncode != 0:
        raise RuntimeError(f"provider exited {completed.returncode}")
    payload, session_id = _provider_payload(provider_name, completed.stdout)
    if payload.get("kind") not in ("solutions", "audit"):
        raise ValueError("provider result must be a solutions or audit artifact")
    if not session_id:
        raise ValueError("provider result lacks a native session id")
    payload["provider"] = provider_name
    payload["provider_session_id"] = session_id
    return write_artifact(output_path, payload)


def gate(db_path, solutions_path, audit_path, output_path,
         content_patch_path=None, content_audit_path=None):
    """Validate artifact provenance, source identity, and deterministic content gates."""
    if bool(content_patch_path) != bool(content_audit_path):
        raise ValueError("content patch and audit must be supplied together")
    solutions = read_artifact(solutions_path)
    audit = read_artifact(audit_path)
    content_patch = read_artifact(content_patch_path) if content_patch_path else None
    content_audit = read_artifact(content_audit_path) if content_audit_path else None
    conn = sqlite3.connect(db_path)
    try:
        report = _gate_data(conn, solutions, audit, content_patch, content_audit)
    finally:
        conn.close()
    report.update({"kind": "gate-report", "solutions": solutions, "audit": audit})
    if content_patch is not None:
        report.update({"content_patch": content_patch, "content_audit": content_audit})
    return write_artifact(output_path, report)


def render(input_path, output_path):
    """Render a gated file artifact with source text escaped by default."""
    artifact = read_artifact(input_path)
    items = artifact.get("items")
    if not isinstance(items, list):
        raise ValueError("render input requires items")
    rendered = []
    for item in items:
        result = dict(item)
        for field in ("source", "solution"):
            if field in item:
                result[f"rendered_{field}"] = render_text(item[field])
        rendered.append(result)
    return write_artifact(output_path, {"kind": "rendered", "items": rendered})


def render_text(text):
    errors = _markup_errors(text)
    if errors:
        raise ValueError("; ".join(errors))
    parts = []
    index = 0
    for match in _TAG.finditer(text):
        parts.append(html.escape(text[index:match.start()]))
        parts.append(match.group(0))
        index = match.end()
    parts.append(html.escape(text[index:]))
    return "".join(parts)


def recipe(name, db_path, input_path, output_dir, apply_changes=False, backup_path=None):
    """Write an official recipe record; the problems and micro-quiz recipes can explicitly apply."""
    if name not in RECIPE_NAMES:
        raise ValueError(f"unknown recipe: {name}")
    database = Path(db_path)
    conn = sqlite3.connect(database)
    try:
        accounting = _accounting(conn)
    finally:
        conn.close()
    result = {
        "kind": "recipe", "recipe": name, "input": str(input_path),
        "accounting": accounting, "applied": False,
    }
    if apply_changes:
        if name == "micro-quiz":
            applied = apply_micro_quiz(database, input_path, backup_path)
            result.update(applied)
        elif name == "flash-card":
            applied = apply_flash_cards(database, input_path, backup_path)
            result.update(applied)
        elif name == "figures":
            applied = apply_figure_patch(database, input_path, backup_path)
            result.update(applied)
        elif name == "problems":
            applied = apply(database, input_path, backup_path)
            result.update(applied)
        else:
            raise ValueError("only the problems, micro-quiz, flash-card, and figures recipes have an apply stage")
    write_artifact(Path(output_dir) / "recipe.json", result)
    return result


def apply(db_path, gate_path, backup_path=None):
    """Revalidate and update every formal problem while holding one write lock."""
    report = read_artifact(gate_path)
    if report.get("kind") != "gate-report":
        raise ValueError("apply requires a gate-report artifact")
    solutions = report.get("solutions")
    audit = report.get("audit")
    content_patch = report.get("content_patch")
    content_audit = report.get("content_audit")
    database = Path(db_path)
    backup = Path(backup_path) if backup_path else database.with_name(database.name + ".ingest-backup")
    if backup.exists():
        raise FileExistsError(f"recoverable copy already exists: {backup}")
    conn = sqlite3.connect(database)
    try:
        conn.execute("BEGIN IMMEDIATE")
        verified = _gate_data(conn, solutions, audit, content_patch, content_audit)
        if not verified["ok"]:
            raise ValueError("; ".join(verified["errors"]))
        batch_id = _allocate_batch_id(conn)
        manifest_path = _write_manifest_snapshot(database, batch_id, report)
        _backup_database(database, backup)
        if content_patch:
            for item in content_patch["knowledge_points"]:
                fields = list(KP_FIELDS)
                if item.get("difficulty") is not None:
                    fields.append("difficulty")
                values = [
                    json.dumps(item[field], ensure_ascii=False)
                    if field == "related_kp_ids" else item[field]
                    for field in fields
                ]
                conn.execute(
                    f"INSERT INTO knowledge_points ({', '.join(fields)}) "
                    f"VALUES ({', '.join('?' for _ in fields)})",
                    values,
                )
        mappings = {
            item["problem"]: json.dumps(item["kp_ids"], ensure_ascii=False)
            for item in (content_patch or {}).get("mappings", [])
        }
        problem_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(problems)")
        }
        rating_reset = "".join(
            f", {field}=NULL" for field in (
                "difficulty", "difficulty_knowledge_breadth",
                "difficulty_reasoning_depth", "difficulty_transfer_distance",
                "difficulty_construction_openness", "difficulty_model",
            ) if field in problem_columns
        )
        for item in solutions["items"]:
            if item["problem"] in mappings:
                cursor = conn.execute(
                    "UPDATE problems SET solution=?, kp_ids=?, ingest_batch_id=?"
                    f"{rating_reset} WHERE problem_id=?",
                    (item["solution"], mappings[item["problem"]], batch_id,
                     item["problem"]),
                )
            else:
                cursor = conn.execute(
                    "UPDATE problems SET solution=?, ingest_batch_id=?"
                    f"{rating_reset} WHERE problem_id=?",
                    (item["solution"], batch_id, item["problem"]),
                )
            if cursor.rowcount != 1:
                raise ValueError(f"missing formal problem: {item['problem']}")
        counts = {"problems": len(solutions["items"])}
        _record_batch(conn, batch_id, report["kind"], manifest_path, counts, backup)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"ok": True, "applied": True, "batch_id": batch_id,
            "backup_path": str(backup), "accounting": verified["accounting"]}


def apply_micro_quiz(db_path, manifest_path, backup_path=None, course=None):
    """Revalidate and insert micro quizzes while holding one write lock."""
    manifest = read_artifact(manifest_path)
    database = Path(db_path)
    backup = Path(backup_path) if backup_path else database.with_name(database.name + ".ingest-backup")
    return _apply_patch(database, manifest, backup, MICRO_QUIZ_KIND, course)


def _gate_micro_quiz(conn, manifest, course=""):
    errors = []
    if not isinstance(manifest, dict) or manifest.get("kind") != MICRO_QUIZ_KIND:
        return {"ok": False, "errors": ["expected micro-quiz-patch artifact"],
                "accounting": _accounting(conn)}
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        return {"ok": False, "errors": ["micro-quiz-patch requires an items list"],
                "accounting": _accounting(conn)}
    prefix = _course_prefix(course, errors)

    known_kps = {row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points")}
    existing_ids = {row[0] for row in conn.execute("SELECT problem_id FROM problems")}
    seen_ids = set()
    for item in items:
        problem_id = item.get("problem_id") if isinstance(item, dict) else None
        if not isinstance(problem_id, str) or not MICRO_QUIZ_ID.match(problem_id):
            errors.append(f"{problem_id}: id must look like <course>-<chapter>-mq-NNN")
            continue
        if not problem_id.startswith(prefix):
            errors.append(f"{problem_id}: id must start with {prefix} (this workspace's course)")
            continue
        if problem_id in existing_ids or problem_id in seen_ids:
            errors.append(f"{problem_id}: problem id already exists")
            continue
        errors.extend(_inline_problem_difficulty_errors(item, problem_id))
        seen_ids.add(problem_id)
        row = _micro_quiz_row(item)
        if row is None:
            errors.append(f"{problem_id}: item must be an object")
            continue
        if isinstance(row["kp_ids"], list) and len(row["kp_ids"]) == 1 \
                and row["kp_ids"][0] not in known_kps:
            errors.append(f"{problem_id}: unknown knowledge point {row['kp_ids'][0]}")
        errors.extend(f"{problem_id}: {reason}" for reason in _markup_errors(row["problem_text"]))
        for field in micro_quiz_rules.LABEL_FIELD_LIMITS:
            if field in row:
                errors.extend(
                    f"{problem_id}: {field} {reason}"
                    for reason in _markup_errors(row[field])
                )
        errors.extend(
            f"{problem_id}: {reason}" for reason in micro_quiz_rules.validate_problem_row(row)
        )
        if row.get("source_kind") not in SOURCE_KINDS:
            errors.append(f"{problem_id}: source_kind is required and must be valid")
        if row.get("origin_kind") not in ORIGIN_KINDS:
            errors.append(f"{problem_id}: origin_kind is required and must be valid")
    return {"ok": not errors, "errors": errors, "accounting": _accounting(conn)}


def _micro_quiz_row(item):
    if not isinstance(item, dict):
        return None
    payload = item.get("micro_quiz")
    if not isinstance(payload, dict):
        payload = {
            "quiz_type": item.get("quiz_type"),
            "options": item.get("options"),
            "answer_key": item.get("answer_key"),
            "error_reason": item.get("error_reason"),
            "source_evidence": item.get("source_evidence"),
        }
    return {
        "problem_id": item.get("problem_id"),
        "kp_ids": [item["kp_id"]] if isinstance(item.get("kp_id"), str) else item.get("kp_ids"),
        "problem_text": item.get("stem", item.get("problem_text")),
        "problem_type": item.get("problem_type") or "other",
        "source_kind": item.get("source_kind"),
        "origin_kind": item.get("origin_kind"),
        **{field: item[field] for field in micro_quiz_rules.LABEL_FIELD_LIMITS
           if field in item},
        "practice_modes": item.get("practice_modes")
        or micro_quiz_rules.practice_modes_for(payload.get("quiz_type")),
        "micro_quiz": payload,
    }


def apply_flash_cards(db_path, manifest_path, backup_path=None, course=None):
    """Revalidate and insert flash cards while holding one write lock."""
    manifest = read_artifact(manifest_path)
    database = Path(db_path)
    backup = Path(backup_path) if backup_path else database.with_name(database.name + ".ingest-backup")
    return _apply_patch(database, manifest, backup, FLASH_CARD_KIND, course)


def apply_batch(db_path, manifest, *, source, backup_path=None, course=None):
    if source not in {"cli", "bridge"}:
        raise ValueError("source must be cli or bridge")
    kind = manifest.get("kind") if isinstance(manifest, dict) else None
    if kind not in {MICRO_QUIZ_KIND, FLASH_CARD_KIND, CONTENT_BUNDLE_KIND}:
        raise ValueError(f"unsupported ingest kind: {kind}")
    database = Path(db_path)
    backup = Path(backup_path) if backup_path else (
        database.with_name(database.name + ".ingest-backup"))
    if kind == CONTENT_BUNDLE_KIND:
        result = _apply_content_bundle(database, manifest, backup, course)
    else:
        result = _apply_patch(database, manifest, backup, kind, course)
    return {key: result[key] for key in (
        "ok", "batch_id", "kind", "counts", "origins", "backup_path", "applied",
    ) if key in result}


def _kp_difficulty_errors(item, label):
    """Optional difficulty: declared means 1-5 with a basis; undeclared passes.

    The basis is gate-time evidence only — it is never written to the pool.
    """
    value = item.get("difficulty")
    if value is None:
        return []
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
        return [f"{label}: difficulty must be an integer from 1 to 5"]
    basis = item.get("difficulty_basis")
    if not isinstance(basis, str) or not basis.strip():
        return [f"{label}: difficulty requires a non-empty difficulty_basis"]
    return []


def _inline_problem_difficulty_errors(item, label):
    fields = {
        "difficulty", "difficulty_basis", "difficulty_model",
        "difficulty_knowledge_breadth", "difficulty_reasoning_depth",
        "difficulty_transfer_distance", "difficulty_construction_openness",
    }
    if isinstance(item, dict) and fields & set(item):
        return [
            f"{label}: difficulty is rated separately with `lesson-kit difficulty`"
        ]
    return []


def _problem_fields(conn):
    """The governed problem columns written by a micro-quiz patch."""
    fields = ["problem_id", "kp_ids", "problem_text", "problem_type", "source_kind",
              "origin_kind", "topic_label", "display_title", "display_summary", "practice_modes",
              "micro_quiz", "ingest_batch_id"]
    return fields


def _course_prefix(course, errors):
    """The `course-` prefix every id of this batch must carry, or "" plus a reason.

    A workspace holds exactly one course; without one there is nothing to check
    ids against, so the batch is refused instead of guessed at.
    """
    if isinstance(course, str) and course:
        return f"{course}-"
    errors.append(
        "this workspace has no course identifier — set it with "
        "`lesson-kit use <course> <chapter>` before adding content"
    )
    return ""


def _apply_patch(database, manifest, backup, kind, course=None):
    if backup.exists():
        raise FileExistsError(f"recoverable copy already exists: {backup}")
    course = course or database.stem          # the pool file name is the course id
    conn = sqlite3.connect(database)
    try:
        conn.execute("BEGIN IMMEDIATE")
        verified = (
            _gate_micro_quiz(conn, manifest, course)
            if kind == MICRO_QUIZ_KIND else _gate_flash_cards(conn, manifest, course)
        )
        if not verified["ok"]:
            raise ValueError("\n".join(verified["errors"]))
        batch_id = _allocate_batch_id(conn)
        manifest_path = _write_manifest_snapshot(database, batch_id, manifest)
        _backup_database(database, backup)
        if kind == MICRO_QUIZ_KIND:
            fields = _problem_fields(conn)
            for item in manifest["items"]:
                row = _micro_quiz_row(item)
                values = [
                    row["problem_id"],
                    json.dumps(row["kp_ids"], ensure_ascii=False),
                    row["problem_text"],
                    row["problem_type"],
                    row["source_kind"],
                    row["origin_kind"],
                    row.get("topic_label"),
                    row.get("display_title"),
                    row.get("display_summary"),
                    json.dumps(row["practice_modes"], ensure_ascii=False),
                    json.dumps(row["micro_quiz"], ensure_ascii=False),
                    batch_id,
                ]
                conn.execute(
                    f"INSERT INTO problems ({', '.join(fields)}, solution)"
                    f" VALUES ({', '.join('?' for _ in values)}, NULL)",
                    values,
                )
            counts = {"problems": len(manifest["items"])}
        else:
            for item in manifest["items"]:
                row = _flash_card_row(item)
                conn.execute(
                    "INSERT INTO flash_cards (card_id, kp_id, front, back, source_evidence,"
                    " topic_label, directions, ingest_batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (row["card_id"], row["kp_id"], row["front"], row["back"],
                     row["source_evidence"], row.get("topic_label"),
                     json.dumps(row["directions"]), batch_id),
                )
            counts = {"flash_cards": len(manifest["items"])}
        _record_batch(conn, batch_id, kind, manifest_path, counts, backup)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"ok": True, "applied": True, "batch_id": batch_id, "kind": kind,
            "counts": counts, "backup_path": str(backup),
            "accounting": verified["accounting"]}


def apply_content_bundle(db_path, manifest, backup_path=None, course=None):
    """Validate and apply one atomic content bundle."""
    database = Path(db_path)
    backup = Path(backup_path) if backup_path else (
        database.with_name(database.name + ".ingest-backup"))
    return _apply_content_bundle(database, manifest, backup, course)


def read_staged_manifest(jobs_folder, reference):
    """Load a manifest staged inside one conversation's jobs directory.

    Absolute paths, traversal, and anything but a readable JSON file inside
    that directory are refused: a staged reference may not address the rest of
    the local filesystem.
    """
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError("staged manifest reference must be a non-empty string")
    folder = Path(jobs_folder).resolve()
    candidate = Path(reference)
    if candidate.is_absolute() or candidate.suffix.lower() != ".json":
        raise ValueError("staged manifest must be a relative .json path")
    target = (folder / candidate).resolve()
    if not target.is_relative_to(folder):
        raise ValueError("staged manifest must stay inside this conversation")
    if not target.is_file():
        raise ValueError(f"staged manifest not found: {reference}")
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("staged manifest must be a JSON object")
    return data


def _bundle_list(manifest, field, errors):
    value = manifest.get(field)
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return []
    return value


def _table_columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _insert_row(conn, table, row):
    """Insert only the columns this pool actually has (old shapes stay usable)."""
    columns = _table_columns(conn, table)
    names = [name for name in row if name in columns]
    conn.execute(
        f"INSERT INTO {table} ({', '.join(names)})"
        f" VALUES ({', '.join('?' for _ in names)})",
        [row[name] for name in names],
    )


def _next_readable_number(conn, table, column, prefix):
    """The first free `<prefix>NNN` number, read inside the current transaction."""
    rows = conn.execute(
        f"SELECT {column} FROM {table} WHERE {column} LIKE ?", (prefix + "%",)
    ).fetchall()
    numbers = [
        int(row[0][len(prefix):]) for row in rows
        if str(row[0])[len(prefix):].isdigit()
    ]
    return max(numbers, default=0) + 1


def _bundle_kp_fields(item):
    """The governed knowledge-point columns a bundle may set."""
    return {
        "knowledge_item": item.get("knowledge_item"),
        "knowledge_type": item.get("knowledge_type"),
        "importance": item.get("importance"),
        "source_location": item.get("source_location"),
        "body": item.get("body"),
        "graph_label": item.get("graph_label"),
        "learning_action": item.get("learning_action"),
        "fragile": item.get("fragile"),
    }


def _bundle_problem_fields(item, kp_ids):
    """The governed problem columns shared by formal and micro items."""
    solution = item.get("solution")
    return {
        "kp_ids": kp_ids,
        "problem_text": item.get("stem", item.get("problem_text")),
        "problem_type": item.get("problem_type"),
        "source_kind": item.get("source_kind"),
        "origin_kind": item.get("origin_kind"),
        "source_evidence": item.get("source_evidence"),
        "source_answer": item.get("source_answer"),
        "solution": solution,
        "solution_origin": item.get("solution_origin"),
        "topic_label": item.get("topic_label"),
        "display_title": item.get("display_title"),
        "display_summary": item.get("display_summary"),
    }


def _bundle_micro_payload(item):
    return {
        "quiz_type": item.get("quiz_type"),
        "options": item.get("options"),
        "answer_key": item.get("answer_key"),
        "error_reason": item.get("error_reason"),
        "source_evidence": item.get("source_evidence"),
    }


def _gate_content_bundle(conn, manifest, course="", chapter=""):
    """Validate a complete bundle; every reason is reported, nothing is written."""
    errors = []
    if not isinstance(manifest, dict) or manifest.get("kind") != CONTENT_BUNDLE_KIND:
        return {"ok": False, "errors": ["expected a content-bundle manifest"]}
    prefix = _course_prefix(course, errors)
    bundle_chapter = manifest.get("chapter") or chapter
    if not isinstance(bundle_chapter, str) or not CHAPTER_ID.fullmatch(bundle_chapter):
        errors.append("content-bundle requires a chapter identifier (lowercase ASCII)")
        bundle_chapter = ""
    scope = f"{course}-{bundle_chapter}"

    kp_items = _bundle_list(manifest, "knowledge_points", errors)
    problem_items = _bundle_list(manifest, "problems", errors)
    card_items = _bundle_list(manifest, "flash_cards", errors)
    if not (kp_items or problem_items or card_items):
        errors.append(
            "content-bundle requires at least one knowledge point, problem, or flash card"
        )

    keys = set()
    kp_plans = []
    kp_ids = []
    allocated = {}

    def allocate(table, column, prefix):
        """Ids are allocated server-side, in order, inside one bundle."""
        key = (table, prefix)
        if key not in allocated:
            allocated[key] = _next_readable_number(conn, table, column, prefix)
        number = allocated[key]
        allocated[key] += 1
        return f"{prefix}{number:03d}"

    for index, item in enumerate(kp_items):
        label = f"knowledge point {index + 1}"
        if not isinstance(item, dict):
            errors.append(f"{label}: must be an object")
            continue
        key = item.get("key")
        if not isinstance(key, str) or not key.strip():
            errors.append(f"{label}: key is required")
            continue
        if key in keys:
            errors.append(f"{label}: duplicate key {key}")
            continue
        fields = _bundle_kp_fields(item)
        if not isinstance(fields["knowledge_item"], str) or not fields["knowledge_item"].strip():
            errors.append(f"{label}: knowledge_item is required")
            continue
        if fields["knowledge_type"] is not None and fields["knowledge_type"] not in KP_TYPES:
            errors.append(f"{label}: unknown knowledge_type {fields['knowledge_type']!r}")
        if fields["importance"] is not None and fields["importance"] not in KP_IMPORTANCE:
            errors.append(f"{label}: unknown importance {fields['importance']!r}")
        kp_id = item.get("kp_id")
        if kp_id is None:
            kp_id = allocate("knowledge_points", "kp_id", f"{scope}-kp-")
        elif not isinstance(kp_id, str) or not kp_id.startswith(prefix):
            errors.append(f"{label}: kp_id must start with {prefix}")
            continue
        exists = conn.execute(
            "SELECT 1 FROM knowledge_points WHERE kp_id=?", (kp_id,)
        ).fetchone()
        if exists or kp_id in kp_ids:
            errors.append(f"{label}: {kp_id} already exists")
            continue
        keys.add(key)
        kp_ids.append(kp_id)
        kp_plans.append({"key": key, "kp_id": kp_id, "fields": fields})

    def resolve_kp(reference):
        if isinstance(reference, str) and reference in {kp["key"] for kp in kp_plans}:
            return next(kp["kp_id"] for kp in kp_plans if kp["key"] == reference)
        return reference

    known_kps = {row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points")}
    known_kps |= set(kp_ids)

    problem_plans = []
    seen_problem_keys = set()
    for index, item in enumerate(problem_items):
        label = f"problem {index + 1}"
        if not isinstance(item, dict):
            errors.append(f"{label}: must be an object")
            continue
        key = item.get("key")
        if not isinstance(key, str) or not key.strip():
            errors.append(f"{label}: key is required")
            continue
        if key in seen_problem_keys:
            errors.append(f"{label}: duplicate key {key}")
            continue
        seen_problem_keys.add(key)
        raw_kp_ids = item.get("kp_ids")
        if isinstance(item.get("kp_id"), str) and raw_kp_ids is None:
            raw_kp_ids = [item["kp_id"]]
        if not isinstance(raw_kp_ids, list) or not raw_kp_ids:
            errors.append(f"{label}: kp_ids must be a non-empty list")
            continue
        resolved = []
        for reference in raw_kp_ids:
            kp_id = resolve_kp(reference)
            if not isinstance(kp_id, str) or kp_id not in known_kps:
                errors.append(f"{label}: unknown knowledge point {reference}")
                continue
            if kp_id not in resolved:
                resolved.append(kp_id)
        errors.extend(_inline_problem_difficulty_errors(item, label))
        is_micro = item.get("quiz_type") is not None or item.get("micro_quiz") is not None
        fields = _bundle_problem_fields(item, resolved)
        if is_micro:
            payload = _bundle_micro_payload(item)
            row = {
                "kp_ids": resolved,
                "problem_text": item.get("stem", item.get("problem_text")),
                "problem_type": fields["problem_type"] or "other",
                "practice_modes": item.get("practice_modes")
                or micro_quiz_rules.practice_modes_for(payload.get("quiz_type")),
                "micro_quiz": payload,
            }
            errors.extend(f"{label}: {reason}" for reason in micro_quiz_rules.validate_problem_row(row))
            fields["problem_type"] = row["problem_type"]
            fields["practice_modes"] = row["practice_modes"]
            fields["micro_quiz"] = payload
            suffix = "mq"
        else:
            text = item.get("problem_text")
            if not isinstance(text, str) or not text.strip():
                errors.append(f"{label}: problem_text is required")
            else:
                errors.extend(f"{label}: {reason}" for reason in _markup_errors(text))
            if fields["problem_type"] not in PROBLEM_TYPES:
                errors.append(
                    f"{label}: problem_type must be one of {sorted(PROBLEM_TYPES)}"
                )
            suffix = "prob"
        if fields["source_kind"] not in SOURCE_KINDS:
            errors.append(f"{label}: source_kind is required and must be valid")
        if fields["origin_kind"] not in ORIGIN_KINDS:
            errors.append(f"{label}: origin_kind is required and must be valid")
        if not isinstance(fields["source_evidence"], str) or not fields["source_evidence"].strip():
            errors.append(f"{label}: source_evidence is required")
        if fields["solution"] not in (None, "") and fields["solution_origin"] not in SOLUTION_ORIGINS:
            errors.append(
                f"{label}: solution_origin must be source or generated when a solution is supplied"
            )
        if fields["source_answer"] is not None and not isinstance(fields["source_answer"], str):
            errors.append(f"{label}: source_answer must be a string")
        problem_id = item.get("problem_id")
        if problem_id is None:
            problem_id = allocate("problems", "problem_id", f"{scope}-{suffix}-")
        elif not isinstance(problem_id, str) or not problem_id.startswith(prefix):
            errors.append(f"{label}: problem_id must start with {prefix}")
            continue
        exists = conn.execute(
            "SELECT 1 FROM problems WHERE problem_id=?", (problem_id,)
        ).fetchone()
        if exists or problem_id in {plan["problem_id"] for plan in problem_plans}:
            errors.append(f"{label}: {problem_id} already exists")
            continue
        plans = _plan_bundle_figures(
            item, label, fields.get("problem_text") or item.get("stem"),
            course, bundle_chapter,
        )
        errors.extend(plans.get("errors") or [])
        fields["problem_text"] = plans["text"]
        problem_plans.append({
            "key": key, "problem_id": problem_id, "fields": fields,
            "is_micro": is_micro, "figures": plans["figures"],
        })

    card_plans = []
    seen_card_keys = set()
    for index, item in enumerate(card_items):
        label = f"flash card {index + 1}"
        if not isinstance(item, dict):
            errors.append(f"{label}: must be an object")
            continue
        key = item.get("key")
        if not isinstance(key, str) or not key.strip():
            errors.append(f"{label}: key is required")
            continue
        if key in seen_card_keys:
            errors.append(f"{label}: duplicate key {key}")
            continue
        seen_card_keys.add(key)
        kp_id = resolve_kp(item.get("kp_id"))
        if not isinstance(kp_id, str) or kp_id not in known_kps:
            errors.append(f"{label}: unknown knowledge point {item.get('kp_id')}")
        card_id = item.get("card_id")
        if card_id is None:
            card_id = allocate("flash_cards", "card_id", f"{scope}-fc-")
        elif not isinstance(card_id, str) or not card_id.startswith(prefix):
            errors.append(f"{label}: card_id must start with {prefix}")
            continue
        exists = conn.execute(
            "SELECT 1 FROM flash_cards WHERE card_id=?", (card_id,)
        ).fetchone()
        if exists or card_id in {plan["card_id"] for plan in card_plans}:
            errors.append(f"{label}: {card_id} already exists")
            continue
        row = {
            "card_id": card_id, "kp_id": kp_id, "front": item.get("front"),
            "back": item.get("back"), "source_evidence": item.get("source_evidence"),
            "directions": item.get("directions") or list(card_rules.DEFAULT_DIRECTIONS),
            **({"topic_label": item["topic_label"]} if "topic_label" in item else {}),
        }
        errors.extend(f"{label}: {reason}" for reason in card_rules.validate_card_row(row))
        card_plans.append(row)

    if errors:
        return {"ok": False, "errors": errors}
    return {
        "ok": True, "errors": [], "course": course, "chapter": bundle_chapter,
        "knowledge_points": kp_plans, "problems": problem_plans,
        "flash_cards": card_plans,
    }


def _plan_bundle_figures(item, label, text, course, chapter):
    """Resolve one problem's declared figures and rewrite its references."""
    errors = []
    figures = item.get("figures")
    if figures is None:
        return {"text": text, "figures": []}
    if not isinstance(figures, list):
        return {"text": text, "figures": [], "errors": [f"{label}: figures must be a list"]}
    if not isinstance(text, str):
        return {"text": text, "figures": [],
                "errors": [f"{label}: figures need a problem text to reference them"]}
    planned = []
    for entry in figures:
        if not isinstance(entry, dict):
            errors.append(f"{label}: each figure must be an object")
            continue
        key = entry.get("key")
        source = entry.get("source_path")
        if not isinstance(key, str) or not key.strip():
            errors.append(f"{label}: each figure needs a key")
            continue
        if not isinstance(source, str) or not source:
            errors.append(f"{label}: figure {key} needs a source_path")
            continue
        if f"](figure:{key})" not in text:
            errors.append(f"{label}: problem text must reference figure:{key}")
            continue
        path = Path(source)
        if not path.is_file():
            errors.append(f"{label}: missing source file {source}")
            continue
        try:
            content = path.read_bytes()
            name = _figure_name(content, path)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
            continue
        planned.append({
            "key": key, "name": name, "logical": f"{course}/{chapter}/{name}",
            "source": str(path.resolve()), "content": content,
        })
    rewritten = text
    for entry in planned:
        rewritten = rewritten.replace(f"](figure:{entry['key']})", f"]({entry['logical']})")
    return {"text": rewritten, "figures": planned, "errors": errors}


def _apply_content_bundle(database, manifest, backup, course=None):
    if backup.exists():
        raise FileExistsError(f"recoverable copy already exists: {backup}")
    course = course or database.stem          # the pool file name is the course id
    conn = sqlite3.connect(database)
    created_files = []
    try:
        conn.execute("BEGIN IMMEDIATE")
        verified = _gate_content_bundle(conn, manifest, course)
        if not verified["ok"]:
            raise ValueError("\n".join(verified["errors"]))
        batch_id = _allocate_batch_id(conn)
        snapshot = {
            **{key: manifest[key] for key in _BUNDLE_LISTS if key in manifest},
            "kind": CONTENT_BUNDLE_KIND,
            "chapter": verified["chapter"],
            "_applied": {
                "knowledge_points": [plan["kp_id"] for plan in verified["knowledge_points"]],
                "problems": [plan["problem_id"] for plan in verified["problems"]],
                "flash_cards": [plan["card_id"] for plan in verified["flash_cards"]],
                "figures": sorted({
                    entry["logical"] for plan in verified["problems"]
                    for entry in plan["figures"]
                }),
            },
        }
        manifest_path = _write_manifest_snapshot(database, batch_id, snapshot)
        _backup_database(database, backup)
        figures_root = _figures_root(database, course, verified["chapter"])
        figures_root.mkdir(parents=True, exist_ok=True)
        for plan in verified["problems"]:
            for entry in plan["figures"]:
                destination = figures_root / entry["name"]
                if destination.exists():
                    if destination.read_bytes() != entry["content"]:
                        raise ValueError(
                            f"{plan['problem_id']}: destination conflict for {entry['name']}")
                    continue
                shutil.copyfile(entry["source"], destination)
                created_files.append(destination)

        counts = {"knowledge_points": 0, "problems": 0, "flash_cards": 0, "figures": 0}
        for plan in verified["knowledge_points"]:
            fields = plan["fields"]
            _insert_row(conn, "knowledge_points", {
                "kp_id": plan["kp_id"],
                "knowledge_item": fields["knowledge_item"],
                "knowledge_type": fields["knowledge_type"],
                "importance": fields["importance"],
                "source_location": fields["source_location"],
                "body": fields["body"],
                "graph_label": fields["graph_label"],
                "learning_action": fields["learning_action"],
                "fragile": (
                    json.dumps(fields["fragile"], ensure_ascii=False)
                    if isinstance(fields["fragile"], (dict, list))
                    else fields["fragile"]
                ),
                "ingest_batch_id": batch_id,
            })
            counts["knowledge_points"] += 1
        for plan in verified["problems"]:
            fields = plan["fields"]
            paths = [entry["logical"] for entry in plan["figures"]]
            conn.execute(
                "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
                " problem_type, source_kind, origin_kind, topic_label, display_title,"
                " display_summary, practice_modes, micro_quiz, figure_paths,"
                " source_evidence, source_answer, solution_origin, ingest_batch_id)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    plan["problem_id"],
                    json.dumps(fields["kp_ids"], ensure_ascii=False),
                    fields["problem_text"], fields["solution"],
                    fields["problem_type"], fields["source_kind"], fields["origin_kind"],
                    fields["topic_label"], fields["display_title"],
                    fields["display_summary"],
                    json.dumps(fields["practice_modes"], ensure_ascii=False)
                    if fields.get("practice_modes") else None,
                    json.dumps(fields["micro_quiz"], ensure_ascii=False)
                    if fields.get("micro_quiz") else None,
                    json.dumps(paths, ensure_ascii=False) if paths else None,
                    fields["source_evidence"], fields["source_answer"],
                    fields["solution_origin"], batch_id,
                ),
            )
            counts["problems"] += 1
            counts["figures"] += len(paths)
        for row in verified["flash_cards"]:
            _insert_row(conn, "flash_cards", {
                **row,
                "directions": json.dumps(row["directions"], ensure_ascii=False),
                "ingest_batch_id": batch_id,
            })
            counts["flash_cards"] += 1
        _record_batch(conn, batch_id, CONTENT_BUNDLE_KIND, manifest_path, counts, backup)
        accounting = _accounting(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        for path in created_files:
            try:
                path.unlink()
            except OSError:
                pass
        raise
    finally:
        conn.close()
    origins = {}
    for plan in verified["problems"]:
        origin = plan["fields"].get("origin_kind")
        if isinstance(origin, str):
            origins[origin] = origins.get(origin, 0) + 1
    return {"ok": True, "applied": True, "batch_id": batch_id, "kind": CONTENT_BUNDLE_KIND,
            "counts": counts, "origins": origins, "backup_path": str(backup),
            "accounting": accounting}


def _rollback_content_bundle(conn, database, batch_id):
    """Delete this bundle's rows, then its now-unreferenced figure files."""
    row = conn.execute(
        "SELECT manifest_path FROM ingest_batches WHERE batch_id=?", (batch_id,),
    ).fetchone()
    snapshot = json.loads(Path(row[0]).read_text(encoding="utf-8"))
    applied = snapshot.get("_applied") or {}
    blockers = []
    for kp_id in applied.get("knowledge_points", []):
        for problem_id, in conn.execute(
            "SELECT problem_id FROM problems WHERE kp_ids LIKE ?"
            " AND (ingest_batch_id IS NULL OR ingest_batch_id<>?)",
            (f'%"{kp_id}"%', batch_id),
        ):
            blockers.append(f"knowledge_points: {kp_id} referenced by problems:{problem_id}")
        for card_id, in conn.execute(
            "SELECT card_id FROM flash_cards WHERE kp_id=?"
            " AND (ingest_batch_id IS NULL OR ingest_batch_id<>?)",
            (kp_id, batch_id),
        ):
            blockers.append(f"knowledge_points: {kp_id} referenced by flash_cards:{card_id}")
    if blockers:
        raise ValueError(
            f"batch {batch_id} created knowledge points that are still referenced:\n"
            + "\n".join(blockers)
        )
    counts = {"problems": 0, "flash_cards": 0, "knowledge_points": 0,
              "figures": 0, "figures_kept": 0}
    counts["problems"] = conn.execute(
        "DELETE FROM problems WHERE ingest_batch_id=?", (batch_id,)
    ).rowcount
    counts["flash_cards"] = conn.execute(
        "DELETE FROM flash_cards WHERE ingest_batch_id=?", (batch_id,)
    ).rowcount
    for kp_id in applied.get("knowledge_points", []):
        conn.execute(
            "DELETE FROM knowledge_relations WHERE source_kp_id=? OR target_kp_id=?",
            (kp_id, kp_id),
        )
        for owner, related in conn.execute(
            "SELECT kp_id, related_kp_ids FROM knowledge_points"
            " WHERE related_kp_ids LIKE ?", (f"%{kp_id}%",),
        ).fetchall():
            remaining = [item for item in json.loads(related or "[]") if item != kp_id]
            conn.execute(
                "UPDATE knowledge_points SET related_kp_ids=? WHERE kp_id=?",
                (json.dumps(remaining, ensure_ascii=False), owner),
            )
        conn.execute("DELETE FROM knowledge_points WHERE kp_id=?", (kp_id,))
        counts["knowledge_points"] += 1
    root = database.resolve().parent.parent
    for logical in applied.get("figures", []):
        if _figure_is_referenced(conn, logical):
            counts["figures_kept"] += 1
            continue
        path = root / ".lessonkit" / "figures" / logical
        if path.is_file():
            path.unlink()
        counts["figures"] += 1
    return counts


def _figure_is_referenced(conn, logical):
    for table, column in (("problems", "figure_paths"), ("knowledge_points", "figure_paths")):
        if conn.execute(
            f"SELECT 1 FROM {table} WHERE {column} LIKE ?", (f"%{logical}%",)
        ).fetchone():
            return True
    return False


def _allocate_batch_id(conn):
    next_value = conn.execute(
        "INSERT INTO content_sequences (scope, entity_type, next_value) "
        "VALUES ('pool', 'batch', 2) "
        "ON CONFLICT(scope, entity_type) DO UPDATE SET "
        "next_value=content_sequences.next_value + 1 RETURNING next_value"
    ).fetchone()[0]
    return f"batch-{next_value - 1:03d}"


def _write_manifest_snapshot(database, batch_id, manifest):
    path = database.parent / "ingest" / f"{batch_id}.json"
    write_artifact(path, manifest)
    return path


def _record_batch(conn, batch_id, kind, manifest_path, counts, backup):
    conn.execute(
        "INSERT INTO ingest_batches "
        "(batch_id, kind, manifest_path, counts_json, backup_path) "
        "VALUES (?, ?, ?, ?, ?)",
        (batch_id, kind, str(manifest_path),
         json.dumps(counts, ensure_ascii=False), str(backup)),
    )


def _figure_name(source_bytes, source_path):
    extension = Path(source_path).suffix.lstrip(".").lower()
    if extension not in FIGURE_EXTENSIONS:
        raise ValueError(f"unsupported figure extension .{extension}")
    return f"{hashlib.sha256(source_bytes).hexdigest()}.{extension}"


def _gate_figure_patch(conn, manifest, course=""):
    errors = []
    if manifest.get("kind") != FIGURE_PATCH_KIND:
        return {"ok": False, "errors": ["manifest kind must be figure-patch"]}
    patch_course = manifest.get("course")
    chapter = manifest.get("chapter")
    if not isinstance(patch_course, str) or not patch_course:
        errors.append("figure-patch requires course")
    elif course and patch_course != course:
        errors.append(
            f"figure-patch course {patch_course!r} is not this workspace's "
            f"course {course!r}"
        )
    if not isinstance(chapter, str) or not CHAPTER_ID.fullmatch(chapter):
        errors.append("figure-patch requires a chapter identifier (lowercase ASCII)")
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        return {"ok": False,
                "errors": errors + ["figure-patch requires a non-empty items list"]}
    plans = []
    for index, item in enumerate(items):
        label = f"item {index}"
        if not isinstance(item, dict):
            errors.append(f"{label}: must be an object")
            continue
        owner_id = item.get("owner_id")
        row = conn.execute(
            "SELECT problem_text, figure_paths FROM problems WHERE problem_id=?",
            (owner_id,),
        ).fetchone()
        if row is None:
            errors.append(f"{label}: unknown problem {owner_id}")
            continue
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{owner_id}: text must be a non-empty replacement")
            continue
        files = item.get("figure_files")
        if not isinstance(files, list) or not files:
            errors.append(f"{owner_id}: figure_files must be a non-empty list")
            continue
        landed = []
        for entry in files:
            source = (entry or {}).get("source_path") if isinstance(entry, dict) else None
            if not isinstance(source, str) or not source:
                errors.append(f"{owner_id}: each figure_file needs source_path")
                continue
            path = Path(source)
            if not path.is_file():
                errors.append(f"{owner_id}: missing source file {source}")
                continue
            try:
                content = path.read_bytes()
                name = _figure_name(content, path)
            except ValueError as exc:
                errors.append(f"{owner_id}: {exc}")
                continue
            logical = f"{patch_course}/{chapter}/{name}"
            if f"]({logical})" not in text and f"]({name})" not in text:
                errors.append(f"{owner_id}: text must reference {logical}")
                continue
            landed.append({"name": name, "logical": logical,
                           "source": str(path), "content": content})
        if landed or not files:
            plans.append({"owner_id": owner_id, "previous": row,
                          "files": landed})
    if errors:
        return {"ok": False, "errors": errors}
    return {"ok": True, "errors": [], "plans": plans}


def _figures_root(database, course, chapter):
    """The figures directory of one course/chapter, which must stay in the workspace."""
    workspace = database.resolve().parent.parent
    figures = (workspace / ".lessonkit" / "figures").resolve()
    root = (figures / course / chapter).resolve()
    if not root.is_relative_to(figures):
        raise ValueError(f"figure path would leave the workspace: {course}/{chapter}")
    return root


def _merge_figure_paths(previous_paths, logicals):
    try:
        existing = json.loads(previous_paths) if previous_paths else []
    except (TypeError, json.JSONDecodeError):
        existing = []
    if not isinstance(existing, list):
        existing = []
    merged = [path for path in existing if isinstance(path, str)]
    merged += [path for path in logicals if path not in merged]
    return merged


def apply_figure_patch(db_path, manifest_path, backup_path=None, course=None):
    manifest = read_artifact(manifest_path)
    return _apply_figure_patch(Path(db_path), manifest, backup_path, course)


def _apply_figure_patch(database, manifest, backup_path=None, course=None):
    backup = (Path(backup_path) if backup_path
              else database.with_name(database.name + ".ingest-backup"))
    if backup.exists():
        raise FileExistsError(f"recoverable copy already exists: {backup}")
    course = course or database.stem          # the pool file name is the course id
    conn = sqlite3.connect(database)
    try:
        conn.execute("BEGIN IMMEDIATE")
        verified = _gate_figure_patch(conn, manifest, course)
        if not verified["ok"]:
            raise ValueError("\n".join(verified["errors"]))
        batch_id = _allocate_batch_id(conn)
        snapshot = dict(manifest)
        snapshot["previous"] = [
            {"owner_id": plan["owner_id"],
             "text": plan["previous"][0],
             "figure_paths": plan["previous"][1]}
            for plan in verified["plans"]
        ]
        manifest_path = _write_manifest_snapshot(database, batch_id, snapshot)
        _backup_database(database, backup)
        figures_root = _figures_root(database, manifest["course"], manifest["chapter"])
        figures_root.mkdir(parents=True, exist_ok=True)
        for plan in verified["plans"]:
            for entry in plan["files"]:
                dest = figures_root / entry["name"]
                if dest.exists() and dest.read_bytes() != entry["content"]:
                    raise ValueError(
                        f"{plan['owner_id']}: destination conflict for {entry['name']}")
                if not dest.exists():
                    shutil.copyfile(entry["source"], dest)
        counts = {"problems": 0, "figures": 0}
        for plan in verified["plans"]:
            item = next(i for i in manifest["items"] if i.get("owner_id") == plan["owner_id"])
            paths = _merge_figure_paths(
                plan["previous"][1], [entry["logical"] for entry in plan["files"]])
            conn.execute(
                "UPDATE problems SET problem_text=?, figure_paths=? WHERE problem_id=?",
                (item["text"], json.dumps(paths, ensure_ascii=False), plan["owner_id"]),
            )
            counts["problems"] += 1
            counts["figures"] += len(plan["files"])
        _record_batch(conn, batch_id, FIGURE_PATCH_KIND, manifest_path, counts, backup)
        accounting = _accounting(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"ok": True, "applied": True, "batch_id": batch_id, "kind": FIGURE_PATCH_KIND,
            "counts": counts, "backup_path": str(backup), "accounting": accounting}


def build_legacy_figure_manifest(db_path, workspace_path):
    """Plan the migration of `](images/…)` references into figure-patches."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT problem_id, problem_text FROM problems "
            "WHERE problem_text LIKE '%](images/%' ORDER BY problem_id"
        ).fetchall()
    finally:
        conn.close()
    workspace = Path(workspace_path)
    errors = []
    grouped = {}
    for problem_id, text in rows:
        owner = re.match(r"^(.+)-(ch[A-Za-z0-9]+)-prob-", problem_id)
        if owner is None:
            errors.append(f"{problem_id}: cannot derive course/chapter from the id")
            continue
        course, chapter = owner.group(1), owner.group(2)
        files, new_text = [], text
        for legacy_name in sorted(set(_LEGACY_IMAGE_REF.findall(text))):
            hits = sorted(workspace.glob(f"intermediate/**/images/{legacy_name}"))
            if not hits:
                errors.append(f"{problem_id}: source image not found: {legacy_name}")
                continue
            source = hits[0]
            true_name = _figure_name(source.read_bytes(), source)
            files.append({"source_path": str(source.resolve())})
            new_text = new_text.replace(
                f"](images/{legacy_name})",
                f"]({course}/{chapter}/{true_name})",
            )
        if files:
            key = (course, chapter)
            grouped.setdefault(key, []).append({
                "owner_type": "problem", "owner_id": problem_id,
                "figure_files": files, "text": new_text,
            })
    if errors:
        return {"ok": False, "errors": errors}
    manifests = [
        {"kind": FIGURE_PATCH_KIND, "course": course, "chapter": chapter,
         "items": items}
        for (course, chapter), items in sorted(grouped.items())
    ]
    return {"ok": True, "errors": [], "manifests": manifests}


def migrate_legacy_figures(db_path, workspace_path, apply_changes=False,
                           backup_path=None):
    """Plan (default) or apply the migration of embedded `](images/…)` refs."""
    plan = build_legacy_figure_manifest(db_path, workspace_path)
    if not plan["ok"] or not apply_changes:
        return {"applied": False, "errors": plan["errors"],
                "manifests": plan.get("manifests", [])}
    return {"applied": True,
            "results": [_apply_figure_patch(Path(db_path), manifest, backup_path)
                        for manifest in plan["manifests"]]}


def list_batches(db_path):
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT batch_id, kind, counts_json, applied_at, rolled_back_at, backup_path "
            "FROM ingest_batches ORDER BY applied_at DESC, rowid DESC"
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "batch_id": batch_id,
            "kind": kind,
            "counts": json.loads(counts_json),
            "applied_at": applied_at,
            "rolled_back_at": rolled_back_at,
            "backup_path": backup_path,
        }
        for batch_id, kind, counts_json, applied_at, rolled_back_at, backup_path in rows
    ]


def rollback_batch(db_path, batch_id, backup_path=None):
    database = Path(db_path)
    conn = sqlite3.connect(database)
    try:
        conn.execute("BEGIN IMMEDIATE")
        batch = conn.execute(
            "SELECT kind, rolled_back_at FROM ingest_batches WHERE batch_id=?",
            (batch_id,),
        ).fetchone()
        if batch is None:
            raise ValueError(f"unknown batch {batch_id}")
        if batch[1] is not None:
            raise ValueError(f"batch {batch_id} already rolled back")
        blockers = _rollback_blockers(conn, batch_id)
        if blockers:
            raise ValueError(
                f"batch {batch_id} has dependent learning records:\n"
                + "\n".join(blockers)
            )
        backup = (Path(backup_path) if backup_path else
                  database.with_name(f"{database.name}.{batch_id}-rollback-backup"))
        if backup.exists():
            raise FileExistsError(f"recoverable copy already exists: {backup}")
        _backup_database(database, backup)
        if batch[0] == FIGURE_PATCH_KIND:
            counts = _rollback_figure_patch(conn, batch_id)
            deleted = counts.get("problems", 0)
        elif batch[0] == CONTENT_BUNDLE_KIND:
            counts = _rollback_content_bundle(conn, database, batch_id)
            deleted = (counts["problems"] + counts["flash_cards"]
                       + counts["knowledge_points"])
        else:
            table = "flash_cards" if batch[0] == FLASH_CARD_KIND else "problems"
            cursor = conn.execute(
                f"DELETE FROM {table} WHERE ingest_batch_id=?", (batch_id,),
            )
            deleted = cursor.rowcount
            counts = {table: deleted}
        conn.execute(
            "UPDATE ingest_batches SET rolled_back_at=datetime('now') WHERE batch_id=?",
            (batch_id,),
        )
        accounting = _accounting(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"ok": True, "batch_id": batch_id, "deleted": deleted,
            "backup_path": str(backup), "accounting": accounting}


def _rollback_figure_patch(conn, batch_id):
    """Restore pre-patch text and figure paths from the batch snapshot."""
    row = conn.execute(
        "SELECT manifest_path FROM ingest_batches WHERE batch_id=?", (batch_id,),
    ).fetchone()
    snapshot = json.loads(Path(row[0]).read_text(encoding="utf-8"))
    restored = 0
    for previous in snapshot.get("previous", []):
        conn.execute(
            "UPDATE problems SET problem_text=?, figure_paths=? WHERE problem_id=?",
            (previous["text"], previous["figure_paths"], previous["owner_id"]),
        )
        restored += 1
    return {"problems": restored}


def _rollback_blockers(conn, batch_id):
    queries = (
        ("problem_attempts",
         "SELECT DISTINCT a.problem_id FROM problem_attempts a "
         "JOIN problems p ON p.problem_id=a.problem_id WHERE p.ingest_batch_id=?",
         (batch_id,)),
        ("problem_progress",
         "SELECT DISTINCT x.problem_id FROM problem_progress x "
         "JOIN problems p ON p.problem_id=x.problem_id WHERE p.ingest_batch_id=?",
         (batch_id,)),
        ("feedback_events",
         "SELECT DISTINCT e.item_type, e.item_id FROM feedback_events e "
         "LEFT JOIN problems p ON e.item_type='problem' AND p.problem_id=e.item_id "
         "LEFT JOIN flash_cards c ON e.item_type='card' AND c.card_id=e.item_id "
         "WHERE p.ingest_batch_id=? OR c.ingest_batch_id=?",
         (batch_id, batch_id)),
        ("review_schedule",
         "SELECT DISTINCT r.item_type, r.item_id FROM review_schedule r "
         "LEFT JOIN problems p ON r.item_type='problem' AND p.problem_id=r.item_id "
         "LEFT JOIN flash_cards c ON r.item_type='card' AND c.card_id=r.item_id "
         "WHERE p.ingest_batch_id=? OR c.ingest_batch_id=?",
         (batch_id, batch_id)),
        ("learning_current_state",
         "SELECT DISTINCT s.item_type, s.item_id FROM learning_current_state s "
         "JOIN problems p ON s.item_type='problem' AND p.problem_id=s.item_id "
         "WHERE p.ingest_batch_id=?",
         (batch_id,)),
        ("learner_signals",
         "SELECT DISTINCT s.target_id FROM learner_signals s "
         "LEFT JOIN problems p ON p.problem_id=s.target_id "
         "LEFT JOIN flash_cards c ON c.card_id=s.target_id "
         "WHERE p.ingest_batch_id=? OR c.ingest_batch_id=?",
         (batch_id, batch_id)),
    )
    blockers = []
    for table, query, params in queries:
        if table == "learning_current_state" and conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone() is None:
            continue
        for row in conn.execute(query, params):
            blockers.append(f"{table}: {':'.join(str(value) for value in row)}")
    return blockers


def _gate_flash_cards(conn, manifest, course=""):
    errors = []
    if not isinstance(manifest, dict) or manifest.get("kind") != FLASH_CARD_KIND:
        return {"ok": False, "errors": ["expected flash-card-patch artifact"],
                "accounting": _accounting(conn)}
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        return {"ok": False, "errors": ["flash-card-patch requires an items list"],
                "accounting": _accounting(conn)}
    prefix = _course_prefix(course, errors)

    known_kps = {row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points")}
    cards_table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='flash_cards'"
    ).fetchone()
    existing_ids = (
        {row[0] for row in conn.execute("SELECT card_id FROM flash_cards")}
        if cards_table else set()
    )
    seen_ids = set()
    for item in items:
        card_id = item.get("card_id") if isinstance(item, dict) else None
        if not card_rules.is_valid_card_id(card_id):
            errors.append(f"{card_id}: id must look like <scope>-fc-NNN")
            continue
        if not card_id.startswith(prefix):
            errors.append(f"{card_id}: id must start with {prefix} (this workspace's course)")
            continue
        if card_id in existing_ids or card_id in seen_ids:
            errors.append(f"{card_id}: card id already exists")
            continue
        seen_ids.add(card_id)
        row = _flash_card_row(item)
        if row is None:
            errors.append(f"{card_id}: item must be an object")
            continue
        if row["kp_id"] not in known_kps:
            errors.append(f"{card_id}: unknown knowledge point {row['kp_id']}")
        for field in ("front", "back"):
            errors.extend(
                f"{card_id}: {field} {reason}"
                for reason in _markup_errors(row[field])
            )
        if "topic_label" in row:
            errors.extend(
                f"{card_id}: topic_label {reason}"
                for reason in _markup_errors(row["topic_label"])
            )
        errors.extend(
            f"{card_id}: {reason}" for reason in card_rules.validate_card_row(row)
        )
    return {"ok": not errors, "errors": errors, "accounting": _accounting(conn)}


def _flash_card_row(item):
    if not isinstance(item, dict):
        return None
    return {
        "card_id": item.get("card_id"),
        "kp_id": item.get("kp_id"),
        "front": item.get("front"),
        "back": item.get("back"),
        "source_evidence": item.get("source_evidence"),
        "directions": item.get("directions", list(card_rules.DEFAULT_DIRECTIONS)),
        **({"topic_label": item["topic_label"]} if "topic_label" in item else {}),
    }


def _provider_payload(provider_name, stdout):
    texts = []
    session_id = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        normalized = conversation_providers.normalize_event(provider_name, event)
        if normalized is None:
            continue
        session_id = normalized.get("provider_session_id") or session_id
        if normalized.get("kind") in ("text", "result"):
            texts.append(normalized.get("text", ""))
    text = "".join(texts).strip()
    try:
        return json.loads(text), session_id
    except json.JSONDecodeError as exc:
        raise ValueError("provider did not return one JSON artifact") from exc


def _gate_data(conn, solutions, audit, content_patch=None, content_audit=None):
    errors = []
    solution_items = _items(solutions, "solutions", errors)
    audit_items = _items(audit, "audit", errors)
    if not _provenance(solutions, solution_items) or not _provenance(audit, audit_items):
        errors.append("solutions and audit require provider session provenance")
    solutions_by_problem = _by_problem(solution_items, "solution", errors)
    audits_by_problem = _by_problem(audit_items, "audit", errors)
    db_rows = dict(conn.execute("SELECT problem_id, problem_text FROM problems"))
    if set(solutions_by_problem) != set(db_rows):
        errors.append("solution coverage does not match active formal pool")
    if set(audits_by_problem) != set(solutions_by_problem):
        errors.append("audit coverage does not match solutions")
    for problem, item in solutions_by_problem.items():
        _plain_fields(item, problem, errors, "solution")
        errors.extend(_inline_problem_difficulty_errors(item, problem))
        if db_rows.get(problem) != item.get("source"):
            errors.append(f"{problem}: artifact source differs from active problem_text")
        errors.extend(f"{problem}: source {reason}" for reason in _markup_errors(item.get("source")))
        errors.extend(f"{problem}: solution {reason}" for reason in _markup_errors(item.get("solution")))
        other = audits_by_problem.get(problem)
        if other is None:
            continue
        if _provider_ref(solutions, item) == _provider_ref(audit, other):
            errors.append(f"{problem}: audit must use a fresh provider session")
        _plain_fields(other, problem, errors, "audit")
        for field in ("source", "problem", "solution"):
            if other.get(field) != item.get(field):
                errors.append(f"{problem}: audit {field} differs from solution artifact")
        decisions = other.get("decisions")
        if not isinstance(decisions, dict):
            errors.append(f"{problem}: audit decisions are missing")
        else:
            for dimension in AUDIT_DIMENSIONS:
                if decisions.get(dimension) != "PASS":
                    errors.append(f"{problem}: audit {dimension} is not PASS")
    current_recovery_pending = _current_recovery_pending(conn, solutions_by_problem)
    if (content_patch is None) != (content_audit is None):
        errors.append("content patch and audit must be supplied together")
    elif content_patch is None and current_recovery_pending:
        errors.append("current formal recovery requires the approved knowledge and mapping patch")
    elif content_patch is not None:
        _gate_content_patch(
            conn, content_patch, content_audit, solutions_by_problem, errors,
        )
        if current_recovery_pending:
            _gate_current_recovery_patch(content_patch, errors)
    return {"ok": not errors, "errors": errors, "accounting": _accounting(conn)}


def _current_recovery_pending(conn, solutions):
    if set(solutions) != _CURRENT_RECOVERY_PROBLEMS:
        return False
    knowledge_points = {
        row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points")
    }
    mappings = {
        problem: json.loads(kp_ids)
        for problem, kp_ids in conn.execute("SELECT problem_id, kp_ids FROM problems")
        if problem in _CURRENT_RECOVERY_MAPPINGS
    }
    return (
        not _CURRENT_RECOVERY_KPS <= knowledge_points
        or mappings != _CURRENT_RECOVERY_MAPPINGS
    )


def _gate_current_recovery_patch(patch, errors):
    knowledge_points = patch.get("knowledge_points")
    mappings = patch.get("mappings")
    if not isinstance(knowledge_points, list) or not isinstance(mappings, list):
        return
    patch_kps = {
        item.get("kp_id") for item in knowledge_points if isinstance(item, dict)
    }
    patch_mappings = {
        item.get("problem"): item.get("kp_ids")
        for item in mappings if isinstance(item, dict)
    }
    if (
        patch_kps != _CURRENT_RECOVERY_KPS
        or patch_mappings != _CURRENT_RECOVERY_MAPPINGS
    ):
        errors.append(
            "current formal recovery patch must contain the approved knowledge points and mappings"
        )


def _gate_content_patch(conn, patch, audit, solutions, errors):
    if patch.get("kind") != "knowledge-mapping-patch":
        errors.append("expected knowledge-mapping-patch artifact")
        return
    if audit.get("kind") != "knowledge-mapping-audit":
        errors.append("expected knowledge-mapping-audit artifact")
        return
    patch_ref = _provider_ref(patch, {})
    audit_ref = _provider_ref(audit, {})
    if not patch_ref or not audit_ref:
        errors.append("content patch and audit require provider session provenance")
    elif patch_ref == audit_ref:
        errors.append("content audit must use a fresh provider session")

    knowledge_points = patch.get("knowledge_points")
    mappings = patch.get("mappings")
    audited_kps = audit.get("knowledge_points")
    audited_mappings = audit.get("mappings")
    if not all(isinstance(items, list) for items in (
            knowledge_points, mappings, audited_kps, audited_mappings)):
        errors.append("content patch and audit require knowledge point and mapping lists")
        return

    existing_kps = {
        row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points")
    }
    proposed_kps = {}
    for item in knowledge_points:
        kp_id = item.get("kp_id") if isinstance(item, dict) else None
        if not kp_id or kp_id in existing_kps or kp_id in proposed_kps:
            errors.append("content patch has invalid or duplicate knowledge point")
            continue
        proposed_kps[kp_id] = item
        if any(field not in item for field in KP_FIELDS):
            errors.append(f"{kp_id}: knowledge point fields are incomplete")
        if item.get("knowledge_type") not in KP_TYPES:
            errors.append(f"{kp_id}: invalid knowledge type")
        if item.get("importance") not in KP_IMPORTANCE:
            errors.append(f"{kp_id}: invalid importance")
        if not isinstance(item.get("knowledge_item"), str) or not item["knowledge_item"].strip():
            errors.append(f"{kp_id}: knowledge item is missing")
        if not isinstance(item.get("body"), str) or not item["body"].strip():
            errors.append(f"{kp_id}: body is missing")
        else:
            errors.extend(f"{kp_id}: body {reason}" for reason in _markup_errors(item["body"]))
        errors.extend(_kp_difficulty_errors(item, kp_id))
        if not isinstance(item.get("related_kp_ids"), list):
            errors.append(f"{kp_id}: related_kp_ids must be a list")

    known_kps = existing_kps | set(proposed_kps)
    for kp_id, item in proposed_kps.items():
        related = item.get("related_kp_ids", [])
        if isinstance(related, list) and (
                len(related) != len(set(related)) or not set(related) <= known_kps):
            errors.append(f"{kp_id}: related knowledge points are invalid")

    audited_kps_by_id = {}
    for item in audited_kps:
        record = item.get("knowledge_point") if isinstance(item, dict) else None
        kp_id = record.get("kp_id") if isinstance(record, dict) else None
        if not kp_id or kp_id in audited_kps_by_id:
            errors.append("content audit has invalid or duplicate knowledge point")
            continue
        audited_kps_by_id[kp_id] = item
    if set(audited_kps_by_id) != set(proposed_kps):
        errors.append("knowledge point audit coverage does not match patch")
    for kp_id, item in proposed_kps.items():
        other = audited_kps_by_id.get(kp_id)
        if not other:
            continue
        if other.get("knowledge_point") != item:
            errors.append(f"{kp_id}: audited knowledge point differs from patch")
        _all_pass(other, KP_AUDIT_DIMENSIONS, kp_id, "knowledge point audit", errors)

    mappings_by_problem = _mapping_items(mappings, "content patch", errors)
    audited_mappings_by_problem = _mapping_items(
        audited_mappings, "content audit", errors,
    )
    if set(audited_mappings_by_problem) != set(mappings_by_problem):
        errors.append("mapping audit coverage does not match patch")
    for problem, item in mappings_by_problem.items():
        kp_ids = item.get("kp_ids")
        if problem not in solutions:
            errors.append(f"{problem}: mapping is not a formal solution")
        if not isinstance(kp_ids, list) or not kp_ids or len(kp_ids) != len(set(kp_ids)):
            errors.append(f"{problem}: mapped knowledge points are invalid")
        elif not set(kp_ids) <= known_kps:
            errors.append(f"{problem}: mapping references an unknown knowledge point")
        other = audited_mappings_by_problem.get(problem)
        solution = solutions.get(problem)
        if not other or not solution:
            continue
        for field in ("problem", "kp_ids"):
            if other.get(field) != item.get(field):
                errors.append(f"{problem}: audited mapping {field} differs from patch")
        for field in ("source", "solution"):
            if other.get(field) != solution.get(field):
                errors.append(f"{problem}: mapping audit {field} differs from solution artifact")
        _all_pass(other, AUDIT_DIMENSIONS, problem, "mapping audit", errors)


def _mapping_items(items, label, errors):
    result = {}
    for item in items:
        problem = item.get("problem") if isinstance(item, dict) else None
        if not problem or problem in result:
            errors.append(f"{label}: invalid or duplicate mapping")
            continue
        result[problem] = item
    return result


def _all_pass(item, dimensions, item_id, label, errors):
    decisions = item.get("decisions")
    if not isinstance(decisions, dict):
        errors.append(f"{item_id}: {label} decisions are missing")
        return
    for dimension in dimensions:
        if decisions.get(dimension) != "PASS":
            errors.append(f"{item_id}: {label} {dimension} is not PASS")


def _items(artifact, expected_kind, errors):
    if not isinstance(artifact, dict) or artifact.get("kind") != expected_kind:
        errors.append(f"expected {expected_kind} artifact")
        return []
    items = artifact.get("items")
    if not isinstance(items, list):
        errors.append(f"{expected_kind} artifact requires items")
        return []
    return items


def _provenance(artifact, items):
    return isinstance(artifact, dict) and all(_provider_ref(artifact, item) for item in items)


def _provider_ref(artifact, item):
    provider = item.get("provider", artifact.get("provider"))
    session = item.get("provider_session_id", artifact.get("provider_session_id"))
    if provider in conversation_providers.SUPPORTED and isinstance(session, str) and session:
        return provider, session
    return None


def _by_problem(items, label, errors):
    result = {}
    for item in items:
        problem = item.get("problem") if isinstance(item, dict) else None
        if not isinstance(problem, str) or not problem or problem in result:
            errors.append(f"{label}: invalid or duplicate problem")
            continue
        result[problem] = item
    return result


def _plain_fields(item, problem, errors, label):
    if not isinstance(item.get("source"), str) or not item["source"]:
        errors.append(f"{problem}: {label} source is missing")
    if not isinstance(item.get("solution"), str) or not item["solution"].strip():
        errors.append(f"{problem}: {label} solution is missing")


def _markup_errors(text):
    if not isinstance(text, str):
        return ["is not text"]
    if "\ufffd" in text:
        return ["has suspicious formula damage"]
    errors = []
    stack = []
    index = 0
    while index < len(text):
        start = text.find("<", index)
        if start < 0:
            break
        match = _TAG.match(text, start)
        if match is None:
            tail = text[start:]
            complete_tag = re.match(r"</?[A-Za-z][A-Za-z0-9]*(?:\s+[^<>]*)?\s*/?>", tail)
            unterminated_tag = (
                (start == 0 or text[start - 1].isspace())
                and re.match(r"</?[A-Za-z][A-Za-z0-9]*(?:\s+[^<>]*)?\s*$", tail)
            )
            if complete_tag or unterminated_tag:
                errors.append("has unknown or unterminated HTML")
            index = start + 1
            continue
        tag = match.group(1)
        closing = text.startswith("</", start)
        if closing:
            if not stack or stack[-1][0] != tag:
                errors.append("has unbalanced sup/sub")
            else:
                _, content_start, opening_start = stack.pop()
                content = text[content_start:start]
                if not content.strip():
                    errors.append("has empty sup/sub")
                left = _word_left(text, opening_start)
                right = _word_right(text, match.end())
                if left and right and (len(left) + len(right) > 2 or (left.islower() and right.islower())):
                    errors.append("sup/sub splits an ordinary word")
        else:
            stack.append((tag, match.end(), start))
        index = match.end()
    if stack:
        errors.append("has unbalanced sup/sub")
    return errors


def _word_left(text, index):
    match = re.search(r"[A-Za-z]+$", text[:index])
    return match.group(0) if match else ""


def _word_right(text, index):
    match = re.match(r"[A-Za-z]+", text[index:])
    return match.group(0) if match else ""


def _accounting(conn):
    return {
        "knowledge_points": conn.execute("SELECT COUNT(*) FROM knowledge_points").fetchone()[0],
        "problems": conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0],
        "knowledge_relations": conn.execute("SELECT COUNT(*) FROM knowledge_relations").fetchone()[0],
    }


def _backup_database(database, backup):
    source = sqlite3.connect(database)
    target = sqlite3.connect(backup)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
