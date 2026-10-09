"""Explicit real-pool conformance check; all writes are temporary backup copies.

Run from the repository root:
    python tests/workbench/real_pool_conformance.py --workspace REGISTERED_NAME
Optionally compare a historical DB with --audit-before PATH (read-only).
This is deliberately outside pytest's automatic fixture discovery.
"""

import argparse
import copy
import importlib.util
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter
from contextlib import closing
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from workbench import ingest, registry
from workbench.data import content_audit
from workbench.data.pool import Pool
from workbench.server import pages

CONTENT = {"knowledge_points": "kp_id", "problems": "problem_id",
           "flash_cards": "card_id"}
LEARNING = ("problem_progress", "problem_attempts", "review_schedule",
            "learner_signals", "feedback_events", "learning_current_state",
            "attempt_operations", "practice_request_operations", "practice_runs",
            "active_practice", "active_practice_items", "kp_progress", "question_progress")
MATH = re.compile(r"\$\$([\s\S]+?)\$\$|\$([^$\n]+)\$")


def readonly(path):
    conn = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def snapshot(conn):
    """Keep full evidence in memory; never print course/learner row contents."""
    result = {}
    for row in conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"):
        name = row[0]
        quoted = '"' + name.replace('"', '""') + '"'
        columns = [r[1] for r in conn.execute(f"PRAGMA table_info({quoted})")]
        rows = sorted((tuple(r) for r in conn.execute(f"SELECT * FROM {quoted}")),
                      key=repr)
        result[name] = {"sql": row[1], "columns": columns, "rows": rows}
    return result


def counts(state):
    return {name: len(table["rows"]) for name, table in state.items()}


def projected(state, name, columns):
    table = state[name]
    positions = [table["columns"].index(column) for column in columns]
    return sorted((tuple(row[i] for i in positions) for row in table["rows"]),
                  key=repr)


def preserve_migration(before, after):
    for name, id_column in CONTENT.items():
        if name not in before:
            continue
        columns = [c for c in (id_column, "problem_text", "solution", "body",
                              "front", "back", "topic_label")
                   if c in before[name]["columns"]]
        assert projected(before, name, columns) == projected(after, name, columns), name
    for name in (*LEARNING, "ingest_batches"):
        if name in before:
            assert projected(before, name, before[name]["columns"]) == projected(
                after, name, before[name]["columns"]), name


def preserve_existing(before, after):
    for name in (*CONTENT, *LEARNING, "ingest_batches"):
        if name not in before:
            continue
        old = before[name]["rows"]
        new = after[name]["rows"]
        assert all(row in new for row in old), f"existing {name} row changed"
        if name in LEARNING:
            assert old == new, f"learning {name} changed"


class MathValues(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.values = []
        self.current = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "span" and "math" in dict(attrs).get("class", "").split():
            self.current = ""

    def handle_data(self, data):
        if self.current is not None:
            self.current += data

    def handle_endtag(self, tag):
        if tag == "span" and self.current is not None:
            self.values.append(self.current)
            self.current = None


def real_math_probes(conn, scratch):
    candidates = []
    for table, id_column, fields in (
            ("problems", "problem_id", ("problem_text", "solution")),
            ("knowledge_points", "kp_id", ("body",))):
        for row in conn.execute(f"SELECT {id_column}, {', '.join(fields)} FROM {table} "
                                f"ORDER BY {id_column}"):
            for field in fields:
                for match in MATH.finditer(row[field] or ""):
                    expression = (match[1].strip("\n") if match[1] is not None
                                  else match[2])
                    traits = [trait for trait, present in (
                        ("ampersand", "&" in expression),
                        ("comparison", "<" in expression or ">" in expression),
                        ("multiline-display", match[1] is not None and "\n" in match[1]))
                        if present]
                    if traits and len(expression) <= 400:
                        candidates.append({"id": row[id_column], "field": field,
                                           "offset": match.start(), "traits": traits,
                                           "markdown": match[0], "expression": expression})
    # One shortest real fragment per available regression shape, with no synthetic fallback.
    selected = []
    for trait in ("ampersand", "comparison", "multiline-display"):
        options = [item for item in candidates if trait in item["traits"]]
        if options:
            item = min(options, key=lambda probe: (len(probe["expression"]), probe["id"]))
            if item not in selected:
                selected.append(item)
    assert selected, "no real ampersand/comparison/multiline math samples in this pool"
    cases = scratch / "real-render-cases.json"
    cases.write_text(json.dumps([{"mode": "block", "markdown": item["markdown"]}
                                 for item in selected], ensure_ascii=False), encoding="utf-8")
    completed = subprocess.run(
        ["node", str(REPO / "tests/workbench/renderer_parity_cases.js"), str(cases)],
        check=True, capture_output=True, text=True, encoding="utf-8", cwd=REPO)
    rendered = [json.loads(line)["out"] for line in completed.stdout.splitlines()]
    assert len(rendered) == len(selected)
    evidence = []
    for item, client in zip(selected, rendered):
        server = pages._render_markdown(item["markdown"], "dmath", item["id"])
        assert server == client, f"renderer parity failed: {item['id']} {item['field']}"
        values = MathValues(server).values
        assert values == [item["expression"]], f"escaped math changed: {item['id']}"
        evidence.append({key: value for key, value in item.items() if key != "markdown"}
                        | {"parsed_math": values, "html_parity": True})
    return evidence


def audit_summary(conn, root, db_path, course, checks=None):
    before = snapshot(conn)
    pool = Pool(root, db_path, course, "")
    pool._conn = conn  # The audit only reads; keep the source's mode=ro connection.
    result = content_audit.audit(pool, checks)
    assert snapshot(conn) == before and conn.total_changes == 0
    summary = {check: 0 for check in result["checks"]}
    summary.update(Counter(item["check"] for item in result["findings"]))
    return {"checks": summary, "findings": len(result["findings"]),
            "sample_finding_ids": {check: sorted({item_id for finding in result["findings"]
                                           if finding["check"] == check
                                           for item_id in finding.get("problem_ids", [])})[:12]
                            for check in result["checks"]}, "total_changes": conn.total_changes}


def bundle(conn, course, real_math):
    kp = conn.execute("SELECT kp_id, knowledge_item, body FROM knowledge_points "
                      "WHERE body IS NOT NULL AND trim(body) != '' ORDER BY kp_id LIMIT 1").fetchone()
    problem = conn.execute("SELECT problem_id, problem_text FROM problems "
                           "WHERE problem_text IS NOT NULL AND trim(problem_text) != '' "
                           "ORDER BY problem_id LIMIT 1").fetchone()
    assert kp is not None and problem is not None
    chapters = sorted({row[0].rsplit("-kp-", 1)[0][len(course) + 1:]
                       for row in conn.execute("SELECT kp_id FROM knowledge_points")
                       if row[0].startswith(course + "-") and "-kp-" in row[0]})[:2]
    assert chapters
    manifest = {"kind": "content-bundle", "knowledge_points": [], "problems": [],
                "flash_cards": []}
    for index, chapter in enumerate(chapters, 1):
        key = f"verification-kp-{index}"
        source = f"Verification-only copy probe of {kp['kp_id']} and {real_math[0]['id']}"
        manifest["knowledge_points"].append({
            "key": key, "chapter": chapter,
            "knowledge_item": f"Verification only {index}: {kp['knowledge_item']}",
            "knowledge_type": "concept-property", "importance": "core",
            "body": kp["body"], "source_location": source})
        manifest["problems"].append({
            "key": f"verification-problem-{index}", "chapter": chapter, "kp_ids": [key],
            "problem_text": f"Verification only unique chapter sample {chapter} {index}: "
                            + "$" + real_math[0]["expression"] + "$",
            "problem_type": "other", "source_kind": "other",
            "origin_kind": "generated_grounded", "source_evidence": source})
        manifest["flash_cards"].append({
            "key": f"verification-card-{index}", "chapter": chapter, "kp_id": key,
            "front": f"Verification only {index}: {kp['knowledge_item']}"[:100],
            "back": "Real-source math: " + real_math[0]["expression"][:240],
            "source_evidence": source})
    return manifest, problem


def refused(database, manifest, backup):
    with closing(sqlite3.connect(database)) as conn:
        before = snapshot(conn)
    files = sorted(str(path.relative_to(database.parent.parent))
                   for path in database.parent.parent.rglob("*") if path.is_file())
    try:
        ingest.apply_batch(database, manifest, source="cli", backup_path=backup,
                           course=database.stem)
    except ValueError as error:
        reason = str(error)
    else:
        raise AssertionError("invalid manifest applied")
    with closing(sqlite3.connect(database)) as conn:
        assert snapshot(conn) == before, "refusal changed rows/schema/ledger"
    assert not backup.exists(), "refusal created a backup"
    assert files == sorted(str(path.relative_to(database.parent.parent))
                           for path in database.parent.parent.rglob("*") if path.is_file())
    return reason


def run(name, before_path=None):
    modules = {module.__name__: str(Path(module.__file__).resolve())
               for module in (ingest, registry, content_audit, pages)}
    assert all(Path(path).is_relative_to(REPO) for path in modules.values())
    registry_path = registry.base_dir() / "workspaces.json"
    registry_before = registry_path.read_bytes()
    workspace = registry.get_workspace(name)
    root = Path(workspace["path"]).resolve()
    source_path = (root / workspace["db"]).resolve()
    course = workspace["active_course"] or source_path.stem
    source = readonly(source_path)
    try:
        source_before = snapshot(source)
        report = {"workspace": name, "course": course, "module_files": modules,
                  "source_counts": counts(source_before)}
        report["historical_unstamped_rows"] = {
            table: (source.execute(f"SELECT COUNT(*) FROM {table} "
                                   "WHERE ingest_batch_id IS NULL OR ingest_batch_id='' ")
                    .fetchone()[0] if "ingest_batch_id" in source_before[table]["columns"]
                    else len(source_before[table]["rows"]))
            for table in CONTENT if table in source_before}
        report["audit_current"] = audit_summary(source, root, source_path, course)
        if before_path:
            with closing(readonly(before_path)) as earlier:
                report["audit_before"] = audit_summary(
                    earlier, root, Path(before_path).resolve(), course,
                    ("duplicates", "fragments", "unmarked-objective", "untitled"))
                report["audit_before"]["problems"] = counts(snapshot(earlier))["problems"]
            report["audit_before"]["figure_comparison"] = "unavailable historical figure tree"
        with tempfile.TemporaryDirectory(prefix="lessonkit-real-conformance-") as temporary:
            scratch = Path(temporary)
            database = scratch / "pool" / f"{course}.db"
            database.parent.mkdir()
            with closing(sqlite3.connect(database)) as conn:
                source.backup(conn)
                assert snapshot(conn) == source_before
            report["real_render_probes"] = real_math_probes(source, scratch)
            schema_path = REPO / "pool/scripts/pool_schema.py"
            spec = importlib.util.spec_from_file_location("conformance_pool_schema", schema_path)
            schema = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(schema)
            report["module_files"]["pool_schema"] = str(Path(schema.__file__).resolve())
            with closing(sqlite3.connect(database)) as conn:
                migration = schema.ensure_workbench_schema(conn)
                conn.commit()
                baseline = snapshot(conn)
                preserve_migration(source_before, baseline)
                conn.row_factory = sqlite3.Row
                manifest, real_problem = bundle(conn, course, report["real_render_probes"])
            report["copy_schema_baseline"] = {"changes": migration, "counts": counts(baseline),
                                               "historical_content_and_learning_preserved": True}
            malformed = copy.deepcopy(manifest)
            malformed["problems"][0].pop("source_evidence")
            assert "source_evidence" in refused(database, malformed, scratch / "malformed-backup.db")
            duplicate = copy.deepcopy(manifest)
            duplicate["problems"][0]["problem_text"] = real_problem["problem_text"]
            assert real_problem["problem_id"] in refused(
                database, duplicate, scratch / "duplicate-backup.db")
            applied = ingest.apply_batch(database, manifest, source="cli",
                                          backup_path=scratch / "apply-backup.db", course=course)
            with closing(sqlite3.connect(database)) as conn:
                applied_state = snapshot(conn)
                preserve_existing(baseline, applied_state)
                for table in CONTENT:
                    assert applied["counts"][table] == len(manifest[table])
                    assert len(applied_state[table]["rows"]) == (
                        len(baseline[table]["rows"]) + len(manifest[table]))
                stamped = {}
                for batch in applied["batches"]:
                    recorded = conn.execute("SELECT counts_json, backup_path FROM ingest_batches "
                                            "WHERE batch_id=?", (batch["batch_id"],)).fetchone()
                    assert json.loads(recorded[0]) == batch["counts"]
                    assert Path(recorded[1]) == scratch / "apply-backup.db"
                    stamped[batch["batch_id"]] = {}
                    for table, id_column in CONTENT.items():
                        ids = [row[0] for row in conn.execute(
                            f"SELECT {id_column} FROM {table} WHERE ingest_batch_id=?",
                            (batch["batch_id"],))]
                        assert len(ids) == batch["counts"][table]
                        assert all(item.startswith(f"{course}-{batch['chapter']}-") for item in ids)
                        stamped[batch["batch_id"]][table] = ids
                assert counts(applied_state)["ingest_batches"] == counts(baseline)["ingest_batches"] + len(stamped)
            for index, batch in enumerate(applied["batches"], 1):
                rolled = ingest.rollback_batch(database, batch["batch_id"],
                                                backup_path=scratch / f"rollback-{index:03d}.db")
                assert all(rolled["counts"][table] == batch["counts"][table]
                           for table in (*CONTENT, "figures"))
                assert rolled["deleted"] == sum(batch["counts"][table] for table in CONTENT)
                with closing(sqlite3.connect(database)) as conn:
                    preserve_existing(baseline, snapshot(conn))
                    for table, id_column in CONTENT.items():
                        assert conn.execute(f"SELECT COUNT(*) FROM {table} WHERE ingest_batch_id=?",
                                            (batch["batch_id"],)).fetchone()[0] == 0
                    for sibling in applied["batches"][index:]:
                        for table, ids in stamped[sibling["batch_id"]].items():
                            assert conn.execute(f"SELECT COUNT(*) FROM {table} WHERE ingest_batch_id=?",
                                                (sibling["batch_id"],)).fetchone()[0] == len(ids)
            with closing(sqlite3.connect(database)) as conn:
                final = snapshot(conn)
                for table in (*CONTENT, *LEARNING):
                    if table in baseline:
                        assert final[table] == baseline[table], f"rollback changed {table} baseline"
                for batch in applied["batches"]:
                    assert conn.execute("SELECT rolled_back_at FROM ingest_batches WHERE batch_id=?",
                                        (batch["batch_id"],)).fetchone()[0] is not None
            report["verification_only_copy_inserts"] = {
                "counts": applied["counts"], "chapter_batch_stamps": stamped,
                "malformed_refusal_atomic": True, "real_stem_duplicate_refusal_atomic": True,
                "existing_rows_unchanged": True, "rollback_content_learning_restored": True,
                "sibling_preserved": True, "rolled_back_ledger_retained": True}
        assert snapshot(source) == source_before and source.total_changes == 0
        assert registry_path.read_bytes() == registry_before
        report["source_zero_write"] = {"mode": "ro", "query_only": True,
                                        "total_changes": source.total_changes,
                                        "rows_schema_batches_unchanged": True,
                                        "registry_unchanged": True}
        report["ok"] = True
        return report
    finally:
        source.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="exact registered workspace name")
    parser.add_argument("--audit-before", type=Path, help="explicit read-only historical DB")
    args = parser.parse_args()
    print(json.dumps(run(args.workspace, args.audit_before), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
