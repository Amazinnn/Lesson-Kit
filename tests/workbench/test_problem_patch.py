"""In-place problem patches: gate, one transaction, previous-value rollback."""

import json
import sqlite3
import unittest
from pathlib import Path

from workbench import ingest

from tests.workbench.fixtures import WorkspaceFixture


def patch_item(problem_id, **fields):
    return {"problem_id": problem_id, **fields}


class ProblemPatchTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        self.db_path = self.fixture.db_path
        self.backups = 0

    def tearDown(self):
        self.fixture.cleanup()

    # -- helpers ----------------------------------------------------------

    def query(self, sql, params=()):
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def row(self, problem_id):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            found = conn.execute(
                "SELECT * FROM problems WHERE problem_id=?", (problem_id,)
            ).fetchone()
            return dict(found) if found else None
        finally:
            conn.close()

    def seed(self, problem_id="dmath-ch06-prob-002", **fields):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO problems (problem_id, kp_ids, problem_text, solution,"
                " problem_type, source_kind, origin_kind, source_evidence,"
                " practice_modes, micro_quiz) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    problem_id, '["dmath-ch06-kp-001"]',
                    fields.get("problem_text", "P2"), fields.get("solution", "S2"),
                    fields.get("problem_type", "calculation"),
                    fields.get("source_kind", "textbook"),
                    fields.get("origin_kind", "source_problem"),
                    fields.get("source_evidence", "教材 第6章 习题6-2"),
                    fields.get("practice_modes"), fields.get("micro_quiz"),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return problem_id

    def apply(self, items, course="dmath"):
        self.backups += 1
        backup = Path(self.fixture.tmp.name) / f"patch-backup-{self.backups:03d}.db"
        return ingest.apply_problem_patch(
            self.db_path,
            _manifest_file(self.fixture.tmp.name, items, self.backups),
            backup_path=backup, course=course)

    # -- applying a patch -------------------------------------------------

    def test_a_patch_converts_an_existing_row_without_changing_its_id(self):
        self.seed()

        result = self.apply([patch_item(
            "dmath-ch06-prob-002",
            problem_text="下列哪个是国际单位制基本单位？",
            micro_quiz={
                "quiz_type": "single_choice",
                "options": ["米", "牛", "焦", "瓦"],
                "answer_key": "米",
                "error_reason": "牛、焦、瓦都是导出单位。",
                "source_evidence": "教材 第6章 习题6-2",
            },
        )])

        self.assertTrue(result["ok"])
        self.assertEqual(result["kind"], "problem-patch")
        self.assertEqual(result["counts"], {"problems": 1, "difficulty_cleared": 0})
        row = self.row("dmath-ch06-prob-002")
        self.assertEqual(row["problem_id"], "dmath-ch06-prob-002")
        self.assertEqual(json.loads(row["practice_modes"]), ["micro"])
        self.assertEqual(json.loads(row["micro_quiz"])["options"],
                         ["米", "牛", "焦", "瓦"])
        self.assertEqual(row["problem_text"], "下列哪个是国际单位制基本单位？")
        # The original import's own batch stamp is left alone.
        self.assertIsNone(row["ingest_batch_id"])

    def test_a_patch_can_split_options_out_of_a_long_stem(self):
        long_stem = "题干" * 150 + "\nA. 甲\nB. 乙\nC. 丙"
        self.seed(problem_text=long_stem)
        self.assertEqual(len(long_stem) > 800, False)

        self.apply([patch_item(
            "dmath-ch06-prob-002",
            problem_text="题干" * 150,
            micro_quiz={"quiz_type": "single_choice", "options": ["甲", "乙", "丙"],
                        "source_evidence": "教材 第6章 习题6-2"},
        )])

        row = self.row("dmath-ch06-prob-002")
        self.assertEqual(row["problem_text"], "题干" * 150)
        self.assertEqual(json.loads(row["micro_quiz"])["options"], ["甲", "乙", "丙"])

    def test_a_patch_counts_cleared_ratings(self):
        self.seed()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE problems SET difficulty=4, difficulty_knowledge_breadth=3,"
            " difficulty_reasoning_depth=4, difficulty_transfer_distance=3,"
            " difficulty_construction_openness=4,"
            " difficulty_model='cognitive-v1-equal-mean'"
            " WHERE problem_id='dmath-ch06-prob-002'")
        conn.commit()
        conn.close()

        result = self.apply([patch_item("dmath-ch06-prob-002",
                                        problem_text="改写后的题干")])

        self.assertEqual(result["counts"]["difficulty_cleared"], 1)
        self.assertIsNone(self.row("dmath-ch06-prob-002")["difficulty"])

    # -- gate -------------------------------------------------------------

    def test_the_whole_batch_writes_nothing_when_one_item_is_bad(self):
        self.seed()
        before = self.row("dmath-ch06-prob-002")

        with self.assertRaises(ValueError) as caught:
            self.apply([
                patch_item("dmath-ch06-prob-002", display_title="好标题"),
                patch_item("dmath-ch06-prob-003", display_title="没有这题"),
            ])

        self.assertIn("unknown problem", str(caught.exception))
        self.assertEqual(self.row("dmath-ch06-prob-002"), before)
        self.assertEqual(self.query("SELECT batch_id FROM ingest_batches"), [])

    def test_the_gate_names_every_reason(self):
        self.seed()
        cases = {
            "typo": {"display_title__typo": "x"},
            "difficulty": {"difficulty": 3},
            "mode without payload": {"practice_modes": ["micro"]},
            "two kps": {"kp_ids": ["dmath-ch06-kp-001", "dmath-ch06-kp-002"],
                        "micro_quiz": {"quiz_type": "yes_no", "error_reason": "r",
                                       "source_evidence": "教材 第6章"}},
            "bad key": {"micro_quiz": {"quiz_type": "single_choice",
                                       "options": ["甲", "乙"], "answer_key": "丙",
                                       "error_reason": "r",
                                       "source_evidence": "教材 第6章"}},
        }
        for case, fields in cases.items():
            with self.subTest(case=case):
                item = {"problem_id": "dmath-ch06-prob-002", **fields}
                conn = sqlite3.connect(self.db_path)
                try:
                    report = ingest._gate_problem_patch(
                        conn, {"kind": "problem-patch", "items": [item]}, "dmath")
                finally:
                    conn.close()
                self.assertFalse(report["ok"], case)
                self.assertTrue(report["errors"], case)

    def test_a_patch_cannot_rename_a_problem(self):
        self.seed()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = ingest.content_data.decode_problem(conn.execute(
                "SELECT * FROM problems WHERE problem_id='dmath-ch06-prob-002'"
            ).fetchone())
        finally:
            conn.close()

        plan = ingest.content_data.plan_problem_patch(
            row, {"problem_id": "dmath-ch06-prob-009"}, course="dmath")

        self.assertTrue(plan["errors"])
        self.assertIn("identity", " ".join(plan["errors"]))

    def test_a_foreign_course_id_is_refused(self):
        self.seed(problem_id="c99-ch06-prob-002")
        with self.assertRaises(ValueError) as caught:
            self.apply([patch_item("c99-ch06-prob-002", display_title="x")])
        self.assertIn("must start with dmath-", str(caught.exception))

    def test_an_item_with_nothing_to_change_is_refused(self):
        self.seed()
        with self.assertRaises(ValueError) as caught:
            self.apply([patch_item("dmath-ch06-prob-002")])
        self.assertIn("nothing to change", str(caught.exception))

    # -- rollback ---------------------------------------------------------

    def test_rollback_restores_the_previous_values_exactly(self):
        self.seed()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE problems SET difficulty=2, difficulty_knowledge_breadth=2,"
            " difficulty_reasoning_depth=2, difficulty_transfer_distance=2,"
            " difficulty_construction_openness=2,"
            " difficulty_model='cognitive-v1-equal-mean'"
            " WHERE problem_id='dmath-ch06-prob-002'")
        conn.commit()
        conn.close()
        before = self.row("dmath-ch06-prob-002")

        applied = self.apply([patch_item(
            "dmath-ch06-prob-002",
            problem_text="改写后的题干",
            practice_modes=["yes_no"],
            micro_quiz={"quiz_type": "yes_no", "answer_key": "是",
                        "error_reason": "因为…",
                        "source_evidence": "教材 第6章 习题6-2"},
            source_answer="是",
        )])
        self.assertEqual(self.row("dmath-ch06-prob-002")["practice_modes"], '["yes_no"]')

        rolled = ingest.rollback_batch(self.db_path, applied["batch_id"])

        self.assertTrue(rolled["ok"])
        self.assertEqual(rolled["counts"], {"problems": 1})
        restored = self.row("dmath-ch06-prob-002")
        for column, value in before.items():
            if column == "updated_at":
                continue
            self.assertEqual(restored[column], value, column)

    def test_rollback_of_a_patch_is_refused_twice(self):
        self.seed()
        applied = self.apply([patch_item("dmath-ch06-prob-002",
                                        display_title="补个标题")])
        ingest.rollback_batch(self.db_path, applied["batch_id"])
        with self.assertRaises(ValueError) as caught:
            ingest.rollback_batch(self.db_path, applied["batch_id"])
        self.assertIn("already rolled back", str(caught.exception))

    def test_a_patch_survives_learning_records(self):
        self.seed()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO problem_attempts (problem_id, status, answer_text)"
            " VALUES ('dmath-ch06-prob-002', 'wrong', '答案')")
        conn.commit()
        conn.close()

        applied = self.apply([patch_item("dmath-ch06-prob-002",
                                        display_title="补个标题")])

        self.assertTrue(applied["ok"])
        rolled = ingest.rollback_batch(self.db_path, applied["batch_id"])
        self.assertTrue(rolled["ok"])
        self.assertEqual(self.row("dmath-ch06-prob-002")["display_title"], None)

    # -- recipe -----------------------------------------------------------

    def test_the_recipe_needs_apply_to_write(self):
        self.seed()
        manifest = _manifest_file(self.fixture.tmp.name, [
            patch_item("dmath-ch06-prob-002", display_title="新标题")], 99)
        output = Path(self.fixture.tmp.name) / "patch-out"

        planned = ingest.recipe("problem-patch", self.db_path, manifest, output)

        self.assertFalse(planned["applied"])
        self.assertIsNone(self.row("dmath-ch06-prob-002")["display_title"])

        applied = ingest.recipe(
            "problem-patch", self.db_path, manifest, output, apply_changes=True,
            backup_path=Path(self.fixture.tmp.name) / "recipe-backup.db")

        self.assertTrue(applied["applied"])
        self.assertEqual(self.row("dmath-ch06-prob-002")["display_title"], "新标题")


def _manifest_file(root, items, index):
    path = Path(root) / f"problem-patch-{index:03d}.json"
    path.write_text(json.dumps({"kind": "problem-patch", "items": items},
                               ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
