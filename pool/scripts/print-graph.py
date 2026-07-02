#!/usr/bin/env python3
"""
Pipeline Read Step: Print knowledge pool as student-facing Markdown outline.

Reads knowledge_points from the SQLite pool and writes per-chapter Markdown
files for Obsidian consumption. Strictly mechanical — no synthesis, no
inference, no LLM. Every character comes from a SQLite field.

Student-facing output rules:
  - Show: knowledge_item (heading), body (paragraph), fragile (callout if 1),
    learning_action (one-liner), related_kp_ids ([[wiki links]])
  - Hide: kp_id, knowledge_type, importance, difficulty, source_location,
    created_at, updated_at
  - Do NOT generate INDEX.md (deferred).
  - Do NOT auto-derive "本章脉络" or chapter summaries.
  - Do NOT inject fragile hints into related-link descriptions.

Usage:
    python pool/scripts/print-graph.py \\
        --db pool/dld.db \\
        --course dld \\
        [--chapter ch02] \\
        --course-name "数字逻辑设计" \\
        --out "知识笔记/数字逻辑设计/graph/"
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SECTION_PATTERN = re.compile(r"(?:§|Section|Sec\.?)\s*([\w\-\.]+)", re.IGNORECASE)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print lesson-kit knowledge pool as student-facing Markdown outline.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    parser.add_argument(
        "--course",
        required=True,
        help="Course prefix used to filter kp_id (e.g., 'dld').",
    )
    parser.add_argument(
        "--chapter",
        default=None,
        help="Optional chapter filter (e.g., 'ch02'). If omitted, all chapters for the course are exported.",
    )
    parser.add_argument(
        "--course-name",
        required=True,
        help="Chinese course name used in the per-chapter title.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory (will be created if missing).",
    )
    return parser.parse_args(argv)


def fetch_kps(
    conn: sqlite3.Connection,
    course: str,
    chapter: Optional[str],
) -> List[Dict[str, Any]]:
    """Fetch all KP rows for the course (optionally filtered to a single chapter).

    Returns a list of dicts with keys:
      kp_id, knowledge_item, source_location, importance, learning_action,
      body, related_kp_ids (list), fragile (int).
    """
    if chapter:
        prefix = f"{course}-{chapter}-"
        like_arg = prefix + "%"
    else:
        prefix = f"{course}-"
        like_arg = prefix + "%"

    rows = conn.execute(
        "SELECT kp_id, knowledge_item, source_location, importance, "
        "learning_action, body, related_kp_ids, fragile "
        "FROM knowledge_points "
        "WHERE kp_id LIKE ? "
        "ORDER BY kp_id",
        (like_arg,),
    ).fetchall()

    kps: List[Dict[str, Any]] = []
    for row in rows:
        (
            kp_id,
            knowledge_item,
            source_location,
            importance,
            learning_action,
            body,
            related_kp_ids_raw,
            fragile,
        ) = row

        related: List[str] = []
        if related_kp_ids_raw:
            try:
                parsed = json.loads(related_kp_ids_raw)
                if isinstance(parsed, list):
                    related = [str(x) for x in parsed]
            except json.JSONDecodeError:
                # Malformed JSON in pool — pass through as warning
                print(
                    f"Warning: bad JSON in related_kp_ids for {kp_id}, ignoring",
                    file=sys.stderr,
                )

        kps.append({
            "kp_id": kp_id,
            "knowledge_item": knowledge_item or "",
            "source_location": source_location or "",
            "importance": importance,
            "learning_action": learning_action,
            "body": body,
            "related_kp_ids": related,
            "fragile": int(fragile) if fragile is not None else 0,
        })

    return kps


def group_by_chapter(
    kps: List[Dict[str, Any]], course: str
) -> "OrderedDict[str, List[Dict[str, Any]]]":
    """Group KPs by their chapter code (the segment between course and kp)."""
    chapters: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    prefix = f"{course}-"
    for kp in kps:
        kp_id: str = kp["kp_id"]
        if not kp_id.startswith(prefix):
            continue
        remainder = kp_id[len(prefix):]
        # remainder like "ch02-kp-001"
        parts = remainder.split("-kp-", 1)
        chapter_code = parts[0] if parts else remainder
        chapters.setdefault(chapter_code, []).append(kp)
    return chapters


def extract_section(source_location: str) -> str:
    """Extract §X-Y section identifier from source_location, or '未分组'.

    Recognises: §2-3, Section 2-3, Sec. 2-3, Sec 2-3.
    """
    if not source_location:
        return "未分组"
    match = SECTION_PATTERN.search(source_location)
    if not match:
        return "未分组"
    return f"§{match.group(1)}"


def slugify(text: str) -> str:
    """Produce a GitHub-compatible anchor from heading text."""
    # Strip whitespace, drop punctuation that breaks anchors in Obsidian
    s = text.strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^\w一-鿿\-]", "", s)
    return s or "kp"


def render_index_section(kps: List[Dict[str, Any]]) -> List[str]:
    """Render the '## KP 索引' section grouped by source_location."""
    groups: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    for kp in kps:
        section = extract_section(kp["source_location"])
        groups.setdefault(section, []).append(kp)

    lines: List[str] = ["## KP 索引", ""]
    for section, items in groups.items():
        lines.append(f"### {section}")
        for kp in items:
            anchor = slugify(kp["knowledge_item"])
            lines.append(f"- [{kp['knowledge_item']}](#{anchor})")
        lines.append("")
    return lines


def render_kp_detail(kp: Dict[str, Any]) -> List[str]:
    """Render one KP's detail block (heading + fragile callout + body + learning + related)."""
    lines: List[str] = []
    anchor = slugify(kp["knowledge_item"])
    lines.append(f'<a id="{anchor}"></a>')
    lines.append(f"### {kp['knowledge_item']}")
    lines.append("")

    if kp["fragile"] == 1:
        lines.append("> ⚠ 易错点")
        lines.append("")

    body = kp["body"] if kp["body"] else "*[正文待补充]*"
    lines.append(body)
    lines.append("")

    if kp["learning_action"]:
        lines.append(f"**学习动作：** {kp['learning_action']}")
        lines.append("")

    if kp["related_kp_ids"]:
        lines.append("**关联知识点：**")
        for ref in kp["related_kp_ids"]:
            lines.append(f"- [[{ref}]]")
        lines.append("")

    return lines


def render_chapter(
    chapter_code: str,
    course_name: str,
    kps: List[Dict[str, Any]],
) -> str:
    """Render one chapter Markdown file."""
    parts: List[str] = []
    parts.append(f"# {course_name} — {chapter_code}")
    parts.append("")
    parts.extend(render_index_section(kps))
    parts.append("---")
    parts.append("")
    parts.append("## KP 详情")
    parts.append("")
    for kp in kps:
        parts.extend(render_kp_detail(kp))
    return "\n".join(parts).rstrip() + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if not os.path.isfile(args.db):
        print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    try:
        kps = fetch_kps(conn, args.course, args.chapter)
    finally:
        conn.close()

    if not kps:
        print(
            f"Warning: no KP rows found for course={args.course}"
            + (f" chapter={args.chapter}" if args.chapter else ""),
            file=sys.stderr,
        )
        return 0

    chapters = group_by_chapter(kps, args.course)
    written: List[str] = []
    for chapter_code, chapter_kps in chapters.items():
        content = render_chapter(chapter_code, args.course_name, chapter_kps)
        target = out_dir / f"{chapter_code}.md"
        target.write_text(content, encoding="utf-8")
        written.append(str(target))

    print(f"Wrote {len(written)} chapter file(s) to {out_dir}:")
    for path in written:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())