"""End-to-end regression for authored figure references plus binary mirroring."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from workbench.data import content_mirror, figure_mirror
from workbench.data.pool import Pool


class ContentMirrorFigureRoundTripTests(unittest.TestCase):
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
                figure_paths TEXT
            );
            CREATE TABLE problems (
                problem_id TEXT PRIMARY KEY,
                figure_paths TEXT
            );
            """
        )
        self.logical = "c02/ch01/diagram.png"
        conn.execute(
            "INSERT INTO problems (problem_id, figure_paths) VALUES (?, ?)",
            ("c02-ch01-prob-001", json.dumps([self.logical])),
        )
        conn.commit()
        conn.close()
        self.pool = Pool(self.root, self.db_path, course="c02", chapter="ch01")

        self.entity_path = content_mirror.entity_path(
            self.repo, "c02", "problem", "c02-ch01-prob-001"
        )
        self.entity_path.parent.mkdir(parents=True, exist_ok=True)
        self.entity_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "entity_type": "problem",
                    "entity_id": "c02-ch01-prob-001",
                    "revision": 1,
                    "content": {"figure_paths": [self.logical]},
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        self.figure_bytes = b"lesson-kit-figure-roundtrip"
        self.workspace_figure = self.root / "figures" / self.logical
        self.workspace_figure.parent.mkdir(parents=True, exist_ok=True)
        self.workspace_figure.write_bytes(self.figure_bytes)

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def test_json_reference_and_binary_figure_round_trip(self):
        envelope = content_mirror.read_entity(
            self.entity_path, "c02", expected_type="problem"
        )
        self.assertEqual(envelope["content"]["figure_paths"], [self.logical])

        pushed = figure_mirror.sync(self.pool, self.repo, direction="push")
        self.assertTrue(pushed["valid"])
        self.assertEqual(pushed["applied"], 1)

        repository_figure = self.repo / "figures" / self.logical
        self.assertEqual(repository_figure.read_bytes(), self.figure_bytes)

        index = json.loads(
            (self.repo / "figures" / "c02" / "_index.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(index["course_id"], "c02")
        self.assertEqual(index["figures"][0]["logical_path"], self.logical)
        self.assertEqual(
            index["figures"][0]["owners"],
            [{"owner_type": "problem", "owner_id": "c02-ch01-prob-001"}],
        )

        self.workspace_figure.unlink()
        pulled = figure_mirror.sync(self.pool, self.repo, direction="pull")
        self.assertTrue(pulled["valid"])
        self.assertEqual(pulled["applied"], 1)

        canonical, legacy = figure_mirror.workspace_paths(self.pool, self.logical)
        self.assertEqual(canonical.read_bytes(), self.figure_bytes)
        self.assertEqual(legacy.read_bytes(), self.figure_bytes)


if __name__ == "__main__":
    unittest.main()
