"""Read-only filter facets: the dimensions a learner can slice the pool by.

Every value is derived from the pool's actual rows, so a filter never offers a
choice that would select nothing. The document dimension folds the free-text
``source_evidence`` into one key per source document — the only place that
carries document-level identity (several papers can share a year and a kind).
"""

import re


_MD_PATH = re.compile(r"^(.*\.[A-Za-z0-9]+)")
_TEXTBOOK = re.compile(r"^教材")
# "题库/final·xxx.md 第12题" / "题库/期末/xxx.md#L29｜题号 fin-p01-s1-q2"
_TAIL = re.compile(r"\s*(第[0-9一二三四五六七八九十百]+题|#L[0-9]+.*|#L[0-9]+.*)?$")


def document_key(source_evidence):
    """The source document one evidence string belongs to, or "" when unknown.

    A `.md`-style path wins verbatim (it is what both real pools write); a
    textbook row folds into the single key 教材 because each exercise carries
    its own per-problem string and no document identity beyond that.
    """
    if not isinstance(source_evidence, str) or not source_evidence.strip():
        return ""
    value = _TAIL.sub("", source_evidence.strip())
    if not value:
        value = source_evidence.strip()
    match = _MD_PATH.match(value)
    if match:
        return match.group(1)
    if _TEXTBOOK.match(value):
        return "教材"
    return value.split("#")[0].split("｜")[0].strip()


def pool_facets(pool):
    """The filter dimensions of one course pool, each with row counts."""
    kinds: dict = {}
    years: dict = {}
    docs: dict = {}
    for problem in pool.problems_all():
        kind = problem.get("source_kind")
        if isinstance(kind, str) and kind:
            kinds[kind] = kinds.get(kind, 0) + 1
        year = problem.get("exam_year")
        if isinstance(year, str) and year:
            years[year] = years.get(year, 0) + 1
        key = document_key(problem.get("source_evidence"))
        if key:
            docs[key] = docs.get(key, 0) + 1
    return {
        "source_kinds": _sorted(kinds),
        "exam_years": _sorted(years),
        "docs": _sorted(docs),
    }


def _sorted(counter):
    """Most common first, then alphabetical; count rides along for the UI."""
    return [
        {"value": value, "count": counter[value]}
        for value in sorted(counter, key=lambda item: (-counter[item], item))
    ]
