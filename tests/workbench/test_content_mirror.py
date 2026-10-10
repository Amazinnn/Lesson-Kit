"""Contract tests for the Git-backed authored-content JSON projection."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from workbench.data import content_mirror
from workbench.data.pool import Pool


class ContentMirrorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "workspace"
        self.repo = Path(self.tmp.name) / "content-repo"
        (self.root / "pool").mkdir(parents=True)
        self.db_path = self.root / "pool" / "c02.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE knowledge_points (
                kp_id TEXT PRIMARY KEY,
                knowledge_item TEXT NOT NULL,
                graph_label TEXT,
                source_location TEXT,
                knowledge_type TEXT,
                related_kp_ids TEXT,
                importance TEXT,
                learning_action TEXT,
                body TEXT,
                difficulty INTEGER,
                fragile TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE problems (
                problem_id TEXT PRIMARY KEY,
                kp_ids TEXT NOT NULL,
                problem_text TEXT NOT NULL,
                solution TEXT,
                problem_type TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                origin_kind TEXT NOT NULL DEFAULT 'source_problem',
                display_title TEXT,
                display_summary TEXT,
                figure_paths TEXT,
                exam_year TEXT,
                source_evidence TEXT,
                source_answer TEXT,
                solution_origin TEXT,
                practice_modes TEXT,
                micro_quiz TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE knowledge_relations (
                relation_id TEXT PRIMARY KEY,
                source_kp_id TEXT NOT NULL,
                target_kp_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                strength TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(source_kp_id, target_kp_id, relation_type)
            );
            CREATE TABLE problem_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id TEXT NOT NULL,
                status TEXT NOT NULL,
                answer_text TEXT
            );
            CREATE TABLE content_mirror_state (
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK (revision > 0),
                content_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY(entity_type, entity_id)
            );
            CREATE TABLE content_mirror_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                direction TEXT NOT NULL,
                from_revision INTEGER,
                to_revision INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            "INSERT INTO knowledge_points "
            "(kp_id, knowledge_item, graph_label, source_location, knowledge_type, "
            " related_kp_ids, importance, learning_action, body, difficulty, fragile) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "c02-ch01-kp-001", "Stack", "Stack", "§1.1", "concept",
                "[]", "core", "practice", "A **stack** uses LIFO. $O(1)$ push.", 2, None,
            ),
        )
        conn.execute(
            "INSERT INTO knowledge_points "
            "(kp_id, knowledge_item, graph_label, source_location, knowledge_type, "
            " related_kp_ids, importance, learning_action, body, difficulty, fragile) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "c02-ch01-kp-002", "Queue", "Queue", "§1.2", "concept",
                "[]", "normal", "practice", "A queue uses FIFO.", 2, None,
            ),
        )
        conn.execute(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind, origin_kind) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "c02-ch01-prob-001", '["c02-ch01-kp-001"]',
                "What is LIFO?", "Last in, first out.", "explanation", "textbook",
                "source_problem",
            ),
        )
        conn.execute(
            "INSERT INTO knowledge_relations "
            "(relation_id, source_kp_id, target_kp_id, relation_type, direction, strength) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "c02-ch01-rel-001", "c02-ch01-kp-001", "c02-ch01-kp-002",
                "contrasts", "symmetric", "medium",
            ),
        )
        conn.execute(
            "INSERT INTO problem_attempts (problem_id, status, answer_text) VALUES (?, ?, ?)",
            ("c02-ch01-prob-001", "wrong", "runtime learner answer"),
        )
        conn.commit()
        conn.close()
        self.pool = Pool(self.root, self.db_path, course="c02", chapter="ch01")

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def entity_json(self, entity_type, entity_id):
        path = content_mirror.entity_path(self.repo, "c02", entity_type, entity_id)
        return path, json.loads(path.read_text(encoding="utf-8"))

    def test_bootstrap_writes_one_entity_per_json_without_runtime_state(self):
        result = content_mirror.init(self.pool, self.repo)
        self.assertTrue(result["valid"])
        self.assertEqual(result["counts"]["initialized"], 4)
        path, problem = self.entity_json("problem", "c02-ch01-prob-001")
        self.assertTrue(path.exists())
        self.assertEqual(problem["revision"], 1)
        self.assertEqual(problem["content"]["problem_text"], "What is LIFO?")
        self.assertNotIn("attempts", problem["content"])
        self.assertNotIn("created_at", problem["content"])
        self.assertNotIn("updated_at", problem["content"])
        self.assertNotIn("runtime learner answer", path.read_text(encoding="utf-8"))

    def test_repository_edit_with_next_revision_updates_pool(self):
        content_mirror.init(self.pool, self.repo)
        path, envelope = self.entity_json("kp", "c02-ch01-kp-001")
        envelope["revision"] = 2
        envelope["content"]["body"] = "Edited from Git with $\\Theta(n)$ math."
        path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        dry = content_mirror.sync(self.pool, self.repo, dry_run=True)
        self.assertEqual(dry["counts"]["repo_to_pool"], 1)
        self.assertEqual(
            self.pool.connect().execute(
                "SELECT body FROM knowledge_points WHERE kp_id='c02-ch01-kp-001'"
            ).fetchone()[0],
            "A **stack** uses LIFO. $O(1)$ push.",
        )

        result = content_mirror.sync(self.pool, self.repo)
        self.assertEqual(result["counts"]["applied"], 1)
        self.assertEqual(
            self.pool.connect().execute(
                "SELECT body FROM knowledge_points WHERE kp_id='c02-ch01-kp-001'"
            ).fetchone()[0],
            "Edited from Git with $\\Theta(n)$ math.",
        )

    def test_repository_problem_edit_normalizes_pool_ledger_and_json(self):
        self.pool.connect().execute(
            "UPDATE problems SET exam_year='2022' WHERE problem_id='c02-ch01-prob-001'"
        )
        self.pool.connect().commit()
        content_mirror.init(self.pool, self.repo)
        path, envelope = self.entity_json("problem", "c02-ch01-prob-001")
        envelope["revision"] = 2
        envelope["content"]["exam_year"] = ""
        path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = content_mirror.sync(self.pool, self.repo)

        self.assertTrue(result["valid"])
        self.assertEqual(result["counts"]["applied"], 1)
        self.assertIsNone(self.pool.problem("c02-ch01-prob-001")["exam_year"])
        self.assertIsNone(self.entity_json("problem", "c02-ch01-prob-001")[1]["content"]["exam_year"])
        state = self.pool.connect().execute(
            "SELECT revision, content_json FROM content_mirror_state "
            "WHERE entity_type='problem' AND entity_id='c02-ch01-prob-001'"
        ).fetchone()
        self.assertEqual(state["revision"], 2)
        self.assertIsNone(json.loads(state["content_json"])["exam_year"])

    def test_repository_edit_rolls_back_when_mirror_log_write_fails(self):
        content_mirror.init(self.pool, self.repo)
        path, envelope = self.entity_json("problem", "c02-ch01-prob-001")
        envelope["revision"] = 2
        envelope["content"]["display_title"] = "Changed title"
        path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.pool.connect().execute(
            "CREATE TRIGGER reject_mirror_log BEFORE INSERT ON content_mirror_log "
            "WHEN NEW.direction='repo_to_pool' BEGIN "
            "SELECT RAISE(ABORT, 'injected mirror log failure'); END"
        )
        self.pool.connect().commit()

        result = content_mirror.sync(self.pool, self.repo)

        self.assertFalse(result["valid"])
        self.assertEqual(self.pool.problem("c02-ch01-prob-001")["display_title"], None)
        state = self.pool.connect().execute(
            "SELECT revision, content_json FROM content_mirror_state "
            "WHERE entity_type='problem' AND entity_id='c02-ch01-prob-001'"
        ).fetchone()
        self.assertEqual(state["revision"], 1)
        self.assertIsNone(json.loads(state["content_json"])["display_title"])
        self.assertEqual(
            self.pool.connect().execute(
                "SELECT COUNT(*) FROM content_mirror_log WHERE direction='repo_to_pool'"
            ).fetchone()[0],
            0,
        )

    def test_pool_edit_exports_as_next_revision(self):
        content_mirror.init(self.pool, self.repo)
        self.pool.connect().execute(
            "UPDATE knowledge_points SET knowledge_item=? WHERE kp_id=?",
            ("Stack ADT", "c02-ch01-kp-001"),
        )
        self.pool.connect().commit()

        result = content_mirror.sync(self.pool, self.repo)
        self.assertEqual(result["counts"]["exported"], 1)
        _path, envelope = self.entity_json("kp", "c02-ch01-kp-001")
        self.assertEqual(envelope["revision"], 2)
        self.assertEqual(envelope["content"]["knowledge_item"], "Stack ADT")

    def test_changed_repository_content_without_revision_bump_is_invalid(self):
        content_mirror.init(self.pool, self.repo)
        path, envelope = self.entity_json("kp", "c02-ch01-kp-001")
        envelope["content"]["body"] = "changed but revision stayed one"
        path.write_text(json.dumps(envelope, ensure_ascii=False), encoding="utf-8")

        result = content_mirror.sync(self.pool, self.repo)
        bad = next(item for item in result["items"] if item.get("entity_id") == "c02-ch01-kp-001")
        self.assertEqual(bad["status"], "invalid")
        self.assertIn("advance revision", bad["detail"])

    def test_two_sided_different_edits_conflict(self):
        content_mirror.init(self.pool, self.repo)
        path, envelope = self.entity_json("kp", "c02-ch01-kp-001")
        envelope["revision"] = 2
        envelope["content"]["body"] = "repo edit"
        path.write_text(json.dumps(envelope, ensure_ascii=False), encoding="utf-8")
        self.pool.connect().execute(
            "UPDATE knowledge_points SET body='pool edit' WHERE kp_id='c02-ch01-kp-001'"
        )
        self.pool.connect().commit()

        result = content_mirror.sync(self.pool, self.repo)
        conflict = next(item for item in result["items"] if item.get("entity_id") == "c02-ch01-kp-001")
        self.assertEqual(conflict["status"], "conflict")
        self.assertEqual(
            self.pool.connect().execute(
                "SELECT body FROM knowledge_points WHERE kp_id='c02-ch01-kp-001'"
            ).fetchone()[0],
            "pool edit",
        )

    def test_missing_repo_file_is_restored_and_never_deletes_pool_row(self):
        content_mirror.init(self.pool, self.repo)
        path, _envelope = self.entity_json("problem", "c02-ch01-prob-001")
        path.unlink()

        result = content_mirror.sync(self.pool, self.repo)
        self.assertEqual(result["counts"]["restored"], 1)
        _path, restored = self.entity_json("problem", "c02-ch01-prob-001")
        self.assertEqual(restored["revision"], 2)
        self.assertIsNotNone(self.pool.problem("c02-ch01-prob-001"))
        attempts = self.pool.connect().execute(
            "SELECT COUNT(*) FROM problem_attempts WHERE problem_id='c02-ch01-prob-001'"
        ).fetchone()[0]
        self.assertEqual(attempts, 1)

    def test_deletion_request_is_reported_but_never_executed(self):
        content_mirror.init(self.pool, self.repo)
        folder = self.repo / "delete-requests"
        folder.mkdir(parents=True)
        (folder / "request-001.json").write_text(json.dumps({
            "schema_version": 1,
            "request_id": "request-001",
            "course_id": "c02",
            "entity_type": "problem",
            "entity_id": "c02-ch01-prob-001",
            "reason": "duplicate imported source",
        }), encoding="utf-8")

        result = content_mirror.sync(self.pool, self.repo)
        self.assertEqual(result["delete_requests"][0]["status"], "pending_non_executing")
        self.assertIsNotNone(self.pool.problem("c02-ch01-prob-001"))

    def test_repository_only_entity_is_refused_in_v1(self):
        content_mirror.init(self.pool, self.repo)
        path = content_mirror.entity_path(
            self.repo, "c02", "kp", "c02-ch01-kp-999"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema_version": 1,
            "entity_type": "kp",
            "entity_id": "c02-ch01-kp-999",
            "revision": 1,
            "content": {
                "knowledge_item": "New remote item"
            },
        }), encoding="utf-8")

        result = content_mirror.plan(self.pool, self.repo)
        row = next(item for item in result["items"] if item.get("entity_id") == "c02-ch01-kp-999")
        self.assertEqual(row["status"], "invalid")
        self.assertIn("remote creation", row["detail"])


if __name__ == "__main__":
    unittest.main()
