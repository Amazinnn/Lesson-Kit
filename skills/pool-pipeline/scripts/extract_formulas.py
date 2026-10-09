"""Take exactly one authoritative copy of every formula from an original export.

The importer that produced these banks copied each `<math>` block twice: the
structured MathML rendering **and** the raw LaTeX text node that sits beside it in
the same element. Concatenating the element's text content therefore yields
`O(N)O\\left(N\\right)`. The fix is to take one copy:

- if the block carries `<annotation encoding="application/x-tex">`, that is the
  authoritative TeX — use it;
- otherwise the raw LaTeX is the trailing text node after the last child element
  (`</mrow>O(\\log N)</math>` → `O(\\log N)`);
- if neither exists the block is reported as a *fallback* — never take the whole
  element silently.

Never "un-double" the text afterwards by guessing: every heuristic that split a
doubled formula in half also ate legitimate content such as
`a=(a_1,a_2,\\ldots,a_j,\\ldots)`, and it cannot tell which of the two copies is
authoritative.

Usage:
    python extract_formulas.py list  <file.html|file.mhtml>
    python extract_formulas.py scan  <file>...
    python extract_formulas.py check <file>...
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

MATH = re.compile(r"<math\b[^>]*>(.*?)</math>", re.S)
ANNOTATION = re.compile(
    r'<annotation[^>]*encoding="application/x-tex"[^>]*>(.*?)</annotation>', re.S)
TAGS = re.compile(r"<[^>]+>")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalize import is_doubled  # noqa: E402


def read(path: Path) -> str:
    raw = path.read_bytes().decode("utf-8", errors="replace")
    if path.suffix.lower() in {".mhtml", ".mht"} and "=3D" in raw[:40000]:
        raw = raw.replace("=\r\n", "").replace("=\n", "")
        raw = re.sub(r"=([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), raw)
    return raw


def extract(text: str) -> tuple[list[str], list[str]]:
    """(formulas, fallbacks) in document order."""
    formulas, fallbacks = [], []
    for inner in MATH.findall(text):
        annotation = ANNOTATION.search(inner)
        if annotation:
            formulas.append(html.unescape(annotation.group(1)).strip())
            continue
        body = ANNOTATION.sub("", inner)
        tail = body[body.rfind(">") + 1:] if ">" in body else body
        tail = html.unescape(tail).strip()
        if tail:
            formulas.append(tail)
        else:
            fallbacks.append(html.unescape(TAGS.sub("", body)).strip())
    return formulas, fallbacks


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cmd, files = sys.argv[1], [Path(p) for p in sys.argv[2:]]
    if cmd == "list":
        formulas, fallbacks = extract(read(files[0]))
        for i, formula in enumerate(formulas, 1):
            print(f"{i:>4}  {formula}")
        for formula in fallbacks:
            print(f"       FALLBACK (verify by hand): {formula}")
        return 0
    if cmd == "scan":
        print(f"{'file':<50} {'blocks':>7} {'tex':>5} {'fallback':>9} {'doubled':>8}")
        for path in files:
            text = read(path)
            formulas, fallbacks = extract(text)
            print(f"{path.name[:48]:<50} {len(MATH.findall(text)):>7} "
                  f"{text.count('application/x-tex'):>5} {len(fallbacks):>9} "
                  f"{sum(1 for f in formulas if is_doubled(f)):>8}")
        return 0
    if cmd == "check":
        ok = True
        for path in files:
            text = read(path)
            blocks = MATH.findall(text)
            annotations = [html.unescape(a).strip() for a in ANNOTATION.findall(text)]
            formulas, fallbacks = extract(text)
            doubled = [f for f in formulas if is_doubled(f)]
            same = len(blocks) == len(formulas) == len(annotations) and not fallbacks and not doubled
            ok &= same
            print(f"{'OK ' if same else 'BAD'} {path.name[:56]:<58} blocks={len(blocks)} "
                  f"annotations={len(annotations)} out={len(formulas)} "
                  f"fallback={len(fallbacks)} doubled={len(doubled)}")
            mismatched = [(a, f) for a, f in zip(annotations, formulas) if a.strip() != f.strip()]
            if mismatched:
                print(f"    {len(mismatched)} annotation mismatches, e.g. {mismatched[0]}")
        print("self-check:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    print(f"unknown subcommand {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
