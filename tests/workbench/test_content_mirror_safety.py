"""Safety regressions for path-independent JSON mirror identity."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from workbench.data import content_mirror
from workbench.data.pool import Pool


class MirrorSafetyTests(unittest.TestCase):
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
                fragile TEXT
            );
            CREATE TABLE problems (problem_id TEXT PRIMARY KEY);
            CREATE TABLE knowledge_relations (relation_id TEXT PRIMARY KEY);
            CREATE TABLE content_mirror_state (
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                revision INTEGER NOT NULL,
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
            INSERT INTO knowledge_points (
                kp_id, knowledge_item, graph_label, source_location, knowledge_type,
                related_kp_ids, importance, learning_action, body, difficulty, fragile
            ) VALUES (
                'c02-ch01-kp-001', 'Stack', 'Stack', '§1.1', 'concept',
                '[]', 'core', 'practice', 'LIFO', 2, NULL
            );
            """
        )
        conn.commit()
        conn.close()
        self.pool = Pool(self.root, self.db_path, course="c02", chapter="ch01")
        content_mirror.init(self.pool, self.repo)
        self.canonical = content_mirror.entity_path(
            self.repo, "c02", "kp", "c02-ch01-kp-001"
        )

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def test_renamed_file_keeps_identity_and_is_updated_in_place(self):
        renamed = self.canonical.parent / "renamed" / "stack-concept.json"
        renamed.parent.mkdir()
        self.canonical.rename(renamed)
        self.pool.connect().execute(
            "UPDATE knowledge_points SET knowledge_item='Stack ADT' "
            "WHERE kp_id='c02-ch01-kp-001'"
        )
        self.pool.connect().commit()

        result = content_mirror.sync(self.pool, self.repo)

        self.assertEqual(result["counts"].get("exported"), 1)
        self.assertFalse(self.canonical.exists())
        envelope = json.loads(renamed.read_text(encoding="utf-8"))
        self.assertEqual(envelope["entity_id"], "c02-ch01-kp-001")
        self.assertEqual(envelope["revision"], 2)
        self.assertEqual(envelope["content"]["knowledge_item"], "Stack ADT")

    def test_malformed_json_is_never_overwritten_as_missing_file(self):
        broken = "{ definitely not valid json"
        self.canonical.write_text(broken, encoding="utf-8")

        result = content_mirror.sync(self.pool, self.repo)

        self.assertFalse(result["valid"])
        self.assertGreaterEqual(result["counts"].get("invalid", 0), 1)
        self.assertEqual(self.canonical.read_text(encoding="utf-8"), broken)
        self.assertEqual(
            self.pool.connect().execute(
                "SELECT knowledge_item FROM knowledge_points "
                "WHERE kp_id='c02-ch01-kp-001'"
            ).fetchone()[0],
            "Stack",
        )

    def test_duplicate_entity_id_blocks_both_files_instead_of_picking_one(self):
        alias = self.canonical.with_name("alias.json")
        alias.write_text(self.canonical.read_text(encoding="utf-8"), encoding="utf-8")
        self.pool.connect().execute(
            "UPDATE knowledge_points SET knowledge_item='Pool-side edit' "
            "WHERE kp_id='c02-ch01-kp-001'"
        )
        self.pool.connect().commit()

        result = content_mirror.sync(self.pool, self.repo)

        self.assertFalse(result["valid"])
        self.assertGreaterEqual(result["counts"].get("invalid", 0), 1)
        self.assertEqual(
            json.loads(self.canonical.read_text(encoding="utf-8"))["revision"], 1
        )
        self.assertEqual(json.loads(alias.read_text(encoding="utf-8"))["revision"], 1)

    def test_init_adopts_a_renamed_file_by_embedded_identity(self):
        envelope = json.loads(self.canonical.read_text(encoding="utf-8"))
        self.canonical.unlink()
        alias = self.canonical.parent / "renamed" / "stack-concept.json"
        alias.parent.mkdir()
        alias.write_text(json.dumps(envelope), encoding="utf-8")
        self.pool.connect().execute("DELETE FROM content_mirror_state")
        self.pool.connect().execute("DELETE FROM content_mirror_log")
        self.pool.connect().commit()

        result = content_mirror.init(self.pool, self.repo)

        self.assertTrue(result["valid"])
        self.assertTrue(alias.exists())
        self.assertFalse(self.canonical.exists())
        self.assertEqual(
            self.pool.connect().execute(
                "SELECT COUNT(*) FROM content_mirror_state "
                "WHERE entity_type='kp' AND entity_id='c02-ch01-kp-001'"
            ).fetchone()[0],
            1,
        )

    def test_invalid_utf8_file_does_not_abort_valid_sibling_sync(self):
        envelope = json.loads(self.canonical.read_text(encoding="utf-8"))
        envelope["revision"] = 2
        envelope["content"]["knowledge_item"] = "Edited Stack"
        self.canonical.write_text(json.dumps(envelope), encoding="utf-8")
        corrupt = self.canonical.with_name("unreadable.json")
        corrupt.write_bytes(b'{"invalid":"\xff"}')

        result = content_mirror.sync(self.pool, self.repo)

        self.assertFalse(result["valid"])
        self.assertEqual(result["counts"].get("applied"), 1)
        self.assertEqual(self.pool.kp("c02-ch01-kp-001")["knowledge_item"], "Edited Stack")
        self.assertGreaterEqual(result["counts"].get("invalid", 0), 1)

    def test_changed_embedded_id_does_not_restore_over_the_file(self):
        envelope = json.loads(self.canonical.read_text(encoding="utf-8"))
        envelope["entity_id"] = "c02-ch01-kp-999"
        self.canonical.write_text(json.dumps(envelope), encoding="utf-8")

        result = content_mirror.sync(self.pool, self.repo)

        self.assertFalse(result["valid"])
        tracked = next(
            item for item in result["items"]
            if item.get("entity_id") == "c02-ch01-kp-001"
        )
        self.assertEqual(tracked["status"], "invalid")
        self.assertIn("identity", tracked.get("detail", "").lower())
        self.assertEqual(
            json.loads(self.canonical.read_text(encoding="utf-8"))["entity_id"],
            "c02-ch01-kp-999",
        )

    def test_schema_version_requires_an_integer_and_entity_type_requires_a_string(self):
        envelope = json.loads(self.canonical.read_text(encoding="utf-8"))
        for version in (True, 1.0):
            invalid = {**envelope, "schema_version": version}
            self.canonical.write_text(json.dumps(invalid), encoding="utf-8")
            with self.subTest(schema_version=version):
                with self.assertRaises(content_mirror.MirrorError):
                    content_mirror.read_entity(self.canonical, "c02", "kp")

        invalid = {**envelope, "entity_type": []}
        self.canonical.write_text(json.dumps(invalid), encoding="utf-8")
        with self.assertRaises(content_mirror.MirrorError):
            content_mirror.read_entity(self.canonical, "c02", "kp")

        for field, value in (("kp_ids", "[]"), ("micro_quiz", [])):
            invalid = {
                "schema_version": 1,
                "entity_type": "problem",
                "entity_id": "c02-ch01-prob-001",
                "revision": 1,
                "content": {field: value},
            }
            self.canonical.write_text(json.dumps(invalid), encoding="utf-8")
            with self.subTest(field=field):
                with self.assertRaises(content_mirror.MirrorError):
                    content_mirror.read_entity(self.canonical, "c02", "problem")

    def test_invalid_delete_request_json_types_are_reported_per_file(self):
        folder = self.repo / "delete-requests"
        folder.mkdir()
        (folder / "invalid.json").write_text(json.dumps({
            "schema_version": True,
            "request_id": "delete-001",
            "course_id": "c02",
            "entity_type": [],
            "entity_id": "c02-ch01-kp-001",
            "reason": "test",
        }), encoding="utf-8")

        result = content_mirror.plan(self.pool, self.repo)

        self.assertEqual(result["delete_requests"][0]["status"], "invalid")
        self.assertIn("schema_version", result["delete_requests"][0]["error"])


if __name__ == "__main__":
    unittest.main()
