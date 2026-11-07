"""Grouped JSON layout for course exchange packages.

Version 1 keeps one envelope per physical file. Version 2 groups envelopes into
bounded files so a full-size export touches far fewer paths. Both layouts carry
the same identities and envelopes; the layout follows the asset count, never a
failure.

``pack`` only chooses the layout and returns the JSON values to publish; the
caller writes them before replacing the manifest. ``load`` reads through the
layout declared by the manifest and never writes or extracts anything.
"""

import json
from pathlib import Path

FORMAT_VERSION_INDIVIDUAL = 1
FORMAT_VERSION_GROUPED = 2
INDIVIDUAL_LIMIT = 512
GROUP_MEMBERS = 256
GROUP_BYTES = 8 * 1024 * 1024


def pack(assets, export_id, previous_manifest=None, previous_assets=None):
    """Return the descriptors and physical files for one export projection.

    ``files`` maps a physical relative JSON path to its JSON value. ``written``
    and ``reused`` count assets, not physical files. A caller that passes
    ``previous_manifest`` and ``previous_assets`` must have loaded that manifest
    first: reuse copies its descriptors verbatim, so an inconsistent one would be
    carried forward rather than repaired here.
    """
    identities = sorted(assets)
    previous_manifest = previous_manifest if isinstance(previous_manifest, dict) else {}
    previous_assets = previous_assets if isinstance(previous_assets, dict) else {}
    if len(identities) <= INDIVIDUAL_LIMIT:
        return _pack_individual(assets, identities, export_id,
                                previous_manifest, previous_assets)
    return _pack_grouped(assets, identities, export_id, previous_manifest, previous_assets)


def load(source, descriptors, version, relative, read_json):
    """Read every declared envelope, caching each physical file once.

    ``relative(root, name)`` validates a safe relative path and ``read_json``
    reads one UTF-8 JSON file. Malformed manifests raise ``ValueError``; missing
    or unreadable files become per-identity ``missing_asset``/``invalid_asset``
    errors so independent files still load.
    """
    if type(version) is not int or version not in {FORMAT_VERSION_INDIVIDUAL,
                                                   FORMAT_VERSION_GROUPED}:
        raise ValueError("unsupported course exchange format_version")
    if not isinstance(descriptors, list):
        raise ValueError("invalid asset descriptors")
    root = Path(source).resolve()
    declared, identities, physical = [], set(), {}
    for descriptor in descriptors:
        if not isinstance(descriptor, dict) or not isinstance(descriptor.get("identity"), str):
            raise ValueError("invalid asset descriptor")
        identity = descriptor["identity"]
        if not identity or identity in identities:
            raise ValueError("duplicate or empty asset identity")
        if version == FORMAT_VERSION_GROUPED and descriptor.get("member") != identity:
            raise ValueError("invalid grouped asset member")
        identities.add(identity)
        target = relative(root, descriptor.get("path"))
        normalized = target.relative_to(root).as_posix()
        key = normalized.casefold()
        if key in physical and (version == FORMAT_VERSION_INDIVIDUAL
                                or physical[key] != normalized):
            raise ValueError("duplicate asset path")
        physical[key] = normalized
        declared.append((identity, normalized, target))
    if version == FORMAT_VERSION_INDIVIDUAL:
        return _read_individual(declared, read_json)
    return _read_grouped(declared, read_json)


def _descriptor(asset, identity, path, member=None):
    descriptor = {"identity": identity, "kind": asset.get("kind"), "path": path,
                  "depends_on": asset.get("depends_on", [])}
    if member is not None:
        descriptor["member"] = member
    return descriptor


def _pack_individual(assets, identities, export_id, previous_manifest, previous_assets):
    reusable = {}
    if previous_manifest.get("format_version") == FORMAT_VERSION_INDIVIDUAL:
        for descriptor in previous_manifest.get("assets") or ():
            if isinstance(descriptor, dict) and isinstance(descriptor.get("path"), str):
                reusable[descriptor.get("identity")] = descriptor["path"]
    descriptors, files = [], {}
    for number, identity in enumerate(identities, 1):
        asset = assets[identity]
        path = reusable.get(identity)
        if path is None or previous_assets.get(identity) != asset:
            path = f"{export_id}/assets/{number:06d}.json"
            files[path] = asset
        descriptors.append(_descriptor(asset, identity, path))
    written = len(files)
    return {"format_version": FORMAT_VERSION_INDIVIDUAL, "descriptors": descriptors,
            "files": files, "written": written, "reused": len(identities) - written}


def _pack_grouped(assets, identities, export_id, previous_manifest, previous_assets):
    previous_descriptors = previous_manifest.get("assets")
    if previous_manifest.get("format_version") == FORMAT_VERSION_GROUPED \
            and previous_assets == assets and isinstance(previous_descriptors, list) \
            and len(previous_descriptors) == len(identities) \
            and all(isinstance(item, dict) for item in previous_descriptors):
        return {"format_version": FORMAT_VERSION_GROUPED,
                "descriptors": [dict(item) for item in previous_descriptors],
                "files": {}, "written": 0, "reused": len(identities)}
    descriptors, files = [], {}
    for number, members in enumerate(_group_members(assets, identities), 1):
        path = f"{export_id}/assets/{number:06d}.json"
        files[path] = {"assets": {identity: assets[identity] for identity in members}}
        descriptors.extend(_descriptor(assets[identity], identity, path, identity)
                           for identity in members)
    return {"format_version": FORMAT_VERSION_GROUPED, "descriptors": descriptors,
            "files": files, "written": len(identities), "reused": 0}


def _size(value):
    """Serialized UTF-8 byte length of one JSON value in this codec's encoding."""
    return len(json.dumps(value, ensure_ascii=False).encode("utf-8"))


def _group_members(assets, identities):
    """Split sorted identities into bounded groups, keeping a huge envelope whole."""
    base = _size({"assets": {}})
    groups, current, size = [], [], base
    for identity in identities:
        entry = _size(identity) + 2 + _size(assets[identity])
        if current and (len(current) >= GROUP_MEMBERS or size + 2 + entry > GROUP_BYTES):
            groups.append(current)
            current, size = [], base
        size += entry + (2 if current else 0)
        current.append(identity)
    groups.append(current)
    return groups


def _errors(members, code, message):
    return [{"identity": identity, "code": code, "message": message} for identity in members]


def _read_individual(declared, read_json):
    assets, errors = {}, []
    for identity, _, target in sorted(declared):
        if not target.is_file():
            errors += _errors([identity], "missing_asset", "asset file is absent")
            continue
        try:
            assets[identity] = read_json(target)
        except (ValueError, OSError) as exc:
            errors += _errors([identity], "invalid_asset", str(exc))
    return assets, errors


def _read_grouped(declared, read_json):
    groups = {}
    for identity, normalized, target in sorted(declared):
        groups.setdefault((normalized, target), []).append(identity)
    assets, errors = {}, []
    for (_, target), members in groups.items():
        if not target.is_file():
            errors += _errors(members, "missing_asset", "asset group file is absent")
            continue
        try:
            group = read_json(target)
        except (ValueError, OSError) as exc:
            errors += _errors(members, "invalid_asset", str(exc))
            continue
        if not isinstance(group, dict) or set(group) != {"assets"} \
                or not isinstance(group["assets"], dict) \
                or set(group["assets"]) != set(members):
            errors += _errors(members, "invalid_asset",
                              "grouped asset file does not match its descriptors")
            continue
        for identity in members:
            assets[identity] = group["assets"][identity]
    return assets, errors
