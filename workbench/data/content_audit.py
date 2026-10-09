"""Read-only hygiene checks for a course content pool."""

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from workbench.domain.content_identity import problem_identity


CHECKS = (
    "duplicates", "fragments", "unmarked-objective", "untitled", "figures",
    "orphan-figures",
)
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_CHAPTER_ID = re.compile(r"-(?:prob|mq)-(\d+)$")
_CONTINUATION = re.compile(
    r"^(?:where|then|for example|given that|such that|and thus|and|or)(?:\b|\s)"
)
_OPTION_ONLY = re.compile(
    r"^\s*(?:(?:option\s*)?[A-H](?:\s*[.)、．:：])?|选项\s*[A-H])\s*$",
    re.IGNORECASE,
)
_QUESTION_MARKERS = re.compile(
    r"[?？]|\b(?:find|solve|compute|calculate|prove|show|which|what|how)\b|"
    r"(?:求|计算|证明|说明|判断|选择|为何|为什么|如何|多少|哪个|哪些)"
)


def audit(pool, checks=None):
    """Return findings without writing pool rows, files, or batch records."""
    selected = tuple(checks or CHECKS)
    unknown = sorted(set(selected) - set(CHECKS))
    if unknown:
        raise ValueError(f"unknown content audit check(s): {', '.join(unknown)}")
    problems = pool.problems_all()
    kps = pool.kps()
    findings = []
    if "duplicates" in selected:
        findings.extend(_duplicate_findings(problems, pool.course))
    if "fragments" in selected:
        findings.extend(_fragment_findings(problems, pool.course))
    if "unmarked-objective" in selected:
        findings.extend(_unmarked_findings(problems))
    if "untitled" in selected:
        findings.extend(_untitled_findings(problems))
    if "figures" in selected:
        findings.extend(_figure_findings(pool, problems))
    if "orphan-figures" in selected:
        findings.extend(_orphan_figure_findings(pool, problems, kps))
    return {"ok": not findings, "checks": list(selected), "findings": findings}


def _duplicate_findings(problems, course):
    groups = {}
    for problem in problems:
        identity = problem_identity(problem.get("problem_text"))
        if identity:
            groups.setdefault(identity, []).append(problem)
    findings = []
    for identity, members in groups.items():
        if len(members) < 2:
            continue
        chapters = {_chapter_id(item.get("problem_id"), course) for item in members}
        chapter = next(iter(chapters)) if len(chapters) == 1 else None
        findings.append({
            "check": "duplicates", "chapter": chapter,
            "problem_ids": sorted(item["problem_id"] for item in members),
            "detail": f"same normalized problem text: {identity}",
        })
    return sorted(findings, key=lambda item: tuple(item["problem_ids"]))


def _fragment_findings(problems, course):
    by_chapter = {}
    for problem in problems:
        chapter = _chapter_id(problem.get("problem_id"), course)
        identity = problem_identity(problem.get("problem_text"))
        if chapter and identity:
            by_chapter.setdefault(chapter, []).append((problem, identity))
    findings = []
    for chapter, items in by_chapter.items():
        for problem, identity in items:
            raw = problem.get("problem_text") or ""
            reasons = []
            if _CONTINUATION.match(identity):
                reasons.append("starts with a continuation token")
            if _OPTION_ONLY.fullmatch(raw):
                reasons.append("contains only an option label")
            images = list(_IMAGE.finditer(raw))
            if images and not _QUESTION_MARKERS.search(raw):
                remainder = _IMAGE.sub(" ", raw).strip(" \t\r\n .。,:：;；")
                if not remainder or len(problem_identity(remainder) or "") <= 12:
                    reasons.append("contains a lone image reference without a question")
            partner = next((
                other for other, other_identity in items
                if other["problem_id"] != problem["problem_id"]
                and len(identity) >= 8 and len(other_identity) > len(identity)
                and (other_identity.startswith(identity) or other_identity.endswith(identity))
                and not _is_standalone_item(problem, other)
            ), None)
            if partner:
                reasons.append(f"stem is a prefix/suffix of {partner['problem_id']}")
            if reasons:
                findings.append({
                    "check": "fragments", "chapter": chapter,
                    "problem_ids": [problem["problem_id"]],
                    "detail": "; ".join(reasons),
                })
    return sorted(findings, key=lambda item: item["problem_ids"][0])


def _text(value):
    return value.strip() if isinstance(value, str) else ""


def _is_standalone_item(problem, partner):
    """Return ``True`` when ``problem`` is a question in its own right.

    A stem that is literally contained in another stem of the same chapter
    only proves that one wording is a substring of the other.  It says nothing
    about ownership: the same question is routinely written both as a terse
    keyword phrase and with a lead-in verb, and the two rows then come from
    different source documents.  Literal containment must not be read as "this
    row is a piece cut out of that row".

    A row that carries its own non-empty ``solution`` **and** cites a
    ``source_evidence`` that differs from the longer row's is sourced from a
    different document, so it is an independent question rather than a
    fragment.  A genuine fragment has no answer of its own, or shares its
    host's source anchor -- both cases keep the finding.
    """
    has_own_answer = bool(_text(problem.get("solution")))
    own_source = _text(problem.get("source_evidence"))
    partner_source = _text(partner.get("source_evidence"))
    return has_own_answer and bool(own_source) and own_source != partner_source


def _unmarked_findings(problems):
    findings = []
    for problem in problems:
        payload = _json_value(problem.get("micro_quiz"))
        quiz_type = payload.get("quiz_type") if isinstance(payload, dict) else None
        objective = quiz_type in {"yes_no", "single_choice", "multiple_choice"}
        objective = objective or "-mq-" in (problem.get("problem_id") or "")
        modes = _json_value(problem.get("practice_modes"))
        if objective and (not isinstance(modes, list) or not modes):
            findings.append({
                "check": "unmarked-objective",
                "chapter": None,
                "problem_ids": [problem["problem_id"]],
                "detail": "objective item has no practice_modes marking",
            })
    return findings


def _untitled_findings(problems):
    return [{
        "check": "untitled", "chapter": None,
        "problem_ids": [problem["problem_id"]],
        "detail": "display_title is missing or blank",
    } for problem in problems
        if not isinstance(problem.get("display_title"), str)
        or not problem["display_title"].strip()]


def _figure_findings(pool, problems):
    findings = []
    root = (pool.root / ".lessonkit" / "figures").resolve()
    for problem in problems:
        problem_id = problem.get("problem_id")
        chapter = _chapter_id(problem_id, pool.course)
        refs = [(match.group(2), "Markdown image") for match in
                _IMAGE.finditer(problem.get("problem_text") or "")]
        refs.extend((path, "figure_paths") for path in
                    _json_list(problem.get("figure_paths")))
        for ref, source in refs:
            path = _resolve_figure_ref(root, pool.course, chapter, ref)
            if path is None or not path.is_file():
                findings.append({
                    "check": "figures", "chapter": chapter,
                    "problem_ids": [problem_id],
                    "detail": f"{source} reference does not resolve: {ref}",
                })
    return findings


def _orphan_figure_findings(pool, problems, kps):
    root = (pool.root / ".lessonkit" / "figures").resolve()
    course_root = (root / pool.course).resolve()
    if not course_root.is_relative_to(root) or not course_root.is_dir():
        return []
    referenced = set()
    for row in [*problems, *kps]:
        referenced.update(_json_list(row.get("figure_paths")))
        for match in _IMAGE.finditer(row.get("problem_text") or row.get("body") or ""):
            ref = match.group(2)
            path = _resolve_figure_ref(root, pool.course, None, ref)
            if path:
                referenced.add(path.relative_to(root).as_posix())
    findings = []
    for path in sorted(course_root.rglob("*")):
        if not path.is_file():
            continue
        logical = path.relative_to(root).as_posix()
        if logical not in referenced:
            findings.append({
                "check": "orphan-figures", "chapter": path.parent.name,
                "problem_ids": [], "detail": f"unreferenced figure file: {logical}",
            })
    return findings


def _resolve_figure_ref(root, course, chapter, ref):
    if not isinstance(ref, str) or not ref.strip():
        return None
    parsed = urlsplit(ref.strip())
    if parsed.scheme or parsed.netloc:
        return None
    target = Path(unquote(parsed.path))
    if target.is_absolute():
        candidate = target.resolve()
        return candidate if candidate.is_relative_to(root) else None
    candidates = [root / target]
    if len(target.parts) == 1 and chapter:
        candidates.append(root / course / chapter / target)
    safe = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_relative_to(root):
            safe.append(resolved)
            if resolved.is_file():
                return resolved
    return safe[-1] if safe else None


def _chapter_id(problem_id, course):
    if not isinstance(problem_id, str) or not problem_id.startswith(f"{course}-"):
        return None
    match = _CHAPTER_ID.search(problem_id)
    if not match:
        return None
    return problem_id[len(course) + 1:match.start()]


def _json_value(value):
    if isinstance(value, str) and value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _json_list(value):
    decoded = _json_value(value)
    return decoded if isinstance(decoded, list) else []
