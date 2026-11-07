"""Runtime source selection and read-only implementation snapshots."""
from pathlib import Path


def project_root(explicit=None, *, installed=None):
    """The checkout holding the installed code; --project-root previews another."""
    source = Path(installed or Path(__file__).resolve().parents[2]).resolve()
    if explicit is None:
        return source
    root = Path(explicit).expanduser().resolve()
    if not (root / "workbench" / "cli").is_dir():
        raise ValueError(f"not a lesson-kit source directory: {root}")
    return root


def snapshot(root):
    """Path -> (mtime_ns, size), excluding data and Python cache directories."""
    root = Path(root)
    files = list((root / "workbench").rglob("*.py"))
    for folder in ("workbench/server/static", "frontend/editable-graph/dist"):
        files.extend(p for p in (root / folder).rglob("*") if p.is_file())
    result = {}
    for path in files:
        if "__pycache__" in path.parts:
            continue
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue  # an editor may atomically replace a watched file
        result[path.relative_to(root).as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return result


def changed_kind(previous, current):
    changed = {path for path in previous.keys() | current.keys()
               if previous.get(path) != current.get(path)}
    if not changed:
        return None
    return "python" if any(p.endswith(".py") for p in changed) else "assets"


def syntax_error(root):
    """Compile changed source without importing it or generating bytecode."""
    for relative in snapshot(root):
        if not relative.endswith(".py"):
            continue
        path = Path(root) / relative
        try:
            compile(path.read_bytes(), str(path), "exec")
        except (SyntaxError, OSError) as exc:
            return str(exc)
    return None
