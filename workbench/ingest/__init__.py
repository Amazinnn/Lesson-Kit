"""Resumable UTF-8 ingestion artifacts and formal-problem gates."""

import html
import json
import re
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
    "related_kp_ids", "importance", "learning_action", "body", "difficulty",
    "fragile", "graph_label",
)
KP_TYPES = {
    "concept-property", "method-modeling", "formula-calculation",
    "algorithm-process", "code-implementation", "system-timing",
    "lab-implementation", "memory-recall",
}
KP_IMPORTANCE = {"core", "supplementary", "optional"}
RECIPE_NAMES = {"knowledge", "problems", "candidates", "views", "micro-quiz",
                "flash-card"}
MICRO_QUIZ_KIND = "micro-quiz-patch"
MICRO_QUIZ_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-mq-\d{3}$")
FLASH_CARD_KIND = "flash-card-patch"
FLASH_CARD_ID = re.compile(r"^[a-z0-9-]+-fc-\d{3}$")
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
    """Run one PATH-native Codex or Claude session, without registry fallback."""
    if provider_name not in ("codex", "claude"):
        raise ValueError("provider must be explicitly codex or claude")
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
        elif name == "problems":
            applied = apply(database, input_path, backup_path)
            result.update(applied)
        else:
            raise ValueError("only the problems, micro-quiz, and flash-card recipes have an apply stage")
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
        _backup_database(database, backup)
        if content_patch:
            for item in content_patch["knowledge_points"]:
                values = [
                    json.dumps(item[field], ensure_ascii=False)
                    if field == "related_kp_ids" else item[field]
                    for field in KP_FIELDS
                ]
                conn.execute(
                    f"INSERT INTO knowledge_points ({', '.join(KP_FIELDS)}) "
                    f"VALUES ({', '.join('?' for _ in KP_FIELDS)})",
                    values,
                )
        mappings = {
            item["problem"]: json.dumps(item["kp_ids"], ensure_ascii=False)
            for item in (content_patch or {}).get("mappings", [])
        }
        for item in solutions["items"]:
            if item["problem"] in mappings:
                cursor = conn.execute(
                    "UPDATE problems SET solution=?, kp_ids=? WHERE problem_id=?",
                    (item["solution"], mappings[item["problem"]], item["problem"]),
                )
            else:
                cursor = conn.execute(
                    "UPDATE problems SET solution=? WHERE problem_id=?",
                    (item["solution"], item["problem"]),
                )
            if cursor.rowcount != 1:
                raise ValueError(f"missing formal problem: {item['problem']}")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"ok": True, "applied": True, "backup_path": str(backup), "accounting": verified["accounting"]}


def apply_micro_quiz(db_path, manifest_path, backup_path=None):
    """Revalidate and insert micro quizzes while holding one write lock."""
    manifest = read_artifact(manifest_path)
    database = Path(db_path)
    backup = Path(backup_path) if backup_path else database.with_name(database.name + ".ingest-backup")
    if backup.exists():
        raise FileExistsError(f"recoverable copy already exists: {backup}")
    conn = sqlite3.connect(database)
    try:
        conn.execute("BEGIN IMMEDIATE")
        verified = _gate_micro_quiz(conn, manifest)
        if not verified["ok"]:
            raise ValueError("; ".join(verified["errors"]))
        _backup_database(database, backup)
        for item in manifest["items"]:
            row = _micro_quiz_row(item)
            conn.execute(
                "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
                " problem_type, source_kind, practice_modes, micro_quiz)"
                " VALUES (?, ?, ?, NULL, ?, ?, ?, ?)",
                (
                    row["problem_id"],
                    json.dumps(row["kp_ids"], ensure_ascii=False),
                    row["problem_text"],
                    row["problem_type"],
                    row["source_kind"],
                    json.dumps(row["practice_modes"], ensure_ascii=False),
                    json.dumps(row["micro_quiz"], ensure_ascii=False),
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"ok": True, "applied": True, "backup_path": str(backup),
            "accounting": verified["accounting"]}


def _gate_micro_quiz(conn, manifest):
    errors = []
    if not isinstance(manifest, dict) or manifest.get("kind") != MICRO_QUIZ_KIND:
        return {"ok": False, "errors": ["expected micro-quiz-patch artifact"],
                "accounting": _accounting(conn)}
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        return {"ok": False, "errors": ["micro-quiz-patch requires an items list"],
                "accounting": _accounting(conn)}

    known_kps = {row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points")}
    existing_ids = {row[0] for row in conn.execute("SELECT problem_id FROM problems")}
    seen_ids = set()
    for item in items:
        problem_id = item.get("problem_id") if isinstance(item, dict) else None
        if not isinstance(problem_id, str) or not MICRO_QUIZ_ID.match(problem_id):
            errors.append(f"{problem_id}: id must look like <course>-<chapter>-mq-NNN")
            continue
        if problem_id in existing_ids or problem_id in seen_ids:
            errors.append(f"{problem_id}: problem id already exists")
            continue
        seen_ids.add(problem_id)
        row = _micro_quiz_row(item)
        if row is None:
            errors.append(f"{problem_id}: item must be an object")
            continue
        if row["kp_ids"][0] not in known_kps:
            errors.append(f"{problem_id}: unknown knowledge point {row['kp_ids'][0]}")
        errors.extend(f"{problem_id}: {reason}" for reason in _markup_errors(row["problem_text"]))
        errors.extend(
            f"{problem_id}: {reason}" for reason in micro_quiz_rules.validate_problem_row(row)
        )
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
        "source_kind": item.get("source_kind") or "quiz",
        "practice_modes": item.get("practice_modes")
        or micro_quiz_rules.practice_modes_for(payload.get("quiz_type")),
        "micro_quiz": payload,
    }


def apply_flash_cards(db_path, manifest_path, backup_path=None):
    """Revalidate and insert flash cards while holding one write lock."""
    manifest = read_artifact(manifest_path)
    database = Path(db_path)
    backup = Path(backup_path) if backup_path else database.with_name(database.name + ".ingest-backup")
    if backup.exists():
        raise FileExistsError(f"recoverable copy already exists: {backup}")
    conn = sqlite3.connect(database)
    try:
        conn.execute("BEGIN IMMEDIATE")
        verified = _gate_flash_cards(conn, manifest)
        if not verified["ok"]:
            raise ValueError("; ".join(verified["errors"]))
        _backup_database(database, backup)
        for item in manifest["items"]:
            row = _flash_card_row(item)
            conn.execute(
                "INSERT INTO flash_cards (card_id, kp_id, front, back, source_evidence)"
                " VALUES (?, ?, ?, ?, ?)",
                (row["card_id"], row["kp_id"], row["front"], row["back"],
                 row["source_evidence"]),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"ok": True, "applied": True, "backup_path": str(backup),
            "accounting": verified["accounting"]}


def _gate_flash_cards(conn, manifest):
    errors = []
    if not isinstance(manifest, dict) or manifest.get("kind") != FLASH_CARD_KIND:
        return {"ok": False, "errors": ["expected flash-card-patch artifact"],
                "accounting": _accounting(conn)}
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        return {"ok": False, "errors": ["flash-card-patch requires an items list"],
                "accounting": _accounting(conn)}

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
        if not isinstance(item.get("difficulty"), int) or not 1 <= item["difficulty"] <= 5:
            errors.append(f"{kp_id}: invalid difficulty")
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
    if provider in ("codex", "claude") and isinstance(session, str) and session:
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
        "candidate_problems": conn.execute("SELECT COUNT(*) FROM candidate_problems").fetchone()[0],
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
