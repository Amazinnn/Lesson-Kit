"""Flash-card contract tests: domain rules, ingest recipe, pull-cards, feedback."""

import json
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from workbench import ingest
from workbench.domain import cards
from workbench.server import api


def manifest_item(card_id="dmath-ch06-fc-001", kp_id="dmath-ch06-kp-001",
                  front="鸽巢原理说的是？",
                  back="把 n+1 只鸽子放进 n 个巢，必有一巢至少两只。", **extra):
    item = {"card_id": card_id, "kp_id": kp_id, "front": front, "back": back,
            "source_evidence": "Rosen 6th, §6.2 定理 1"}
    item.update(extra)
    return item


class CardRulesTests(unittest.TestCase):
    def test_field_contract(self):
        self.assertEqual(cards.validate_card_row(manifest_item()), [])
        missing = cards.validate_card_row({"card_id": "dmath-ch06-fc-009"})
        self.assertEqual(len(missing), 4)
        too_long = cards.validate_card_row(manifest_item(front="长" * 101))
        self.assertTrue(any("front exceeds" in e for e in too_long))
        long_back = cards.validate_card_row(manifest_item(back="长" * 301))
        self.assertTrue(any("back exceeds" in e for e in long_back))

    def test_card_id_pattern(self):
        self.assertTrue(cards.is_valid_card_id("dmath-ch06-fc-001"))
        self.assertTrue(cards.is_valid_card_id("kp-001-fc-012"))
        self.assertFalse(cards.is_valid_card_id("dmath-ch06-fc-1"))
        self.assertFalse(cards.is_valid_card_id("dmath-ch06-mq-001"))


class CardIngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "pool.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY,
                knowledge_item TEXT);
            CREATE TABLE problems (problem_id TEXT PRIMARY KEY,
                kp_ids TEXT NOT NULL, problem_text TEXT NOT NULL,
                solution TEXT, problem_type TEXT, source_kind TEXT,
                practice_modes TEXT, micro_quiz TEXT);
            CREATE TABLE candidate_problems (candidate_id TEXT PRIMARY KEY,
                problem_text TEXT);
            CREATE TABLE knowledge_relations (relation_id TEXT PRIMARY KEY,
                source_kp_id TEXT, target_kp_id TEXT);
            CREATE TABLE flash_cards (card_id TEXT PRIMARY KEY,
                kp_id TEXT NOT NULL, front TEXT NOT NULL, back TEXT NOT NULL,
                source_evidence TEXT NOT NULL);
        """)
        conn.execute("INSERT INTO knowledge_points VALUES ('dmath-ch06-kp-001', 'Counting')")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def manifest(self, items):
        path = self.root / "fc.json"
        path.write_text(json.dumps(
            {"kind": "flash-card-patch", "items": items}, ensure_ascii=False,
        ), encoding="utf-8")
        return path

    def test_gate_and_apply_insert_contract_rows(self):
        path = self.manifest([manifest_item()])
        conn = sqlite3.connect(self.db_path)
        try:
            report = ingest._gate_flash_cards(
                conn, json.loads(path.read_text(encoding="utf-8")))
        finally:
            conn.close()
        self.assertTrue(report["ok"], report["errors"])
        result = ingest.apply_flash_cards(self.db_path, path)
        self.assertTrue(result["applied"])
        self.assertTrue(Path(result["backup_path"]).exists())
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT kp_id, front, back, source_evidence FROM flash_cards"
                " WHERE card_id='dmath-ch06-fc-001'"
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(row, ("dmath-ch06-kp-001", manifest_item()["front"],
                               manifest_item()["back"], manifest_item()["source_evidence"]))

    def test_bad_items_are_rejected_without_writing(self):
        items = [
            manifest_item(),
            manifest_item(card_id="dmath-ch06-fc-002", kp_id="kp-missing"),
            manifest_item(card_id="dmath-ch06-fc-003", source_evidence=""),
            manifest_item(card_id="dmath-ch06-fc-004", front="长" * 101),
            manifest_item(card_id="not-an-id"),
        ]
        path = self.manifest(items)
        conn = sqlite3.connect(self.db_path)
        try:
            report = ingest._gate_flash_cards(
                conn, json.loads(path.read_text(encoding="utf-8")))
        finally:
            conn.close()
        self.assertFalse(report["ok"])
        self.assertGreaterEqual(len(report["errors"]), 4)
        conn = sqlite3.connect(self.db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM flash_cards").fetchone()[0]
        except sqlite3.OperationalError:
            count = 0
        finally:
            conn.close()
        self.assertEqual(count, 0)

    def test_recipe_apply_and_duplicate_rejection(self):
        path = self.manifest([manifest_item()])
        recipe = ingest.recipe("flash-card", self.db_path, path, self.root,
                               apply_changes=True, backup_path=self.root / "bak.db")
        self.assertTrue(recipe["applied"])
        with self.assertRaises(ValueError):
            ingest.recipe("flash-card", self.db_path, path, self.root,
                          apply_changes=True, backup_path=self.root / "bak2.db")
        conn = sqlite3.connect(self.db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM flash_cards").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 1)


class CardPracticeTests(unittest.TestCase):
    def setUp(self):
        from tests.workbench.fixtures import WorkspaceFixture
        self.fixture = WorkspaceFixture()
        conn = sqlite3.connect(self.fixture.db_path)
        conn.executemany(
            "INSERT INTO flash_cards (card_id, kp_id, front, back, source_evidence)"
            " VALUES (?, ?, ?, ?, ?)",
            [
                ("dmath-ch06-fc-001", "dmath-ch06-kp-001", "正面前排", "背面后排", "src"),
                ("dmath-ch06-fc-002", "dmath-ch06-kp-001", "正面前二", "背面后二", "src"),
            ],
        )
        conn.execute(
            "INSERT INTO review_schedule (item_type, item_id, direction, due_at)"
            " VALUES ('card', 'dmath-ch06-fc-002', '', ?)",
            (date.today().isoformat(),),
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        self.fixture.cleanup()

    def pool(self):
        from workbench.data.pool import Pool
        return Pool(root=self.fixture.ws, db_path=self.fixture.db_path,
                    course="dmath", chapter="ch06")

    def test_pull_cards_due_first_and_scope_and_exclude(self):
        pool = self.pool()
        try:
            result = api.pull_cards(pool, {}, {}, {
                "kp_ids": ["dmath-ch06-kp-001"],
            })
            self.assertEqual(
                [c["card_id"] for c in result["cards"]],
                ["dmath-ch06-fc-002", "dmath-ch06-fc-001"],
            )
            result = api.pull_cards(pool, {}, {}, {
                "kp_ids": ["dmath-ch06-kp-001"],
                "exclude_ids": ["dmath-ch06-fc-002", "dmath-ch06-fc-001"],
            })
            self.assertEqual(result["cards"], [])
        finally:
            pool.close()

    def test_pull_cards_rejects_unknown_kp(self):
        pool = self.pool()
        try:
            with self.assertRaises(api.ApiError):
                api.pull_cards(pool, {}, {}, {"kp_ids": ["kp-missing"]})
        finally:
            pool.close()

    def test_feedback_card_writes_schedule_signal_and_state(self):
        from workbench.domain import feedback
        pool = self.pool()
        try:
            changes = feedback.apply(
                pool, "card", "dmath-ch06-fc-001", rating=2, note="想不起来")
            row = pool.schedule_get("card", "dmath-ch06-fc-001")
            self.assertIsNotNone(row)
            self.assertIsNotNone(row["due_at"])
            state = pool.current_state("kp", "dmath-ch06-kp-001")
            self.assertEqual(state["state"], "needs_work")
            signals = [s for s in pool.signals()
                       if s["target_id"] == "dmath-ch06-kp-001"]
            self.assertEqual(len(signals), 1)
            events = pool.feedback_events("card", "dmath-ch06-fc-001")
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["rating"], 2)
        finally:
            pool.close()

    def test_review_overview_labels_cards(self):
        from workbench.data import queries
        pool = self.pool()
        try:
            overview = queries.review_overview(pool)
            card_items = [i for i in overview["items"]
                          if i["item_type"] == "card"]
            self.assertEqual(len(card_items), 1)
            self.assertEqual(card_items[0]["item_id"], "dmath-ch06-fc-002")
            self.assertEqual(card_items[0]["label"], "正面前二")
        finally:
            pool.close()


class CardSchemaMigrationTests(unittest.TestCase):
    def test_old_check_tables_are_widened_and_marks_replaced(self):
        from tests.workbench.fixtures import load_script
        tmp = tempfile.TemporaryDirectory()
        try:
            db_path = Path(tmp.name) / "pool.db"
            conn = sqlite3.connect(db_path)
            conn.executescript("""
                CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY,
                    knowledge_item TEXT);
                CREATE TABLE problems (problem_id TEXT PRIMARY KEY,
                    kp_ids TEXT NOT NULL, problem_text TEXT NOT NULL,
                    solution TEXT, problem_type TEXT, source_kind TEXT,
                    practice_modes TEXT, micro_quiz TEXT);
                CREATE TABLE candidate_problems (candidate_id TEXT PRIMARY KEY,
                    problem_text TEXT);
                CREATE TABLE knowledge_relations (relation_id TEXT PRIMARY KEY,
                    source_kp_id TEXT, target_kp_id TEXT);
                CREATE TABLE review_schedule (
                    item_type TEXT NOT NULL CHECK (item_type IN ('kp', 'problem')),
                    item_id TEXT NOT NULL,
                    direction TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL DEFAULT 'learning',
                    repetitions INTEGER NOT NULL DEFAULT 0,
                    ease REAL NOT NULL DEFAULT 2.5,
                    interval_days REAL NOT NULL DEFAULT 0,
                    due_at TEXT,
                    last_rating INTEGER,
                    last_reviewed_at TEXT,
                    PRIMARY KEY (item_type, item_id, direction)
                );
                CREATE TABLE feedback_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_type TEXT NOT NULL CHECK (item_type IN ('kp', 'problem')),
                    item_id TEXT NOT NULL,
                    rating INTEGER,
                    note TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                INSERT INTO problems VALUES ('p-1', '["kp-1"]', 't', NULL,
                    'other', 'quiz', '["flash_card"]', NULL);
                INSERT INTO review_schedule (item_type, item_id) VALUES ('kp', 'kp-1');
                INSERT INTO feedback_events (item_type, item_id, rating) VALUES ('problem', 'p-1', 3);
            """)
            conn.commit()
            schema = load_script("pool_schema_cards", "pool/scripts/pool_schema.py")
            changes = schema.ensure_workbench_schema(conn)
            conn.commit()

            for table in ("review_schedule", "feedback_events"):
                sql = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)).fetchone()[0]
                self.assertIn("'card'", sql, table)
            self.assertIn("flash_cards", changes)
            # Existing data survives the rebuild.
            rows = conn.execute(
                "SELECT item_type, item_id FROM review_schedule").fetchall()
            self.assertEqual(rows, [("kp", "kp-1")])
            events = conn.execute("SELECT item_type, rating FROM feedback_events").fetchall()
            self.assertEqual(events, [("problem", 3)])
            # New item types are accepted.
            conn.execute(
                "INSERT INTO review_schedule (item_type, item_id, direction)"
                " VALUES ('card', 'c-1', '')")
            conn.execute(
                "INSERT INTO feedback_events (item_type, item_id, rating)"
                " VALUES ('card', 'c-1', 4)")
            # Marks migrated to the renamed mode.
            marks = conn.execute(
                "SELECT practice_modes FROM problems WHERE problem_id='p-1'"
            ).fetchone()[0]
            self.assertEqual(json.loads(marks), ["micro"])
            conn.close()
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
