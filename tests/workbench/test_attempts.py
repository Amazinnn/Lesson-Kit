"""Agent-assisted practice records: attempt CLI, atomic apply, correction (TDD)."""

import contextlib
import importlib.util
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TODAY = date.today()


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pool_schema = load_script("attempts_pool_schema", Path("pool/scripts/pool_schema.py"))
create_tables = load_script("attempts_create_tables", Path("pipeline/scripts/create-tables.py"))


class AttemptsTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["LESSONKIT_WB_HOME"] = self.tmp.name
        self.ws = Path(self.tmp.name) / "course"
        (self.ws / "pool").mkdir(parents=True)
        self.db_path = self.ws / "pool" / "dmath.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript(create_tables.SCHEMA_SQL)
        pool_schema.ensure_workbench_schema(conn)
        for kp_id, item in (("dmath-ch12-kp-001", "鸽巢原理"),
                            ("dmath-ch12-kp-002", "组合计数")):
            conn.execute(
                "INSERT INTO knowledge_points "
                "(kp_id, knowledge_item, knowledge_type, importance) VALUES (?, ?, ?, ?)",
                (kp_id, item, "concept-property", "core"),
            )
        for problem_id, kp_ids, text in (
            ("dmath-ch12-prob-001", '["dmath-ch12-kp-001"]', "证明题一"),
            ("dmath-ch12-prob-002", '["dmath-ch12-kp-001", "dmath-ch12-kp-002"]',
             "证明题二"),
        ):
            conn.execute(
                "INSERT INTO problems "
                "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (problem_id, kp_ids, text, "解析", "proof", "textbook"),
            )
        conn.commit()
        conn.close()
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from cli import main as cli_mod
        from registry import register

        self.cli = cli_mod
        self.registry = sys.modules["registry"]
        register(str(self.ws), name="course", course="dmath", chapter="ch12")

    def tearDown(self):
        os.environ.pop("LESSONKIT_WB_HOME", None)
        self.tmp.cleanup()

    # -- helpers ----------------------------------------------------------

    def write_json(self, name, value):
        path = Path(self.tmp.name) / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.cli.main(list(args))
        return code, out.getvalue()

    def json_cli(self, *args):
        code, output = self.run_cli(*args)
        return code, json.loads(output)

    def manifest(self, name, request_id, items):
        return self.write_json(name, {"request_id": request_id, "items": items})

    def apply(self, request_id, items, name="manifest.json"):
        return self.json_cli("attempts", "course", "apply",
                             "--input", self.manifest(name, request_id, items))

    def check(self, request_id, items, name="check.json"):
        return self.json_cli("attempts", "course", "check",
                             "--input", self.manifest(name, request_id, items))

    def correct(self, attempt_id, request_id, payload):
        payload = {"request_id": request_id, **payload}
        return self.json_cli("attempts", "course", "correct", str(attempt_id),
                             "--input", self.write_json("correction.json", payload))

    def rows(self, sql, params=()):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute(sql, params)]
        finally:
            conn.close()

    def learning_rows(self):
        """Every learning table, so a zero-write claim is checkable."""
        return {
            table: self.rows(f"SELECT * FROM {table} ORDER BY 1")
            for table in ("problem_attempts", "feedback_events", "learner_signals",
                          "problem_progress", "learning_current_state",
                          "review_schedule", "attempt_operations")
        }

    def answer_texts(self, db_path):
        conn = sqlite3.connect(db_path)
        try:
            return conn.execute(
                "SELECT answer_text FROM problem_attempts ORDER BY id").fetchall()
        finally:
            conn.close()

    def signal(self, kp_id):
        rows = self.rows("SELECT * FROM learner_signals WHERE target_id=?", (kp_id,))
        return rows[0] if rows else None

    def schedule(self, problem_id):
        rows = self.rows("SELECT * FROM review_schedule WHERE item_id=?", (problem_id,))
        return rows[0] if rows else None


class ManifestValidationTests(AttemptsTestCase):
    def test_check_previews_rated_and_ungraded_items_without_writing(self):
        before = self.learning_rows()
        code, result = self.check("conv-001-turn-004-record", [
            {"problem_id": "dmath-ch12-prob-001", "answer_text": "先设 n 个鸽巢",
             "note": "混淆了鸽巢与抽屉的边界", "rating": 3},
            {"problem_id": "dmath-ch12-prob-002", "answer_text": "只写了开头",
             "note": "第二问没做完"},
        ])

        self.assertEqual(code, 0)
        self.assertEqual(result["writes"], 0)
        self.assertFalse(result["replay"])
        self.assertEqual(result["counts"], {"attempts": 2, "graded": 1, "ungraded": 1})
        self.assertEqual(result["items"][0]["status"], "reviewing")
        self.assertEqual(result["items"][0]["signal_targets"], ["dmath-ch12-kp-001"])
        self.assertEqual(
            result["items"][1]["signal_targets"],
            ["dmath-ch12-kp-001", "dmath-ch12-kp-002"])
        self.assertEqual(result["items"][1]["status"], "new")
        self.assertIsNone(result["items"][1]["projected_due_at"])
        self.assertEqual(result["items"][0]["projected_due_at"],
                         (TODAY + timedelta(days=1)).isoformat())
        self.assertEqual(self.learning_rows(), before)

    def test_unsupported_item_field_is_itemized_and_writes_nothing(self):
        before = self.learning_rows()
        code, result = self.check("r1", [
            {"problem_id": "dmath-ch12-prob-001", "answer_text": "作答", "rating": 3},
            {"problem_id": "dmath-ch12-prob-002", "answer_text": "作答",
             "images": ["D:/photos/p2.jpg"]},
        ])
        self.assertEqual(code, 2)
        self.assertIn("item 1", result["error"])
        self.assertIn("images", result["error"])
        self.assertEqual(result["errors"], [{
            "index": 1, "problem_id": "dmath-ch12-prob-002",
            "error": "unsupported field: images — an attempt item carries only "
                     "problem_id, answer_text, note, and rating (no image, path, exam "
                     "mark, or grader field)",
        }])
        self.assertEqual(self.learning_rows(), before)

    def test_manifest_rejects_unknown_problem_bad_rating_and_duplicates(self):
        cases = [
            ([{"problem_id": "dmath-ch12-prob-999", "answer_text": "x"}],
             "unknown problem: dmath-ch12-prob-999"),
            ([{"problem_id": "dmath-ch12-prob-001", "answer_text": "x", "rating": 6}],
             "rating must be an integer from 1 to 5"),
            ([{"problem_id": "dmath-ch12-prob-001", "answer_text": "x", "rating": True}],
             "rating must be an integer from 1 to 5"),
            ([{"problem_id": "dmath-ch12-prob-001"}],
             "answer_text or note must be non-empty"),
            ([{"problem_id": "dmath-ch12-prob-001", "answer_text": "x"},
              {"problem_id": "dmath-ch12-prob-001", "answer_text": "y"}],
             "duplicate problem in this manifest: dmath-ch12-prob-001"),
            ([{"problem_id": "dmath-ch12-prob-001", "answer_text": 7}],
             "answer_text must be a string"),
        ]
        for items, message in cases:
            with self.subTest(message=message):
                code, result = self.check("r1", items)
                self.assertEqual(code, 2)
                self.assertIn(message, result["error"])

    def test_manifest_shape_is_checked(self):
        for payload, message in (
            ({"items": [{"problem_id": "dmath-ch12-prob-001", "answer_text": "x"}]},
             "non-empty request_id"),
            ({"request_id": "r1"}, "non-empty items list"),
            ({"request_id": "r1", "items": []}, "non-empty items list"),
            ({"request_id": "r1", "items": [{"problem_id": "dmath-ch12-prob-001",
                                             "answer_text": "x"}], "grader": "agent"},
             "unsupported field: grader"),
            ({"request_id": "  ", "items": [{"problem_id": "dmath-ch12-prob-001",
                                             "answer_text": "x"}]},
             "non-empty request_id"),
        ):
            with self.subTest(message=message):
                path = self.write_json("bad.json", payload)
                code, result = self.json_cli(
                    "attempts", "course", "check", "--input", path)
                self.assertEqual(code, 2)
                self.assertIn(message, result["error"])


class ApplyTests(AttemptsTestCase):
    def test_apply_records_two_attempts_from_one_atomic_call(self):
        before = self.learning_rows()
        code, result = self.apply("conv-001-turn-004-record", [
            {"problem_id": "dmath-ch12-prob-001", "answer_text": "第一题作答",
             "note": "混淆了边界条件", "rating": 2},
            {"problem_id": "dmath-ch12-prob-002", "answer_text": "第二题作答",
             "note": "第二问没做完"},
        ])

        self.assertEqual(code, 0)
        self.assertEqual(result["counts"], {"attempts": 2, "graded": 1, "ungraded": 1})
        graded, ungraded = result["items"]
        self.assertEqual(graded["status"], "wrong")
        self.assertEqual(graded["due_at"], TODAY.isoformat())
        self.assertEqual(ungraded["status"], "new")
        self.assertIsNone(ungraded["due_at"])

        attempts = self.rows("SELECT * FROM problem_attempts ORDER BY id")
        self.assertEqual([row["id"] for row in attempts],
                         [graded["attempt_id"], ungraded["attempt_id"]])
        self.assertEqual(attempts[0]["answer_text"], "第一题作答")
        self.assertEqual(attempts[1]["status"], "new")
        self.assertEqual(self.learning_rows()["attempt_operations"][0]["request_id"],
                         "conv-001-turn-004-record")

        # The ungraded item leaves every projection exactly as it was.
        self.assertIsNone(self.signal("dmath-ch12-kp-002"))
        self.assertEqual(before["review_schedule"], [])
        self.assertEqual(len(self.learning_rows()["review_schedule"]), 1)

    def test_rated_attempt_reuses_the_existing_rating_rules_once(self):
        code, result = self.apply("r1", [{
            "problem_id": "dmath-ch12-prob-002", "answer_text": "证明作答",
            "note": "混淆了两种计数模型", "rating": 2,
        }])
        self.assertEqual(code, 0)
        attempt_id = result["items"][0]["attempt_id"]

        for kp_id in ("dmath-ch12-kp-001", "dmath-ch12-kp-002"):
            signal = self.signal(kp_id)
            self.assertEqual(signal["weight"], "high")
            self.assertEqual(signal["evidence_count"], 1)
            self.assertEqual(signal["signal_type"], "confusion")
            self.assertEqual(signal["note"], "混淆了两种计数模型")
            state = self.rows("SELECT * FROM learning_current_state "
                              "WHERE item_type='kp' AND item_id=?", (kp_id,))
            self.assertEqual(state[0]["state"], "needs_work")

        events = self.rows("SELECT * FROM feedback_events")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["attempt_id"], attempt_id)
        self.assertEqual(events[0]["rating"], 2)
        self.assertEqual(self.rows("SELECT * FROM problem_progress")[0]["status"], "wrong")
        self.assertEqual(
            self.rows("SELECT * FROM learning_current_state WHERE item_type='problem'")[0]["state"],
            "needs_work")
        schedule = self.schedule("dmath-ch12-prob-002")
        self.assertEqual(schedule["repetitions"], 0)
        self.assertEqual(schedule["due_at"], TODAY.isoformat())

    def test_ungraded_attempt_is_durable_without_any_projection_change(self):
        before = self.learning_rows()
        code, result = self.apply("r1", [{
            "problem_id": "dmath-ch12-prob-001",
            "answer_text": "被拍成三张照片的作答原文",
            "note": "只写了一半",
        }])
        self.assertEqual(code, 0)
        item = result["items"][0]
        self.assertFalse(item["graded"])
        self.assertEqual(item["changes"], [])
        attempts = self.rows("SELECT * FROM problem_attempts")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["answer_text"], "被拍成三张照片的作答原文")
        self.assertEqual(attempts[0]["note"], "只写了一半")
        self.assertEqual(attempts[0]["status"], "new")
        for table, rows in self.learning_rows().items():
            if table in ("problem_attempts", "attempt_operations"):
                continue
            self.assertEqual(rows, before[table], table)

    def test_one_invalid_item_protects_the_whole_batch(self):
        before = self.learning_rows()
        code, result = self.apply("r1", [
            {"problem_id": "dmath-ch12-prob-001", "answer_text": "有效", "rating": 5},
            {"problem_id": "dmath-ch12-prob-002", "answer_text": "无效", "rating": 0},
        ])
        self.assertEqual(code, 2)
        self.assertIn("item 1: rating must be an integer from 1 to 5", result["error"])
        self.assertEqual(self.learning_rows(), before)

    def test_identical_retry_returns_the_first_result_without_recording_twice(self):
        items = [{"problem_id": "dmath-ch12-prob-001", "answer_text": "作答",
                  "note": "卡点", "rating": 4}]
        first = self.apply("conv-001-turn-009-record", items)
        after_first = self.learning_rows()
        second = self.apply("conv-001-turn-009-record", items)

        self.assertEqual(first, second)
        self.assertEqual(self.learning_rows(), after_first)
        self.assertEqual(len(after_first["problem_attempts"]), 1)
        self.assertEqual(len(after_first["feedback_events"]), 1)

    def test_request_id_reuse_with_different_content_fails_and_writes_nothing(self):
        self.apply("r1", [{"problem_id": "dmath-ch12-prob-001", "answer_text": "第一版",
                           "rating": 3}])
        after_first = self.learning_rows()
        code, result = self.apply("r1", [{"problem_id": "dmath-ch12-prob-001",
                                          "answer_text": "第二版", "rating": 5}])
        self.assertEqual(code, 2)
        self.assertIn("already used for different content", result["error"])
        self.assertEqual(self.learning_rows(), after_first)

        code, replay = self.check("r1", [{"problem_id": "dmath-ch12-prob-001",
                                          "answer_text": "第一版", "rating": 3}])
        self.assertEqual(code, 0)
        self.assertTrue(replay["replay"])
        self.assertEqual(replay["counts"], {"attempts": 1, "graded": 1, "ungraded": 0})

    def test_a_new_request_id_records_a_new_attempt_for_the_same_problem(self):
        _, first = self.apply("r1", [{"problem_id": "dmath-ch12-prob-001",
                                      "answer_text": "第一次", "rating": 2}])
        _, second = self.apply("r2", [{"problem_id": "dmath-ch12-prob-001",
                                       "answer_text": "第二次", "rating": 5}])
        self.assertNotEqual(first["items"][0]["attempt_id"],
                            second["items"][0]["attempt_id"])
        self.assertEqual(len(self.rows("SELECT * FROM problem_attempts")), 2)
        schedule = self.schedule("dmath-ch12-prob-001")
        self.assertEqual(schedule["repetitions"], 1)
        self.assertEqual(schedule["interval_days"], 1.0)
        self.assertEqual(schedule["last_rating"], 5)

    def test_apply_on_an_unmigrated_pool_explains_the_migration(self):
        old = Path(self.tmp.name) / "legacy"
        (old / "pool").mkdir(parents=True)
        db = old / "pool" / "dmath.db"
        conn = sqlite3.connect(db)
        conn.executescript(create_tables.SCHEMA_SQL)
        conn.execute(
            "INSERT INTO problems (problem_id, kp_ids, problem_text, problem_type,"
            " source_kind) VALUES (?, ?, ?, ?, ?)",
            ("dmath-ch12-prob-001", "[]", "text", "proof", "textbook"))
        conn.commit()
        conn.close()
        self.registry.register(str(old), name="legacy", course="dmath", chapter="ch12")
        code, result = self.json_cli(
            "attempts", "legacy", "apply",
            "--input", self.manifest("legacy.json", "r1", [
                {"problem_id": "dmath-ch12-prob-001", "answer_text": "x"}]))
        self.assertEqual(code, 2)
        self.assertIn("migrate-progress.py --db pool/dmath.db", result["error"])


class CorrectionTests(AttemptsTestCase):
    def apply_rated(self, problem_id="dmath-ch12-prob-001", rating=2, request_id="r1",
                    answer_text="原始作答", note="原始卡点"):
        code, result = self.apply(request_id, [{
            "problem_id": problem_id, "answer_text": answer_text, "note": note,
            "rating": rating}])
        self.assertEqual(code, 0)
        return result["items"][0]["attempt_id"]

    def test_correct_latest_rated_attempt_recomputes_its_effects_once(self):
        attempt_id = self.apply_rated(rating=2)
        self.assertEqual(self.signal("dmath-ch12-kp-001")["weight"], "high")
        code, result = self.correct(attempt_id, "conv-001-turn-011-correct", {
            "answer_text": "更正后的作答", "note": "其实卡在归纳步", "rating": 3})

        self.assertEqual(code, 0)
        item = result["items"][0]
        self.assertTrue(item["corrected"])
        self.assertEqual(item["attempt_id"], attempt_id)
        self.assertEqual(item["status"], "reviewing")

        attempts = self.rows("SELECT * FROM problem_attempts")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["id"], attempt_id)
        self.assertEqual(attempts[0]["answer_text"], "更正后的作答")
        self.assertEqual(attempts[0]["note"], "其实卡在归纳步")
        self.assertEqual(attempts[0]["status"], "reviewing")

        events = self.rows("SELECT * FROM feedback_events")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["attempt_id"], attempt_id)
        self.assertEqual(events[0]["rating"], 3)
        self.assertEqual(events[0]["note"], "其实卡在归纳步")

        # The old 2-rating effect is withdrawn, not stacked: evidence is 1 again,
        # the weight follows the replacement, and the schedule restarts from the
        # default ease instead of continuing the earlier relearning row.
        signal = self.signal("dmath-ch12-kp-001")
        self.assertEqual(signal["evidence_count"], 1)
        self.assertEqual(signal["weight"], "medium")
        self.assertEqual(signal["signal_type"], "weak_node")
        self.assertEqual(self.rows("SELECT * FROM problem_progress")[0]["status"], "reviewing")
        schedule = self.schedule("dmath-ch12-prob-001")
        self.assertEqual(schedule["repetitions"], 1)
        self.assertEqual(schedule["interval_days"], 1.0)
        self.assertEqual(schedule["ease"], 2.6)
        self.assertEqual(schedule["last_rating"], 3)
        self.assertEqual(schedule["due_at"], (TODAY + timedelta(days=1)).isoformat())

    def test_correcting_to_mastery_leaves_no_stale_weakness_evidence(self):
        attempt_id = self.apply_rated(rating=1)
        code, result = self.correct(attempt_id, "c1", {
            "answer_text": "更正后的作答", "note": "其实完全掌握了", "rating": 5})
        self.assertEqual(code, 0)
        self.assertEqual(result["items"][0]["status"], "mastered")
        attempt = self.rows("SELECT * FROM problem_attempts")[0]
        self.assertEqual(attempt["status"], "mastered")
        self.assertEqual(self.rows("SELECT * FROM learner_signals"), [])
        self.assertEqual(
            [row["state"] for row in
             self.rows("SELECT * FROM learning_current_state ORDER BY item_id")],
            ["mastered", "mastered"])
        self.assertEqual(self.rows("SELECT * FROM problem_progress")[0]["status"], "mastered")
        self.assertEqual(self.schedule("dmath-ch12-prob-001")["last_rating"], 5)

    def test_correction_can_remove_a_rating_and_withdraw_its_effects(self):
        attempt_id = self.apply_rated(rating=1)
        code, result = self.correct(attempt_id, "c2", {
            "answer_text": "作答原文（未评分）", "note": "还判断不出掌握程度"})

        self.assertEqual(code, 0)
        self.assertFalse(result["items"][0]["graded"])
        self.assertEqual(result["items"][0]["status"], "new")
        attempt = self.rows("SELECT * FROM problem_attempts")[0]
        self.assertEqual(attempt["status"], "new")
        self.assertEqual(attempt["answer_text"], "作答原文（未评分）")
        self.assertEqual(self.rows("SELECT * FROM feedback_events"), [])
        self.assertEqual(self.rows("SELECT * FROM learner_signals"), [])
        self.assertEqual(self.rows("SELECT * FROM problem_progress"), [])
        self.assertEqual(self.rows("SELECT * FROM learning_current_state"), [])
        self.assertEqual(self.rows("SELECT * FROM review_schedule"), [])
        self.assertTrue(result["items"][0]["corrected"])

    def test_correction_of_an_ungraded_attempt_can_add_the_rating(self):
        code, result = self.apply("r1", [{"problem_id": "dmath-ch12-prob-001",
                                          "answer_text": "未评分作答"}])
        attempt_id = result["items"][0]["attempt_id"]
        code, corrected = self.correct(attempt_id, "c1", {
            "answer_text": "未评分作答", "note": "补评：推理完整", "rating": 4})
        self.assertEqual(code, 0)
        self.assertEqual(corrected["items"][0]["status"], "reviewing")
        events = self.rows("SELECT * FROM feedback_events")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["attempt_id"], attempt_id)
        self.assertEqual(events[0]["rating"], 4)
        self.assertEqual(self.schedule("dmath-ch12-prob-001")["repetitions"], 1)

    def test_later_activity_blocks_correction_with_zero_writes(self):
        attempt_id = self.apply_rated(rating=2)
        # A later attempt on the same problem, then a graph-state edit.
        self.apply_rated(rating=4, request_id="r2", answer_text="第二次")
        blocked = self.learning_rows()
        code, result = self.correct(attempt_id, "c1", {
            "answer_text": "更正", "note": "更正", "rating": 5})
        self.assertEqual(code, 2)
        self.assertIn("cannot be corrected", result["error"])
        self.assertIn("record a fresh attempt", result["error"])
        self.assertEqual(self.learning_rows(), blocked)

    def test_a_newer_attempt_alone_blocks_correction(self):
        attempt_id = self.apply_rated(rating=2)
        self.apply("r2", [{"problem_id": "dmath-ch12-prob-001", "answer_text": "第二次"}])
        blocked = self.learning_rows()
        code, result = self.correct(attempt_id, "c1", {
            "answer_text": "更正", "note": "更正", "rating": 5})
        self.assertEqual(code, 2)
        self.assertIn("came later", result["error"])
        self.assertEqual(self.learning_rows(), blocked)

    def test_graph_state_edit_blocks_correction(self):
        attempt_id = self.apply_rated(rating=2)
        code, _ = self.json_cli("data", "course", "state", "problem",
                                "dmath-ch12-prob-001", "mastered")
        self.assertEqual(code, 0)
        blocked = self.learning_rows()
        code, result = self.correct(attempt_id, "c1", {
            "answer_text": "更正", "note": "更正", "rating": 5})
        self.assertEqual(code, 2)
        self.assertIn("cannot be corrected", result["error"])
        self.assertEqual(self.learning_rows(), blocked)

    def test_legacy_and_unknown_attempts_are_not_correctable(self):
        code, _ = self.run_cli("practice", "course", "--problem",
                               "dmath-ch12-prob-001", "--result", "correct")
        self.assertEqual(code, 0)
        legacy_id = self.rows("SELECT * FROM problem_attempts")[0]["id"]
        code, detail = self.json_cli("attempts", "course", "get", str(legacy_id))
        self.assertEqual(code, 0)
        self.assertFalse(detail["agent_recorded"])
        self.assertFalse(detail["correctable"])
        self.assertIsNone(detail["operation"])

        blocked = self.learning_rows()
        code, result = self.correct(legacy_id, "c1", {
            "answer_text": "更正", "note": "更正", "rating": 5})
        self.assertEqual(code, 2)
        self.assertIn("no Agent recording to correct", result["error"])
        self.assertEqual(self.learning_rows(), blocked)

        code, result = self.correct(999, "c1", {
            "answer_text": "更正", "note": "更正", "rating": 5})
        self.assertEqual(code, 2)
        self.assertIn("unknown attempt: 999", result["error"])

    def test_correction_retry_returns_the_first_result(self):
        attempt_id = self.apply_rated(rating=2)
        payload = {"answer_text": "更正后的作答", "note": "更正", "rating": 5}
        first = self.correct(attempt_id, "c1", payload)
        settled = self.learning_rows()
        second = self.correct(attempt_id, "c1", payload)
        self.assertEqual(first, second)
        self.assertEqual(self.learning_rows(), settled)

    def test_correction_revalidates_and_rejects_unsupported_fields(self):
        attempt_id = self.apply_rated(rating=2)
        blocked = self.learning_rows()
        code, result = self.json_cli(
            "attempts", "course", "correct", str(attempt_id),
            "--input", self.write_json("bad-correction.json", {
                "request_id": "c1", "answer_text": "x", "rating": 5,
                "image_path": "D:/photos/p1.jpg"}))
        self.assertEqual(code, 2)
        self.assertIn("unsupported field: image_path", result["error"])
        self.assertEqual(self.learning_rows(), blocked)

    def test_get_reports_the_linkage_and_correction_eligibility(self):
        attempt_id = self.apply_rated(rating=3, note="思路对但算错")
        code, detail = self.json_cli("attempts", "course", "get", str(attempt_id))
        self.assertEqual(code, 0)
        self.assertTrue(detail["agent_recorded"])
        self.assertTrue(detail["correctable"])
        self.assertIsNone(detail["correction_conflict"])
        self.assertEqual(detail["operation"],
                         {"request_id": "r1", "kind": "apply", "rating": 3})
        self.assertEqual(detail["feedback_event"]["rating"], 3)
        self.assertEqual(detail["feedback_event"]["attempt_id"], attempt_id)
        self.assertEqual(detail["problem_progress"]["status"], "reviewing")
        self.assertEqual(detail["current_state"]["state"], "review")
        self.assertEqual(detail["schedule"]["last_rating"], 3)
        self.assertNotIn("dmath-ch12-prob-002", json.dumps(detail, ensure_ascii=False))


class AttemptReadTests(AttemptsTestCase):
    def test_list_and_get_are_read_only_and_show_both_records(self):
        self.apply("r1", [{"problem_id": "dmath-ch12-prob-001",
                           "answer_text": "第一次", "rating": 2}])
        self.apply("r2", [{"problem_id": "dmath-ch12-prob-001",
                           "answer_text": "第二次（未评分）"}])
        before = self.learning_rows()
        code, listed = self.json_cli("attempts", "course", "list",
                                     "--problem", "dmath-ch12-prob-001")
        self.assertEqual(code, 0)
        self.assertEqual(listed["count"], 2)
        first, second = listed["attempts"]
        self.assertTrue(first["agent_recorded"])
        self.assertEqual(first["rating"], 2)
        self.assertTrue(first["graded"])
        self.assertFalse(first["latest"])
        self.assertEqual(first["request_id"], "r1")
        self.assertEqual(second["answer_text"], "第二次（未评分）")
        self.assertTrue(second["latest"])
        self.assertFalse(second["graded"])
        self.assertEqual(self.learning_rows(), before)

    def test_list_rejects_an_unknown_problem(self):
        code, result = self.json_cli("attempts", "course", "list",
                                     "--problem", "dmath-ch12-prob-999")
        self.assertEqual(code, 2)
        self.assertIn("unknown problem: dmath-ch12-prob-999", result["error"])


class AnswerSourceTests(AttemptsTestCase):
    def test_add_list_remove_keeps_paths_only(self):
        photos = Path(self.tmp.name) / "photos"
        photos.mkdir()
        (photos / "p1.jpg").write_bytes(b"not-an-image")

        code, added = self.json_cli("attempts", "course", "sources", "add",
                                    "--path", str(photos))
        self.assertEqual(code, 0)
        self.assertEqual(added["paths"], [str(photos.resolve())])
        self.assertTrue(added["added"])

        code, again = self.json_cli("attempts", "course", "sources", "add",
                                    "--path", str(photos))
        self.assertEqual(code, 0)
        self.assertFalse(again["added"])
        self.assertEqual(again["paths"], [str(photos.resolve())])

        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        code, both = self.json_cli("attempts", "course", "sources", "add",
                                   "--path", str(outside))
        self.assertEqual(code, 0)
        self.assertIn(str(outside.resolve()), both["paths"])

        code, listed = self.json_cli("attempts", "course", "sources", "list")
        self.assertEqual(code, 0)
        self.assertEqual(listed["paths"], both["paths"])
        self.assertEqual(self.learning_rows()["problem_attempts"], [])

        stored = json.loads(
            self.registry.answer_sources_path().read_text(encoding="utf-8"))
        self.assertEqual(stored["workspaces"]["course"], both["paths"])
        self.assertNotIn("p1.jpg", json.dumps(stored))

        code, removed = self.json_cli("attempts", "course", "sources", "remove",
                                      "--path", str(photos))
        self.assertEqual(code, 0)
        self.assertEqual(removed["paths"], [str(outside.resolve())])

    def test_sources_reject_a_missing_directory_and_unknown_removal(self):
        code, result = self.json_cli("attempts", "course", "sources", "add",
                                     "--path", str(Path(self.tmp.name) / "nope"))
        self.assertEqual(code, 2)
        self.assertIn("not a readable directory", result["error"])

        code, result = self.json_cli("attempts", "course", "sources", "remove",
                                     "--path", str(Path(self.tmp.name) / "nope"))
        self.assertEqual(code, 2)
        self.assertIn("not configured for course", result["error"])

    def test_sources_are_scoped_to_one_workspace(self):
        photos = Path(self.tmp.name) / "photos"
        photos.mkdir()
        self.json_cli("attempts", "course", "sources", "add", "--path", str(photos))
        other = Path(self.tmp.name) / "other"
        (other / "pool").mkdir(parents=True)
        conn = sqlite3.connect(other / "pool" / "dmath.db")
        conn.executescript(create_tables.SCHEMA_SQL)
        pool_schema.ensure_workbench_schema(conn)
        conn.commit()
        conn.close()
        self.registry.register(str(other), name="other", course="dmath", chapter="ch12")
        code, listed = self.json_cli("attempts", "other", "sources", "list")
        self.assertEqual(code, 0)
        self.assertEqual(listed["paths"], [])


class ScenarioTests(AttemptsTestCase):
    def test_multi_page_answer_two_problems_one_page_and_a_later_correction(self):
        transcription = "\n".join([
            "第一页：设 n+1 个物体放入 n 个盒子，由反证法假设……",
            "第二页：取两个落在同一盒子的物体，其差为 n 的倍数。",
            "第三页：故矛盾，原命题成立。",
        ])
        manifest = [
            {"problem_id": "dmath-ch12-prob-001", "answer_text": transcription,
             "note": "转录自三张照片；当前掌握程度 3", "rating": 3},
            {"problem_id": "dmath-ch12-prob-002", "answer_text": "只写了一个开头：令 f(x)=……",
             "note": "同一页第二题，未完成，暂不评分"},
        ]

        code, first = self.apply("conv-002-turn-001-record", manifest)
        self.assertEqual(code, 0)
        self.assertEqual(first["counts"], {"attempts": 2, "graded": 1, "ungraded": 1})
        recorded = self.rows(
            "SELECT * FROM problem_attempts ORDER BY id")
        self.assertEqual(recorded[0]["answer_text"], transcription)
        self.assertEqual(recorded[1]["status"], "new")

        # The response was lost, so the Agent retries the identical request.
        code, retry = self.apply(
            "conv-002-turn-001-record", manifest, name="retry.json")
        self.assertEqual(code, 0)
        self.assertEqual(retry, first)
        self.assertEqual(len(self.rows("SELECT * FROM problem_attempts")), 2)

        # The learner then corrects the grading of the finished problem only.
        code, corrected = self.correct(recorded[0]["id"], "conv-002-turn-002-correct", {
            "answer_text": transcription, "note": "重看照片后改为 2", "rating": 2})
        self.assertEqual(code, 0)
        self.assertEqual(corrected["items"][0]["attempt_id"], recorded[0]["id"])
        self.assertEqual(corrected["items"][0]["status"], "wrong")
        self.assertEqual(
            len(self.rows("SELECT * FROM problem_attempts")), 2)
        self.assertEqual(
            [row["rating"] for row in
             self.rows("SELECT * FROM feedback_events ORDER BY id")], [2])
        self.assertEqual(
            self.rows("SELECT * FROM problem_progress WHERE problem_id=?",
                      ("dmath-ch12-prob-001",))[0]["status"], "wrong")
        self.assertIsNone(self.schedule("dmath-ch12-prob-002"))
        self.assertEqual(
            self.schedule("dmath-ch12-prob-001")["last_rating"], 2)

        code, listed = self.json_cli("attempts", "course", "list",
                                     "--problem", "dmath-ch12-prob-001")
        self.assertEqual(listed["attempts"][0]["rating"], 2)

    def test_attempts_and_corrections_stay_inside_their_workspace(self):
        other = Path(self.tmp.name) / "other"
        (other / "pool").mkdir(parents=True)
        conn = sqlite3.connect(other / "pool" / "dmath.db")
        conn.executescript(create_tables.SCHEMA_SQL)
        pool_schema.ensure_workbench_schema(conn)
        conn.execute(
            "INSERT INTO problems (problem_id, kp_ids, problem_text, problem_type,"
            " source_kind) VALUES (?, ?, ?, ?, ?)",
            ("dmath-ch12-prob-001", '["dmath-ch12-kp-001"]', "另一工作区的同名题",
             "proof", "textbook"))
        conn.commit()
        conn.close()
        self.registry.register(str(other), name="other", course="dmath", chapter="ch12")

        self.apply("r1", [{"problem_id": "dmath-ch12-prob-001",
                           "answer_text": "本工作区的作答", "rating": 4}])
        code, result = self.json_cli("attempts", "other", "list",
                                     "--problem", "dmath-ch12-prob-001")
        self.assertEqual(code, 0)
        self.assertEqual(result["count"], 0)

        code, replayed = self.json_cli(
            "attempts", "other", "apply",
            "--input", self.manifest("other.json", "r1",
                                     [{"problem_id": "dmath-ch12-prob-001",
                                       "answer_text": "另一工作区的作答", "rating": 5}]))
        self.assertEqual(code, 0)
        self.assertEqual(replayed["counts"], {"attempts": 1, "graded": 1, "ungraded": 0})

        self.assertEqual(self.answer_texts(self.db_path), [("本工作区的作答",)])
        self.assertEqual(
            self.answer_texts(other / "pool" / "dmath.db"), [("另一工作区的作答",)])
        code, still_mine = self.json_cli("attempts", "course", "list",
                                         "--problem", "dmath-ch12-prob-001")
        self.assertEqual(still_mine["count"], 1)
        self.assertEqual(still_mine["attempts"][0]["rating"], 4)
        self.assertEqual(still_mine["attempts"][0]["request_id"], "r1")


if __name__ == "__main__":
    unittest.main()
