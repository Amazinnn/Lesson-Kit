"""Fresh-course bootstrap for a device that has never seen the course.

Receiving a package on an unregistered device has to end with a real pool and the
``.lessonkit`` skeleton. The pool is created through the same canonical route
``lesson-kit init`` uses (``pipeline/scripts/create-tables.py``) rather than a
second schema definition. There is no fallback: when the canonical script is not
part of the imported source, bootstrap refuses instead of faking a pool.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

from workbench import registry

COURSE = re.compile(r"[a-z0-9][a-z0-9-]*")
POOL = ".lessonkit/pool"
SKELETON = ("figures", "explain", "jobs")
#: Canonical creation route of the checkout this module was imported from.
CREATE_TABLES = (
    Path(__file__).resolve().parents[2] / "pipeline" / "scripts" / "create-tables.py"
)
#: Enough of the child's output to name a failure, never a full transcript.
OUTPUT_LIMIT = 2000
TIMEOUT_SECONDS = 300


def bootstrap(root, course):
    """Create ``<root>/.lessonkit/pool/<course>.db`` and its skeleton folders.

    Returns the database path relative to the workspace root (POSIX form).
    A pool that already exists anywhere in the root refuses the whole call
    before any write, and nothing is registered here — the caller owns the
    registry. A child failure leaves whatever it created in place for explicit
    repair instead of rolling the course back.
    """
    if not isinstance(course, str) or not COURSE.fullmatch(course):
        raise ValueError(
            f"course {course!r} is not a lowercase ASCII identifier — it becomes "
            "the pool file name and part of every content id"
        )
    root = Path(root)
    if root.exists() and not root.is_dir():
        raise ValueError(f"not a folder: {root}")
    existing = registry.pool_candidates(root)
    if existing:
        raise ValueError(
            f"{root} already holds a pool database ({', '.join(existing)}) — "
            "fresh course bootstrap never overwrites one"
        )
    if not CREATE_TABLES.is_file():
        raise RuntimeError(
            f"the canonical pool creation script is missing: {CREATE_TABLES}\n"
            "a fresh course needs a source checkout; an installed wheel without "
            "pipeline/scripts/create-tables.py cannot bootstrap one"
        )
    relative = f"{POOL}/{course}.db"
    root.mkdir(parents=True, exist_ok=True)
    _create_tables(root, relative)
    for name in SKELETON:
        (root / ".lessonkit" / name).mkdir(parents=True, exist_ok=True)
    return relative


def _create_tables(root, relative):
    """Run the canonical script with an explicit argument list and working folder."""
    try:
        completed = subprocess.run(
            [sys.executable, str(CREATE_TABLES), "--db", relative],
            cwd=str(root), env=dict(os.environ, PYTHONIOENCODING="utf-8"),
            stdin=subprocess.DEVNULL, capture_output=True, check=False,
            timeout=TIMEOUT_SECONDS, **_hidden_window(),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"creating {relative} timed out after {TIMEOUT_SECONDS}s"
        ) from exc
    if completed.returncode:
        detail = _tail(completed.stderr) or _tail(completed.stdout) or "no output"
        raise RuntimeError(
            f"creating {relative} failed (exit {completed.returncode}): {detail}"
        )


def _hidden_window():
    """Never flash a console window for the schema child on Windows."""
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


def _tail(output):
    text = (output or b"").decode("utf-8", "replace").strip()
    return text[-OUTPUT_LIMIT:]
