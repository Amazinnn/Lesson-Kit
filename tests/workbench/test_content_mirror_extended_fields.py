"""Extended authored-field coverage for the Git content mirror."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from workbench.data import content_mirror
from workbench.data.pool import Pool


class ExtendedContentMirrorFieldTests(unittest.TestCase):
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
                figure_paths TEXT
            );
            CREATE TABLE problems (
                problem_id TEXT PRIMARY KEY,
                kp_ids TEXT NOT NULL,
                problem_text TEXT NOT NULL,
                solution TEXT,
                problem_type TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                origin_kind TEXT NOT NULL,
                display_title TEXT,
                display_summary TEXT,
                figure_paths TEXT,
                exam_year TEXT,
                source_evidence TEXT,
                source_answer TEXT,
                solution_origin TEXT,
                practice_modes TEXT,
                micro_quiz TEXT,
                difficulty REAL,
                difficulty_knowledge_breadth INTEGER,
                difficulty_reasoning_depth INTEGER,
                difficulty_transfer_distance INTEGER,
                difficulty_construction_openness INTEGER,
                difficulty_model TEXT
            );
            CREATE TABLE knowledge_relations (
                relation_id TEXT PRIMARY KEY,
                source_kp_id TEXT NOT NULL,
                target_kp_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                strength TEXT NOT NULL,
                UNIQUE(source_kp_id, target_kp_id, relation_type)
            );
            CREATE TABLE content_mirror_state (
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                revision INTEGER NOT NULL,
                content_json TEXT NOT NULL,
                updated_at TEXT,
                PRIMARY KEY(entity_type, entity_id)
            );
            CREATE TABLE content_mirror_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                direction TEXT NOT NULL,
                from_revision INTEGER,
                to_revision INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            "INSERT INTO knowledge_points ("
            "kp_id, knowledge_item, related_kp_ids, figure_paths"
            ") VALUES (?, ?, ?, ?)",
            (
                "c02-ch01-kp-001", "Stack", "[]",
                '["c02/ch01/c02-ch01-kp-001-fig-001.png"]',
            ),
        )
        conn.execute(
            "INSERT INTO problems ("
            "problem_id, kp_ids, problem_text, solution, problem_type, source_kind, origin_kind, "
            "figure_paths, difficulty, difficulty_knowledge_breadth, difficulty_reasoning_depth, "
            "difficulty_transfer_distance, difficulty_construction_openness, difficulty_model"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "c02-ch01-prob-001", '["c02-ch01-kp-001"]', "Original stem", "Solution",
                "explanation", "textbook", "source_problem",
                '["c02/ch01/c02-ch01-prob-001-fig-001.png"]',
                2.0, 2, 2, 2, 2, "cognitive-v1-equal-mean",
            ),
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

    def problem_json(self):
        return self.entity_json("problem", "c02-ch01-prob-001")

    def kp_json(self):
        return self.entity_json("kp", "c02-ch01-kp-001")

    def test_bootstrap_includes_figure_paths_and_full_difficulty_group(self):
        result = content_mirror.init(self.pool, self.repo)

        self.assertTrue(result["valid"])
        _path, kp = self.kp_json()
        self.assertEqual(
            kp["content"]["figure_paths"],
            ["c02/ch01/c02-ch01-kp-001-fig-001.png"],
        )
        _path, envelope = self.problem_json()
        content = envelope["content"]
        self.assertEqual(
            content["figure_paths"],
            ["c02/ch01/c02-ch01-prob-001-fig-001.png"],
        )
        self.assertEqual(content["difficulty"], 2.0)
        self.assertEqual(content["difficulty_knowledge_breadth"], 2)
        self.assertEqual(content["difficulty_reasoning_depth"], 2)
        self.assertEqual(content["difficulty_transfer_distance"], 2)
        self.assertEqual(content["difficulty_construction_openness"], 2)
        self.assertEqual(content["difficulty_model"], "cognitive-v1-equal-mean")

    def test_repository_difficulty_dimensions_recompute_total_and_model(self):
        content_mirror.init(self.pool, self.repo)
        path, envelope = self.problem_json()
        envelope["revision"] = 2
        envelope["content"]["difficulty_reasoning_depth"] = 4
        path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = content_mirror.sync(self.pool, self.repo)

        self.assertTrue(result["valid"])
        row = self.pool.connect().execute(
            "SELECT difficulty, difficulty_reasoning_depth, difficulty_model FROM problems "
            "WHERE problem_id='c02-ch01-prob-001'"
        ).fetchone()
        self.assertEqual(tuple(row), (2.5, 4, "cognitive-v1-equal-mean"))
        _path, rewritten = self.problem_json()
        self.assertEqual(rewritten["content"]["difficulty"], 2.5)
        self.assertEqual(rewritten["content"]["difficulty_model"], "cognitive-v1-equal-mean")

    def test_repository_problem_figure_paths_round_trip_as_json_array(self):
        content_mirror.init(self.pool, self.repo)
        path, envelope = self.problem_json()
        envelope["revision"] = 2
        envelope["content"]["figure_paths"] = [
            "c02/ch01/c02-ch01-prob-001-fig-002.png"
        ]
        path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = content_mirror.sync(self.pool, self.repo)

        self.assertTrue(result["valid"])
        raw = self.pool.connect().execute(
            "SELECT figure_paths FROM problems WHERE problem_id='c02-ch01-prob-001'"
        ).fetchone()[0]
        self.assertEqual(
            json.loads(raw), ["c02/ch01/c02-ch01-prob-001-fig-002.png"]
        )

    def test_repository_kp_figure_paths_round_trip_as_json_array(self):
        content_mirror.init(self.pool, self.repo)
        path, envelope = self.kp_json()
        envelope["revision"] = 2
        envelope["content"]["figure_paths"] = [
            "c02/ch01/c02-ch01-kp-001-fig-002.png"
        ]
        path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = content_mirror.sync(self.pool, self.repo)

        self.assertTrue(result["valid"])
        raw = self.pool.connect().execute(
            "SELECT figure_paths FROM knowledge_points WHERE kp_id='c02-ch01-kp-001'"
        ).fetchone()[0]
        self.assertEqual(
            json.loads(raw), ["c02/ch01/c02-ch01-kp-001-fig-002.png"]
        )

    def test_existing_v1_projection_upgrades_without_becoming_invalid(self):
        content_mirror.init(self.pool, self.repo)
        path, envelope = self.problem_json()
        added = {
            "figure_paths",
            "difficulty",
            "difficulty_knowledge_breadth",
            "difficulty_reasoning_depth",
            "difficulty_transfer_distance",
            "difficulty_construction_openness",
            "difficulty_model",
        }
        old_content = {
            key: value for key, value in envelope["content"].items() if key not in added
        }
        envelope["content"] = old_content
        path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.pool.connect().execute(
            "UPDATE content_mirror_state SET content_json=? "
            "WHERE entity_type='problem' AND entity_id='c02-ch01-prob-001'",
            (json.dumps(old_content, ensure_ascii=False),),
        )
        self.pool.connect().commit()

        result = content_mirror.sync(self.pool, self.repo)

        self.assertTrue(result["valid"])
        self.assertEqual(result["counts"].get("exported"), 1)
        _path, upgraded = self.problem_json()
        self.assertEqual(upgraded["revision"], 2)
        self.assertTrue(added <= set(upgraded["content"]))

    def test_content_axis_edit_clears_stale_difficulty_in_pool_and_repo(self):
        content_mirror.init(self.pool, self.repo)
        path, envelope = self.problem_json()
        envelope["revision"] = 2
        envelope["content"]["problem_text"] = "Changed stem"
        path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = content_mirror.sync(self.pool, self.repo)

        self.assertTrue(result["valid"])
        row = self.pool.connect().execute(
            "SELECT difficulty, difficulty_knowledge_breadth, difficulty_reasoning_depth, "
            "difficulty_transfer_distance, difficulty_construction_openness, difficulty_model "
            "FROM problems WHERE problem_id='c02-ch01-prob-001'"
        ).fetchone()
        self.assertEqual(tuple(row), (None, None, None, None, None, None))
        _path, rewritten = self.problem_json()
        for field in content_mirror.PROBLEM_DIFFICULTY_FIELDS:
            self.assertIsNone(rewritten["content"][field])


if __name__ == "__main__":
    unittest.main()
