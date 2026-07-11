#!/usr/bin/env python3
"""Build a focused Course Learning Network JSON packet.

The Focus Map is a query result, not a new source of truth. Low-level audited
relations live in knowledge_relations; this script derives higher-level
context such as local neighborhoods, shared neighbors, and shortest paths.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from course_network import (  # noqa: E402
    build_adjacency,
    compute_degrees,
    fetch_knowledge_nodes,
    fetch_knowledge_relations,
    fetch_problem_counts,
    shortest_path,
)
from pool_schema import table_exists  # noqa: E402
from learner_signals import fetch_learner_signals  # noqa: E402


SIGNAL_TYPES = (
    "weak_node",
    "confusion",
    "missing_prerequisite",
    "transfer_failure",
    "relation_gap",
)
SIGNAL_WEIGHTS = {"low": 1, "medium": 2, "high": 3}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query a focused Course Learning Network subgraph as JSON.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    parser.add_argument("--course", required=True, help="Course prefix, e.g. dmath.")
    parser.add_argument("--chapter", required=True, help="Chapter code, e.g. ch06.")
    parser.add_argument(
        "--seed",
        action="append",
        required=True,
        help="Seed KP id. Repeat or comma-separate for multiple seeds.",
    )
    parser.add_argument("--target", help="Optional target KP id for shortest-path search.")
    parser.add_argument("--depth", type=int, default=2, help="BFS depth from seed nodes.")
    parser.add_argument("--max-nodes", type=int, default=30, help="Maximum nodes in output.")
    parser.add_argument("--signals", help="Optional signal-map JSON file.")
    parser.add_argument(
        "--directed",
        action="store_true",
        help="Respect directed relation orientation during traversal.",
    )
    return parser.parse_args(argv)


def expand_ids(values: Optional[Sequence[str]]) -> List[str]:
    ids: List[str] = []
    for raw in values or []:
        for item in str(raw).split(","):
            item = item.strip()
            if item and item not in ids:
                ids.append(item)
    return ids


def load_signal_map(path: Optional[str]) -> List[Dict[str, Any]]:
    if not path:
        return []
    with open(path, "r", encoding="utf-8-sig") as handle:
        raw = json.load(handle)
    rows = raw.get("signals", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise ValueError("signal map must be a list or an object with signals[]")

    signals: List[Dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"signal #{index} must be an object")
        target_type = str(row.get("target_type", "node")).strip() or "node"
        target_id = str(row.get("target_id", "")).strip()
        signal_type = str(row.get("signal_type", "")).strip()
        weight = str(row.get("weight", "medium")).strip() or "medium"
        if target_type not in ("node", "relation"):
            raise ValueError(f"signal #{index}: target_type must be node or relation")
        if not target_id:
            raise ValueError(f"signal #{index}: target_id is required")
        if signal_type not in SIGNAL_TYPES:
            raise ValueError(f"signal #{index}: unsupported signal_type '{signal_type}'")
        if weight not in SIGNAL_WEIGHTS:
            raise ValueError(f"signal #{index}: unsupported weight '{weight}'")
        signals.append({
            "signal_id": str(row.get("signal_id") or f"signal:{index:03d}"),
            "target_type": target_type,
            "target_id": target_id,
            "signal_type": signal_type,
            "weight": weight,
            "note": str(row.get("note", "") or ""),
            "source": str(row.get("source", "") or ""),
        })
    return signals


def fetch_kp_progress(
    conn: sqlite3.Connection,
    kp_ids: Iterable[str],
) -> Dict[str, str]:
    ids = sorted(set(kp_ids))
    if not ids or not table_exists(conn, "kp_progress"):
        return {}
    placeholders = ",".join("?" for _ in ids)
    try:
        rows = conn.execute(
            f"SELECT kp_id, mastery_state FROM kp_progress WHERE kp_id IN ({placeholders})",
            tuple(ids),
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    return {str(kp_id): str(state or "") for kp_id, state in rows}


def fetch_problem_state_counts(
    conn: sqlite3.Connection,
    course: str,
    chapter: str,
    kp_ids: Iterable[str],
) -> Dict[str, Dict[str, int]]:
    ids = sorted(set(kp_ids))
    counts = {
        kp_id: {"new": 0, "wrong": 0, "stuck": 0, "reviewing": 0, "mastered": 0}
        for kp_id in ids
    }
    if not ids or not table_exists(conn, "problems") or not table_exists(conn, "problem_progress"):
        return counts

    prefix = f"{course}-{chapter}"
    try:
        rows = conn.execute(
            "SELECT p.problem_id, p.kp_ids, COALESCE(pp.status, 'new') "
            "FROM problems p "
            "LEFT JOIN problem_progress pp ON pp.problem_id = p.problem_id "
            "WHERE p.problem_id LIKE ?",
            (f"{prefix}-%",),
        ).fetchall()
    except sqlite3.OperationalError:
        return counts

    known = set(counts)
    for _problem_id, raw_kp_ids, status in rows:
        try:
            linked = json.loads(raw_kp_ids or "[]")
        except json.JSONDecodeError:
            linked = []
        status = str(status or "new")
        if status not in counts[ids[0]]:
            status = "new"
        for kp_id in linked:
            kp_id = str(kp_id)
            if kp_id in known:
                counts[kp_id][status] += 1
    return counts


def bfs_distances(
    adjacency: Dict[str, List[Tuple[str, Dict[str, Any]]]],
    seeds: Sequence[str],
    depth: int,
) -> Dict[str, int]:
    distances: Dict[str, int] = {}
    queue = deque()
    for seed in seeds:
        distances[seed] = 0
        queue.append(seed)
    while queue:
        current = queue.popleft()
        if distances[current] >= depth:
            continue
        for neighbor, _relation in adjacency.get(current, []):
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return distances


def shared_neighbors(
    adjacency: Dict[str, List[Tuple[str, Dict[str, Any]]]],
    seeds: Sequence[str],
) -> List[Dict[str, Any]]:
    if len(seeds) < 2:
        return []
    seed_set = set(seeds)
    seen_by: Dict[str, Set[str]] = defaultdict(set)
    relation_ids: Dict[str, Set[str]] = defaultdict(set)
    for seed in seeds:
        for neighbor, relation in adjacency.get(seed, []):
            if neighbor in seed_set:
                continue
            seen_by[neighbor].add(seed)
            relation_ids[neighbor].add(str(relation.get("relation_id", "")))
    rows = []
    for node_id, linked_seeds in seen_by.items():
        if len(linked_seeds) >= 2:
            rows.append({
                "node_id": node_id,
                "seed_ids": sorted(linked_seeds),
                "relation_ids": sorted(item for item in relation_ids[node_id] if item),
            })
    rows.sort(key=lambda row: (-len(row["seed_ids"]), row["node_id"]))
    return rows


def build_clusters(nodes: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by_section: Dict[str, List[str]] = defaultdict(list)
    by_type: Dict[str, List[str]] = defaultdict(list)
    for node in nodes:
        by_section[str(node.get("section") or "未分组")].append(node["id"])
        by_type[str(node.get("knowledge_type") or "unknown")].append(node["id"])
    return {
        "by_section": _cluster_rows(by_section),
        "by_type": _cluster_rows(by_type),
    }


def _cluster_rows(groups: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    return [
        {"name": name, "count": len(ids), "node_ids": sorted(ids)}
        for name, ids in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    ]


def normalize_signal_targets(
    signals: Sequence[Dict[str, Any]],
    relation_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]], Set[str]]:
    node_signals: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    relation_signals: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    signal_nodes: Set[str] = set()
    for signal in signals:
        if signal["target_type"] == "node":
            node_signals[signal["target_id"]].append(signal)
            signal_nodes.add(signal["target_id"])
            continue
        relation = relation_by_id.get(signal["target_id"])
        relation_signals[signal["target_id"]].append(signal)
        if relation:
            signal_nodes.add(relation["source"])
            signal_nodes.add(relation["target"])
    return dict(node_signals), dict(relation_signals), signal_nodes


def relation_endpoints(relations: Sequence[Dict[str, Any]], relation_ids: Set[str]) -> Set[str]:
    nodes: Set[str] = set()
    for relation in relations:
        if relation.get("relation_id") in relation_ids:
            nodes.add(relation["source"])
            nodes.add(relation["target"])
    return nodes


def crop_nodes(
    candidate_ids: Set[str],
    required_ids: Set[str],
    *,
    node_by_id: Dict[str, Dict[str, Any]],
    degrees: Dict[str, int],
    problem_counts: Dict[str, int],
    distances: Dict[str, int],
    node_signals: Dict[str, List[Dict[str, Any]]],
    max_nodes: int,
) -> Tuple[Set[str], List[str]]:
    max_nodes = max(max_nodes, len(required_ids), 1)
    if len(candidate_ids) <= max_nodes:
        return set(candidate_ids), []

    def score(node_id: str) -> Tuple[int, int, int, int, str]:
        signal_score = sum(SIGNAL_WEIGHTS.get(sig["weight"], 2) for sig in node_signals.get(node_id, []))
        distance_score = 100 - distances[node_id] * 12 if node_id in distances else 0
        required_score = 10000 if node_id in required_ids else 0
        return (
            required_score + distance_score + signal_score * 50 + degrees.get(node_id, 0) * 8 + problem_counts.get(node_id, 0) * 3,
            -distances.get(node_id, 99),
            degrees.get(node_id, 0),
            problem_counts.get(node_id, 0),
            node_by_id[node_id].get("graph_label", node_id),
        )

    selected = set(required_ids)
    ranked = sorted(
        (node_id for node_id in candidate_ids if node_id in node_by_id and node_id not in selected),
        key=score,
        reverse=True,
    )
    selected.update(ranked[: max_nodes - len(selected)])
    truncated = sorted(candidate_ids - selected)
    return selected, truncated


def build_findings(
    *,
    target_id: Optional[str],
    path: Optional[Dict[str, Any]],
    shared: Sequence[Dict[str, Any]],
    truncated: Sequence[str],
    selected_nodes: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    if target_id:
        if path:
            findings.append({
                "type": "path_found",
                "severity": "info",
                "node_ids": path["node_ids"],
                "relation_ids": path["relation_ids"],
            })
            bridge_nodes = path["node_ids"][1:-1]
            if bridge_nodes:
                findings.append({
                    "type": "bridge_nodes",
                    "severity": "info",
                    "node_ids": bridge_nodes,
                })
        else:
            findings.append({
                "type": "path_missing",
                "severity": "warning",
                "target_id": target_id,
            })
    if shared:
        findings.append({
            "type": "shared_neighbors",
            "severity": "info",
            "items": list(shared),
        })
    if selected_nodes:
        section_counts = Counter(node.get("section") or "未分组" for node in selected_nodes)
        section, count = section_counts.most_common(1)[0]
        if count >= 2:
            findings.append({
                "type": "dense_section",
                "severity": "info",
                "section": section,
                "count": count,
            })
    if truncated:
        findings.append({
            "type": "truncated_context",
            "severity": "notice",
            "omitted_node_ids": list(truncated),
        })
    return findings


def build_focus_map(
    conn: sqlite3.Connection,
    *,
    course: str,
    chapter: str,
    seed_ids: Sequence[str],
    target_id: Optional[str] = None,
    depth: int = 2,
    max_nodes: int = 30,
    signals: Optional[Sequence[Dict[str, Any]]] = None,
    directed: bool = False,
) -> Dict[str, Any]:
    depth = max(0, depth)
    nodes = fetch_knowledge_nodes(conn, course, chapter)
    node_by_id = {node["id"]: node for node in nodes}
    missing_seeds = [seed for seed in seed_ids if seed not in node_by_id]
    if missing_seeds:
        raise ValueError(f"seed KP not found in chapter scope: {', '.join(missing_seeds)}")
    if target_id and target_id not in node_by_id:
        raise ValueError(f"target KP not found in chapter scope: {target_id}")

    relations = fetch_knowledge_relations(conn, nodes)
    relation_by_id = {str(relation["relation_id"]): relation for relation in relations}
    adjacency = build_adjacency(relations, directed=directed)
    degrees = compute_degrees(nodes, relations)
    problem_counts = fetch_problem_counts(conn, course, chapter, node_by_id)
    problem_state_counts = fetch_problem_state_counts(conn, course, chapter, node_by_id)
    kp_progress = fetch_kp_progress(conn, node_by_id)
    loaded_signals = (
        fetch_learner_signals(conn, course, chapter)
        if signals is None
        else list(signals)
    )
    node_signals, relation_signals, signal_nodes = normalize_signal_targets(loaded_signals, relation_by_id)

    distances = bfs_distances(adjacency, seed_ids, depth)
    path = shortest_path(relations, seed_ids, target_id, directed=directed) if target_id else None
    shared = shared_neighbors(adjacency, seed_ids)

    candidate_ids = set(distances)
    candidate_ids.update(row["node_id"] for row in shared if row["node_id"] in node_by_id)
    candidate_ids.update(node_id for node_id in signal_nodes if node_id in node_by_id)
    required_ids = set(seed_ids)
    if target_id:
        required_ids.add(target_id)
    if path:
        candidate_ids.update(path["node_ids"])
        required_ids.update(path["node_ids"])
        candidate_ids.update(relation_endpoints(relations, set(path["relation_ids"])))
    candidate_ids.update(required_ids)

    selected_ids, truncated = crop_nodes(
        candidate_ids,
        required_ids,
        node_by_id=node_by_id,
        degrees=degrees,
        problem_counts=problem_counts,
        distances=distances,
        node_signals=node_signals,
        max_nodes=max_nodes,
    )
    selected_relations = [
        relation
        for relation in relations
        if relation["source"] in selected_ids and relation["target"] in selected_ids
    ]
    path_relation_ids = set(path["relation_ids"]) if path else set()

    output_nodes: List[Dict[str, Any]] = []
    for node_id in sorted(selected_ids):
        node = node_by_id[node_id]
        output_nodes.append({
            "id": node_id,
            "label": node["label"],
            "graph_label": node["graph_label"],
            "section": node["section"],
            "knowledge_type": node["knowledge_type"],
            "importance": node["importance"],
            "learning_action": node["learning_action"],
            "body": node["body"],
            "difficulty": node["difficulty"],
            "fragile": node["fragile"],
            "degree": degrees.get(node_id, 0),
            "distance": distances.get(node_id),
            "problem_count": problem_counts.get(node_id, 0),
            "problem_states": problem_state_counts.get(node_id, {}),
            "kp_state": kp_progress.get(node_id, ""),
            "is_seed": node_id in seed_ids,
            "is_target": node_id == target_id,
            "on_path": bool(path and node_id in path["node_ids"]),
            "signals": node_signals.get(node_id, []),
        })

    output_relations = []
    for relation in selected_relations:
        relation_id = str(relation["relation_id"])
        output_relations.append({
            "relation_id": relation_id,
            "source": relation["source"],
            "target": relation["target"],
            "relation_type": relation["relation_type"],
            "direction": relation["direction"],
            "strength": relation["strength"],
            "fallback": bool(relation.get("fallback", False)),
            "on_path": relation_id in path_relation_ids,
            "signals": relation_signals.get(relation_id, []),
        })

    return {
        "meta": {
            "course": course,
            "chapter": chapter,
            "view": "focus-map",
            "node_count": len(output_nodes),
            "relation_count": len(output_relations),
            "total_chapter_nodes": len(nodes),
            "total_chapter_relations": len(relations),
            "uses_formal_relations": any(not relation.get("fallback", False) for relation in relations),
            "directed": directed,
        },
        "query": {
            "seed_ids": list(seed_ids),
            "target_id": target_id,
            "depth": depth,
            "max_nodes": max_nodes,
        },
        "nodes": output_nodes,
        "relations": output_relations,
        "paths": [path] if path else [],
        "clusters": build_clusters(output_nodes),
        "findings": build_findings(
            target_id=target_id,
            path=path,
            shared=shared,
            truncated=truncated,
            selected_nodes=output_nodes,
        ),
        "signals": [
            signal
            for signal in loaded_signals
            if (
                signal["target_type"] == "node"
                and signal["target_id"] in selected_ids
            ) or (
                signal["target_type"] == "relation"
                and signal["target_id"] in {relation["relation_id"] for relation in output_relations}
            )
        ],
        "truncated": {
            "node_ids": truncated,
        },
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if not os.path.isfile(args.db):
        print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
        return 1
    seed_ids = expand_ids(args.seed)
    if not seed_ids:
        print("ERROR: at least one --seed is required", file=sys.stderr)
        return 1
    try:
        signals = load_signal_map(args.signals) if args.signals else None
        conn = sqlite3.connect(args.db)
        try:
            packet = build_focus_map(
                conn,
                course=args.course,
                chapter=args.chapter,
                seed_ids=seed_ids,
                target_id=args.target,
                depth=args.depth,
                max_nodes=args.max_nodes,
                signals=signals,
                directed=args.directed,
            )
        finally:
            conn.close()
    except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(packet, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
