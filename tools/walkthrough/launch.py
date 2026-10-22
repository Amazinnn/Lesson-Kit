"""Walkthrough launcher: an isolated workbench service with the recorder inside.

Specification: ``openspec/changes/workbench-visual-language-v2/design-notes/
walkthrough-harness.md`` §1 (isolation) and §2 (request capture).

What this module guarantees, and how:

* **The real pool is never written.**  The service runs against a *copy* of
  the pool inside a scratch directory, and the workspace registry is
  redirected through ``LESSONKIT_WB_HOME`` (§1.1).  Two hard gates already
  exist in the product (``workbench/registry.py:46-50`` and
  ``workbench/data/pool.py:19-22``); this launcher adds A1/A2/A3 on top of
  them (§1.6).
* **The service runs the repository's code, not the installed snapshot.**
  ``lesson-kit`` is pip-installed as an *editable* install that points at
  ``.worktrees/runtime-main`` — an old copy of the workbench.  Importing
  ``workbench`` from outside the repository therefore silently serves stale
  assets.  The launcher puts the repository root first on ``sys.path``, runs
  with the repository root as the working directory, and asserts
  ``workbench.__file__`` is inside the repository (§1.7, R-6, R-22).
* **The port is not the user's default.**  ``3081`` is rejected; the launcher
  uses its own port and refuses to start on a busy one (§1.5, R-23).

Usage::

    python tools/walkthrough/launch.py --scratch <dir> --port 3191 --side after

The service runs in the foreground (never ``daemon``), so the recorder lives
in the same process as the request handling and the port is released when
the process ends (§8.2.4).
"""

import argparse
import hashlib
import json
import os
import shutil
import socket
import sys
from pathlib import Path

# ── the repository root is derived from this file, never from the cwd ────
REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PORT = 3091
FORBIDDEN_PORT = 3081


class IsolationBreach(RuntimeError):
    """Raised when an isolation assertion fails.  Never downgraded to a warning."""


# ─────────────────────────────────────────────────────────────────────────
# code resolution (§1.7, R-6, R-22)
# ─────────────────────────────────────────────────────────────────────────


def force_repo_on_path(repo_root):
    """Put the repository root first on ``sys.path`` and chdir into it."""
    repo_root = Path(repo_root).resolve()
    text = str(repo_root)
    while text in sys.path:
        sys.path.remove(text)
    sys.path.insert(0, text)
    os.chdir(repo_root)
    return repo_root


def assert_repo_code(repo_root):
    """Fail loudly when ``import workbench`` would resolve to the pip snapshot."""
    import workbench  # noqa: WPS433 — the import is the assertion

    module_file = Path(workbench.__file__).resolve()
    if not module_file.is_relative_to(Path(repo_root).resolve()):
        raise IsolationBreach(
            f"import workbench resolved to {module_file}, which is outside "
            f"{repo_root}. The pip-installed snapshot would serve stale assets."
        )
    return module_file


# ─────────────────────────────────────────────────────────────────────────
# isolation helpers (§1.2, §1.6)
# ─────────────────────────────────────────────────────────────────────────


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_paths(paths):
    """A4 snapshot: sha256 + size + mtime of every watched file."""
    snapshot = {}
    for path in paths:
        path = Path(path)
        if not path.exists():
            snapshot[str(path)] = None
            continue
        stat = path.stat()
        snapshot[str(path)] = {
            "sha256": sha256_file(path),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
    return snapshot


def real_watched_paths(repo_root):
    """The files that must not change during a walkthrough (A4, §8.2.2)."""
    repo_root = Path(repo_root)
    watched = [repo_root / "pool" / "dmath.db"]
    pool_dir = repo_root / "pool"
    if pool_dir.is_dir():
        watched.extend(sorted(pool_dir.glob("*.db")))
    real_registry = Path.home() / ".lessonkit-workbench"
    watched.extend([real_registry / "workspaces.json", real_registry / "daemon.json"])
    return watched


def copy_file_bytes(source, target):
    """Copy by bytes, never by link semantics (R-3)."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = Path(source).read_bytes()
    target.write_bytes(data)
    return target


def copy_tree(source, target):
    source, target = Path(source), Path(target)
    if not source.is_dir():
        return None
    shutil.copytree(source, target, dirs_exist_ok=True)
    return target


def build_workspace(scratch, repo_root, ws_name, course, seed_pool, chapter):
    """Build the isolated workspace: a pool *copy* plus the content files."""
    repo_root = Path(repo_root)
    ws_dir = Path(scratch) / f"ws-{ws_name}"
    (ws_dir / ".lessonkit").mkdir(parents=True, exist_ok=True)

    seed_pool = Path(seed_pool).resolve()
    if not seed_pool.is_file():
        raise IsolationBreach(f"seed pool not found: {seed_pool}")
    pool_copy = copy_file_bytes(seed_pool, ws_dir / "pool" / f"{course}.db")
    if os.path.samefile(seed_pool, pool_copy):
        raise IsolationBreach("the pool copy is the same file as the seed")
    if seed_pool.stat().st_ino == pool_copy.stat().st_ino:
        raise IsolationBreach("the pool copy shares the inode of the seed")

    figures = copy_tree(repo_root / ".lessonkit" / "figures", ws_dir / ".lessonkit" / "figures")
    (ws_dir / ".lessonkit" / "explain").mkdir(parents=True, exist_ok=True)
    (ws_dir / ".lessonkit" / "jobs").mkdir(parents=True, exist_ok=True)
    output = copy_tree(repo_root / "output", ws_dir / "output")

    return {
        "dir": ws_dir,
        "pool": pool_copy,
        "figures": figures,
        "output": output,
        "chapter": chapter,
    }


def register_workspace(ws_dir, ws_name, course, chapter):
    """Register the workspace in the *isolated* registry.

    This is the same call ``workbench.cli.main init`` makes (§1.3).  The
    bootstrap step is deliberately skipped: the pool copy is already in
    place, so ``registry.looks_like_workspace()`` is true and the product
    never rebuilds the pool (R-2, R-16, R-17).
    """
    from workbench import registry

    if not registry.looks_like_workspace(Path(ws_dir)):
        raise IsolationBreach(
            f"{ws_dir} does not look like a workspace; the pool copy is missing")
    workspace = registry.register(str(ws_dir), name=ws_name, course=course,
                                  chapter=chapter)
    return workspace


def assert_isolated(scratch, phase, real_pool=None):
    """A1 / A2 / A3 — the isolation assertions (§1.6, §8.2.1).

    Any failure raises; nothing here is ever a warning.
    """
    scratch = Path(scratch).resolve()
    wb_home = Path(os.environ.get("LESSONKIT_WB_HOME", "")).resolve()
    real_home = (Path.home() / ".lessonkit-workbench").resolve()

    # A1 — configuration layer
    if wb_home == real_home:
        raise IsolationBreach(f"[{phase}] A1: LESSONKIT_WB_HOME points at the real registry")
    if not wb_home.is_relative_to(scratch):
        raise IsolationBreach(f"[{phase}] A1: LESSONKIT_WB_HOME {wb_home} is outside {scratch}")

    registry_file = wb_home / "workspaces.json"
    workspaces = []
    if registry_file.is_file():
        workspaces = json.loads(registry_file.read_text(encoding="utf-8")).get("workspaces", [])

    # A2 — registry layer
    for workspace in workspaces:
        for key in ("path", "db"):
            value = workspace.get(key)
            if not value:
                continue
            resolved = Path(value)
            if not resolved.is_absolute():
                resolved = (Path(workspace["path"]) / resolved).resolve()
            else:
                resolved = resolved.resolve()
            if not resolved.is_relative_to(scratch):
                raise IsolationBreach(
                    f"[{phase}] A2: {key} escapes $SCRATCH: {value}")

    # A3 — data layer
    if real_pool is not None:
        real_pool = Path(real_pool).resolve()
        for workspace in workspaces:
            db = Path(workspace["db"])
            if not db.is_absolute():
                db = (Path(workspace["path"]) / db).resolve()
            if db.is_file() and real_pool.is_file() and os.path.samefile(db, real_pool):
                raise IsolationBreach(
                    f"[{phase}] A3: the workspace pool is the same file as the real pool")
    return workspaces


# ─────────────────────────────────────────────────────────────────────────
# the launcher
# ─────────────────────────────────────────────────────────────────────────


def port_is_free(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def check_port(port):
    if port == FORBIDDEN_PORT:
        raise SystemExit(f"refusing to use {FORBIDDEN_PORT}: that is the user's default workbench")
    if not port_is_free("127.0.0.1", port):
        raise SystemExit(f"port {port} is already in use; pick another one")
    return port


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Start an isolated workbench service with the request recorder attached.")
    parser.add_argument("--repo", default=str(REPO_ROOT),
                        help="repository root (default: the root of this checkout)")
    parser.add_argument("--scratch", default=None,
                        help="scratch directory holding the isolated registry and workspace")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"port to serve on (never {FORBIDDEN_PORT})")
    parser.add_argument("--side", default="after", choices=("before", "after"),
                        help="which side of the comparison this run is")
    parser.add_argument("--out", default=None,
                        help="requests.jsonl path (default: <scratch>/evidence/<side>/requests.jsonl)")
    parser.add_argument("--ws", default="walk", help="workspace name inside the isolated registry")
    parser.add_argument("--course", default="dmath", help="course identifier")
    parser.add_argument("--chapter", default="ch06", help="chapter identifier")
    parser.add_argument("--seed-pool", default=None,
                        help="pool file to copy (default: <repo>/pool/<course>.db)")
    parser.add_argument("--no-record", action="store_true",
                        help="do not install the recorder (same as WALKTHROUGH_RECORD=0)")
    parser.add_argument("--seed-records", type=int, default=0,
                        help="seed this many attempt records into the pool COPY "
                             "(the real pool is never written)")
    parser.add_argument("--seed-sessions", type=int, default=0,
                        help="seed this many AI conversations into the workspace COPY")
    parser.add_argument("--seed-out", default=None,
                        help="where the seed summary and the all-correct plan go")
    parser.add_argument("--check-only", action="store_true",
                        help="build the isolated environment, assert it, then exit")
    parser.add_argument("--ready-file", default=None,
                        help="write a JSON descriptor of the running service here")
    args = parser.parse_args(argv)

    repo_root = force_repo_on_path(args.repo)
    seed_pool = Path(args.seed_pool) if args.seed_pool else repo_root / "pool" / f"{args.course}.db"
    scratch = Path(args.scratch).resolve() if args.scratch else \
        (repo_root / "tmp" / "walkthrough-scratch").resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    registry_home = scratch / "registry"
    registry_home.mkdir(parents=True, exist_ok=True)

    # the isolated registry — set before any product call that reads it
    os.environ["LESSONKIT_WB_HOME"] = str(registry_home)

    module_file = assert_repo_code(repo_root)
    check_port(args.port)

    workspace = build_workspace(scratch, repo_root, args.ws, args.course,
                                seed_pool, args.chapter)
    registered = register_workspace(workspace["dir"], args.ws, args.course, args.chapter)
    assert_isolated(scratch, "after-init", real_pool=seed_pool)

    out_path = Path(args.out) if args.out else \
        scratch / "evidence" / args.side / "requests.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        "repo_root": str(repo_root),
        "workbench_module": str(module_file),
        "scratch": str(scratch),
        "registry_home": str(registry_home),
        "workspace": registered,
        "pool_copy": str(workspace["pool"]),
        "seed_pool": str(Path(seed_pool).resolve()),
        "port": args.port,
        "side": args.side,
        "requests_jsonl": str(out_path),
        "real_pool": str(Path(seed_pool).resolve()),
    }

    if args.seed_records or args.seed_sessions or args.seed_out:
        # The seed runs **before** the service starts: the pool copy is
        # written while nothing holds it open, so there is no lock
        # contention, and the service reads the seeded data from the start.
        # It only ever writes the copy (seed.assert_isolated).
        from tools.walkthrough import seed as seed_mod

        seed_out = Path(args.seed_out) if args.seed_out else \
            Path(scratch) / "seed" / args.side
        seed_summary = seed_mod.seed_workspace(
            workspace["dir"], workspace["pool"], seed_out,
            records=args.seed_records, sessions=args.seed_sessions,
            real_pool=seed_pool, plan=True)
        summary["seed"] = {
            "records": seed_summary["records"],
            "sessions": seed_summary["sessions"],
            "plan": str(seed_out / "plan.json"),
            "summary": str(seed_out / "summary.json"),
            "realPoolUnchanged": seed_summary["realPoolUnchanged"],
        }

    if args.check_only:
        summary["checked"] = True
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    from workbench.server import app

    recorder = None
    if not args.no_record and os.environ.get("WALKTHROUGH_RECORD") != "0":
        from tools.walkthrough import recorder as recorder_mod

        recorder = recorder_mod.install(app, out_path)
        summary["recorder"] = "installed"

    if args.ready_file:
        Path(args.ready_file).parent.mkdir(parents=True, exist_ok=True)
        Path(args.ready_file).write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                         encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"[walkthrough] serving http://127.0.0.1:{args.port}/  "
          f"(workspace {args.ws!r}) — Ctrl-C to stop", file=sys.stderr)
    try:
        app.serve(port=args.port)
    finally:
        if recorder is not None:
            recorder.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
