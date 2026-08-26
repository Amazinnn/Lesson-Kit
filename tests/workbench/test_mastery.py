"""Mastery v0 experiment tests (TDD: domain rules and read-only projection)."""

import sqlite3
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "workbench"))


def problem(problem_id, kp_ids, attempts=(), feedback=(), schedule=None):
    return {
        "id": problem_id,
        "kp_ids": list(kp_ids),
        "attempts": list(attempts),
        "feedback": list(feedback),
        "schedule": schedule,
    }


def kp(kp_id, feedback=(), schedule=None):
    return {"id": kp_id, "feedback": list(feedback), "schedule": schedule}


def attempt(status, created_at):
    return {"status": status, "created_at": created_at}


def rating(value, created_at, note=None):
    return {"rating": value, "created_at": created_at, "note": note}


class MasteryDomainTests(unittest.TestCase):
    def setUp(self):
        from domain import mastery

        self.mastery = mastery
        self.today = date(2026, 8, 26)

    def evaluate(self, problems=(), kps=(), candidates=()):
        return self.mastery.evaluate(
            {"problems": list(problems), "kps": list(kps), "candidates": list(candidates)},
            self.today,
        )

    def one_problem(self, result, problem_id="p1"):
        return next(item for item in result["problems"] if item["id"] == problem_id)

    def one_kp(self, result, kp_id="k1"):
        return next(item for item in result["knowledge_points"] if item["id"] == kp_id)

    def test_result_has_version_categories_chinese_explanation_and_reasons(self):
        result = self.evaluate(problems=[problem("p1", ["k1"])], kps=[kp("k1")])
        item = self.one_problem(result)
        self.assertEqual(result["version"], "v0")
        self.assertEqual(item["category"], "evidence_insufficient")
        self.assertIn("证据", item["explanation"])
        self.assertTrue(item["reasons"])

    def test_latest_decisive_negative_beats_positive_and_due(self):
        result = self.evaluate(
            problems=[problem(
                "p1", ["k1"],
                attempts=[attempt("mastered", "2026-08-20")],
                feedback=[rating(1, "2026-08-25")],
                schedule={"due_at": "2026-08-01"},
            )],
            kps=[kp("k1")],
        )
        item = self.one_problem(result)
        self.assertEqual(item["category"], "needs_work")
        self.assertEqual(item["reasons"][0]["date"], "2026-08-25")
        self.assertIn("1", item["reasons"][0]["evidence"])

    def test_due_follows_negative_precedence(self):
        result = self.evaluate(
            problems=[problem("p1", ["k1"], schedule={"due_at": "2026-08-26"})],
            kps=[kp("k1")],
        )
        self.assertEqual(self.one_problem(result)["category"], "due_review")

    def test_cross_date_strong_positive_establishes_problem_stability(self):
        result = self.evaluate(
            problems=[problem(
                "p1", ["k1"],
                attempts=[attempt("mastered", "2026-08-20")],
                feedback=[rating(4, "2026-08-21")],
            )],
            kps=[kp("k1")],
        )
        self.assertEqual(self.one_problem(result)["category"], "recently_stable")

    def test_production_mastered_attempt_is_strong_positive(self):
        result = self.evaluate(
            problems=[problem(
                "p1", ["k1"], attempts=[attempt("mastered", "2026-08-20T09:00:00")],
                feedback=[rating(4, "2026-08-21T10:00:00")],
            )],
            kps=[kp("k1")],
        )
        self.assertEqual(self.one_problem(result)["category"], "recently_stable")

    def test_later_decisive_positive_supersedes_an_older_negative(self):
        result = self.evaluate(
            problems=[problem(
                "p1", ["k1"],
                attempts=[
                    attempt("wrong", "2026-08-20T09:00:00"),
                    attempt("mastered", "2026-08-21T09:00:00"),
                ],
                feedback=[rating(4, "2026-08-22T09:00:00")],
            )],
            kps=[kp("k1")],
        )
        self.assertEqual(self.one_problem(result)["category"], "recently_stable")

    def test_reasons_keep_full_timestamps_for_traceability(self):
        result = self.evaluate(
            problems=[problem(
                "p1", ["k1"],
                feedback=[
                    rating(4, "2026-08-20T09:00:00"),
                    rating(5, "2026-08-20T10:00:00"),
                    rating(4, "2026-08-21T11:00:00"),
                ],
            )],
            kps=[kp("k1")],
        )
        timestamps = {reason["date"] for reason in self.one_problem(result)["reasons"]}
        self.assertIn("2026-08-21T11:00:00", timestamps)

    def test_three_positive_self_ratings_across_dates_establish_problem_stability(self):
        result = self.evaluate(
            problems=[problem(
                "p1", ["k1"],
                feedback=[
                    rating(4, "2026-08-20"), rating(5, "2026-08-20"),
                    rating(4, "2026-08-21"),
                ],
            )],
            kps=[kp("k1")],
        )
        self.assertEqual(self.one_problem(result)["category"], "recently_stable")

    def test_neutral_skip_note_and_rating_three_do_not_create_mastery_evidence(self):
        result = self.evaluate(
            problems=[problem(
                "p1", ["k1"], attempts=[attempt("skip", "2026-08-20")],
                feedback=[rating(3, "2026-08-21"), rating(None, "2026-08-22", "note")],
            )],
            kps=[kp("k1")],
        )
        self.assertEqual(self.one_problem(result)["category"], "evidence_insufficient")

    def test_formal_failure_propagates_to_every_linked_knowledge_point(self):
        result = self.evaluate(
            problems=[problem("p1", ["k1", "k2"], attempts=[attempt("wrong", "2026-08-25")])],
            kps=[kp("k1"), kp("k2")],
        )
        for kp_id in ("k1", "k2"):
            item = self.one_kp(result, kp_id)
            self.assertEqual(item["category"], "needs_work")
            self.assertEqual(item["reasons"][0]["item_id"], "p1")

    def test_direct_kp_negative_rating_has_negative_precedence(self):
        result = self.evaluate(
            problems=[problem("p1", ["k1"])],
            kps=[kp("k1", feedback=[rating(2, "2026-08-25")], schedule={"due_at": "2026-08-01"})],
        )
        item = self.one_kp(result)
        self.assertEqual(item["category"], "needs_work")
        self.assertIn("2", item["reasons"][0]["evidence"])

    def test_two_distinct_formal_problems_across_dates_establish_kp_stability(self):
        result = self.evaluate(
            problems=[
                problem("p1", ["k1"], attempts=[attempt("mastered", "2026-08-20")]),
                problem("p2", ["k1"], feedback=[rating(4, "2026-08-21")]),
            ],
            kps=[kp("k1")],
        )
        self.assertEqual(self.one_kp(result)["category"], "recently_stable")

    def test_candidate_positive_evidence_completes_kp_cross_date_evidence(self):
        result = self.evaluate(
            problems=[
                problem("p1", ["k1"], feedback=[rating(4, "2026-08-20T09:00:00")]),
                problem("p2", ["k1"], feedback=[rating(5, "2026-08-20T10:00:00")]),
            ],
            kps=[kp("k1")],
            candidates=[{
                "id": "c1", "kp_ids": ["k1"],
                "attempts": [{"status": "reviewing", "is_correct": 1, "created_at": "2026-08-21T09:00:00"}],
            }],
        )
        self.assertEqual(self.one_kp(result)["category"], "recently_stable")

    def test_single_formal_problem_requires_different_date_direct_kp_review(self):
        base = problem("p1", ["k1"], attempts=[attempt("mastered", "2026-08-20")])
        without_direct = self.evaluate(problems=[base], kps=[kp("k1")])
        with_direct = self.evaluate(
            problems=[base], kps=[kp("k1", feedback=[rating(5, "2026-08-21")])],
        )
        self.assertEqual(self.one_kp(without_direct)["category"], "evidence_insufficient")
        self.assertEqual(self.one_kp(with_direct)["category"], "recently_stable")

    def test_candidate_positive_does_not_replace_single_formal_problem_evidence(self):
        result = self.evaluate(
            problems=[problem("p1", ["k1"])],
            kps=[kp("k1", feedback=[rating(5, "2026-08-21T09:00:00")])],
            candidates=[{
                "id": "c1", "kp_ids": ["k1"],
                "attempts": [{"status": "reviewing", "is_correct": 1, "created_at": "2026-08-20T09:00:00"}],
            }],
        )
        self.assertEqual(self.one_kp(result)["category"], "evidence_insufficient")

    def test_candidate_date_does_not_replace_a_different_date_direct_review(self):
        result = self.evaluate(
            problems=[problem("p1", ["k1"], attempts=[attempt("mastered", "2026-08-20T08:00:00")])],
            kps=[kp("k1", feedback=[rating(5, "2026-08-20T09:00:00")])],
            candidates=[{
                "id": "c1", "kp_ids": ["k1"],
                "attempts": [{"status": "reviewing", "is_correct": 1,
                              "created_at": "2026-08-21T09:00:00"}],
            }],
        )
        item = self.one_kp(result)
        self.assertEqual(item["category"], "evidence_insufficient")

    def test_candidate_positive_reason_uses_a_truthful_label(self):
        result = self.evaluate(
            problems=[
                problem("p1", ["k1"], feedback=[rating(4, "2026-08-20T08:00:00")]),
                problem("p2", ["k1"], feedback=[rating(5, "2026-08-20T09:00:00")]),
            ],
            kps=[kp("k1")],
            candidates=[{
                "id": "c1", "kp_ids": ["k1"],
                "attempts": [{"status": "reviewing", "is_correct": 1,
                              "created_at": "2026-08-21T09:00:00"}],
            }],
        )
        evidence = [reason["evidence"] for reason in self.one_kp(result)["reasons"]]
        self.assertIn("自动结果 correct", evidence)

    def test_zero_formal_problem_kp_stays_evidence_insufficient(self):
        result = self.evaluate(kps=[kp("k1", feedback=[rating(5, "2026-08-20")])])
        self.assertEqual(self.one_kp(result)["category"], "evidence_insufficient")

    def test_gate_passed_candidate_evidence_is_kp_only(self):
        result = self.evaluate(
            problems=[problem("p1", ["k1"])],
            kps=[kp("k1")],
            candidates=[{
                "id": "c1", "kp_ids": ["k1"],
                "attempts": [attempt("wrong", "2026-08-25")],
            }],
        )
        self.assertEqual([item["id"] for item in result["problems"]], ["p1"])
        item = self.one_kp(result)
        self.assertEqual(item["category"], "needs_work")
        self.assertEqual(item["reasons"][0]["item_id"], "c1")


class MasteryProjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "pool.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE knowledge_points (kp_id TEXT PRIMARY KEY);
            CREATE TABLE problems (problem_id TEXT PRIMARY KEY, kp_ids TEXT NOT NULL);
            CREATE TABLE problem_attempts (
                id INTEGER PRIMARY KEY, problem_id TEXT, status TEXT, note TEXT, created_at TEXT
            );
            CREATE TABLE feedback_events (
                id INTEGER PRIMARY KEY, item_type TEXT, item_id TEXT, rating INTEGER, note TEXT, created_at TEXT
            );
            CREATE TABLE review_schedule (
                item_type TEXT, item_id TEXT, direction TEXT, due_at TEXT
            );
            CREATE TABLE candidate_problems (candidate_id TEXT PRIMARY KEY, kp_ids TEXT NOT NULL, status TEXT);
            CREATE TABLE candidate_attempts (
                id INTEGER PRIMARY KEY, candidate_id TEXT, status TEXT, is_correct INTEGER, note TEXT, created_at TEXT
            );
            INSERT INTO knowledge_points VALUES ('k1');
            INSERT INTO problems VALUES ('p1', '["k1"]');
            INSERT INTO problem_attempts VALUES (1, 'p1', 'mastered', NULL, '2026-08-20');
            INSERT INTO feedback_events VALUES (1, 'problem', 'p1', 4, NULL, '2026-08-21');
            INSERT INTO review_schedule VALUES ('problem', 'p1', '', '2026-09-01');
            INSERT INTO candidate_problems VALUES ('c1', '["k1"]', 'gate_passed');
            INSERT INTO candidate_attempts VALUES (1, 'c1', 'reviewing', 1, NULL, '2026-08-22');
            """
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_projection_reads_v0_inputs_without_writes(self):
        from data import mastery as mastery_data

        conn = sqlite3.connect(self.db_path)
        before = self.table_contents(conn)
        snapshot = mastery_data.snapshot(conn)
        after = self.table_contents(conn)
        conn.close()

        self.assertEqual(after, before)
        self.assertEqual(snapshot["problems"][0]["attempts"][0]["status"], "mastered")
        self.assertEqual(snapshot["candidates"][0]["id"], "c1")
        self.assertEqual(snapshot["candidates"][0]["attempts"][0]["is_correct"], 1)

    @staticmethod
    def table_contents(conn):
        tables = (
            "knowledge_points", "problems", "problem_attempts", "feedback_events",
            "review_schedule", "candidate_problems", "candidate_attempts",
        )
        return {
            table: conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            for table in tables
        }


if __name__ == "__main__":
    unittest.main()
