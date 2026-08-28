"""Micro-quiz content contract tests: domain rules, ingest recipe, pull."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from workbench import ingest
from workbench.domain import micro_quiz


def manifest_item(problem_id="dmath-ch06-mq-001", kp_id="dmath-ch06-kp-001",
                  stem="自然数 1 是质数吗？", **payload):
    payload.setdefault("quiz_type", "yes_no")
    payload.setdefault("answer_key", "否")
    payload.setdefault("error_reason", "1 只有 1 个正因数，不算质数。")
    payload.setdefault("source_evidence", "Rosen 6th, §3.1 定义")
    return {"problem_id": problem_id, "kp_id": kp_id, "stem": stem, **payload}


class MicroQuizRulesTests(unittest.TestCase):
    def test_validates_choice_payloads(self):
        ok = micro_quiz.validate_payload("single_choice", {
            "options": ["3", "4"], "answer_key": "3",
            "error_reason": "r", "source_evidence": "s",
        })
        self.assertEqual(ok, [])
        missing_answer = micro_quiz.validate_payload("single_choice", {
            "options": ["3", "4"], "answer_key": "9",
            "error_reason": "r", "source_evidence": "s",
        })
        self.assertEqual(len(missing_answer), 1)

    def test_multiple_choice_answer_must_be_subset(self):
        errors = micro_quiz.validate_payload("multiple_choice", {
            "options": ["a", "b", "c"], "answer_key": ["a", "z"],
            "error_reason": "r", "source_evidence": "s",
        })
        self.assertEqual(len(errors), 1)
        ok = micro_quiz.validate_payload("multiple_choice", {
            "options": ["a", "b", "c"], "answer_key": ["a", "c"],
            "error_reason": "r", "source_evidence": "s",
        })
        self.assertEqual(ok, [])

    def test_reference_types_take_no_options(self):
        errors = micro_quiz.validate_payload("short_answer", {
            "options": ["x"], "answer_key": "参考",
            "error_reason": "r", "source_evidence": "s",
        })
        self.assertGreaterEqual(len(errors), 1)

    def test_stem_and_kp_rules(self):
        row = {
            "kp_ids": ["kp-1", "kp-2"], "problem_text": "短题干",
            "practice_modes": ["yes_no"],
            "micro_quiz": {"quiz_type": "yes_no", "answer_key": "是",
                           "error_reason": "r", "source_evidence": "s"},
        }
        errors = micro_quiz.validate_problem_row(row)
        self.assertTrue(any("exactly one" in e for e in errors))
        row["kp_ids"] = ["kp-1"]
        row["problem_text"] = "长" * 201
        errors = micro_quiz.validate_problem_row(row)
        self.assertTrue(any("exceeds" in e for e in errors))

    def test_check_answer_objective_only(self):
        item = {"micro_quiz": {"quiz_type": "yes_no", "answer_key": "否"}}
        self.assertIs(micro_quiz.check_answer(item, "否"), True)
        self.assertIs(micro_quiz.check_answer(item, "是"), False)
        multi = {"micro_quiz": {"quiz_type": "multiple_choice",
                                "answer_key": ["a", "c"]}}
        self.assertIs(micro_quiz.check_answer(multi, ["c", "a"]), True)
        self.assertIs(micro_quiz.check_answer(multi, ["a"]), False)
        text_item = {"micro_quiz": {"quiz_type": "short_answer",
                                    "answer_key": "参考"}}
        self.assertIsNone(micro_quiz.check_answer(text_item, "随便"))


class MicroQuizIngestTests(unittest.TestCase):
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
        """)
        conn.execute("INSERT INTO knowledge_points VALUES ('dmath-ch06-kp-001', 'Counting')")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def manifest(self, items):
        path = self.root / "mq.json"
        path.write_text(json.dumps(
            {"kind": "micro-quiz-patch", "items": items}, ensure_ascii=False,
        ), encoding="utf-8")
        return path

    def test_gate_and_apply_insert_contract_rows(self):
        path = self.manifest([manifest_item()])
        conn = sqlite3.connect(self.db_path)
        try:
            report = ingest._gate_micro_quiz(
                conn, json.loads(path.read_text(encoding="utf-8")))
        finally:
            conn.close()
        self.assertTrue(report["ok"], report["errors"])
        result = ingest.apply_micro_quiz(self.db_path, path)
        self.assertTrue(result["applied"])
        self.assertTrue(Path(result["backup_path"]).exists())
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT kp_ids, problem_text, practice_modes, micro_quiz"
                " FROM problems WHERE problem_id='dmath-ch06-mq-001'"
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(json.loads(row[0]), ["dmath-ch06-kp-001"])
        self.assertEqual(json.loads(row[2]), ["yes_no"])
        payload = json.loads(row[3])
        self.assertEqual(payload["quiz_type"], "yes_no")
        self.assertEqual(payload["answer_key"], "否")

    def test_bad_items_are_rejected_without_writing(self):
        items = [
            manifest_item(),
            manifest_item(problem_id="dmath-ch06-mq-002",
                          kp_id="kp-missing"),
            manifest_item(problem_id="dmath-ch06-mq-003", stem="长" * 201),
            manifest_item(problem_id="dmath-ch06-mq-004", answer_key="对"),
            manifest_item(problem_id="not-an-id"),
        ]
        path = self.manifest(items)
        conn = sqlite3.connect(self.db_path)
        try:
            report = ingest._gate_micro_quiz(
                conn, json.loads(path.read_text(encoding="utf-8")))
        finally:
            conn.close()
        self.assertFalse(report["ok"])
        self.assertGreaterEqual(len(report["errors"]), 4)

    def test_apply_failure_rolls_back_and_recipe_applies(self):
        path = self.manifest([manifest_item()])
        recipe = ingest.recipe("micro-quiz", self.db_path, path, self.root,
                               apply_changes=True, backup_path=self.root / "bak.db")
        self.assertTrue(recipe["applied"])
        # Re-applying must fail on the duplicate and keep the pool unchanged.
        with self.assertRaises(ValueError):
            ingest.recipe("micro-quiz", self.db_path, path, self.root,
                          apply_changes=True, backup_path=self.root / "bak2.db")
        conn = sqlite3.connect(self.db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 1)


class MicroQuizPullTests(unittest.TestCase):
    def setUp(self):
        from tests.workbench.fixtures import WorkspaceFixture
        self.fixture = WorkspaceFixture()
        conn = sqlite3.connect(self.fixture.db_path)
        conn.execute(
            "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
            " problem_type, source_kind, practice_modes, micro_quiz)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "dmath-ch06-mq-001",
                json.dumps(["dmath-ch06-kp-001"]),
                "自然数 1 是质数吗？", None, "other", "quiz",
                json.dumps(["yes_no"]),
                json.dumps({"quiz_type": "yes_no", "answer_key": "否",
                            "error_reason": "1 只有一个正因数。",
                            "source_evidence": "Rosen §3.1"}),
            ),
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        self.fixture.cleanup()

    def pool(self):
        import sys
        sys.path.insert(0, str(self.fixture.ws))
        from data import pool as pool_mod
        return pool_mod.Pool(root=self.fixture.ws, db_path=self.fixture.db_path,
                             course="dmath", chapter="ch06")

    def test_marked_item_is_yes_no_eligible_and_parsed(self):
        pool = self.pool()
        try:
            result = pull_select(pool, mode="yes_no")
            problem = result["problems"][0]
            self.assertEqual(problem["problem_id"], "dmath-ch06-mq-001")
            self.assertEqual(problem["practice_modes"], ["yes_no"])
            self.assertEqual(problem["micro_quiz"]["quiz_type"], "yes_no")
        finally:
            pool.close()

    def test_flash_card_pull_skips_other_quiz_marks(self):
        pool = self.pool()
        try:
            result = pull_select(pool, mode="flash_card")
            self.assertEqual(result["problems"], [])
            self.assertEqual(result["shortage"], ["dmath-ch06-kp-001"])
        finally:
            pool.close()

    def test_unmarked_problem_stays_exam_only(self):
        pool = self.pool()
        try:
            result = pull_select(pool, mode="exam")
            ids = [p["problem_id"] for p in result["problems"]]
            self.assertNotIn("dmath-ch06-mq-001", ids)
        finally:
            pool.close()


def pull_select(pool, mode="flash_card"):
    from workbench.domain import pull
    return pull.select(pool, ["dmath-ch06-kp-001"], 5, mode=mode)


if __name__ == "__main__":
    unittest.main()
