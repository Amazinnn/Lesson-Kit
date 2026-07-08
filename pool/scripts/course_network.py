"""Course learning network helpers for lesson-kit pool scripts."""

from __future__ import annotations

import json
import sqlite3
import sys
from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from pool_schema import table_exists


LEGACY_RELATION_TYPE = "related"
LEGACY_RELATION_DIRECTION = "symmetric"
LEGACY_RELATION_STRENGTH = "medium"


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


def chapter_prefix(course: str, chapter: str) -> str:
    return f"{course}-{chapter}"


def fetch_knowledge_nodes(
    conn: sqlite3.Connection,
    course: str,
    chapter: str,
) -> List[Dict[str, Any]]:
    prefix = chapter_prefix(course, chapter)
    graph_label_select = "graph_label" if _column_exists(conn, "knowledge_points", "graph_label") else "NULL"
    rows = conn.execute(
        f"SELECT kp_id, knowledge_item, {graph_label_select} AS graph_label, source_location, "
        "knowledge_type, related_kp_ids, importance, learning_action, body, difficulty, fragile "
        "FROM knowledge_points "
        "WHERE kp_id LIKE ? "
        "ORDER BY kp_id",
        (f"{prefix}-%",),
    ).fetchall()
    nodes: List[Dict[str, Any]] = []
    for row in rows:
        (
            kp_id,
            knowledge_item,
            graph_label,
            source_location,
            knowledge_type,
            related_raw,
            importance,
            learning_action,
            body,
            difficulty,
            fragile,
        ) = row
        nodes.append({
            "id": str(kp_id),
            "label": knowledge_item or kp_id,
            "graph_label": (str(graph_label).strip() if graph_label else "") or _fallback_graph_label(knowledge_item or "", kp_id),
            "source_location": source_location or "",
            "section": _extract_section(source_location or ""),
            "knowledge_type": knowledge_type or "",
            "importance": importance or "",
            "learning_action": learning_action or "",
            "body": body or "",
            "difficulty": difficulty or "",
            "fragile": fragile or "",
            "related": parse_json_list(related_raw, str(kp_id), "related_kp_ids"),
        })
    return nodes


def fetch_problem_counts(
    conn: sqlite3.Connection,
    course: str,
    chapter: str,
    kp_ids: Iterable[str],
) -> Dict[str, int]:
    counts = {kp_id: 0 for kp_id in kp_ids}
    if not table_exists(conn, "problems"):
        return counts
    prefix = chapter_prefix(course, chapter)
    known = set(counts)
    rows = conn.execute(
        "SELECT problem_id, kp_ids FROM problems WHERE problem_id LIKE ?",
        (f"{prefix}-%",),
    ).fetchall()
    for problem_id, raw in rows:
        for kp_id in parse_json_list(raw, str(problem_id), "kp_ids"):
            if kp_id in known:
                counts[kp_id] += 1
    return counts


def fetch_knowledge_relations(
    conn: sqlite3.Connection,
    nodes: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return formal relations when present, otherwise legacy related_kp_ids edges."""
    known = {node["id"] for node in nodes}
    if table_exists(conn, "knowledge_relations"):
        placeholders = ",".join("?" for _ in known)
        if placeholders:
            rows = conn.execute(
                "SELECT relation_id, source_kp_id, target_kp_id, relation_type, direction, strength "
                "FROM knowledge_relations "
                f"WHERE source_kp_id IN ({placeholders}) AND target_kp_id IN ({placeholders}) "
                "ORDER BY relation_id",
                tuple(sorted(known)) + tuple(sorted(known)),
            ).fetchall()
            if rows:
                return [
                    {
                        "relation_id": str(relation_id),
                        "source": str(source),
                        "target": str(target),
                        "relation_type": str(relation_type),
                        "direction": str(direction),
                        "strength": str(strength),
                        "fallback": False,
                    }
                    for relation_id, source, target, relation_type, direction, strength in rows
                ]
    return build_legacy_relations(nodes)


def build_legacy_relations(nodes: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    known = {node["id"] for node in nodes}
    seen: Set[Tuple[str, str]] = set()
    relations: List[Dict[str, Any]] = []
    for node in nodes:
        source = node["id"]
        for target in node.get("related", []):
            if target not in known:
                continue
            left, right = sorted((source, target))
            key = (left, right)
            if key in seen:
                continue
            seen.add(key)
            relations.append({
                "relation_id": f"legacy:{left}:{right}",
                "source": left,
                "target": right,
                "relation_type": LEGACY_RELATION_TYPE,
                "direction": LEGACY_RELATION_DIRECTION,
                "strength": LEGACY_RELATION_STRENGTH,
                "fallback": True,
            })
    return relations


def compute_degrees(
    nodes: Sequence[Dict[str, Any]],
    relations: Sequence[Dict[str, Any]],
) -> Dict[str, int]:
    neighbors = {node["id"]: set() for node in nodes}
    for relation in relations:
        source = relation["source"]
        target = relation["target"]
        if source in neighbors and target in neighbors:
            neighbors[source].add(target)
            neighbors[target].add(source)
    return {kp_id: len(linked) for kp_id, linked in neighbors.items()}


def build_adjacency(
    relations: Sequence[Dict[str, Any]],
    *,
    directed: bool = False,
) -> Dict[str, List[Tuple[str, Dict[str, Any]]]]:
    adjacency: Dict[str, List[Tuple[str, Dict[str, Any]]]] = defaultdict(list)
    for relation in relations:
        source = relation["source"]
        target = relation["target"]
        adjacency[source].append((target, relation))
        if not directed or relation.get("direction") == "symmetric":
            adjacency[target].append((source, relation))
    for edges in adjacency.values():
        edges.sort(key=lambda item: (item[0], item[1].get("relation_id", "")))
    return dict(adjacency)


def shortest_path(
    relations: Sequence[Dict[str, Any]],
    seed_ids: Sequence[str],
    target_id: str,
    *,
    directed: bool = False,
) -> Optional[Dict[str, Any]]:
    adjacency = build_adjacency(relations, directed=directed)
    queue = deque()
    visited: Set[str] = set()
    previous: Dict[str, Tuple[str, Dict[str, Any]]] = {}
    for seed_id in seed_ids:
        queue.append(seed_id)
        visited.add(seed_id)
        if seed_id == target_id:
            return {"start": seed_id, "target": target_id, "node_ids": [seed_id], "relation_ids": []}

    while queue:
        current = queue.popleft()
        for neighbor, relation in adjacency.get(current, []):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            previous[neighbor] = (current, relation)
            if neighbor == target_id:
                node_ids = [target_id]
                relation_ids: List[str] = []
                cursor = target_id
                while cursor not in seed_ids:
                    parent, edge = previous[cursor]
                    relation_ids.append(edge["relation_id"])
                    node_ids.append(parent)
                    cursor = parent
                node_ids.reverse()
                relation_ids.reverse()
                return {
                    "start": node_ids[0],
                    "target": target_id,
                    "node_ids": node_ids,
                    "relation_ids": relation_ids,
                }
            queue.append(neighbor)
    return None


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    if not table_exists(conn, table):
        return False
    return column in [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})")]


def _fallback_graph_label(knowledge_item: str, kp_id: str) -> str:
    text = knowledge_item.strip()
    if not text:
        return kp_id.rsplit("-", 1)[-1]
    return text


def _extract_section(source_location: str) -> str:
    import re

    match = re.search(r"(?:§|Section|Sec\.?)\s*([\w\-\.]+)", source_location, re.IGNORECASE)
    if not match:
        return "未分组"
    return f"§{match.group(1)}"
