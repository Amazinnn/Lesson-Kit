"""Output-contract validation: deterministic checks, never trusts model text."""

EXPLAIN_SECTIONS = ["结论", "逐步拆解", "易错点", "回源指向"]
DIAGNOSE_SECTIONS = ["定位", "提示", "溯源", "追问"]

_KINDS = {"explain": EXPLAIN_SECTIONS, "diagnose": DIAGNOSE_SECTIONS}


def validate(kind, text):
    """Return (ok, reasons). A result is trusted only when ok."""
    sections = _KINDS.get(kind)
    if sections is None:
        return False, ["unknown operation kind"]
    if not text or not text.strip():
        return False, ["empty result"]
    reasons = []
    for name in sections:
        if not _has_section(text, name):
            reasons.append(f"missing section {name}")
        elif not _section_content(text, name):
            reasons.append(f"empty section {name}")
    return (not reasons), reasons


def _has_section(text, name):
    return f"## {name}" in text


def _section_content(text, name):
    lines = text.splitlines()
    inside = False
    content = []
    for line in lines:
        if line.startswith("## "):
            if line[3:].strip() == name:
                inside = True
                continue
            if inside:
                break
        elif inside and line.strip():
            content.append(line)
    return bool(content)
