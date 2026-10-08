"""Locate a question's own text inside its source document — the anchor step.

Why this is not a plain `str.find`: the converted markdown keeps each question
inside HTML tables on very long lines, with tags interrupting the prose, and the
formulas were rewritten. A verbatim search therefore fails for most rows. The
skeleton index (alphanumeric only, character → line map) survives both problems.

Usage:
    python anchors.py <rows.json> <source-dir> [--field problem_text] [--json out.json]

`rows.json` is any list of objects with an id (``problem_id``) and the text field.
The output maps id → {file, line, snippet} or {unmatched: true}. Rows that cannot
be located in the named source are searched across the whole directory: if they
turn up in a *different* file, the row's recorded provenance is wrong, which is
itself worth knowing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalize import PROBE_CHARS, strip_markup  # noqa: E402


def index(path: Path) -> tuple[str, list[int], list[str]]:
    """(skeleton, line-of-char, lines) for one document."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    chars, line_of = [], []
    for n, line in enumerate(lines, 1):
        for ch in strip_markup(line):
            if ch.isalnum():
                chars.append(ch.lower())
                line_of.append(n)
    return "".join(chars), line_of, lines


def locate(path: Path, text: str) -> dict | None:
    hay, line_of, lines = index(path)
    probe = "".join(c for c in strip_markup(text) if c.isalnum()).lower()
    for length in (200, 140, 100, 70, 45, PROBE_CHARS):
        if length > len(probe):
            continue
        pos = hay.find(probe[:length])
        if pos >= 0:
            line = line_of[pos]
            return {
                "file": path.name,
                "line": line,
                "snippet": lines[line - 1].strip()[:220],
            }
    return None


def main() -> int:
    rows_path, source_dir = Path(sys.argv[1]), Path(sys.argv[2])
    field = "problem_text"
    if "--field" in sys.argv:
        field = sys.argv[sys.argv.index("--field") + 1]
    rows = json.loads(rows_path.read_text(encoding="utf-8"))
    documents = sorted(p for p in source_dir.rglob("*.md"))

    out, elsewhere = {}, 0
    for row in rows:
        pid, text = row.get("problem_id"), row.get(field) or ""
        hit = None
        named = row.get("source_file")
        if named:
            candidate = next((d for d in documents if d.name == Path(named).name), None)
            if candidate is not None:
                hit = locate(candidate, text)
        if hit is None:
            for doc in documents:
                found = locate(doc, text)
                if found:
                    found["elsewhere"] = True
                    hit = found
                    elsewhere += 1
                    break
        out[pid] = hit or {"unmatched": True}

    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    matched = sum(1 for v in out.values() if not v.get("unmatched"))
    print(f"{matched}/{len(out)} located ({elsewhere} in a file other than the recorded source)")
    for pid, v in out.items():
        if v.get("unmatched"):
            print(f"  UNMATCHED {pid} — read it by hand; do not guess its source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
