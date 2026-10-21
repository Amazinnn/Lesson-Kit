"""Workspace filesystem layout and explicit, reversible directory relocation."""

import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit

from workbench import registry


OWNED_DIRECTORIES = ("pool", "intermediate")
_REFERENCE = re.compile(r'^ {0,3}\[[^\]\r\n]+\]:[ \t]*(<[^>\r\n]+>|(?:\\.|[^\\\s])+)', re.MULTILINE)


def _rewrite_inline_links(text, rewrite):
    """Scan one non-code line segment, balancing bare destination parentheses."""
    parts, previous = [], 0
    for match in re.finditer(r"\]\([ \t]*", text):
        if match.start() < previous:
            continue
        start = end = match.end()
        depth = 0
        if text[start:start + 1] == "<":
            closing = text.find(">", start + 1)
            if closing < 0:
                continue
            end = closing + 1
        else:
            while end < len(text):
                char = text[end]
                if char == "\\":
                    end += 2
                    continue
                if char == "(":
                    depth += 1
                elif char == ")":
                    if depth == 0:
                        break
                    depth -= 1
                elif char.isspace():
                    break
                end += 1
        following = text[end:].lstrip(" \t")
        if depth or end == start or not following or following[0] not in ")\"'":
            continue
        parts.extend((text[previous:start], rewrite(text[start:end])))
        previous = end
    parts.append(text[previous:])
    return "".join(parts)


def _relocated(path, moves):
    for source, target in moves:
        if path.is_relative_to(source):
            return target / path.relative_to(source)
    return path


def _markdown_changes(moves):
    """Rebase actual local link targets, preserving all surrounding bytes."""
    changes = []
    for source, destination in moves:
        for path in source.rglob("*.md"):
            before = path.read_bytes()
            try:
                text = before.decode("utf-8")
            except UnicodeDecodeError:
                continue
            relocated = destination / path.relative_to(source)
            targets = []

            def replace(token):
                angle = token.startswith("<")
                raw = token[1:-1] if angle else token
                decoded = re.sub(r"\\([ !\"#$%&'()*+,\-./:;<=>?@\[\]^_`{|}~])", r"\1", raw)
                if re.match(r"(?:[a-zA-Z][\w+.-]*:|//|#)", decoded):
                    return token
                url = urlsplit(decoded)
                if url.scheme or url.netloc or not url.path or Path(unquote(url.path)).is_absolute():
                    return token
                old_target = (path.parent / unquote(url.path)).resolve()
                if not old_target.exists():
                    return token
                new_target = _relocated(old_target, moves)
                if (relocated.parent / unquote(url.path)).resolve() == new_target:
                    return token
                # Rebase the original spelling as well, retaining escapes/Unicode.
                prefix = Path(os.path.relpath(new_target, relocated.parent)).as_posix()
                old_parts = unquote(url.path).replace("\\", "/").split("/")
                new_parts = prefix.split("/")
                while old_parts and new_parts and old_parts[-1] == new_parts[-1]:
                    old_parts.pop()
                    new_parts.pop()
                suffix_count = len(prefix.split("/")) - len(new_parts)
                raw_parts = raw.split("#", 1)[0].split("?", 1)[0].split("/")
                new_path = "/".join(new_parts + (raw_parts[-suffix_count:] if suffix_count else []))
                ending = raw[len(raw.split("#", 1)[0].split("?", 1)[0]):]
                replacement = new_path + ending
                if angle:
                    replacement = "<" + replacement + ">"
                targets.append({"before": token, "after": replacement})
                return replacement

            lines = []
            fence = None
            for line in text.splitlines(keepends=True):
                marker = re.match(r" {0,3}(`{3,}|~{3,})", line)
                if marker:
                    mark = marker.group(1)
                    if fence is None:
                        fence = mark
                    elif mark[0] == fence[0] and len(mark) >= len(fence):
                        fence = None
                    lines.append(line)
                elif fence:
                    lines.append(line)
                else:
                    # Code spans are examples, not navigable Markdown links.
                    parts = re.split(r"(`+[^`]*`+)", line)
                    def references(match):
                        return match.group(0)[:match.start(1) - match.start()] + replace(match.group(1))

                    lines.append("".join(part if i % 2 else _REFERENCE.sub(references, _rewrite_inline_links(part, replace))
                                         for i, part in enumerate(parts)))
            after = "".join(lines).encode("utf-8")
            if after != before:
                changes.append({"source": path, "destination": relocated,
                                "before": before, "after": after, "targets": targets})
    return changes


def workspace_root(database):
    """Keep the legacy arbitrary-DB fallback used by ingest callers."""
    parent = Path(database).resolve().parent
    return parent.parent.parent if parent.name == "pool" and parent.parent.name == ".lessonkit" else parent.parent


def hidden_database(database):
    path = Path(database)
    return path.parent.name == "pool" and path.parent.parent.name == ".lessonkit"


def internal_path(root, database, name):
    return Path(root) / (".lessonkit" if hidden_database(database) else "") / name


def ingest_result_path(workspace, task):
    task = Path(task)
    if not hidden_database(workspace["db"]):
        return task / "result.json"
    root = Path(workspace["path"]) / ".lessonkit"
    source_dir = task if task.is_dir() else task.parent
    if source_dir.resolve().is_relative_to(root.resolve()):
        return source_dir / ("result.generated.json" if task.name == "result.json" else "result.json")
    return root / "intermediate" / "ingest" / source_dir.name / "result.json"


def graph_artifact_path(workspace):
    course = workspace.get("active_course", "")
    chapter = workspace.get("active_chapter", "")
    relative = Path("output") / course / chapter / f"{chapter}-graph.html"
    root = Path(workspace["path"])
    hidden = root / ".lessonkit" / relative
    legacy = root / relative
    return hidden if hidden.is_file() or not legacy.is_file() else legacy


def resolve_history_path(database, reference):
    """Resolve only owned legacy path prefixes; leave stored history untouched."""
    root = workspace_root(database)
    path = Path(reference)
    absolute = path if path.is_absolute() else root / path
    if not hidden_database(database):
        return path
    try:
        relative = absolute.resolve().relative_to(root)
    except ValueError:
        return path
    if relative.parts and relative.parts[0] in OWNED_DIRECTORIES:
        moved = root / ".lessonkit" / relative
        if moved.exists():
            return moved
    return path


def _preflight(root, moves):
    hidden = root / ".lessonkit"
    if hidden.is_symlink() or getattr(hidden, "is_junction", lambda: False)():
        raise ValueError(f"layout destination link escapes or aliases workspace: {hidden}")
    for source, target in moves:
        if not source.is_dir():
            raise ValueError(f"layout source is not a directory: {source}")
        if target.exists():
            raise ValueError(f"layout destination already exists: {target}")
        for path in (source, target, *source.rglob("*")):
            if not path.resolve().is_relative_to(root):
                raise ValueError(f"layout path escapes the workspace: {path}")
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                raise ValueError(f"layout relocation does not follow links: {path}")


def _require_idle(root):
    from workbench.cli import service

    if service.running_state():
        raise ValueError("stop the managed workbench service before migrating layout")
    jobs = root / ".lessonkit" / "jobs"
    for path in (*jobs.glob("conv-*/conversation.json"), *jobs.glob("conv-*/turn-*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") in {"running", "queued", "waiting_for_stop"}:
            raise ValueError(f"workspace has active work: {path}")


def migrate(workspace, *, apply=False):
    """Preview by default; move complete owned directories without merging."""
    root = Path(workspace["path"]).resolve()
    database = root / workspace["db"]
    if not database.is_file() or not database.resolve().is_relative_to(root):
        raise ValueError(f"registered database is missing or outside workspace: {database}")
    relative = database.relative_to(root)
    if relative.parts[0] != "pool" and relative.parts[:2] != (".lessonkit", "pool"):
        raise ValueError(f"registered database does not use a supported pool layout: {relative}")
    moves = [(root / name, root / ".lessonkit" / name)
             for name in OWNED_DIRECTORIES if (root / name).exists()]
    _preflight(root, moves)
    links = _markdown_changes(moves)
    receipt_dir = root / ".lessonkit" / "layout-migration"
    if moves and receipt_dir.exists():
        raise ValueError(f"layout migration receipt already exists: {receipt_dir}")
    new_db = (Path(".lessonkit") / relative).as_posix() if relative.parts[0] == "pool" else relative.as_posix()
    report = {"workspace": workspace["name"], "applied": False,
              "moves": [{"source": str(source), "destination": str(target)} for source, target in moves],
              "registration": {"before": workspace["db"], "after": new_db},
              "link_changes": [{"path": str(item["destination"]), "targets": item["targets"],
                                "backup": str(receipt_dir / "before" / item["source"].relative_to(root))}
                               for item in links]}
    if not apply or not moves:
        return report
    _require_idle(root)
    registry_path = registry.base_dir() / "workspaces.json"
    registry_before = registry_path.read_bytes()
    data = registry.load_registry()
    registered = next(row for row in data["workspaces"] if row["name"] == workspace["name"])
    registered["db"] = new_db
    moved = []
    hidden = root / ".lessonkit"
    hidden_existed = hidden.exists()
    try:
        hidden.mkdir(exist_ok=True)
        for source, target in moves:
            source.rename(target)
            moved.append((source, target))
        receipt_dir.mkdir()
        for item, entry in zip(links, report["link_changes"]):
            backup = Path(entry["backup"])
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(item["before"])
            item["destination"].write_bytes(item["after"])
        report["receipt"] = str(receipt_dir / "receipt.json")
        report["applied"] = True
        Path(report["receipt"]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        registry.save_registry(data)
    except Exception:
        if registry_path.read_bytes() != registry_before:
            registry_path.write_bytes(registry_before)
        for item in links:
            if item["destination"].is_file():
                item["destination"].write_bytes(item["before"])
        if receipt_dir.exists():
            shutil.rmtree(receipt_dir)
        for source, target in reversed(moved):
            target.rename(source)
        if not hidden_existed:
            hidden.rmdir()
        raise
    report["applied"] = True
    return report
