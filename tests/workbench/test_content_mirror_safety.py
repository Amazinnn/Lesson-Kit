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
        renamed = self.canonical.with_name("stack-concept.json")
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


if __name__ == "__main__":
    unittest.main()
