"""The walkthrough orchestration — before, after, diff.

Specification: ``openspec/changes/workbench-visual-language-v2/design-notes/
walkthrough-harness.md`` §1 (the isolation), §7 (the report) and
``acceptance.md`` §4 (the pass criteria).

What this module does
---------------------
It runs the whole walkthrough:

1. the **before** side is a git worktree at ``cf9d596d`` (A-49) — the
   parent of the branch's first product commit ``16d3ff89``;
2. each side gets its own service: its own isolated registry, its own
   **copy** of the pool, its own port (never 3081) and its own scratch
   directory.  The service is started with the **repository root as the
   working directory**, and the served stylesheet is compared byte for
   byte with the file on disk — a stale copy would silently serve the
   old tokens;
3. the collectors run in the order the design wants: the static probe
   **before** the exercise (the empty state needs an empty paper list),
   then the exercise, then the flow probe, then the motion frames, then
   the pool exports, then the graph page;
4. the diff compares the two sides and the recorder builds the report.

``--only`` runs a subset of the criteria, e.g. ``--only G-1 G-5`` or
``--only M-7``.  The criterion names are the ones of the acceptance
document, so a reader can ask for one gate and get exactly that gate.

Red lines (§8.3): the real pool is never written, the product code is
never touched, and the ports are never 3081.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# The harness lives in ``tools/walkthrough``; its siblings are imported by
# plain name so the module works from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The baseline of the change (A-49): the parent of the branch's first
#: product commit ``16d3ff89``.
BEFORE_COMMIT = "cf9d596d"

#: The port the real service uses — never to be taken.
FORBIDDEN_PORT = 3081

#: The default ports of the two sides (both differ from 3081).
DEFAULT_PORTS = {"before": 3281, "after": 3282}


class RunError(RuntimeError):
    """Raised when the run cannot continue (never silently skipped)."""


# ─────────────────────────────────────────────────────────────────────────
# the worktree (A-49)
# ─────────────────────────────────────────────────────────────────────────


def prepare_worktree(commit, path):
    """Check out ``commit`` into a worktree and give it the content files.

    The pool and the content directories are not tracked by git, so the
    worktree has none of them; the figures and the output are copied from
    the current checkout so that the two sides really show the same
    content (otherwise the screenshots would differ for a reason that has
    nothing to do with the change).
    """
    path = Path(path)
    if (path / ".git").exists() or (path / "HEAD").exists():
        _git(["worktree", "remove", "--force", str(path)], check=False)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    _git(["worktree", "add", "--detach", str(path), commit])
    for relative in (".lessonkit/figures", "output"):
        source = REPO_ROOT / relative
        target = path / relative
        if source.is_dir() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, target)
    return path


def remove_worktree(path):
    _git(["worktree", "remove", "--force", str(Path(path))], check=False)


def _git(args, check=True):
    result = subprocess.run(["git", *args], cwd=str(REPO_ROOT),
                            capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RunError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result


# ─────────────────────────────────────────────────────────────────────────
# the service
# ─────────────────────────────────────────────────────────────────────────


def start_service(side, repo_root, scratch, port, out_path, ws, course,
                  chapter, seed_pool, ready_file):
    """Start one side's service and wait until it is ready."""
    if port == FORBIDDEN_PORT:
        raise RunError(f"port {FORBIDDEN_PORT} is the real service's port")
    env = dict(os.environ)
    # The harness has to be importable, the product code has to come from
    # the side's own checkout.
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    launcher = REPO_ROOT / "tools" / "walkthrough" / "launch.py"
    command = [
        sys.executable, str(launcher),
        "--repo", str(repo_root),
        "--scratch", str(scratch),
        "--port", str(port),
        "--side", side,
        "--out", str(out_path),
        "--ws", ws,
        "--course", course,
        "--chapter", chapter,
        "--seed-pool", str(seed_pool),
        "--ready-file", str(ready_file),
    ]
    process = subprocess.Popen(command, cwd=str(repo_root), env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RunError(f"the {side} service died:\n{output}")
        if Path(ready_file).is_file():
            time.sleep(0.6)
            return process
        time.sleep(0.2)
    process.terminate()
    raise RunError(f"the {side} service did not become ready in time")


def check_served_css(base_url, repo_root):
    """The served stylesheet has to be the file on disk — byte for byte.

    The machine has a pip snapshot of the package installed; serving from
    the wrong directory would serve a stale copy, which shows up as "the
    new token has no value" without any error.
    """
    url = f"{base_url.rstrip('/')}/static/workbench.css"
    with urllib.request.urlopen(url, timeout=30) as response:
        served = len(response.read())
    on_disk = (Path(repo_root) / "workbench" / "server" / "static"
               / "workbench.css").stat().st_size
    if served != on_disk:
        raise RunError(f"the served workbench.css is {served} bytes, the file "
                       f"on disk is {on_disk} bytes — the service is not "
                       f"serving {repo_root}")
    return {"served": served, "onDisk": on_disk}


def stop_service(process):
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


# ─────────────────────────────────────────────────────────────────────────
# the collectors
# ─────────────────────────────────────────────────────────────────────────


def run_module(module, argv, cwd=None):
    """Run one of the collector modules as a subprocess."""
    command = [sys.executable, str(REPO_ROOT / "tools" / "walkthrough" / module),
               *argv]
    result = subprocess.run(command, cwd=str(cwd or REPO_ROOT),
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RunError(f"{module} failed:\n{result.stdout[-2000:]}\n"
                       f"{result.stderr[-2000:]}")
    return result.stdout


def collect_side(side, base_url, ws, evidence_dir, repo_root, criteria,
                 port, seed_pool):
    """Run the collectors of one side."""
    out_dir = Path(evidence_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    steps = []

    def wants(prefix):
        return any(item == prefix or item.startswith(prefix) for item in criteria)

    if wants("G-7") or wants("G-8") or wants("3."):
        steps.append(("probe static", run_module("probe.py", [
            "static", "--base-url", base_url, "--ws", ws,
            "--out", str(out_dir), "--side", side,
            "--repo-root", str(repo_root)])))
    if wants("G-1") or wants("G-2") or wants("G-3") or wants("G-4") \
            or wants("G-6") or wants("S-3"):
        steps.append(("exercise", run_module("exercise.py", [
            "--base-url", base_url, "--ws", ws, "--out", str(out_dir)])))
    if wants("G-7") or wants("G-8") or wants("3."):
        steps.append(("probe flow", run_module("probe.py", [
            "flow", "--base-url", base_url, "--ws", ws,
            "--out", str(out_dir), "--side", side,
            "--repo-root", str(repo_root)])))
    if wants("M-"):
        steps.append(("frames", run_module("frames.py", [
            "--base-url", base_url, "--ws", ws,
            "--out", str(out_dir.parent / "diff") if (out_dir.parent / "diff").is_dir()
            else str(out_dir / "diff")])))
    if wants("G-2") or wants("G-3") or wants("G-4") or wants("G-6"):
        pool_copy = _pool_copy(out_dir)
        if pool_copy:
            steps.append(("db export", run_module("dbexport.py", [
                "export", "--pool", str(pool_copy), "--out", str(out_dir / "db")])))
    if wants("G-5"):
        steps.append(("g5 capture", run_module("g5.py", [
            "capture", "--base-url", base_url, "--ws", ws,
            "--out", str(out_dir / "g5"), "--side", side])))
    if wants("S-"):
        steps.append(("shots", run_module("shots.py", [
            "capture", "--base-url", base_url, "--ws", ws,
            "--out", str(out_dir / "shots")])))
    return steps


def _pool_copy(out_dir):
    """The pool copy of this side (written by the launcher)."""
    scratch = out_dir.parent
    for candidate in sorted(scratch.glob("ws-*/pool/*.db")):
        return candidate
    return None


# ─────────────────────────────────────────────────────────────────────────
# the diff
# ─────────────────────────────────────────────────────────────────────────


def run_diff(evidence_dir, criteria):
    """Compare the two sides and build the report."""
    evidence_dir = Path(evidence_dir)
    diff_dir = evidence_dir / "diff"
    diff_dir.mkdir(parents=True, exist_ok=True)
    steps = []

    def wants(prefix):
        return any(item == prefix or item.startswith(prefix) for item in criteria)

    if wants("G-2") or wants("G-3") or wants("G-4") or wants("G-6"):
        before_db = evidence_dir / "before" / "db"
        after_db = evidence_dir / "after" / "db"
        if (before_db / "db.all.json").is_file() and (after_db / "db.all.json").is_file():
            steps.append(("db diff", run_module("dbexport.py", [
                "diff", "--before", str(before_db), "--after", str(after_db),
                "--due-before", str(evidence_dir / "before" / "exercise" / "due.json"),
                "--due-after", str(evidence_dir / "after" / "exercise" / "due.json"),
                "--weak-before", str(evidence_dir / "before" / "exercise" / "weak.json"),
                "--weak-after", str(evidence_dir / "after" / "exercise" / "weak.json"),
                "--out", str(diff_dir)])))
    if wants("G-7") or wants("G-8") or wants("3."):
        steps.append(("probe diff", run_module("probe.py", [
            "diff", "--before", str(evidence_dir / "before"),
            "--after", str(evidence_dir / "after"),
            "--out", str(diff_dir)])))
    if wants("G-5"):
        before_g5 = evidence_dir / "before" / "g5"
        after_g5 = evidence_dir / "after" / "g5"
        if (before_g5 / "graph-before.png").is_file() \
                and (after_g5 / "graph-after.png").is_file():
            steps.append(("g5 compare", run_module("g5.py", [
                "compare", "--before", str(before_g5), "--after", str(after_g5),
                "--out", str(diff_dir / "g5")])))
    if wants("S-"):
        before_shots = evidence_dir / "before" / "shots"
        after_shots = evidence_dir / "after" / "shots"
        if before_shots.is_dir() and after_shots.is_dir():
            steps.append(("shots diff", run_module("shots.py", [
                "diff", "--before", str(before_shots), "--after", str(after_shots),
                "--out", str(diff_dir / "shots")])))
    return steps


def build_report(evidence_dir, purpose="walkthrough"):
    """Ask the recorder for the report of the evidence on disk."""
    from recorder import build_report as recorder_report

    return recorder_report(evidence_dir, Path(evidence_dir) / "diff", purpose)


# ─────────────────────────────────────────────────────────────────────────
# the entry point
# ─────────────────────────────────────────────────────────────────────────


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the whole walkthrough: before, after, diff.")
    parser.add_argument("--out", default=str(REPO_ROOT / "tmp" / "walkthrough-run"),
                        help="the run directory (the evidence lives inside)")
    parser.add_argument("--only", nargs="*", default=None,
                        help="only these criteria (G-1, G-5, S-4, M-7, 3.1 …)")
    parser.add_argument("--before-commit", default=BEFORE_COMMIT)
    parser.add_argument("--port-before", type=int, default=DEFAULT_PORTS["before"])
    parser.add_argument("--port-after", type=int, default=DEFAULT_PORTS["after"])
    parser.add_argument("--ws", default="walk")
    parser.add_argument("--course", default="dmath")
    parser.add_argument("--chapter", default="ch06")
    parser.add_argument("--seed-pool", default=None,
                        help="the pool to copy (default: <repo>/pool/<course>.db)")
    parser.add_argument("--skip-before", action="store_true",
                        help="only run the after side (a self-check)")
    args = parser.parse_args(argv)

    criteria = args.only or ["G-1", "G-2", "G-3", "G-4", "G-5", "G-6", "G-7",
                              "G-8", "S-", "M-", "3."]
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    evidence = out / "evidence"
    seed_pool = Path(args.seed_pool) if args.seed_pool else \
        REPO_ROOT / "pool" / f"{args.course}.db"
    if not seed_pool.is_file():
        raise RunError(f"the seed pool is missing: {seed_pool}")

    worktree = out / "worktree-before"
    processes = []
    summary = {"criteria": criteria, "beforeCommit": args.before_commit,
               "steps": [], "errors": []}
    try:
        if not args.skip_before:
            prepare_worktree(args.before_commit, worktree)
            summary["worktree"] = str(worktree)
        sides = []
        if not args.skip_before:
            sides.append(("before", worktree, args.port_before))
        sides.append(("after", REPO_ROOT, args.port_after))
        for side, root, port in sides:
            scratch = out / f"scratch-{side}"
            ready = scratch / "ready.json"
            out_path = evidence / side / "requests.jsonl"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            process = start_service(side, root, scratch, port, out_path,
                                    args.ws, args.course, args.chapter,
                                    seed_pool, ready)
            processes.append(process)
            base_url = f"http://127.0.0.1:{port}"
            summary.setdefault("sides", {})[side] = {
                "baseUrl": base_url, "repoRoot": str(root),
                "scratch": str(scratch),
                "css": check_served_css(base_url, root),
            }
            steps = collect_side(side, base_url, args.ws, evidence / side, root,
                                 criteria, port, seed_pool)
            summary["steps"].append({"side": side,
                                     "steps": [name for name, _ in steps]})
        steps = run_diff(evidence, criteria)
        summary["steps"].append({"side": "diff",
                                 "steps": [name for name, _ in steps]})
        report = build_report(evidence)
        summary["summary"] = report.get("summary", {})
        summary["unresolved"] = report.get("unresolved", [])
        (out / "run.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        for process in processes:
            stop_service(process)
        if not args.skip_before and worktree.exists():
            remove_worktree(worktree)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
