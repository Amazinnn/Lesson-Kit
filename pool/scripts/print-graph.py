#!/usr/bin/env python3
"""
Pipeline Read Step: Print knowledge pool as student-facing narrative Markdown.

Reads knowledge_points from the SQLite pool and writes per-chapter Markdown
files. Strictly mechanical — no synthesis, no inference, no LLM. Every
character comes from a SQLite field.

Output structure (narrative, no meta-labels):
    # {course_name} — {chapter_code}                H1 (chapter)
    #### §X-Y {section}                            H4 (section, skip H2/H3)
    **{name}** [[{self-kp-id}]] {body}             paragraph
    {fragile}                                      paragraph (if non-NULL)
    [[related-kp-id-1]] [[related-kp-id-2]] ...    inline at end of paragraph

Display rules:
  - Show: knowledge_item (bold), kp_id (self + related), body, fragile
  - Hide: importance, difficulty, knowledge_type, source_location,
          learning_action, created_at, updated_at
  - No "KP 索引" / "KP 详情" / "学习动作" / "易错点" labels

Script-parseable invariants (for future non-LLM updates):
  1. Each KP occupies one paragraph (blank line separated)
  2. Paragraph starts with: \\*\\*.+?\\*\\*\\s*\\[\\[(?P<self_id>{course}-ch\\d{2}-kp-\\d{3})\\]\\]
  3. Paragraph ends with:    \\[\\[(?P<rel_id>{course}-ch\\d{2}-kp-\\d{3})\\]\\](\\s+\\[\\[..\\]\\])*
  4. wiki links use strict kp_id format

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
from typing import Any, Dict, List, Optional


SECTION_PATTERN = re.compile(r"(?:§|Section|Sec\.?)\s*([\w\-\.]+)", re.IGNORECASE)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print lesson-kit knowledge pool as student-facing narrative Markdown.",
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
        help="Course name used in the H1 chapter title.",
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
    """Fetch all KP rows for the course (optionally filtered to a single chapter)."""
    if chapter:
        prefix = f"{course}-{chapter}-"
    else:
        prefix = f"{course}-"

    rows = conn.execute(
        "SELECT kp_id, knowledge_item, source_location, importance, "
        "learning_action, body, related_kp_ids, fragile "
        "FROM knowledge_points "
        "WHERE kp_id LIKE ? "
        "ORDER BY kp_id",
        (prefix + "%",),
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
            "fragile": fragile,  # None or string
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


def render_kp_paragraph(kp: Dict[str, Any]) -> str:
    """Render one KP as a single Markdown paragraph.

    Format: **{name}** [[{self-kp-id}]] {body}{fragile_inline}
    If fragile is non-NULL, append it as a separate paragraph below the body.
    """
    name = kp["knowledge_item"]
    self_id = kp["kp_id"]
    body = kp["body"] if kp["body"] else "*[正文待补充]*"
    related = kp["related_kp_ids"]

    parts: List[str] = [f"**{name}** [[{self_id}]] {body}"]
    para = "".join(parts).rstrip()

    if kp["fragile"]:
        para += "\n\n" + kp["fragile"].rstrip()

    if related:
        para += "\n\n" + " ".join(f"[[{r}]]" for r in related)

    return para + "\n"


def render_chapter(
    chapter_code: str,
    course_name: str,
    kps: List[Dict[str, Any]],
) -> str:
    """Render one chapter Markdown file with H4 section groups.

    Spacing convention: two blank lines between any two KP blocks
    (titles, sections, KP entries). Keeps Obsidian and most readers
    visually separating each unit clearly.
    """
    groups: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    for kp in kps:
        section = extract_section(kp["source_location"])
        groups.setdefault(section, []).append(kp)

    blocks: List[str] = [f"# {course_name} — {chapter_code}"]

    for section, items in groups.items():
        blocks.append(f"#### {section}")
        for kp in items:
            blocks.append(render_kp_paragraph(kp).rstrip("\n"))

    return "\n\n".join(blocks) + "\n"


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