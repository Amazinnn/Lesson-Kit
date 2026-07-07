#!/usr/bin/env python3
"""
Render a static chapter-level knowledge graph HTML preview.

The renderer reads lesson-kit's SQLite pool and writes one standalone HTML
file. It is intentionally dependency-free: no CDN, no Node build, no server.
The graph is a read-only learning map, not a CRUD surface.
"""

import argparse
import html
import json
import math
import os
import re
import sqlite3
import sys
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


SECTION_PATTERN = re.compile(r"(?:§|Section|Sec\.?)\s*([\w\-\.]+)", re.IGNORECASE)
PROBLEM_STATES = ("new", "wrong", "stuck", "reviewing", "mastered")
GRAPH_WIDTH = 1600
GRAPH_HEIGHT = 1000
MIN_NODE_DISTANCE = 96


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a standalone HTML knowledge graph from a lesson-kit SQLite pool.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    parser.add_argument("--course", required=True, help="Course prefix, e.g. dmath.")
    parser.add_argument("--chapter", required=True, help="Chapter code, e.g. ch06.")
    parser.add_argument(
        "--course-name",
        required=True,
        help="Human-readable course name used in the page title.",
    )
    parser.add_argument("--out", required=True, help="Output directory.")
    return parser.parse_args(argv)


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (name,),
    ).fetchone()
    return row is not None


def column_names(conn: sqlite3.Connection, table: str) -> List[str]:
    if not table_exists(conn, table):
        return []
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})")]


def parse_json_list(raw: Optional[str], row_id: str, field_name: str) -> List[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print(
            f"Warning: invalid JSON in {field_name} for {row_id}; ignoring.",
            file=sys.stderr,
        )
        return []
    if not isinstance(parsed, list):
        print(
            f"Warning: {field_name} for {row_id} is not a JSON array; ignoring.",
            file=sys.stderr,
        )
        return []
    return [str(item) for item in parsed if item is not None]


def extract_section(source_location: str) -> str:
    if not source_location:
        return "未分组"
    match = SECTION_PATTERN.search(source_location)
    if not match:
        return "未分组"
    return f"§{match.group(1)}"


def chapter_prefix(course: str, chapter: str) -> str:
    return f"{course}-{chapter}"


def fallback_graph_label(knowledge_item: str, kp_id: str) -> str:
    text = re.sub(r"\([^)]*\)", "", knowledge_item or "").strip()
    text = re.sub(r"\s+", " ", text)
    if not text:
        return kp_id.rsplit("-", 1)[-1]
    return text


def normalize_problem_text(text: str) -> str:
    return str(text or "").strip()


def fetch_knowledge_points(
    conn: sqlite3.Connection,
    course: str,
    chapter: str,
) -> List[Dict[str, Any]]:
    prefix = chapter_prefix(course, chapter)
    graph_label_select = "graph_label" if "graph_label" in column_names(conn, "knowledge_points") else "NULL"
    try:
        rows = conn.execute(
            f"SELECT kp_id, knowledge_item, {graph_label_select} AS graph_label, source_location, knowledge_type, "
            "related_kp_ids, importance, learning_action, body, difficulty, fragile "
            "FROM knowledge_points "
            "WHERE kp_id LIKE ? "
            "ORDER BY kp_id",
            (f"{prefix}-%",),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        raise RuntimeError(f"failed to query knowledge_points: {exc}") from exc

    kps: List[Dict[str, Any]] = []
    for row in rows:
        (
            kp_id,
            knowledge_item,
            graph_label,
            source_location,
            knowledge_type,
            related_kp_ids_raw,
            importance,
            learning_action,
            body,
            difficulty,
            fragile,
        ) = row
        source_location = source_location or ""
        graph_label = str(graph_label).strip() if graph_label else ""
        kps.append({
            "id": kp_id,
            "label": knowledge_item or kp_id,
            "graph_label": graph_label or fallback_graph_label(knowledge_item or "", kp_id),
            "source_location": source_location,
            "section": extract_section(source_location),
            "knowledge_type": knowledge_type or "",
            "importance": importance or "",
            "learning_action": learning_action or "",
            "body": body or "",
            "difficulty": difficulty or "",
            "fragile": fragile or "",
            "related": parse_json_list(related_kp_ids_raw, kp_id, "related_kp_ids"),
        })
    return kps


def fetch_kp_states(conn: sqlite3.Connection, kp_ids: Iterable[str]) -> Dict[str, str]:
    kp_id_set = set(kp_ids)
    if not kp_id_set or not table_exists(conn, "kp_progress"):
        return {}
    placeholders = ",".join("?" for _ in kp_id_set)
    try:
        rows = conn.execute(
            f"SELECT kp_id, mastery_state FROM kp_progress WHERE kp_id IN ({placeholders})",
            tuple(sorted(kp_id_set)),
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    return {str(kp_id): str(state) for kp_id, state in rows}


def latest_problem_status_column(conn: sqlite3.Connection) -> Optional[str]:
    if not table_exists(conn, "problem_progress"):
        return None
    columns = [row[1] for row in conn.execute("PRAGMA table_info(problem_progress)")]
    for candidate in ("status", "problem_state", "state", "mastery_state"):
        if candidate in columns:
            return candidate
    return None


def fetch_problem_status_counts(
    conn: sqlite3.Connection,
    course: str,
    chapter: str,
    kp_ids: Iterable[str],
) -> Dict[str, Dict[str, int]]:
    """Return per-KP problem state counts when a future progress table exists.

    The current v1 pool has no problem_progress table. This function is tolerant:
    if the table or a recognizable state column is absent, it returns zeros.
    """
    counts: Dict[str, Dict[str, int]] = {
        kp_id: {state: 0 for state in PROBLEM_STATES}
        for kp_id in kp_ids
    }
    if not table_exists(conn, "problems"):
        return counts
    state_col = latest_problem_status_column(conn)
    if state_col is None:
        return counts

    prefix = chapter_prefix(course, chapter)
    try:
        rows = conn.execute(
            "SELECT p.kp_ids, pp.{state_col} "
            "FROM problems p "
            "INNER JOIN problem_progress pp ON pp.problem_id = p.problem_id "
            "WHERE p.problem_id LIKE ?".format(state_col=state_col),
            (f"{prefix}-%",),
        ).fetchall()
    except sqlite3.OperationalError:
        return counts

    known = set(counts)
    for kp_ids_raw, state in rows:
        state = str(state or "new")
        if state not in PROBLEM_STATES:
            state = "new"
        for kp_id in parse_json_list(kp_ids_raw, "problem", "kp_ids"):
            if kp_id in known:
                counts[kp_id][state] += 1
    return counts


def count_problem_links(
    conn: sqlite3.Connection,
    course: str,
    chapter: str,
    kp_ids: Iterable[str],
) -> Dict[str, int]:
    counts = {kp_id: 0 for kp_id in kp_ids}
    if not table_exists(conn, "problems"):
        return counts
    prefix = chapter_prefix(course, chapter)
    try:
        rows = conn.execute(
            "SELECT problem_id, kp_ids FROM problems WHERE problem_id LIKE ?",
            (f"{prefix}-%",),
        ).fetchall()
    except sqlite3.OperationalError:
        return counts
    known = set(counts)
    for problem_id, kp_ids_raw in rows:
        linked = parse_json_list(kp_ids_raw, str(problem_id), "kp_ids")
        for kp_id in linked:
            if kp_id in known:
                counts[kp_id] += 1
    return counts


def fetch_problem_summaries(
    conn: sqlite3.Connection,
    course: str,
    chapter: str,
    kp_ids: Iterable[str],
) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    grouped = {
        kp_id: {state: [] for state in PROBLEM_STATES}
        for kp_id in kp_ids
    }
    if not table_exists(conn, "problems"):
        return grouped

    prefix = chapter_prefix(course, chapter)
    state_col = latest_problem_status_column(conn)
    if state_col:
        sql = (
            "SELECT p.problem_id, p.kp_ids, p.problem_text, "
            f"COALESCE(pp.{state_col}, 'new') AS status "
            "FROM problems p "
            "LEFT JOIN problem_progress pp ON pp.problem_id = p.problem_id "
            "WHERE p.problem_id LIKE ? "
            "ORDER BY p.problem_id"
        )
    else:
        sql = (
            "SELECT problem_id, kp_ids, problem_text, 'new' AS status "
            "FROM problems "
            "WHERE problem_id LIKE ? "
            "ORDER BY problem_id"
        )

    try:
        rows = conn.execute(sql, (f"{prefix}-%",)).fetchall()
    except sqlite3.OperationalError:
        return grouped

    known = set(grouped)
    for problem_id, kp_ids_raw, problem_text, status in rows:
        status = str(status or "new")
        if status not in PROBLEM_STATES:
            status = "new"
        summary = {
            "problem_id": str(problem_id),
            "status": status,
            "text": normalize_problem_text(str(problem_text or "")),
        }
        for kp_id in parse_json_list(kp_ids_raw, str(problem_id), "kp_ids"):
            if kp_id in known:
                grouped[kp_id][status].append(summary)
    return grouped


def build_edges(kps: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    known = {kp["id"] for kp in kps}
    seen = set()
    edges: List[Dict[str, str]] = []
    for kp in kps:
        source = kp["id"]
        for target in kp["related"]:
            if target not in known:
                continue
            key = tuple(sorted((source, target)))
            if key in seen:
                continue
            seen.add(key)
            edges.append({"source": source, "target": target})
    return edges


def compute_degrees(kps: List[Dict[str, Any]], edges: List[Dict[str, str]]) -> Dict[str, int]:
    neighbors = {kp["id"]: set() for kp in kps}
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source in neighbors and target in neighbors:
            neighbors[source].add(target)
            neighbors[target].add(source)
    return {kp_id: len(linked) for kp_id, linked in neighbors.items()}


def stable_layout(kps: List[Dict[str, Any]], width: int = GRAPH_WIDTH, height: int = GRAPH_HEIGHT) -> None:
    """Assign deterministic section-based coordinates to each KP in place."""
    grouped: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    for kp in kps:
        grouped.setdefault(kp["section"], []).append(kp)

    sections = list(grouped.items())
    if not sections:
        return

    margin_x = 140
    margin_y = 110
    usable_w = max(width - margin_x * 2, 200)
    usable_h = max(height - margin_y * 2, 200)
    columns = min(5, max(1, math.ceil(math.sqrt(len(sections)))))
    rows = max(1, math.ceil(len(sections) / columns))
    cell_w = usable_w / columns
    cell_h = usable_h / rows

    for index, (_section, items) in enumerate(sections):
        col = index % columns
        row = index // columns
        cx = margin_x + cell_w * (col + 0.5)
        cy = margin_y + cell_h * (row + 0.5)
        radius = min(cell_w, cell_h) * 0.28
        n = len(items)
        for item_index, kp in enumerate(items):
            if n == 1:
                x, y = cx, cy
            else:
                angle = -math.pi / 2 + 2 * math.pi * item_index / n
                ring = radius * (0.72 + 0.18 * (item_index % 2))
                x = cx + math.cos(angle) * ring
                y = cy + math.sin(angle) * ring
            kp["x"] = round(x, 2)
            kp["y"] = round(y, 2)
    relax_node_spacing(kps, width, height, MIN_NODE_DISTANCE + 1)


def relax_node_spacing(
    kps: List[Dict[str, Any]],
    width: int,
    height: int,
    min_distance: int,
    iterations: int = 120,
) -> None:
    if len(kps) < 2:
        return
    margin = 58
    for _ in range(iterations):
        moved = False
        for i in range(len(kps)):
            a = kps[i]
            for j in range(i + 1, len(kps)):
                b = kps[j]
                dx = float(b["x"]) - float(a["x"])
                dy = float(b["y"]) - float(a["y"])
                distance = math.hypot(dx, dy)
                if distance >= min_distance:
                    continue
                if distance == 0:
                    dx, dy, distance = 1.0, 0.0, 1.0
                push = (min_distance - distance) / 2.0
                ux = dx / distance
                uy = dy / distance
                a["x"] = float(a["x"]) - ux * push
                a["y"] = float(a["y"]) - uy * push
                b["x"] = float(b["x"]) + ux * push
                b["y"] = float(b["y"]) + uy * push
                moved = True
        for kp in kps:
            kp["x"] = min(width - margin, max(margin, float(kp["x"])))
            kp["y"] = min(height - margin, max(margin, float(kp["y"])))
        if not moved:
            break
    for kp in kps:
        kp["x"] = round(float(kp["x"]), 2)
        kp["y"] = round(float(kp["y"]), 2)


def status_class(problem_counts: Dict[str, int], kp_state: str) -> str:
    if problem_counts.get("wrong", 0) > 0:
        return "wrong"
    if problem_counts.get("stuck", 0) > 0:
        return "stuck"
    if problem_counts.get("reviewing", 0) > 0:
        return "reviewing"
    if kp_state:
        return kp_state
    if problem_counts.get("mastered", 0) > 0:
        return "mastered"
    return "neutral"


def build_graph_data(
    conn: sqlite3.Connection,
    course: str,
    chapter: str,
    course_name: str,
) -> Dict[str, Any]:
    kps = fetch_knowledge_points(conn, course, chapter)
    kp_ids = [kp["id"] for kp in kps]
    kp_states = fetch_kp_states(conn, kp_ids)
    problem_groups = fetch_problem_summaries(conn, course, chapter, kp_ids)
    stable_layout(kps, GRAPH_WIDTH, GRAPH_HEIGHT)
    edges = build_edges(kps)
    degrees = compute_degrees(kps, edges)

    for kp in kps:
        kp_id = kp["id"]
        groups = problem_groups.get(kp_id, {state: [] for state in PROBLEM_STATES})
        problem_counts = {state: len(groups.get(state, [])) for state in PROBLEM_STATES}
        kp["kp_state"] = kp_states.get(kp_id, "")
        kp["problem_count"] = sum(problem_counts.values())
        kp["problem_states"] = {state: int(problem_counts.get(state, 0)) for state in PROBLEM_STATES}
        kp["problem_groups"] = groups
        kp["status"] = status_class(kp["problem_states"], kp["kp_state"])
        kp["degree"] = degrees.get(kp_id, 0)

    sections = Counter(kp["section"] for kp in kps)
    return {
        "meta": {
            "course": course,
            "chapter": chapter,
            "course_name": course_name,
            "node_count": len(kps),
            "edge_count": len(edges),
            "layout": {
                "width": GRAPH_WIDTH,
                "height": GRAPH_HEIGHT,
                "min_node_distance": MIN_NODE_DISTANCE,
            },
            "sections": [{"name": name, "count": count} for name, count in sections.items()],
        },
        "nodes": kps,
        "edges": edges,
    }


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def render_html(graph: Dict[str, Any], editable: bool = False) -> str:
    graph = dict(graph)
    graph["meta"] = dict(graph.get("meta", {}))
    graph["meta"]["editable"] = bool(editable)
    data_json = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    script_json = data_json.replace("</", "<\\/")
    title = f"{graph['meta']['course_name']} {graph['meta']['chapter']} Knowledge Graph"
    escaped_title = html.escape(title)
    node_count = int(graph["meta"]["node_count"])
    edge_count = int(graph["meta"]["edge_count"])
    section_count = len(graph["meta"]["sections"])
    view_width = int(graph["meta"].get("layout", {}).get("width", GRAPH_WIDTH))
    view_height = int(graph["meta"].get("layout", {}).get("height", GRAPH_HEIGHT))

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>{escaped_title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f4ed;
      --panel: #fffdfa;
      --ink: #1e1f22;
      --muted: #64615b;
      --line: #d9d1c1;
      --accent: #0b6b72;
      --accent-2: #b6403a;
      --accent-3: #8a6f13;
      --good: #2f6b3f;
      --shadow: 0 18px 50px rgba(42, 34, 22, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      overflow: hidden;
      color: var(--ink);
      background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.2)),
        radial-gradient(circle at 12% 18%, rgba(11, 107, 114, 0.16), transparent 32%),
        radial-gradient(circle at 84% 10%, rgba(182, 64, 58, 0.13), transparent 30%),
        var(--bg);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    button, input, select {{ font: inherit; }}
    .app {{
      width: 100vw;
      height: 100vh;
      display: grid;
      grid-template-columns: minmax(260px, 320px) minmax(460px, 1fr) minmax(320px, 390px);
      gap: 14px;
      padding: 14px;
    }}
    .rail, .detail {{
      min-width: 0;
      border: 1px solid rgba(91, 82, 67, 0.18);
      background: rgba(255, 253, 250, 0.88);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
      border-radius: 8px;
      overflow: hidden;
    }}
    .rail {{
      display: flex;
      flex-direction: column;
      padding: 18px;
      gap: 16px;
    }}
    .brand h1 {{
      margin: 0;
      max-width: 17rem;
      font-size: clamp(1.25rem, 2.2vw, 2.15rem);
      line-height: 1.04;
      font-weight: 760;
    }}
    .brand p {{
      margin: 10px 0 0;
      color: var(--muted);
      line-height: 1.45;
      font-size: 0.92rem;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }}
    .metric {{
      min-width: 0;
      border: 1px solid rgba(91, 82, 67, 0.16);
      border-radius: 8px;
      padding: 10px;
      background: rgba(255, 255, 255, 0.58);
    }}
    .metric strong {{
      display: block;
      font-size: 1.25rem;
      line-height: 1;
    }}
    .metric span {{
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 0.76rem;
    }}
    .control {{
      display: grid;
      gap: 8px;
    }}
    .control label {{
      color: var(--muted);
      font-size: 0.8rem;
      font-weight: 650;
    }}
    .search, .select {{
      width: 100%;
      height: 40px;
      border: 1px solid rgba(91, 82, 67, 0.22);
      border-radius: 8px;
      background: #fffefa;
      color: var(--ink);
      padding: 0 12px;
      outline: none;
    }}
    .search:focus, .select:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(11, 107, 114, 0.14);
    }}
    .button-row {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .btn {{
      min-height: 36px;
      border: 1px solid rgba(91, 82, 67, 0.22);
      border-radius: 8px;
      padding: 0 12px;
      background: #1e1f22;
      color: #fffefa;
      cursor: pointer;
    }}
    .btn.secondary {{
      background: #fffefa;
      color: var(--ink);
    }}
    .legend {{
      display: grid;
      gap: 8px;
      margin-top: auto;
    }}
    .legend-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 0.84rem;
    }}
    .dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 1px solid rgba(30, 31, 34, 0.24);
      flex: 0 0 auto;
    }}
    .dot.neutral {{ background: #7e817c; }}
    .dot.wrong {{ background: var(--accent-2); }}
    .dot.stuck {{ background: #6c4ca3; }}
    .dot.reviewing {{ background: var(--accent-3); }}
    .dot.mastered {{ background: var(--good); }}
    .graph-shell {{
      position: relative;
      min-width: 0;
      overflow: hidden;
      border: 1px solid rgba(91, 82, 67, 0.16);
      border-radius: 8px;
      box-shadow: var(--shadow);
      background:
        linear-gradient(rgba(30, 31, 34, 0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(30, 31, 34, 0.035) 1px, transparent 1px),
        rgba(255, 253, 250, 0.66);
      background-size: 34px 34px;
    }}
    .graph-toolbar {{
      position: absolute;
      z-index: 4;
      top: 14px;
      left: 14px;
      display: flex;
      gap: 8px;
      align-items: center;
      padding: 8px;
      border: 1px solid rgba(91, 82, 67, 0.16);
      border-radius: 8px;
      background: rgba(255, 253, 250, 0.84);
      backdrop-filter: blur(10px);
    }}
    .graph-toolbar span {{
      color: var(--muted);
      font-size: 0.82rem;
      white-space: nowrap;
    }}
    .zoom-btn {{
      width: 30px;
      height: 30px;
      border: 1px solid rgba(91, 82, 67, 0.2);
      border-radius: 8px;
      background: #fffefa;
      color: var(--ink);
      cursor: pointer;
      line-height: 1;
    }}
    .scale-pill {{
      min-width: 48px;
      height: 30px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid rgba(91, 82, 67, 0.16);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.58);
      color: var(--ink);
      font-size: 0.78rem;
      font-weight: 720;
    }}
    svg {{
      width: 100%;
      height: 100%;
      display: block;
      touch-action: none;
    }}
    .edge {{
      stroke: rgba(69, 63, 53, 0.34);
      stroke-width: 1.35;
      transition: opacity 160ms ease, stroke 160ms ease;
    }}
    .edge.focused {{
      stroke: rgba(11, 107, 114, 0.76);
      stroke-width: 2.1;
    }}
    .edge.dimmed {{ opacity: 0.08; }}
    .node {{
      cursor: pointer;
      transition: opacity 160ms ease, transform 160ms ease;
    }}
    .node .halo {{
      fill: transparent;
      stroke: rgba(11, 107, 114, 0);
      stroke-width: 8;
      transition: opacity 160ms ease, stroke 160ms ease;
      opacity: 0;
    }}
    .node .core {{
      fill: #5f625f;
      stroke: #64615b;
      stroke-width: 1.2;
      filter: drop-shadow(0 5px 10px rgba(42, 34, 22, 0.16));
      transition: fill 160ms ease, stroke 160ms ease, stroke-width 160ms ease;
    }}
    .node .node-label {{
      pointer-events: none;
      fill: var(--ink);
      font-size: 13px;
      font-weight: 520;
      text-anchor: middle;
      paint-order: stroke;
      stroke: rgba(255, 253, 250, 0.94);
      stroke-width: 4.4px;
      stroke-linejoin: round;
      stroke-linecap: round;
      transition: opacity 160ms ease, font-weight 160ms ease;
    }}
    .node.focused .node-label,
    .node.pinned .node-label {{
      font-weight: 680;
    }}
    .node .marker {{
      fill: #fffefa;
      stroke-width: 1.3;
      stroke: #7e817c;
      opacity: 0.92;
    }}
    .node.neutral .core, .node.neutral .marker {{ stroke: #6b6d69; }}
    .node.wrong .core {{ stroke: var(--accent-2); fill: var(--accent-2); }}
    .node.wrong .marker {{ stroke: var(--accent-2); fill: #ffe1dc; }}
    .node.stuck .core {{ stroke: #6c4ca3; fill: #6c4ca3; }}
    .node.stuck .marker {{ stroke: #6c4ca3; fill: #eee4ff; }}
    .node.reviewing .core {{ stroke: var(--accent-3); fill: var(--accent-3); }}
    .node.reviewing .marker {{ stroke: var(--accent-3); fill: #fff1b8; }}
    .node.mastered .core {{ stroke: var(--good); fill: var(--good); }}
    .node.mastered .marker {{ stroke: var(--good); fill: #dff0e1; }}
    .node.focused .core {{
      stroke: var(--accent);
      stroke-width: 3;
    }}
    .node.focused .halo {{
      opacity: 0.2;
      stroke: var(--accent);
    }}
    .node.pinned .core {{
      stroke: #1e1f22;
      stroke-width: 3.2;
    }}
    .node.pinned .halo {{
      opacity: 0.28;
      stroke: #1e1f22;
    }}
    .node.dimmed {{
      opacity: 0.14;
    }}
    .node.hidden, .edge.hidden {{
      opacity: 0;
      pointer-events: none;
    }}
    .detail {{
      display: flex;
      flex-direction: column;
      min-height: 0;
    }}
    .detail-inner {{
      padding: 18px;
      overflow: auto;
    }}
    .detail h2 {{
      margin: 0;
      font-size: 1.45rem;
      line-height: 1.08;
    }}
    .detail-head {{
      position: sticky;
      top: -18px;
      z-index: 2;
      margin: -18px -18px 0;
      padding: 18px;
      border-bottom: 1px solid rgba(91, 82, 67, 0.14);
      background: rgba(255, 253, 250, 0.94);
      backdrop-filter: blur(12px);
    }}
    .detail .id {{
      margin-top: 9px;
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      font-size: 0.78rem;
      overflow-wrap: anywhere;
    }}
    .detail-block {{
      margin-top: 18px;
      padding-top: 16px;
      border-top: 1px solid rgba(91, 82, 67, 0.16);
    }}
    .detail-block.compact {{
      margin-top: 12px;
      padding-top: 12px;
    }}
    .detail-block h3 {{
      margin: 0 0 8px;
      font-size: 0.84rem;
      color: var(--muted);
      text-transform: none;
    }}
    .detail-block p {{
      margin: 0;
      line-height: 1.58;
      white-space: pre-wrap;
    }}
    .rich-text {{
      line-height: 1.58;
      overflow-wrap: anywhere;
    }}
    .rich-text p {{
      margin: 0 0 0.72rem;
      white-space: normal;
    }}
    .rich-text p:last-child {{
      margin-bottom: 0;
    }}
    .math {{
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      color: #111827;
      font-family: Cambria Math, STIX Two Math, Georgia, "Times New Roman", serif;
      font-size: 1.02em;
      line-height: 1.35;
      white-space: nowrap;
      vertical-align: baseline;
    }}
    .math.block {{
      display: flex;
      margin: 0.72rem 0;
      padding: 10px 12px;
      overflow-x: auto;
      border: 1px solid rgba(91, 82, 67, 0.14);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.56);
      font-size: 1.08em;
    }}
    .frac, .binom {{
      display: inline-grid;
      grid-template-rows: auto auto;
      align-items: center;
      justify-items: center;
      margin: 0 0.16em;
      vertical-align: middle;
    }}
    .frac > .top {{
      border-bottom: 1px solid currentColor;
      padding: 0 0.14em 0.08em;
    }}
    .frac > .bottom {{
      padding: 0.08em 0.14em 0;
    }}
    .binom {{
      position: relative;
      padding: 0 0.42em;
    }}
    .binom::before {{ content: "("; position: absolute; left: 0; top: 18%; }}
    .binom::after {{ content: ")"; position: absolute; right: 0; top: 18%; }}
    .math sup, .math sub {{
      font-size: 0.72em;
      line-height: 0;
    }}
    .op {{
      display: inline-grid;
      grid-template-rows: auto auto auto;
      align-items: center;
      justify-items: center;
      margin: 0 0.18em;
      vertical-align: middle;
    }}
    .op .symbol {{ font-size: 1.28em; line-height: 0.9; }}
    .op .limit {{ font-size: 0.66em; line-height: 1; }}
    .edit-field {{
      width: 100%;
      min-height: 132px;
      resize: vertical;
      border: 1px solid rgba(91, 82, 67, 0.22);
      border-radius: 8px;
      background: #fffefa;
      color: var(--ink);
      padding: 10px;
      line-height: 1.5;
      outline: none;
    }}
    .edit-field.small {{
      min-height: 78px;
    }}
    .edit-field:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(11, 107, 114, 0.14);
    }}
    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }}
    .chip {{
      border: 1px solid rgba(91, 82, 67, 0.2);
      border-radius: 999px;
      padding: 5px 9px;
      background: rgba(255, 255, 255, 0.62);
      color: var(--ink);
      font-size: 0.78rem;
      line-height: 1;
    }}
    .problem-groups {{
      display: grid;
      gap: 12px;
    }}
    .problem-group {{
      display: grid;
      gap: 7px;
      border: 1px solid rgba(91, 82, 67, 0.14);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.42);
      overflow: hidden;
    }}
    .problem-group-title {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 9px 10px;
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 720;
      cursor: pointer;
      list-style: none;
    }}
    .problem-group-title::-webkit-details-marker {{
      display: none;
    }}
    .problem-group-title::after {{
      content: "+";
      margin-left: auto;
      color: var(--muted);
      font-weight: 800;
    }}
    .problem-group[open] .problem-group-title::after {{
      content: "-";
    }}
    .problem-list {{
      display: grid;
      gap: 7px;
      padding: 0 9px 9px;
    }}
    .problem-row {{
      display: grid;
      gap: 6px;
      border: 1px solid rgba(91, 82, 67, 0.15);
      border-radius: 8px;
      padding: 9px;
      background: rgba(255, 255, 255, 0.5);
    }}
    .problem-id {{
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      font-size: 0.74rem;
    }}
    .problem-text {{
      line-height: 1.42;
      font-size: 0.86rem;
    }}
    .record-line {{
      display: grid;
      grid-template-columns: minmax(92px, 120px) minmax(0, 1fr) auto;
      gap: 6px;
      align-items: center;
    }}
    .record-line input, .record-line select {{
      min-width: 0;
      height: 32px;
      border: 1px solid rgba(91, 82, 67, 0.2);
      border-radius: 8px;
      background: #fffefa;
      color: var(--ink);
      padding: 0 8px;
      font-size: 0.78rem;
    }}
    .toast {{
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 20;
      max-width: min(360px, calc(100vw - 36px));
      border: 1px solid rgba(91, 82, 67, 0.18);
      border-radius: 8px;
      padding: 10px 12px;
      background: rgba(30, 31, 34, 0.94);
      color: #fffefa;
      box-shadow: var(--shadow);
      opacity: 0;
      transform: translateY(8px);
      pointer-events: none;
      transition: opacity 160ms ease, transform 160ms ease;
      font-size: 0.86rem;
    }}
    .toast.show {{
      opacity: 1;
      transform: translateY(0);
    }}
    .empty {{
      color: var(--muted);
      line-height: 1.55;
    }}
    @media (max-width: 1080px) {{
      body {{ overflow: auto; }}
      .app {{
        height: auto;
        min-height: 100vh;
        grid-template-columns: 1fr;
      }}
      .graph-shell {{
        height: 68vh;
        min-height: 520px;
      }}
    }}
  </style>
</head>
<body>
  <main class="app">
    <aside class="rail">
      <section class="brand">
        <h1>{html.escape(graph['meta']['course_name'])} {html.escape(graph['meta']['chapter'])}</h1>
        <p>章节知识地图。悬停节点查看一步连通关系，点击节点固定聚焦。</p>
      </section>
      <section class="metrics" aria-label="图谱概览">
        <div class="metric"><strong>{node_count}</strong><span>知识点</span></div>
        <div class="metric"><strong>{edge_count}</strong><span>关系</span></div>
        <div class="metric"><strong>{section_count}</strong><span>分组</span></div>
      </section>
      <section class="control">
        <label for="search">搜索</label>
        <input id="search" class="search" type="search" placeholder="名称、ID、正文" autocomplete="off">
      </section>
      <section class="control">
        <label for="statusFilter">状态筛选</label>
        <select id="statusFilter" class="select">
          <option value="all">全部状态</option>
          <option value="wrong">wrong</option>
          <option value="stuck">stuck</option>
          <option value="reviewing">reviewing</option>
          <option value="mastered">mastered</option>
          <option value="neutral">neutral</option>
          <option value="fragile">有 fragile note</option>
        </select>
      </section>
      <section class="button-row">
        <button id="resetFocus" class="btn" type="button">重置聚焦</button>
        <button id="fitGraph" class="btn secondary" type="button">适应画布</button>
      </section>
      <section class="legend" aria-label="状态图例">
        <div class="legend-row"><span class="dot wrong"></span><span>wrong 优先显示</span></div>
        <div class="legend-row"><span class="dot stuck"></span><span>stuck 需要卡点处理</span></div>
        <div class="legend-row"><span class="dot reviewing"></span><span>reviewing 正在复习</span></div>
        <div class="legend-row"><span class="dot mastered"></span><span>mastered 已掌握</span></div>
        <div class="legend-row"><span class="dot neutral"></span><span>neutral 暂无状态</span></div>
      </section>
    </aside>
    <section class="graph-shell" aria-label="知识图谱">
      <div class="graph-toolbar">
        <button id="zoomOut" class="zoom-btn" type="button" title="缩小">−</button>
        <button id="zoomIn" class="zoom-btn" type="button" title="放大">+</button>
        <span id="scaleBadge" class="scale-pill">100%</span>
        <span id="focusHint">未固定节点</span>
      </div>
      <svg id="graph" viewBox="0 0 {view_width} {view_height}" role="img" aria-label="Knowledge graph"></svg>
    </section>
    <aside class="detail" aria-label="知识点详情">
      <div id="detail" class="detail-inner"></div>
    </aside>
  </main>
  <div id="toast" class="toast" aria-live="polite"></div>
  <script id="graph-data" type="application/json">{script_json}</script>
  <script>
    const graph = JSON.parse(document.getElementById('graph-data').textContent);
    const editable = Boolean(graph.meta && graph.meta.editable);
    const svg = document.getElementById('graph');
    const detail = document.getElementById('detail');
    const search = document.getElementById('search');
    const statusFilter = document.getElementById('statusFilter');
    const focusHint = document.getElementById('focusHint');
    const scaleBadge = document.getElementById('scaleBadge');
    const toast = document.getElementById('toast');
    const nodeById = new Map(graph.nodes.map(node => [node.id, node]));
    const neighbors = new Map(graph.nodes.map(node => [node.id, new Set([node.id])]));
    graph.edges.forEach(edge => {{
      neighbors.get(edge.source)?.add(edge.target);
      neighbors.get(edge.target)?.add(edge.source);
    }});

    let hoverId = null;
    let pinnedId = null;
    let selectedId = graph.nodes[0]?.id || null;
    let view = {{ x: 0, y: 0, scale: 1 }};
    let drag = null;
    const layers = {{
      root: document.createElementNS('http://www.w3.org/2000/svg', 'g'),
      edges: document.createElementNS('http://www.w3.org/2000/svg', 'g'),
      nodes: document.createElementNS('http://www.w3.org/2000/svg', 'g')
    }};
    layers.root.append(layers.edges, layers.nodes);
    svg.appendChild(layers.root);

    function esc(value) {{
      return String(value ?? '').replace(/[&<>"']/g, char => ({{
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }}[char]));
    }}

    function showToast(message) {{
      toast.textContent = message;
      toast.classList.add('show');
      window.clearTimeout(showToast.timer);
      showToast.timer = window.setTimeout(() => toast.classList.remove('show'), 2200);
    }}

    function renderLatex(raw) {{
      let text = String(raw || '').trim();
      const stash = [];
      const put = html => {{
        const token = `\\u0000${{stash.length}}\\u0000`;
        stash.push(html);
        return token;
      }};
      text = text
        .replace(/\\\\left|\\\\right/g, '')
        .replace(/\\\\,/g, ' ')
        .replace(/\\\\;/g, ' ')
        .replace(/\\\\!/g, '')
        .replace(/\\\\mathrm\\s*\\{{([^{{}}]+)\\}}/g, '$1')
        .replace(/\\\\text\\s*\\{{([^{{}}]+)\\}}/g, '$1')
        .replace(/\\\\begin\\s*\\{{[^{{}}]+\\}}\\s*(?:\\{{[^{{}}]*\\}})?/g, '')
        .replace(/\\\\end\\s*\\{{[^{{}}]+\\}}/g, '')
        .replace(/\\\\\\\\/g, ' ; ')
        .replace(/\\\\cdot/g, '·')
        .replace(/\\\\times/g, '×')
        .replace(/\\\\dots|\\\\ldots|\\\\cdots/g, '…')
        .replace(/\\\\leq|\\\\le/g, '≤')
        .replace(/\\\\geq|\\\\ge/g, '≥')
        .replace(/\\\\neq|\\\\ne/g, '≠')
        .replace(/\\\\infty/g, '∞')
        .replace(/\\\\to/g, '→')
        .replace(/\\\\cup/g, '∪')
        .replace(/\\\\cap/g, '∩')
        .replace(/\\\\in/g, '∈')
        .replace(/\\\\notin/g, '∉')
        .replace(/\\\\emptyset/g, '∅')
        .replace(/\\\\lceil/g, '⌈')
        .replace(/\\\\rceil/g, '⌉')
        .replace(/\\\\lfloor/g, '⌊')
        .replace(/\\\\rfloor/g, '⌋')
        .replace(/\\\\alpha/g, 'α')
        .replace(/\\\\beta/g, 'β')
        .replace(/\\\\gamma/g, 'γ')
        .replace(/\\\\Delta/g, 'Δ')
        .replace(/\\\\pi/g, 'π');

      text = text.replace(/\\\\(?:dfrac|frac)\\s*\\{{([^{{}}]+)\\}}\\s*\\{{([^{{}}]+)\\}}/g, (_match, top, bottom) =>
        put(`<span class="frac"><span class="top">${{renderLatex(top)}}</span><span class="bottom">${{renderLatex(bottom)}}</span></span>`)
      );
      text = text.replace(/\\\\binom\\s*\\{{([^{{}}]+)\\}}\\s*\\{{([^{{}}]+)\\}}/g, (_match, top, bottom) =>
        put(`<span class="binom"><span>${{renderLatex(top)}}</span><span>${{renderLatex(bottom)}}</span></span>`)
      );
      text = text.replace(/\\\\(sum|prod)\\s*(?:_\\s*\\{{([^{{}}]+)\\}})?\\s*(?:\\^\\s*\\{{([^{{}}]+)\\}})?/g, (_match, op, lower, upper) => {{
        const symbol = op === 'sum' ? '∑' : '∏';
        return put(`<span class="op">${{upper ? `<span class="limit">${{renderLatex(upper)}}</span>` : '<span></span>'}}<span class="symbol">${{symbol}}</span>${{lower ? `<span class="limit">${{renderLatex(lower)}}</span>` : '<span></span>'}}</span>`);
      }});

      let escaped = esc(text);
      escaped = escaped
        .replace(/([A-Za-z0-9\\)\\]])\\s*\\^\\s*\\{{([^{{}}]+)\\}}/g, '$1<sup>$2</sup>')
        .replace(/([A-Za-z0-9\\)\\]])\\s*_\\s*\\{{([^{{}}]+)\\}}/g, '$1<sub>$2</sub>')
        .replace(/([A-Za-z0-9\\)\\]])\\s*\\^\\s*([A-Za-z0-9]+)/g, '$1<sup>$2</sup>')
        .replace(/([A-Za-z0-9\\)\\]])\\s*_\\s*([A-Za-z0-9]+)/g, '$1<sub>$2</sub>')
        .replace(/\\\\sqrt\\s*\\{{([^{{}}]+)\\}}/g, '√<span class="radicand">$1</span>')
        .replace(/\\\\\\{{/g, '{{')
        .replace(/\\\\\\}}/g, '}}');
      stash.forEach((html, index) => {{
        escaped = escaped.replaceAll(`\\u0000${{index}}\\u0000`, html);
      }});
      return escaped;
    }}

    function renderInlineText(raw) {{
      return esc(raw).replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
    }}

    function renderRichText(raw) {{
      const text = String(raw || '');
      if (!text.trim()) return '';
      const parts = [];
      let cursor = 0;
      const pattern = /\\$\\$([\\s\\S]*?)\\$\\$|\\$([^$\\n]+?)\\$/g;
      let match;
      while ((match = pattern.exec(text)) !== null) {{
        if (match.index > cursor) {{
          parts.push({{ type: 'text', value: text.slice(cursor, match.index) }});
        }}
        parts.push({{ type: match[1] !== undefined ? 'math-block' : 'math-inline', value: match[1] ?? match[2] }});
        cursor = pattern.lastIndex;
      }}
      if (cursor < text.length) parts.push({{ type: 'text', value: text.slice(cursor) }});

      return parts.map(part => {{
        if (part.type === 'math-inline') {{
          return `<span class="math inline">${{renderLatex(part.value)}}</span>`;
        }}
        if (part.type === 'math-block') {{
          return `<div class="math block">${{renderLatex(part.value)}}</div>`;
        }}
        return part.value
          .split(/\\n{{2,}}/)
          .map(block => block.trim())
          .filter(Boolean)
          .map(block => `<p>${{renderInlineText(block).replace(/\\n/g, '<br>')}}</p>`)
          .join('');
      }}).join('');
    }}

    function labelLines(value) {{
      const label = String(value || '').replace(/\\s+/g, ' ').trim();
      if (!label) return [];
      const maxChars = 14;
      const lines = [];
      let line = '';
      for (const char of Array.from(label)) {{
        if (line && line.length + char.length > maxChars) {{
          lines.push(line);
          line = char;
        }} else {{
          line += char;
        }}
        if (/[ _/\\\\\\-:：·、，,；;]/.test(char) && line.length >= 10) {{
          lines.push(line);
          line = '';
        }}
      }}
      if (line) lines.push(line);
      return lines;
    }}

    function appendNodeLabel(group, node, radius) {{
      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('class', 'node-label');
      label.setAttribute('y', radius + 18);
      labelLines(node.graph_label || node.label).forEach((line, index) => {{
        const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
        tspan.setAttribute('x', '0');
        tspan.setAttribute('dy', index === 0 ? '0' : '1.18em');
        tspan.textContent = line;
        label.appendChild(tspan);
      }});
      group.appendChild(label);
    }}

    function matchesFilters(node) {{
      const q = search.value.trim().toLowerCase();
      const status = statusFilter.value;
      const text = [node.id, node.label, node.graph_label, node.body, node.source_location].join(' ').toLowerCase();
      if (q && !text.includes(q)) return false;
      if (status === 'fragile') return Boolean(node.fragile);
      if (status !== 'all' && node.status !== status) return false;
      return true;
    }}

    function activeFocus() {{
      return pinnedId || hoverId;
    }}

    function applyTransform() {{
      layers.root.setAttribute('transform', `translate(${{view.x}} ${{view.y}}) scale(${{view.scale}})`);
      scaleBadge.textContent = `${{Math.round(view.scale * 100)}}%`;
    }}

    function setZoom(nextScale) {{
      view.scale = Math.max(0.42, Math.min(3.2, nextScale));
      applyTransform();
    }}

    function render() {{
      layers.edges.innerHTML = '';
      layers.nodes.innerHTML = '';
      graph.edges.forEach(edge => {{
        const source = nodeById.get(edge.source);
        const target = nodeById.get(edge.target);
        if (!source || !target) return;
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.dataset.source = edge.source;
        line.dataset.target = edge.target;
        line.setAttribute('x1', source.x);
        line.setAttribute('y1', source.y);
        line.setAttribute('x2', target.x);
        line.setAttribute('y2', target.y);
        line.setAttribute('class', 'edge');
        layers.edges.appendChild(line);
      }});
      graph.nodes.forEach(node => {{
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.dataset.id = node.id;
        group.setAttribute('class', `node ${{node.status || 'neutral'}}`);
        group.setAttribute('transform', `translate(${{node.x}} ${{node.y}})`);
        group.setAttribute('tabindex', '0');
        group.setAttribute('role', 'button');
        group.setAttribute('aria-label', node.label);

        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = node.label;
        group.appendChild(title);

        const radius = Math.max(8, Math.min(12, 7 + Math.sqrt(node.problem_count || 0) * 0.9));
        const halo = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        halo.setAttribute('class', 'halo');
        halo.setAttribute('r', radius + 7);
        group.appendChild(halo);

        const core = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        core.setAttribute('class', 'core');
        core.setAttribute('r', radius);
        group.appendChild(core);

        if (node.problem_count) {{
          const marker = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          marker.setAttribute('class', 'marker');
          marker.setAttribute('r', 3.2);
          marker.setAttribute('cx', Math.round(radius * 0.92));
          marker.setAttribute('cy', Math.round(-radius * 0.92));
          group.appendChild(marker);
        }}

        appendNodeLabel(group, node, radius);

        group.addEventListener('mouseenter', () => {{ hoverId = node.id; updateState(); }});
        group.addEventListener('mouseleave', () => {{ hoverId = null; updateState(); }});
        group.addEventListener('click', event => {{
          event.stopPropagation();
          pinnedId = pinnedId === node.id ? null : node.id;
          selectedId = node.id;
          renderDetail(node);
          updateState();
        }});
        group.addEventListener('keydown', event => {{
          if (event.key === 'Enter' || event.key === ' ') {{
            event.preventDefault();
            pinnedId = pinnedId === node.id ? null : node.id;
            selectedId = node.id;
            renderDetail(node);
            updateState();
          }}
        }});
        layers.nodes.appendChild(group);
      }});
      updateState();
      applyTransform();
    }}

    function updateState() {{
      const focus = activeFocus();
      const allowed = focus ? neighbors.get(focus) || new Set([focus]) : null;
      const visible = new Set(graph.nodes.filter(matchesFilters).map(node => node.id));

      layers.nodes.querySelectorAll('.node').forEach(el => {{
        const id = el.dataset.id;
        const isVisible = visible.has(id);
        el.classList.toggle('hidden', !isVisible);
        el.classList.toggle('dimmed', Boolean(focus && !allowed.has(id)));
        el.classList.toggle('focused', Boolean(focus && allowed.has(id)));
        el.classList.toggle('pinned', id === pinnedId);
      }});

      layers.edges.querySelectorAll('.edge').forEach(el => {{
        const source = el.dataset.source;
        const target = el.dataset.target;
        const inFilter = visible.has(source) && visible.has(target);
        const inFocus = !focus || (allowed.has(source) && allowed.has(target));
        const directlyConnected = focus && (source === focus || target === focus);
        el.classList.toggle('hidden', !inFilter);
        el.classList.toggle('dimmed', Boolean(focus && !inFocus));
        el.classList.toggle('focused', Boolean(directlyConnected));
      }});
      focusHint.textContent = pinnedId
        ? `固定：${{nodeById.get(pinnedId)?.label || pinnedId}}`
        : hoverId
          ? `聚焦：${{nodeById.get(hoverId)?.label || hoverId}}`
          : '未固定节点';
    }}

    function renderProblemGroups(node) {{
      const groups = node.problem_groups || {{}};
      const blocks = ['wrong', 'stuck', 'reviewing', 'mastered', 'new']
        .map(status => {{
          const items = groups[status] || [];
          if (!items.length) return '';
          const rows = items.map(problem => {{
            const editControls = editable ? `
              <div class="record-line">
                <select data-problem-status="${{esc(problem.problem_id)}}">
                  ${{['new', 'wrong', 'stuck', 'reviewing', 'mastered'].map(value => `
                    <option value="${{value}}" ${{value === problem.status ? 'selected' : ''}}>${{value}}</option>
                  `).join('')}}
                </select>
                <input data-problem-note="${{esc(problem.problem_id)}}" placeholder="备注 / 错因">
                <button class="btn secondary" data-record-problem="${{esc(problem.problem_id)}}" type="button">记录</button>
              </div>` : '';
            return `
              <div class="problem-row">
                <div class="problem-id">${{esc(problem.problem_id)}}</div>
                <div class="problem-text rich-text">${{renderRichText(problem.text || '题干待补充')}}</div>
                ${{editControls}}
              </div>`;
          }}).join('');
          const open = ['wrong', 'stuck', 'reviewing'].includes(status) ? ' open' : '';
          return `
            <details class="problem-group"${{open}}>
              <summary class="problem-group-title"><span class="dot ${{status}}"></span><span>${{status}} · ${{items.length}}</span></summary>
              <div class="problem-list">${{rows}}</div>
            </details>`;
        }})
        .join('');
      return blocks || '<p class="empty">暂无关联题目。</p>';
    }}

    async function saveKp(node) {{
      const body = detail.querySelector('[data-edit-body]')?.value ?? '';
      const fragile = detail.querySelector('[data-edit-fragile]')?.value ?? '';
      const response = await fetch('/api/kp/' + encodeURIComponent(node.id), {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ body, fragile }})
      }});
      if (!response.ok) {{
        const text = await response.text();
        throw new Error(text || 'save failed');
      }}
      node.body = body;
      node.fragile = fragile;
      renderDetail(node);
      updateState();
      showToast('正文已保存');
    }}

    async function recordProblem(problemId) {{
      const status = detail.querySelector(`[data-problem-status="${{CSS.escape(problemId)}}"]`)?.value || 'new';
      const note = detail.querySelector(`[data-problem-note="${{CSS.escape(problemId)}}"]`)?.value || '';
      const response = await fetch('/api/problem/' + encodeURIComponent(problemId) + '/record', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ status, note }})
      }});
      if (!response.ok) {{
        const text = await response.text();
        throw new Error(text || 'record failed');
      }}
      showToast('做题记录已保存');
      window.setTimeout(() => window.location.reload(), 450);
    }}

    function bindDetailActions(node) {{
      detail.querySelectorAll('[data-jump]').forEach(button => {{
        button.addEventListener('click', () => {{
          const id = button.dataset.jump;
          const next = nodeById.get(id);
          if (next) {{
            selectedId = id;
            pinnedId = id;
            renderDetail(next);
            updateState();
          }}
        }});
      }});
      detail.querySelector('[data-save-kp]')?.addEventListener('click', async () => {{
        try {{
          await saveKp(node);
        }} catch (error) {{
          showToast(error.message || String(error));
        }}
      }});
      detail.querySelectorAll('[data-record-problem]').forEach(button => {{
        button.addEventListener('click', async () => {{
          try {{
            await recordProblem(button.dataset.recordProblem);
          }} catch (error) {{
            showToast(error.message || String(error));
          }}
        }});
      }});
    }}

    function renderDetail(node) {{
      if (!node) {{
        detail.innerHTML = '<p class="empty">选择一个知识点查看正文、关系和状态摘要。</p>';
        return;
      }}
      const related = (node.related || [])
        .filter(id => nodeById.has(id))
        .map(id => `<button class="chip" data-jump="${{esc(id)}}">${{esc(nodeById.get(id).graph_label || nodeById.get(id).label)}}</button>`)
        .join('');
      const states = Object.entries(node.problem_states || {{}})
        .map(([name, count]) => `<span class="chip">${{esc(name)}} ${{count}}</span>`)
        .join('');
      const bodyBlock = editable
        ? `<textarea class="edit-field" data-edit-body>${{esc(node.body || '')}}</textarea>`
        : `<div class="rich-text">${{renderRichText(node.body || '正文待补充')}}</div>`;
      const fragileBlock = editable
        ? `<textarea class="edit-field small" data-edit-fragile>${{esc(node.fragile || '')}}</textarea>`
        : `<div class="rich-text">${{renderRichText(node.fragile || '暂无易错提醒')}}</div>`;
      const saveBlock = editable
        ? `<div class="button-row"><button class="btn" data-save-kp type="button">保存正文</button></div>`
        : '';
      detail.innerHTML = `
        <div class="detail-head">
          <h2>${{esc(node.label)}}</h2>
          <div class="id">${{esc(node.id)}} · ${{esc(node.graph_label || '')}}</div>
        </div>
        <div class="detail-block compact">
          <h3>来源</h3>
          <p>${{esc(node.source_location || node.section || '未分组')}}</p>
        </div>
        <div class="detail-block">
          <h3>正文</h3>
          ${{bodyBlock}}
        </div>
        <div class="detail-block">
          <h3>易错点</h3>
          ${{fragileBlock}}
        </div>
        ${{saveBlock}}
        <div class="detail-block compact">
          <h3>状态摘要</h3>
          <div class="chips">
            <span class="chip">KP ${{esc(node.kp_state || 'neutral')}}</span>
            <span class="chip">${{node.problem_count || 0}} 题</span>
            ${{states}}
          </div>
        </div>
        <div class="detail-block">
          <h3>关联题目</h3>
          <div class="problem-groups">${{renderProblemGroups(node)}}</div>
        </div>
        <div class="detail-block">
          <h3>一步关系</h3>
          <div class="chips">${{related || '<span class="empty">暂无直接关系。</span>'}}</div>
        </div>
      `;
      bindDetailActions(node);
    }}

    svg.addEventListener('click', event => {{
      if (event.target === svg || event.target === layers.root) {{
        pinnedId = null;
        updateState();
      }}
    }});
    svg.addEventListener('pointerdown', event => {{
      if (event.target.closest && event.target.closest('.node')) return;
      drag = {{ x: event.clientX, y: event.clientY, startX: view.x, startY: view.y }};
      svg.setPointerCapture(event.pointerId);
    }});
    svg.addEventListener('pointermove', event => {{
      if (!drag) return;
      view.x = drag.startX + (event.clientX - drag.x);
      view.y = drag.startY + (event.clientY - drag.y);
      applyTransform();
    }});
    svg.addEventListener('pointerup', () => {{ drag = null; }});
    svg.addEventListener('wheel', event => {{
      event.preventDefault();
      const delta = event.deltaY > 0 ? 0.92 : 1.08;
      setZoom(view.scale * delta);
    }}, {{ passive: false }});

    search.addEventListener('input', updateState);
    statusFilter.addEventListener('change', updateState);
    document.getElementById('resetFocus').addEventListener('click', () => {{
      pinnedId = null;
      hoverId = null;
      updateState();
    }});
    document.getElementById('fitGraph').addEventListener('click', () => {{
      view = {{ x: 0, y: 0, scale: 1 }};
      applyTransform();
    }});
    document.getElementById('zoomIn').addEventListener('click', () => setZoom(view.scale * 1.16));
    document.getElementById('zoomOut').addEventListener('click', () => setZoom(view.scale / 1.16));
    window.addEventListener('keydown', event => {{
      if (event.key === 'Escape') {{
        pinnedId = null;
        hoverId = null;
        updateState();
      }}
    }});

    render();
    renderDetail(nodeById.get(selectedId));
  </script>
</body>
</html>
"""


def write_graph_html(
    db_path: Path,
    course: str,
    chapter: str,
    course_name: str,
    out_dir: Path,
) -> Path:
    if not db_path.is_file():
        raise FileNotFoundError(f"DB not found: {db_path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        graph = build_graph_data(conn, course, chapter, course_name)
    finally:
        conn.close()
    if not graph["nodes"]:
        print(
            f"Warning: no KP rows found for {course}-{chapter}; writing empty graph.",
            file=sys.stderr,
        )
    target = out_dir / f"{chapter}-graph.html"
    target.write_text(render_html(graph), encoding="utf-8")
    return target


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        target = write_graph_html(
            Path(args.db),
            args.course,
            args.chapter,
            args.course_name,
            Path(args.out),
        )
    except (FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote graph preview: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
