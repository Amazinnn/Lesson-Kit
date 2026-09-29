"""Parse and validate structured actions emitted in conversation replies."""

import json
import re

from workbench import ingest


_GOAL_KINDS = {"stage", "long_term"}
_ACTION_BLOCK_RE = re.compile(r"```lessonkit-action\s*([\s\S]*?)```", re.IGNORECASE)
CONTENT_ACTION_TYPES = ("check_ingest", "content-bundle")
FLASH_CARD_KIND = "flash-card-patch"
MICRO_QUIZ_KIND = "micro-quiz-patch"
CONTENT_BUNDLE_KIND = "content-bundle"
PROBLEM_PATCH_KIND = "problem-patch"
_MANIFEST_KINDS = {FLASH_CARD_KIND, MICRO_QUIZ_KIND, CONTENT_BUNDLE_KIND,
                   PROBLEM_PATCH_KIND}
_CONTENT_LISTS = ("knowledge_points", "problems", "flash_cards")


def extract_action(answer, context, folder=None):
    """Return visible text, content actions, and an intent-gated notice."""
    blocks = list(_ACTION_BLOCK_RE.finditer(answer))
    if not blocks:
        return answer, [], None
    content = []
    notice = None
    invalid_json = False
    matched_intent = False
    recognized = False
    for match in blocks:
        try:
            raw = json.loads(match.group(1).strip())
        except (TypeError, ValueError):
            invalid_json = True
            continue
        if not isinstance(raw, dict):
            continue
        action = None
        raw_type = raw.get("type")
        if raw_type in ("replace_practice_selection", "prefill_goal_form"):
            recognized = True
            if notice is not None:
                continue
            if raw_type == "replace_practice_selection" and context.get("practice_intent"):
                matched_intent = True
                allowed = set(context.get("knowledge_point_ids") or [])
                ids = []
                for item in raw.get("kp_ids") or []:
                    if item in allowed and item not in ids:
                        ids.append(item)
                if ids:
                    notice = {"type": raw_type, "kp_ids": ids}
            elif raw_type == "prefill_goal_form" and context.get("goal_intent"):
                matched_intent = True
                notice = _clean_goal_form_action(raw)
        elif _looks_like_content_block(raw):
            action = _clean_content_action(raw, folder)
            if action is not None:
                content.append(action)
    cleaned = _ACTION_BLOCK_RE.sub("", answer).strip()
    if content or notice is not None:
        return cleaned, content, notice
    if invalid_json:
        return cleaned, [], {"type": "check_ingest", "error": "action block is not valid JSON"}
    if matched_intent:
        return cleaned, [], None
    if recognized:
        return cleaned, [], {"ignored": "no block matched the active intent"}
    if blocks:
        return cleaned, [], {
            "type": "check_ingest",
            "error": "回复包含 lessonkit-action 区块，但没有区块符合已知动作契约，未写入任何内容",
        }
    return answer, [], None


def _looks_like_content_block(raw):
    """Accept the supported content wrappers and bare manifest shapes."""
    if raw.get("type") in CONTENT_ACTION_TYPES:
        return True
    if raw.get("type") is not None:
        return False
    if raw.get("kind") in _MANIFEST_KINDS:
        return True
    return any(isinstance(raw.get(field), list) for field in _CONTENT_LISTS)


def _clean_content_action(raw, folder=None):
    action = {"type": "check_ingest"}
    reference = raw.get("staged_manifest") or raw.get("manifest_path")
    manifest = raw.get("manifest") if raw.get("type") == "check_ingest" else raw
    if reference is not None:
        action["staged_manifest"] = str(reference)
        if folder is None:
            action["error"] = "staged manifest needs a conversation folder to read from"
            return action
        try:
            manifest = ingest.read_staged_manifest(folder, reference)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            action["error"] = str(exc)
            return action
    normalized = _implied_manifest_kind(manifest)
    error = _manifest_contract_error(normalized)
    if error:
        action["error"] = error
        return action
    action["manifest"] = normalized
    return action


def _implied_manifest_kind(manifest):
    """Resolve the accepted kind/type/nested/list-only bundle spellings."""
    if not isinstance(manifest, dict):
        return manifest
    nested = manifest.get("manifest")
    if isinstance(nested, dict) and not any(
            isinstance(manifest.get(field), list) for field in _CONTENT_LISTS):
        return _implied_manifest_kind(nested)
    if manifest.get("kind"):
        return manifest
    if manifest.get("type") in _MANIFEST_KINDS:
        return {**manifest, "kind": manifest["type"]}
    if any(isinstance(manifest.get(field), list) for field in _CONTENT_LISTS):
        return {**manifest, "kind": CONTENT_BUNDLE_KIND}
    return manifest


def _manifest_contract_error(manifest):
    if not isinstance(manifest, dict):
        return "manifest must be an object"
    kind = manifest.get("kind")
    if kind in {FLASH_CARD_KIND, MICRO_QUIZ_KIND, PROBLEM_PATCH_KIND}:
        if not isinstance(manifest.get("items"), list) or not manifest["items"]:
            return "manifest items must be a non-empty list"
        return ""
    if kind == CONTENT_BUNDLE_KIND:
        for field in _CONTENT_LISTS:
            value = manifest.get(field)
            if isinstance(value, list) and value:
                return ""
        return ("content-bundle requires at least one knowledge point, "
                "problem, or flash card")
    return (f"manifest kind must be {FLASH_CARD_KIND}, {MICRO_QUIZ_KIND}, "
            f"{PROBLEM_PATCH_KIND}, or {CONTENT_BUNDLE_KIND} — a "
            f"{CONTENT_BUNDLE_KIND} carries " + " / ".join(_CONTENT_LISTS))


def clean_check_ingest_action(manifest):
    error = _manifest_contract_error(manifest)
    if error:
        return {"type": "check_ingest", "error": error}
    return {"type": "check_ingest", "manifest": manifest}


def _clean_goal_form_action(raw):
    title = str(raw.get("title") or "").strip()[:120]
    if not title:
        return None
    kind = raw.get("kind") if raw.get("kind") in _GOAL_KINDS else "stage"
    start_date = str(raw.get("start_date") or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", start_date):
        start_date = ""
    deadline = str(raw.get("deadline") or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", deadline):
        deadline = ""
    description = str(raw.get("description") or "").strip()[:500]
    return {
        "type": "prefill_goal_form",
        "title": title,
        "kind": kind,
        "start_date": start_date,
        "deadline": deadline,
        "description": description,
    }
