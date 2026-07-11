"""Validation and serialization contract for Problem Candidates."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


CANDIDATE_ID_PATTERN = re.compile(r"^[a-z0-9]+-ch\d{2}-cand-\d{3}$")
KP_ID_PATTERN = re.compile(r"^[a-z0-9]+-ch\d{2}-kp-\d{3}$")
COLLAPSED_SUBPART_PATTERN = re.compile(r"[^\n][ \t]+[a-j]\s*\)[ \t]+")

PROBLEM_TYPES = {
    "calculation",
    "proof",
    "modeling",
    "explanation",
    "experiment",
    "design",
    "application",
    "counterexample",
    "other",
}
SOURCE_KINDS = {"textbook", "quiz", "midterm", "final", "makeup", "other"}
INTERACTION_TYPES = {"single_choice", "true_false", "free_response"}
GENERATION_PURPOSES = {"first_pass_check", "remediation"}
ORIGIN_KINDS = {"source_problem", "adapted_problem", "generated_grounded"}
SIGNAL_TYPES = {
    "weak_node",
    "confusion",
    "missing_prerequisite",
    "transfer_failure",
    "relation_gap",
}


def expected_prefix(course: str, chapter: str) -> str:
    chapter = chapter if chapter.startswith("ch") else f"ch{chapter}"
    return f"{course}-{chapter}-cand-"


def validate_text_block(
    candidate_id: str,
    field: str,
    value: Any,
    errors: List[str],
    required: bool = True,
) -> bool:
    if value is None and not required:
        return True
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{candidate_id}: {field} must be a non-empty string")
        return False
    if COLLAPSED_SUBPART_PATTERN.search(value):
        errors.append(
            f"{candidate_id}: {field} has collapsed subparts; use blank-line-separated paragraphs"
        )
        return False
    return True


def validate_evidence(candidate_id: str, evidence: Any, errors: List[str]) -> bool:
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{candidate_id}: source_evidence must be a non-empty list")
        return False
    ok = True
    for index, item in enumerate(evidence, start=1):
        if not isinstance(item, dict):
            errors.append(f"{candidate_id}: source_evidence #{index} must be an object")
            ok = False
            continue
        for field in ("source", "location"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(
                    f"{candidate_id}: source_evidence #{index} requires non-empty {field}"
                )
                ok = False
    return ok


def validate_error_lure(
    candidate_id: str,
    option_id: str,
    lure: Any,
    kp_ids: Set[str],
    relation_ids: Set[str],
    errors: List[str],
) -> bool:
    if not isinstance(lure, dict):
        errors.append(f"{candidate_id}: option {option_id} error_lure must be an object")
        return False
    ok = True
    signal_type = lure.get("signal_type")
    target_type = lure.get("target_type")
    target_id = lure.get("target_id")
    if signal_type not in SIGNAL_TYPES:
        errors.append(f"{candidate_id}: option {option_id} error_lure has invalid signal_type")
        ok = False
    if target_type not in {"node", "relation"}:
        errors.append(f"{candidate_id}: option {option_id} error_lure has invalid target_type")
        ok = False
    elif target_type == "node" and target_id not in kp_ids:
        errors.append(f"{candidate_id}: option {option_id} error_lure targets unknown kp_id")
        ok = False
    elif target_type == "relation" and target_id not in relation_ids:
        errors.append(f"{candidate_id}: option {option_id} error_lure targets unknown relation_id")
        ok = False
    return ok


def validate_options(
    candidate_id: str,
    interaction_type: str,
    generation_purpose: str,
    options: Any,
    correct_option_id: Any,
    kp_ids: Set[str],
    relation_ids: Set[str],
    errors: List[str],
) -> bool:
    if interaction_type == "free_response":
        if options not in (None, []):
            errors.append(f"{candidate_id}: free_response options must be null or empty")
            return False
        if correct_option_id not in (None, ""):
            errors.append(f"{candidate_id}: free_response correct_option_id must be null")
            return False
        return True

    if not isinstance(options, list) or len(options) < 2:
        errors.append(f"{candidate_id}: choice interactions require at least two options")
        return False
    if interaction_type == "true_false" and len(options) != 2:
        errors.append(f"{candidate_id}: true_false requires exactly two options")
        return False

    ok = True
    ids: List[str] = []
    for index, option in enumerate(options, start=1):
        if not isinstance(option, dict):
            errors.append(f"{candidate_id}: option #{index} must be an object")
            ok = False
            continue
        option_id = str(option.get("id", "")).strip()
        if not option_id or option_id in ids:
            errors.append(f"{candidate_id}: option #{index} has missing or duplicate id")
            ok = False
        ids.append(option_id)
        for field in ("text", "explanation"):
            if not isinstance(option.get(field), str) or not option[field].strip():
                errors.append(f"{candidate_id}: option {option_id or index} requires {field}")
                ok = False
        if option_id != correct_option_id:
            lure = option.get("error_lure")
            if generation_purpose == "remediation" and lure is None:
                errors.append(
                    f"{candidate_id}: remediation wrong option {option_id or index} requires error_lure"
                )
                ok = False
            elif lure is not None and not validate_error_lure(
                candidate_id,
                option_id,
                lure,
                kp_ids,
                relation_ids,
                errors,
            ):
                ok = False

    if not isinstance(correct_option_id, str) or correct_option_id not in ids:
        errors.append(f"{candidate_id}: correct_option_id must match one option id")
        ok = False
    return ok


def validate_candidate(
    candidate: Mapping[str, Any],
    course: str,
    chapter: str,
    existing_kp_ids: Set[str],
    relation_ids: Set[str] | None = None,
) -> Tuple[bool, Dict[str, Any], List[str]]:
    errors: List[str] = []
    relation_ids = relation_ids or set()
    candidate_id = str(candidate.get("candidate_id", "")).strip()
    if not CANDIDATE_ID_PATTERN.match(candidate_id) or not candidate_id.startswith(
        expected_prefix(course, chapter)
    ):
        errors.append(
            f"{candidate_id or '<missing>'}: invalid candidate_id; expected "
            f"{expected_prefix(course, chapter)}NNN"
        )

    raw_kp_ids = candidate.get("kp_ids")
    kp_ids = raw_kp_ids if isinstance(raw_kp_ids, list) else []
    if not kp_ids:
        errors.append(f"{candidate_id}: kp_ids must be a non-empty list")
    for kp_id in kp_ids:
        if not isinstance(kp_id, str) or not KP_ID_PATTERN.match(kp_id):
            errors.append(f"{candidate_id}: invalid kp_id '{kp_id}'")
        elif kp_id not in existing_kp_ids:
            errors.append(f"{candidate_id}: unknown kp_id '{kp_id}'")

    validate_text_block(candidate_id, "problem_text", candidate.get("problem_text"), errors)
    validate_text_block(candidate_id, "solution", candidate.get("solution"), errors)

    enum_fields = (
        ("problem_type", PROBLEM_TYPES),
        ("source_kind", SOURCE_KINDS),
        ("interaction_type", INTERACTION_TYPES),
        ("generation_purpose", GENERATION_PURPOSES),
        ("origin_kind", ORIGIN_KINDS),
    )
    for field, allowed in enum_fields:
        if candidate.get(field) not in allowed:
            errors.append(f"{candidate_id}: invalid {field} '{candidate.get(field)}'")

    evidence = candidate.get("source_evidence")
    validate_evidence(candidate_id, evidence, errors)
    validate_options(
        candidate_id,
        str(candidate.get("interaction_type", "")),
        str(candidate.get("generation_purpose", "")),
        candidate.get("options"),
        candidate.get("correct_option_id"),
        set(kp_ids) & existing_kp_ids,
        relation_ids,
        errors,
    )

    cleaned = {
        "candidate_id": candidate_id,
        "kp_ids": json.dumps(kp_ids, ensure_ascii=False),
        "problem_text": candidate.get("problem_text"),
        "options_json": (
            json.dumps(candidate.get("options"), ensure_ascii=False)
            if candidate.get("options") not in (None, [])
            else None
        ),
        "correct_option_id": candidate.get("correct_option_id") or None,
        "solution": candidate.get("solution"),
        "problem_type": candidate.get("problem_type"),
        "interaction_type": candidate.get("interaction_type"),
        "generation_purpose": candidate.get("generation_purpose"),
        "origin_kind": candidate.get("origin_kind"),
        "source_kind": candidate.get("source_kind"),
        "source_evidence_json": json.dumps(evidence, ensure_ascii=False),
    }
    return not errors, cleaned, errors


def row_to_candidate(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "candidate_id": row["candidate_id"],
        "kp_ids": json.loads(row["kp_ids"]),
        "problem_text": row["problem_text"],
        "options": json.loads(row["options_json"]) if row["options_json"] else None,
        "correct_option_id": row["correct_option_id"],
        "solution": row["solution"],
        "problem_type": row["problem_type"],
        "interaction_type": row["interaction_type"],
        "generation_purpose": row["generation_purpose"],
        "origin_kind": row["origin_kind"],
        "source_kind": row["source_kind"],
        "source_evidence": json.loads(row["source_evidence_json"]),
    }


def fetch_relation_ids(conn: Any) -> Set[str]:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'knowledge_relations'"
    ).fetchone()
    if row is None:
        return set()
    return {str(item[0]) for item in conn.execute("SELECT relation_id FROM knowledge_relations")}
