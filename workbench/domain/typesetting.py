"""Read-only body measurements; findings never prescribe or refuse content."""

import math
import re


# kp-text-typesetting-check: Knowledge-point body paragraph typesetting check.
MIN_VISIBLE = 40
MAX_VISIBLE = 300
_CONSTRUCT = re.compile(r"(?P<ticks>`+).*?(?P=ticks)|\$\$.*?\$\$|\$[^$\n]*\$", re.DOTALL)


def _paragraph_counts(body):
    text = body.replace("\r\n", "\n")
    # Mask before splitting: a fenced construct may span several paragraphs.
    # Keep positions/line breaks so only original blank lines define boundaries.
    masked = _CONSTRUCT.sub(
        lambda match: re.sub(r"[^\n]", "\0", match.group()), text)
    counts, lines = [], []
    for original, measured in zip(text.split("\n"), masked.split("\n")):
        if original.strip():
            lines.append(measured.replace("\0", ""))
        elif lines:
            counts.append(len("\n".join(lines).strip()))
            lines = []
    if lines:
        counts.append(len("\n".join(lines).strip()))
    return counts


def check(rows, available=True):
    """Measure kp_id/key and body rows without changing their text or mappings."""
    rows = list(rows) if available else []
    over_long, short, lengths = [], [], []
    over_count = short_count = 0
    for row in rows:
        counts = _paragraph_counts(row.get("body") or "")
        lengths.extend(counts)
        over = sum(count > MAX_VISIBLE for count in counts)
        under = sum(0 < count < MIN_VISIBLE for count in counts)
        over_count += bool(over)
        short_count += bool(under)
        if over or under:
            entry = {
                "kp_id": row.get("kp_id") or row["key"],
                "over_long_paragraphs": over, "short_paragraphs": under,
                "min_visible_characters": min(counts),
                "max_visible_characters": max(counts),
            }
            (over_long if over else short).append(entry)
    lengths.sort()
    return {
        "available": available, "band": {"min": MIN_VISIBLE, "max": MAX_VISIBLE},
        "over_long": over_long, "short": short,
        "summary": {
            "knowledge_points": len(rows), "paragraphs": len(lengths),
            "visible_characters": {
                f"p{percent}": lengths[math.ceil(len(lengths) * percent / 100) - 1]
                if lengths else None for percent in (50, 75, 90, 99)
            },
            "over_long": {"knowledge_points": over_count,
                          "share": over_count / len(rows) if rows else 0},
            "short": {"knowledge_points": short_count,
                      "share": short_count / len(rows) if rows else 0},
        },
    }


def render_text(report):
    """Shared plain-text wording for both hosts, containing measured facts only."""
    if not report["available"]:
        return "Typesetting check: no input available to check."
    low, high = report["band"]["min"], report["band"]["max"]
    lines = ["Typesetting check (advisory)"]
    for field, label in (("over_long", "Over-long paragraphs"), ("short", "Short paragraphs")):
        if report[field]:
            lines.append(f"{label}:")
            for row in report[field]:
                lines.append(
                    f"  {row['kp_id']}: over {high}: {row['over_long_paragraphs']}, "
                    f"under {low}: {row['short_paragraphs']}; "
                    f"min {row['min_visible_characters']}, max {row['max_visible_characters']}")
    summary = report["summary"]
    percentiles = ", ".join(
        f"{name} {value if value is not None else 'n/a'}"
        for name, value in summary["visible_characters"].items())
    lines.append(
        f"Typesetting summary: knowledge points {summary['knowledge_points']}, "
        f"paragraphs {summary['paragraphs']}; visible characters {percentiles}; "
        f"over {high}: {summary['over_long']['knowledge_points']} knowledge points "
        f"({summary['over_long']['share']:.1%}); "
        f"under {low}: {summary['short']['knowledge_points']} knowledge points "
        f"({summary['short']['share']:.1%}).")
    return "\n".join(lines)
