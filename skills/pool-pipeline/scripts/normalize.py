"""Shared text normalization for question-bank work. Python stdlib only.

Every function here exists because a *different* guess produced a silent error at
least once during the ADS repair (2026-09-26). Keep them in one place: the
deduplication pass, the fragment-absorption check and the identity fingerprint
must agree, or two passes will disagree about what counts as the same question.

Measured pitfalls this module encodes:

- Truncating the identity key (the earlier tool used the first 400 chars) lets
  near-duplicates through, because the differing part is usually after the cut.
  ``identity()`` therefore never truncates.
- Comparing raw text fails on `$x$` vs `` `x` `` vs rendering variants, so both
  are stripped and folded away.
- A 60-character probe produced false negatives when two copies diverged at
  char 41; 30 characters was the reliable length (``PROBE_CHARS``).
- A fragment whose content is a pure formula has an empty skeleton, so no
  skeleton check can ever confirm it; use ``canon_formula`` for those and route
  the rest to a human list.
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata

PROBE_CHARS = 30

_IMG = re.compile(r"!\[[^\]]*\]\([^)\s]+\)")
_CODE = re.compile(r"`[^`\n]{1,160}`")
_SPAN = re.compile(r"\$[^$\n]{1,200}\$")
_DISPLAY = re.compile(r"\$\$.+?\$\$", re.S)
_TAG = re.compile(r"<[^>]+>")


def strip_markup(text: str | None) -> str:
    """Drop images, code spans, formulas and tags — what is left is prose."""
    t = text or ""
    t = _IMG.sub(" ", t)
    t = _DISPLAY.sub(" ", t)
    t = _SPAN.sub(" ", t)
    t = _CODE.sub(" ", t)
    return _TAG.sub(" ", t)


def skeleton(text: str | None) -> str:
    """Alphanumeric skeleton, lowercased — for locating text and checking absorption."""
    return "".join(c for c in strip_markup(text) if c.isalnum()).lower()


def identity(text: str | None) -> str:
    """Full-content identity for deduplication and the idempotency ledger."""
    t = unicodedata.normalize("NFKC", strip_markup(text))
    t = t.replace("≤", "<=").replace("≥", ">=").replace("×", "*").replace("−", "-")
    return "".join(ch for ch in t if ch.isalnum()).lower()


def identity_hash(text: str | None) -> str:
    """Short stable hash of ``identity()`` — the key of the ledger and of the skip-set."""
    return hashlib.sha256(identity(text).encode("utf-8")).hexdigest()[:16]


def canon_formula(formula: str) -> str:
    """Fold the two renderings of one formula onto a common form."""
    s = formula
    s = s.replace("\\left", "").replace("\\right", "")
    s = s.replace("\\leq", "\\le").replace("\\geq", "\\ge")
    s = re.sub(r"\\[a-zA-Z]*[ ,;:!]", "", s)
    s = re.sub(r"[\s{}$\\]", "", s)
    s = s.replace("≤", "<=").replace("≥", ">=").replace("×", "*").replace("·", "*")
    return s.lower()


def is_doubled(formula: str) -> bool:
    """True when the canonical form is an exact repetition of a shorter block."""
    c = canon_formula(formula)
    n = len(c)
    if n < 8:
        return False
    for p in range(4, n // 2 + 1):
        if n % p == 0 and c == c[:p] * (n // p):
            return True
    return False


def probe(text: str | None) -> str:
    """The slice to look for inside a target row."""
    return skeleton(text)[:PROBE_CHARS]


def contains_probe(target_text: str | None, fragment_text: str | None) -> bool | None:
    """Is the fragment's content inside the target? None = cannot decide."""
    p = probe(fragment_text)
    if not p:
        return None
    return p in skeleton(target_text)


def unescape(text: str) -> str:
    """HTML entities are common in these exports and are *not* markup tags."""
    return html.unescape(text)


if __name__ == "__main__":
    assert is_doubled(r"O(N)O\left(N\right)")
    assert not is_doubled(r"a=(a_1,a_2,\ldots,a_j,\ldots)")
    assert identity("A. foo  bar") == identity("a. foo bar")
    assert contains_probe("x " + "Hello World Foo" + " y", "Hello World Foo") is True
    assert contains_probe("nothing here", "Hello World Foo") is False
    assert contains_probe("whatever", r"$O(N)$") is None
    print("normalize.py self-test OK")
