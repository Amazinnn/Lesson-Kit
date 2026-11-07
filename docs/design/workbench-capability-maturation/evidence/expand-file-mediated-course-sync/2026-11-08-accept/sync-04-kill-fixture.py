"""SYNC-04: kill the real `lesson-kit course-sync` process mid-run, retry, prove consistency.

Three boundaries are exercised with a hard process kill (TerminateProcess, i.e.
no cleanup): export into a package, receive into an empty course, and the file
publication phase inside receive (stretched with extra learning files).

After every kill the same command is retried until it succeeds; the received
course must then equal the source exactly - same table counts, no duplicated
attempt rows, every declared file present. Report: tmp/accept/p3-kill-report.json
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tmp" / "accept"))
from p3_f1 import build_course  # noqa: E402  (fixture builder reused unchanged)

REPORT = ROOT / "tmp/accept/p3-kill-report.json"
report = {"fixture": "F1 complete small course + 120 extra learning files", "steps": {}}


def save():
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def step(name, **values):
    report["steps"][name] = values
    save()
    print(name, json.dumps(values, ensure_ascii=False)[:280], flush=True)


def spawn(*argv, home):
    env = dict(os.environ, PYTHONUTF8="1", LESSONKIT_WB_HOME=str(home))
    return subprocess.Popen(
        [sys.executable, "-B", "-m", "workbench.cli.main", "course-sync", *argv],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def run(*argv, home):
    started = time.perf_counter()
    done = spawn(*argv, home=home)
    output, _ = done.communicate(timeout=180)
    return done.returncode, output, round(time.perf_counter() - started, 2)


def run_and_kill(*argv, home, delay):
    started = time.perf_counter()
    process = spawn(*argv, home=home)
    time.sleep(delay)
    killed = process.poll() is None
    if killed:
        process.kill()
    output = process.communicate()[0]
    return {"killed": killed, "delay": delay,
            "seconds": round(time.perf_counter() - started, 2),
            "exit": process.returncode,
            "tail": (output or "").strip().splitlines()[-1:] }


def registry_register(home, name, path):
    from workbench import registry
    previous = os.environ.get("LESSONKIT_WB_HOME")
    os.environ["LESSONKIT_WB_HOME"] = str(home)
    try:
        registry.register(name=name, path=path, db="pool/course.db", course="dmath", chapter="")
    finally:
        if previous is None:
            os.environ.pop("LESSONKIT_WB_HOME", None)
        else:
            os.environ["LESSONKIT_WB_HOME"] = previous


def counts(root):
    connection = sqlite3.connect(root / "pool/course.db")
    try:
        names = ("knowledge_points", "problems", "flash_cards", "knowledge_relations",
                 "problem_attempts", "kp_experiences", "active_practice", "paper_state",
                 "retired_paper_items")
        present = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        result = {name: (connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                         if name in present else 0)
                  for name in names}
        result["distinct_attempts"] = connection.execute(
            "SELECT COUNT(*) FROM (SELECT DISTINCT id FROM problem_attempts)"
        ).fetchone()[0]
        result["attempt_min"] = connection.execute(
            "SELECT MIN(id) FROM problem_attempts").fetchone()[0]
        result["attempt_max"] = connection.execute(
            "SELECT MAX(id) FROM problem_attempts").fetchone()[0]
        return result
    finally:
        connection.close()


def files_under(root):
    # Local media config is read for managed_paths but is not itself an asset.
    return sorted(p.relative_to(root).as_posix()
                  for p in (root / ".lessonkit").rglob("*") if p.is_file()
                  and p.relative_to(root).as_posix() != ".lessonkit/course-sync/config.json")


def main():
    work = Path(tempfile.mkdtemp(prefix="p3-kill-"))
    report["work"] = str(work)
    home_a, home_b = work / "registry-a", work / "registry-b"
    source = work / "A"
    build_course(source)
    learning = source / ".lessonkit/learning"
    learning.mkdir(parents=True, exist_ok=True)
    for index in range(1, 121):
        (learning / f"bulk-{index:03d}.md").write_text(
            f"# bulk note {index}\n\n" + ("content line\n" * 40), encoding="utf-8")
    registry_register(home_a, "dmath-a", source)
    source_counts = counts(source)
    step("fixture", counts=source_counts,
         learning_files=len(list(learning.glob("*.md"))))

    # Boundary 1: export into a package.
    warm = work / "export-warm"
    code, _, seconds = run("dmath-a", "export", "--to", str(warm), home=home_a)
    baseline_export = seconds
    package = work / "export-killed"
    killed = run_and_kill("dmath-a", "export", "--to", str(package),
                          home=home_a, delay=round(baseline_export * 0.5, 3))
    code, output, seconds = run("dmath-a", "export", "--to", str(package), home=home_a)
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    step("sync-04-export-kill", baseline_seconds=baseline_export, kill=killed,
         retry={"exit": code, "seconds": seconds}, retry_tail=output.strip()[-200:],
         manifest_course=manifest.get("course"), assets=len(manifest.get("assets", [])))

    # Boundary 2 + 3: receive into an empty course, and its file publication phase.
    target = work / "B"
    build_course(target, seed=False)
    registry_register(home_b, "dmath-b", target)
    first = run("dmath-b", "receive", "--from", str(package), home=home_b)
    baseline_receive = first[2]
    step("sync-04-receive-baseline", exit=first[0], seconds=baseline_receive)

    rounds = []
    for fraction in (0.3, 0.6, 0.9):
        victim = work / f"B-{int(fraction * 100)}"
        build_course(victim, seed=False)
        home = work / f"registry-b-{int(fraction * 100)}"
        registry_register(home, f"dmath-b{int(fraction * 100)}", victim)
        name = f"dmath-b{int(fraction * 100)}"
        killed = run_and_kill(name, "receive", "--from", str(package),
                              home=home, delay=round(baseline_receive * fraction, 3))
        retry = run(name, "receive", "--from", str(package), home=home)
        state = counts(victim)
        received_files = files_under(victim)
        source_files = files_under(source)
        rounds.append({
            "fraction": fraction, "kill": killed,
            "retry_exit": retry[0], "retry_seconds": retry[2],
            "table_counts_equal": state == source_counts,
            "attempts_duplicated": state["problem_attempts"] != source_counts["problem_attempts"],
            "missing_files": sorted(set(source_files) - set(received_files)),
            "extra_files": sorted(set(received_files) - set(source_files)),
            "counts": state,
        })
        step(f"sync-04-receive-kill-{int(fraction * 100)}", **rounds[-1])

    report["verdict"] = {
        "all_counts_equal": all(r["table_counts_equal"] for r in rounds),
        "no_duplicate_attempts": not any(r["attempts_duplicated"] for r in rounds),
        "no_missing_or_extra_files": all(not r["missing_files"] and not r["extra_files"]
                                         for r in rounds),
        "all_retries_succeeded": all(r["retry_exit"] == 0 for r in rounds),
    }
    save()
    print(json.dumps(report["verdict"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
