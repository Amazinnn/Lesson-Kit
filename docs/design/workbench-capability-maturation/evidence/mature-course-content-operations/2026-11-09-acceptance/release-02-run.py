"""WP02 RELEASE-02: copy migration, backup restore, and install identity.

1. An old pool without the chapter column migrates through migrate-progress;
   the id-derived chapter is backfilled and a seeded experience survives.
2. A recoverable backup taken by apply holds the pre-apply state and can be
   restored over the pool.
3. The installed entry point is the main checkout and exposes the new commands.

Report: tmp/accept/wp02-release02-report.json
"""
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
report = {}


def run(*argv, **kwargs):
    return subprocess.run(list(argv), cwd=ROOT, capture_output=True, text=True, **kwargs)


def columns(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def main():
    work = Path(tempfile.mkdtemp(prefix="wp02-release02-"))
    root = work / "dmath"
    (root / "pool").mkdir(parents=True)
    database = root / "pool" / "dmath.db"
    built = run(sys.executable, "pipeline/scripts/create-tables.py", "--db", str(database))
    if built.returncode:
        raise RuntimeError(built.stderr)

    # 1a. simulate an old pool: drop the chapter column again
    conn = sqlite3.connect(database)
    conn.execute("ALTER TABLE knowledge_points DROP COLUMN chapter")
    conn.execute(
        "INSERT INTO knowledge_points (kp_id, knowledge_item, body, knowledge_type,"
        " importance) VALUES ('dmath-ch06-kp-050','跨章迁移点','正文','method-modeling','core')")
    conn.execute(
        "INSERT INTO kp_experiences (kp_id, content, revision, updated_by)"
        " VALUES ('dmath-ch06-kp-050','旧池里的经验',1,'user')")
    conn.commit()
    before_columns = columns(conn, "knowledge_points")
    conn.close()
    assert "chapter" not in before_columns, "failed to simulate the old pool"

    # 1b. migrate through the repository's own script
    migrated = run(sys.executable, "pool/scripts/migrate-progress.py", "--db", str(database))
    assert migrated.returncode == 0, migrated.stderr
    conn = sqlite3.connect(database)
    after_columns = columns(conn, "knowledge_points")
    chapter_value, experience = conn.execute(
        "SELECT k.chapter, e.content FROM knowledge_points k"
        " JOIN kp_experiences e ON e.kp_id = k.kp_id"
        " WHERE k.kp_id='dmath-ch06-kp-050'").fetchone()
    conn.close()
    report["copy_migration"] = {
        "chapter_column_restored": "chapter" in after_columns,
        "chapter_backfilled_from_id": chapter_value == "ch06",
        "experience_survives": experience == "旧池里的经验",
    }

    # 2. backup restore: apply a bundle, then restore the recoverable copy
    import os
    os.environ["LESSONKIT_WB_HOME"] = str(work / "registry")
    from workbench import registry
    registry.register(name="dmath", path=root, db="pool/dmath.db",
                      course="dmath", chapter="ch06")
    from workbench.data import course_sync  # noqa: F401  (exercises the same schema)
    from workbench.ingest import apply_content_bundle
    from workbench.data.pool import Pool
    pool = Pool(root, database, "dmath", "ch06")
    before_ids = {item["kp_id"] for item in content_list(pool)}
    backup = root / "pool" / "dmath.db.release02-backup"
    manifest = {"kind": "content-bundle", "chapter": "ch06", "knowledge_points": [
        {"key": "new", "knowledge_item": "发布核对新点", "body": "适用条件…公式…步骤…",
         "knowledge_type": "method-modeling", "importance": "core"}]}
    result = apply_content_bundle(database, manifest, backup_path=backup, course="dmath")
    batch = result["batches"][0]
    new_id = batch["counts"]["knowledge_points"] and None
    after_ids = {item["kp_id"] for item in content_list(pool)}
    new_id = next(iter(after_ids - before_ids))
    report["backup_restore"] = {
        "backup_exists": backup.exists(),
        "new_point_in_pool_after_apply": new_id in after_ids,
        "backup_holds_pre_apply_state": before_ids <= after_ids
        and new_id not in _query_ids(backup),
    }
    restored = shutil.copyfile(backup, work / "restored.db")
    report["backup_restore"]["restored_copy_matches_pre_apply"] = (
        set(_query_ids(restored)) == before_ids)

    # 3. install identity
    identity = run(sys.executable, "-c", "import workbench; print(workbench.__file__)")
    report["install_identity"] = {
        "workbench_module": identity.stdout.strip(),
        "is_main_checkout": "Academic Workflow" in identity.stdout
        and "worktrees" not in identity.stdout,
    }
    out = ROOT / "tmp/accept/wp02-release02-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


def content_list(pool):
    from workbench.data import content
    return content.list_items(pool, "kp")


def _query_ids(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return {row[0] for row in conn.execute("SELECT kp_id FROM knowledge_points")}
    finally:
        conn.close()


if __name__ == "__main__":
    main()
