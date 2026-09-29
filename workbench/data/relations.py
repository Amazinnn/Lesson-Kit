"""Strict knowledge-relation editing and atomic batch operations."""

from collections import Counter


RELATION_FIELDS = frozenset({
    "source_kp_id", "target_kp_id", "relation_type", "direction", "strength",
})
RELATION_TYPES = frozenset({
    "prerequisite", "part_of", "contrasts",
    "generalizes", "variant_of", "applies_to",
})
DIRECTIONS = frozenset({"directed", "symmetric"})
STRENGTHS = frozenset({"high", "medium", "low"})


def create(pool, data):
    """Create one fully validated relation."""
    with pool.transaction(immediate=True):
        conn = pool.connect()
        errors = _record_errors(conn, data, create=True)
        if not errors:
            errors.extend(_duplicate_errors(conn, data))
        if errors:
            raise ValueError("; ".join(errors))

        # Local import avoids making generic content depend on relation policy
        # during module import, while still sharing the one content-id allocator.
        from workbench.data import content

        relation_id = content.next_id(pool, "relation", conn=conn)
        conn.execute(
            "INSERT INTO knowledge_relations "
            "(relation_id, source_kp_id, target_kp_id, relation_type, direction, strength) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                relation_id,
                data["source_kp_id"],
                data["target_kp_id"],
                data["relation_type"],
                data["direction"],
                data["strength"],
            ),
        )
    return _get(pool.connect(), relation_id)


def update(pool, relation_id, patch):
    """Update one relation after validating the resulting full row."""
    if not isinstance(patch, dict):
        raise ValueError("relation update must be a JSON object")
    unknown = sorted(set(patch) - RELATION_FIELDS)
    if unknown:
        raise ValueError(_unsupported(unknown))
    if not patch:
        row = _get(pool.connect(), relation_id)
        if row is None:
            raise KeyError(relation_id)
        return row

    with pool.transaction(immediate=True):
        conn = pool.connect()
        current = _get(conn, relation_id)
        if current is None:
            raise KeyError(relation_id)
        prospective = {
            field: patch.get(field, current[field])
            for field in RELATION_FIELDS
        }
        errors = _record_errors(conn, prospective, create=True)
        if not errors:
            errors.extend(_duplicate_errors(conn, prospective, exclude_id=relation_id))
        if errors:
            raise ValueError("; ".join(errors))
        conn.execute(
            "UPDATE knowledge_relations SET "
            "source_kp_id=?, target_kp_id=?, relation_type=?, direction=?, strength=?, "
            "updated_at=datetime('now') WHERE relation_id=?",
            (
                prospective["source_kp_id"],
                prospective["target_kp_id"],
                prospective["relation_type"],
                prospective["direction"],
                prospective["strength"],
                relation_id,
            ),
        )
    return _get(pool.connect(), relation_id)


def delete(pool, relation_id):
    """Delete exactly one relation and relation-targeted learner signals."""
    with pool.transaction(immediate=True):
        conn = pool.connect()
        if _get(conn, relation_id) is None:
            raise KeyError(relation_id)
        conn.execute("DELETE FROM learner_signals WHERE target_id=?", (relation_id,))
        conn.execute("DELETE FROM knowledge_relations WHERE relation_id=?", (relation_id,))


def check(pool, manifest):
    """Validate a relation batch without writing anything."""
    result, _ = _plan(pool.connect(), manifest)
    return result


def apply(pool, manifest):
    """Validate and apply the whole relation batch in one transaction."""
    with pool.transaction(immediate=True):
        conn = pool.connect()
        result, plan = _plan(conn, manifest)
        if not result["valid"]:
            return {**result, "applied": False}

        from workbench.data import content

        output = []
        for operation in plan:
            action = operation["action"]
            index = operation["index"]
            if action == "create":
                row = operation["row"]
                relation_id = content.next_id(pool, "relation", conn=conn)
                conn.execute(
                    "INSERT INTO knowledge_relations "
                    "(relation_id, source_kp_id, target_kp_id, relation_type, direction, strength) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        relation_id,
                        row["source_kp_id"],
                        row["target_kp_id"],
                        row["relation_type"],
                        row["direction"],
                        row["strength"],
                    ),
                )
            elif action == "update":
                relation_id = operation["relation_id"]
                row = operation["row"]
                conn.execute(
                    "UPDATE knowledge_relations SET "
                    "source_kp_id=?, target_kp_id=?, relation_type=?, direction=?, strength=?, "
                    "updated_at=datetime('now') WHERE relation_id=?",
                    (
                        row["source_kp_id"],
                        row["target_kp_id"],
                        row["relation_type"],
                        row["direction"],
                        row["strength"],
                        relation_id,
                    ),
                )
            else:
                relation_id = operation["relation_id"]
                conn.execute("DELETE FROM learner_signals WHERE target_id=?", (relation_id,))
                conn.execute(
                    "DELETE FROM knowledge_relations WHERE relation_id=?", (relation_id,)
                )
            output.append({
                "index": index,
                "action": action,
                "valid": True,
                "relation_id": relation_id,
            })

        return {
            "valid": True,
            "applied": True,
            "counts": result["counts"],
            "items": output,
            "errors": [],
        }


def _plan(conn, manifest):
    if not isinstance(manifest, dict):
        return _invalid_manifest("relation batch must be a JSON object"), []
    unknown_top = sorted(set(manifest) - {"items"})
    if unknown_top:
        return _invalid_manifest(
            "unsupported batch field(s): " + ", ".join(unknown_top)
        ), []
    items = manifest.get("items")
    if not isinstance(items, list):
        return _invalid_manifest("relation batch needs an items array"), []

    current = {
        row["relation_id"]: dict(row)
        for row in conn.execute("SELECT * FROM knowledge_relations")
    }
    final = dict(current)
    origins = {}
    touched = set()
    plan = []
    errors = []
    counts = Counter()

    def add_error(index, action, message, field=None):
        error = {"index": index, "action": action, "message": message}
        if field:
            error["field"] = field
        marker = (index, action, field, message)
        if marker not in {
            (e.get("index"), e.get("action"), e.get("field"), e["message"])
            for e in errors
        }:
            errors.append(error)

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            add_error(index, None, "relation batch item must be a JSON object")
            continue
        action = item.get("action")
        if action not in {"create", "update", "delete"}:
            add_error(index, action, "action must be create, update, or delete", "action")
            continue
        counts[action] += 1

        if action == "create":
            unknown = sorted(set(item) - RELATION_FIELDS - {"action"})
            if unknown:
                add_error(index, action, _unsupported(unknown))
                continue
            row = {field: item.get(field) for field in RELATION_FIELDS}
            provisional = f"@create:{index}"
            final[provisional] = {"relation_id": provisional, **row}
            origins[provisional] = index
            plan.append({"index": index, "action": action, "row": row})
            continue

        unknown = sorted(set(item) - RELATION_FIELDS - {"action", "relation_id"})
        if action == "delete":
            unknown = sorted(set(item) - {"action", "relation_id"})
        if unknown:
            add_error(index, action, _unsupported(unknown))
            continue
        relation_id = item.get("relation_id")
        if not isinstance(relation_id, str) or not relation_id:
            add_error(index, action, "relation_id is required", "relation_id")
            continue
        if relation_id in touched:
            add_error(
                index, action,
                f"relation {relation_id} is changed more than once in this batch",
                "relation_id",
            )
            continue
        touched.add(relation_id)
        if relation_id not in current:
            add_error(index, action, f"unknown relation: {relation_id}", "relation_id")
            continue

        if action == "delete":
            final.pop(relation_id, None)
            plan.append({
                "index": index, "action": action, "relation_id": relation_id,
            })
            continue

        patch = {field: item[field] for field in RELATION_FIELDS if field in item}
        row = {
            field: patch.get(field, current[relation_id][field])
            for field in RELATION_FIELDS
        }
        final[relation_id] = {**current[relation_id], **row}
        origins[relation_id] = index
        plan.append({
            "index": index,
            "action": action,
            "relation_id": relation_id,
            "row": row,
        })

    kp_ids = {
        row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points")
    }
    changed_ids = set(origins)
    rows = list(final.values())

    for relation_id in changed_ids:
        row = final.get(relation_id)
        if row is None:
            continue
        index = origins[relation_id]
        action = "create" if relation_id.startswith("@create:") else "update"
        for message, field in _row_errors(row, kp_ids):
            add_error(index, action, message, field)

    for relation_id in changed_ids:
        row = final.get(relation_id)
        if row is None:
            continue
        index = origins[relation_id]
        action = "create" if relation_id.startswith("@create:") else "update"
        for other in rows:
            other_id = other["relation_id"]
            if other_id == relation_id:
                continue
            if _same_relation(row, other) or _symmetric_reverse(row, other):
                add_error(
                    index, action,
                    f"duplicate relation with {other_id}",
                    "relation_type",
                )

    invalid_indexes = {error["index"] for error in errors if error["index"] is not None}
    item_results = []
    for index, item in enumerate(items):
        action = item.get("action") if isinstance(item, dict) else None
        item_results.append({
            "index": index,
            "action": action,
            "valid": index not in invalid_indexes,
        })

    result = {
        "valid": not errors,
        "counts": {
            "create": counts["create"],
            "update": counts["update"],
            "delete": counts["delete"],
        },
        "items": item_results,
        "errors": errors,
    }
    return result, plan


def _record_errors(conn, data, create):
    if not isinstance(data, dict):
        return ["relation must be a JSON object"]
    unknown = sorted(set(data) - RELATION_FIELDS)
    if unknown:
        return [_unsupported(unknown)]
    if create:
        missing = sorted(field for field in RELATION_FIELDS if field not in data)
        if missing:
            return ["missing required field(s): " + ", ".join(missing)]
    kp_ids = {row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points")}
    return [message for message, _field in _row_errors(data, kp_ids)]


def _row_errors(row, kp_ids):
    errors = []
    source = row.get("source_kp_id")
    target = row.get("target_kp_id")
    if not isinstance(source, str) or not source:
        errors.append(("source_kp_id is required", "source_kp_id"))
    elif source not in kp_ids:
        errors.append((f"unknown source knowledge point: {source}", "source_kp_id"))
    if not isinstance(target, str) or not target:
        errors.append(("target_kp_id is required", "target_kp_id"))
    elif target not in kp_ids:
        errors.append((f"unknown target knowledge point: {target}", "target_kp_id"))
    if source and target and source == target:
        errors.append((f"relation cannot point to itself: {source}", "target_kp_id"))
    if row.get("relation_type") not in RELATION_TYPES:
        errors.append((
            "relation_type must be one of: " + ", ".join(sorted(RELATION_TYPES)),
            "relation_type",
        ))
    if row.get("direction") not in DIRECTIONS:
        errors.append(("direction must be directed or symmetric", "direction"))
    if row.get("strength") not in STRENGTHS:
        errors.append(("strength must be high, medium, or low", "strength"))
    return errors


def _duplicate_errors(conn, row, exclude_id=None):
    errors = []
    for other_row in conn.execute("SELECT * FROM knowledge_relations"):
        other = dict(other_row)
        if other["relation_id"] == exclude_id:
            continue
        if _same_relation(row, other) or _symmetric_reverse(row, other):
            errors.append(f"duplicate relation with {other['relation_id']}")
    return errors


def _same_relation(left, right):
    return (
        left.get("source_kp_id") == right.get("source_kp_id")
        and left.get("target_kp_id") == right.get("target_kp_id")
        and left.get("relation_type") == right.get("relation_type")
    )


def _symmetric_reverse(left, right):
    return (
        left.get("direction") == "symmetric"
        and right.get("direction") == "symmetric"
        and left.get("relation_type") == right.get("relation_type")
        and left.get("source_kp_id") == right.get("target_kp_id")
        and left.get("target_kp_id") == right.get("source_kp_id")
    )


def _get(conn, relation_id):
    row = conn.execute(
        "SELECT * FROM knowledge_relations WHERE relation_id=?", (relation_id,)
    ).fetchone()
    return dict(row) if row else None


def _unsupported(fields):
    return (
        f"unsupported relation field(s) {fields} — writable fields: "
        + ", ".join(sorted(RELATION_FIELDS))
    )


def _invalid_manifest(message):
    return {
        "valid": False,
        "counts": {"create": 0, "update": 0, "delete": 0},
        "items": [],
        "errors": [{"index": None, "action": None, "message": message}],
    }
