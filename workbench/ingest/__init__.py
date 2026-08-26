"""Resumable UTF-8 ingestion artifacts and formal-problem gates."""

import html
import json
import re
import sqlite3
import subprocess
from pathlib import Path

from workbench.bridge import conversation_providers


AUDIT_DIMENSIONS = (
    "source_consistency", "meaning", "formatting", "knowledge_point_mapping",
    "answer_correctness", "solution_completeness",
)
RECIPE_NAMES = {"knowledge", "problems", "candidates", "views"}
_TAG = re.compile(r"</?(sup|sub)>")


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


def gate(db_path, solutions_path, audit_path, output_path):
    """Validate artifact provenance, source identity, and deterministic content gates."""
    solutions = read_artifact(solutions_path)
    audit = read_artifact(audit_path)
    conn = sqlite3.connect(db_path)
    try:
        report = _gate_data(conn, solutions, audit)
    finally:
        conn.close()
    report.update({"kind": "gate-report", "solutions": solutions, "audit": audit})
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
    """Write an official recipe record; only the problems recipe can explicitly apply."""
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
        if name != "problems":
            raise ValueError("only the problems recipe has an apply stage")
        applied = apply(database, input_path, backup_path)
        result.update(applied)
    write_artifact(Path(output_dir) / "recipe.json", result)
    return result


def apply(db_path, gate_path, backup_path=None):
    """Revalidate and update every formal problem while holding one write lock."""
    report = read_artifact(gate_path)
    if report.get("kind") != "gate-report":
        raise ValueError("apply requires a gate-report artifact")
    solutions = report.get("solutions")
    audit = report.get("audit")
    database = Path(db_path)
    backup = Path(backup_path) if backup_path else database.with_name(database.name + ".ingest-backup")
    if backup.exists():
        raise FileExistsError(f"recoverable copy already exists: {backup}")
    conn = sqlite3.connect(database)
    try:
        conn.execute("BEGIN IMMEDIATE")
        verified = _gate_data(conn, solutions, audit)
        if not verified["ok"]:
            raise ValueError("; ".join(verified["errors"]))
        _backup_database(database, backup)
        for item in solutions["items"]:
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


def _gate_data(conn, solutions, audit):
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
    return {"ok": not errors, "errors": errors, "accounting": _accounting(conn)}


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
            if re.match(r"</?[A-Za-z]", tail):
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
