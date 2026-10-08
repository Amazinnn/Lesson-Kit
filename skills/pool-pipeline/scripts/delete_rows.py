"""Delete reviewed rows, after re-proving each one is safe to lose.

Deletion is the only irreversible action in this pipeline, so this tool refuses to
be trusting: for every id it first asks the pool for the row's learning records
(attempts, progress, schedule, signals, feedback) and skips anything that has one.
A record means the learner has touched that question; deleting it would destroy
study history rather than just a duplicate.

Usage:
    python delete_rows.py <delete-manifest.json> --workspace <name> [--cli lesson-kit] [--dry-run]

The manifest is a list of ``{"problem_id": ..., "kind": ..., "reason": ...}``.
Every run appends to ``deletions-executed.log`` next to the manifest, so the
deletion ledger survives even if the pool does not.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

LEARNING_TABLES = (
    "attempts", "progress", "schedule", "signals", "feedback",
)


def run(cli: str, *args: str) -> tuple[int, str]:
    proc = subprocess.run([cli, *args], capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def has_learning_records(cli: str, workspace: str, pid: str) -> bool | None:
    """True/False, or None when the history cannot be read (then do not delete)."""
    code, out = run(cli, "data", workspace, "history", "problem", pid)
    if code != 0:
        return None
    try:
        history = json.loads(out)
    except json.JSONDecodeError:
        return None
    return any(history.values())


def main() -> int:
    manifest = Path(sys.argv[1])
    workspace = sys.argv[sys.argv.index("--workspace") + 1]
    cli = sys.argv[sys.argv.index("--cli") + 1] if "--cli" in sys.argv else "lesson-kit"
    dry = "--dry-run" in sys.argv
    entries = json.loads(manifest.read_text(encoding="utf-8"))

    deleted, skipped, failed, unknown = [], [], [], []
    for entry in entries:
        pid = entry["problem_id"]
        state = has_learning_records(cli, workspace, pid)
        if state is None:
            unknown.append(pid)
            continue
        if state:
            skipped.append(pid)
            continue
        if dry:
            deleted.append(pid)
            continue
        code, out = run(cli, "data", workspace, "delete", "problem", pid)
        (deleted if code == 0 else failed).append(pid)
        if code != 0:
            print(f"  FAILED {pid}: {out.strip()[:140]}")

    log = manifest.with_name(manifest.stem + ".executed.log")
    with log.open("a", encoding="utf-8") as fh:
        for pid in deleted:
            fh.write(f"{'would-delete' if dry else 'deleted'}\t{pid}\n")
        for pid in skipped:
            fh.write(f"skipped\t{pid}\thas learning records\n")
        for pid in unknown:
            fh.write(f"skipped\t{pid}\thistory unreadable\n")
        for pid in failed:
            fh.write(f"failed\t{pid}\n")

    print(f"{'would delete' if dry else 'deleted'}={len(deleted)}  skipped={len(skipped)}  "
          f"unreadable={len(unknown)}  failed={len(failed)}  (log: {log.name})")
    if skipped:
        print("  skipped because a learner has records on them: " + ", ".join(skipped[:10]))
    return 0 if not failed and not unknown else 1


if __name__ == "__main__":
    sys.exit(main())
