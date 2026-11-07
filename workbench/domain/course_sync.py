"""Pure three-way comparison of portable course asset projections."""

from copy import deepcopy


def _equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _equal(value, right[key]) for key, value in left.items()
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(map(_equal, left, right))
    return left == right


def _semantic(asset):
    return {"kind": asset["kind"], "content": asset.get("content"),
            "depends_on": sorted(set(asset.get("depends_on", []))),
            "deleted": asset.get("deleted", False)}


def _valid(asset):
    return (isinstance(asset, dict)
            and isinstance(asset.get("kind"), str) and bool(asset["kind"])
            and isinstance(asset.get("deleted", False), bool)
            and ("content" in asset or asset.get("deleted") is True)
            and isinstance(asset.get("depends_on", []), list)
            and all(isinstance(item, str) and item for item in asset.get("depends_on", [])))


def _mutation(identity, selected, previous):
    action = "update"
    if selected.get("deleted"):
        action = "delete"
    elif previous is None or previous.get("deleted"):
        action = "create"
    return {"identity": identity, "action": action, "asset": deepcopy(selected)}


def _validate_dependencies(changes, destination, blocked, error, side):
    """Reject incomplete connected mutations without rejecting independent ones."""
    pending = {item["identity"]: item for item in changes}
    while pending:
        target = dict(destination)
        target.update({key: item["asset"] for key, item in pending.items()})
        rejected = set()
        for key, asset in sorted(target.items()):
            if not _valid(asset) or asset.get("deleted"):
                continue
            for dependency in asset.get("depends_on", []):
                endpoint = target.get(dependency)
                if dependency in blocked or not _valid(endpoint) or endpoint.get("deleted"):
                    # An unchanged live dependent also prevents deleting its target.
                    culprit = key if key in pending else dependency
                    if culprit in pending:
                        rejected.add(culprit)
                        error(culprit, "invalid_dependency",
                              f"{side}: {key} depends on unavailable asset {dependency}")
        if not rejected:
            break
        blocked.update(rejected)
        for key in rejected:
            del pending[key]
    return [pending[key] for key in sorted(pending)]


def plan_exchange(base, local, incoming):
    """Plan both directions, retaining explicit conflicts and incomplete assets.

    Keys carry persistent source identities. Each draft question and immutable
    history record is a separate key, so ordinary set comparison preserves
    independent edits without numeric-id or timestamp heuristics.
    """
    if not all(isinstance(value, dict) for value in (base, local, incoming)):
        raise ValueError("base, local and incoming must be asset maps")
    identities = set(base) | set(local) | set(incoming)
    if not all(isinstance(key, str) and key for key in identities):
        raise ValueError("asset identities must be non-empty strings")
    result = {"changes": [], "outgoing": [], "conflicts": [], "errors": [], "unchanged": []}
    blocked = set()
    reported = set()

    def error(identity, code, message):
        marker = (identity, code, message)
        if marker not in reported:
            reported.add(marker)
            result["errors"].append({"identity": identity, "code": code, "message": message})

    for identity in sorted(identities):
        ancestor, here, there = (projection.get(identity) for projection in (base, local, incoming))
        present = [projection[identity] for projection in (base, local, incoming)
                   if identity in projection]
        if not all(_valid(value) for value in present):
            error(identity, "invalid_asset", "asset envelope is invalid")
            blocked.add(identity)
            continue
        if identity in base and (identity not in local or identity not in incoming):
            error(identity, "missing_asset", "tracked asset is absent without an explicit deletion")
            blocked.add(identity)
            continue
        if here is None:
            result["changes"].append(_mutation(identity, there, None))
        elif there is None:
            result["outgoing"].append(_mutation(identity, here, None))
        elif _equal(_semantic(here), _semantic(there)):
            result["unchanged"].append(identity)
        elif ancestor is not None and _equal(_semantic(here), _semantic(ancestor)):
            result["changes"].append(_mutation(identity, there, here))
        elif ancestor is not None and _equal(_semantic(there), _semantic(ancestor)):
            result["outgoing"].append(_mutation(identity, here, there))
        else:
            result["conflicts"].append({"identity": identity, "base": deepcopy(ancestor),
                                        "local": deepcopy(here), "incoming": deepcopy(there)})
            blocked.add(identity)
    # Each direction has its own target. An error in one does not invalidate a
    # compatible independent update in the other direction.
    result["changes"] = _validate_dependencies(
        result["changes"], local, set(blocked), error, "local")
    result["outgoing"] = _validate_dependencies(
        result["outgoing"], incoming, set(blocked), error, "incoming")
    result["errors"].sort(key=lambda item: (item["identity"], item["code"], item["message"]))
    return result
