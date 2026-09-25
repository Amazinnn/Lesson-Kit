"""Atomic staged content bundles: knowledge points, problems, cards, figures."""

import json
import sqlite3
import unittest
from pathlib import Path

from workbench import ingest

from tests.workbench.fixtures import WorkspaceFixture


def formal(key, kp_ids, text="P", **extra):
    item = {
        "key": key,
        "problem_type": "calculation",
        "problem_text": text,
        "kp_ids": kp_ids,
        "source_kind": "textbook",
        "origin_kind": "source_problem",
        "source_evidence": "教材 第12章 习题12-1",
    }
    item.update(extra)
    return item


def micro(key, kp_ids, **extra):
    item = {
        "key": key,
        "problem_type": "other",
        "stem": "判断：电场是矢量。",
        "quiz_type": "yes_no",
        "answer_key": "是",
        "error_reason": "电场有大小和方向。",
        "kp_ids": kp_ids,
        "source_kind": "textbook",
        "origin_kind": "generated_grounded",
        "source_evidence": "教材 第12章 §12-1",
    }
    item.update(extra)
    return item


class ContentBundleTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        self.ws = self.fixture.ws
        self.db_path = self.fixture.db_path
        (self.ws / ".lessonkit" / "jobs" / "conv-001").mkdir(parents=True, exist_ok=True)
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

    def count(self, table):
        return self.query(f"SELECT COUNT(*) FROM {table}")[0][0]

    def column(self, table, problem_id, field, id_field):
        rows = self.query(
            f"SELECT {field} FROM {table} WHERE {id_field}=?", (problem_id,)
        )
        return rows[0][0] if rows else None

    def image(self, name="figure.png", payload=b"\x89PNG-original-bytes"):
        path = Path(self.fixture.tmp.name) / name
        path.write_bytes(payload)
        return path

    def apply(self, manifest, **kwargs):
        # each governed batch owns its own recoverable copy, like the bridge does
        self.backups += 1
        backup = Path(self.fixture.tmp.name) / f"backup-{self.backups:03d}.db"
        return ingest.apply_content_bundle(
            self.db_path, manifest, backup_path=backup, course="dmath", **kwargs
        )

    # -- atomic multi-asset bundle ---------------------------------------

    def test_thirty_items_commit_under_one_batch_id(self):
        figure = self.image()
        problems = [
            formal(f"p{index}", ["kp-new"], text=f"题目 {index}")
            for index in range(1, 27)
        ]
        problems.append(formal(
            "p27", ["kp-new"], text="图题 ![图](figure:f1)",
            figures=[{"key": "f1", "source_path": str(figure)}],
        ))
        manifest = {
            "kind": "content-bundle",
            "chapter": "ch06",
            "knowledge_points": [{
                "key": "kp-new", "knowledge_item": "电场强度",
                "knowledge_type": "concept-property", "importance": "core",
                "source_location": "教材 第12章 §12-1",
            }],
            "problems": problems,
            "flash_cards": [{
                "key": "c1", "kp_id": "kp-new", "front": "E 的单位？",
                "back": "N/C", "source_evidence": "教材 第12章",
            }],
        }
        manifest["problems"].append(micro("m1", ["kp-new"]))

        before_problems = self.count("problems")
        result = self.apply(manifest)

        self.assertTrue(result["ok"])
        self.assertEqual(result["kind"], "content-bundle")
        self.assertEqual(
            {key: result["counts"][key] for key in
             ("knowledge_points", "problems", "flash_cards", "figures")},
            {"knowledge_points": 1, "problems": 28, "flash_cards": 1, "figures": 1},
        )
        self.assertEqual(self.count("problems"), before_problems + 28)
        batch = self.query(
            "SELECT kind, counts_json FROM ingest_batches WHERE batch_id=?",
            (result["batch_id"],),
        )
        self.assertEqual(batch[0][0], "content-bundle")
        self.assertEqual(json.loads(batch[0][1])["problems"], 28)
        self.assertEqual(
            self.query("SELECT COUNT(*) FROM problems WHERE ingest_batch_id=?",
                       (result["batch_id"],))[0][0],
            28,
        )
        self.assertEqual(
            self.query("SELECT COUNT(*) FROM knowledge_points WHERE ingest_batch_id=?",
                       (result["batch_id"],))[0][0],
            1,
        )
        self.assertEqual(
            self.query("SELECT COUNT(*) FROM flash_cards WHERE ingest_batch_id=?",
                       (result["batch_id"],))[0][0],
            1,
        )
        kp_id = self.query(
            "SELECT kp_id FROM knowledge_points WHERE ingest_batch_id=?",
            (result["batch_id"],),
        )[0][0]
        self.assertRegex(kp_id, r"^dmath-ch06-kp-\d{3}$")
        problem_ids = [row[0] for row in self.query(
            "SELECT problem_id FROM problems WHERE ingest_batch_id=? ORDER BY problem_id",
            (result["batch_id"],),
        )]
        self.assertEqual(len(problem_ids), 28)
        formal_ids = [item for item in problem_ids if "-prob-" in item]
        micro_ids = [item for item in problem_ids if "-mq-" in item]
        self.assertEqual(len(formal_ids), 27)
        self.assertEqual(len(micro_ids), 1)
        self.assertTrue(all(item.startswith("dmath-ch06-prob-") for item in formal_ids))

    def test_every_problem_carries_the_shared_batch_id(self):
        result = self.apply({
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [
                formal("p1", ["dmath-ch06-kp-001"]),
                formal("p2", ["dmath-ch06-kp-001"]),
            ],
        })
        rows = self.query(
            "SELECT ingest_batch_id FROM problems WHERE problem_id LIKE 'dmath-ch06-prob-0%'"
            " AND problem_id != 'dmath-ch06-prob-001'"
        )
        self.assertTrue(rows)
        self.assertEqual({row[0] for row in rows}, {result["batch_id"]})

    # -- all-or-nothing ---------------------------------------------------

    def test_missing_required_image_blocks_the_whole_bundle(self):
        before = (self.count("problems"), self.count("knowledge_points"),
                  self.count("flash_cards"))
        with self.assertRaises(ValueError) as caught:
            self.apply({
                "kind": "content-bundle",
                "chapter": "ch06",
                "knowledge_points": [{
                    "key": "kp-new", "knowledge_item": "电场",
                    "knowledge_type": "concept-property", "importance": "core",
                }],
                "problems": [
                    formal("p1", ["kp-new"]),
                    formal("p2", ["kp-new"], text="图题 ![图](figure:f1)",
                           figures=[{"key": "f1", "source_path": str(
                               Path(self.fixture.tmp.name) / "absent.png")}]),
                ],
            })
        message = str(caught.exception)
        self.assertIn("absent.png", message)
        self.assertEqual(
            (self.count("problems"), self.count("knowledge_points"),
             self.count("flash_cards")),
            before,
        )
        self.assertEqual(self.count("ingest_batches"), 0)
        self.assertFalse((self.ws / ".lessonkit" / "figures").exists())

    def test_unknown_reference_blocks_the_whole_bundle(self):
        before = self.count("problems")
        with self.assertRaises(ValueError) as caught:
            self.apply({
                "kind": "content-bundle",
                "chapter": "ch06",
                "problems": [
                    formal("p1", ["dmath-ch06-kp-001"]),
                    formal("p2", ["dmath-ch06-kp-999"]),
                ],
            })
        self.assertIn("dmath-ch06-kp-999", str(caught.exception))
        self.assertEqual(self.count("problems"), before)
        self.assertEqual(self.count("ingest_batches"), 0)

    def test_unreferenced_declared_figure_is_refused(self):
        figure = self.image(name="unused.png")
        with self.assertRaises(ValueError) as caught:
            self.apply({
                "kind": "content-bundle",
                "chapter": "ch06",
                "problems": [formal(
                    "p1", ["dmath-ch06-kp-001"], text="没有图片引用",
                    figures=[{"key": "f1", "source_path": str(figure)}],
                )],
            })
        self.assertIn("f1", str(caught.exception))

    def test_unsupported_figure_extension_is_refused(self):
        source = Path(self.fixture.tmp.name) / "notes.txt"
        source.write_bytes(b"not an image")
        with self.assertRaises(ValueError) as caught:
            self.apply({
                "kind": "content-bundle",
                "chapter": "ch06",
                "problems": [formal(
                    "p1", ["dmath-ch06-kp-001"], text="![图](figure:f1)",
                    figures=[{"key": "f1", "source_path": str(source)}],
                )],
            })
        self.assertIn("extension", str(caught.exception))

    # -- source and solution fidelity ------------------------------------

    def test_formal_source_problem_keeps_type_answer_and_solution_origin(self):
        result = self.apply({
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [formal(
                "p1", ["dmath-ch06-kp-001"],
                text="证明：静电场是无旋场。",
                problem_type="proof",
                source_answer="由环路定理可得。",
                solution="教材原解：取任意闭合回路积分。",
                solution_origin="source",
            )],
        })
        problem_id = self.query(
            "SELECT problem_id FROM problems WHERE ingest_batch_id=?",
            (result["batch_id"],),
        )[0][0]
        row = self.query(
            "SELECT problem_type, origin_kind, source_evidence, source_answer,"
            " solution, solution_origin FROM problems WHERE problem_id=?",
            (problem_id,),
        )[0]
        self.assertEqual(row[0], "proof")
        self.assertEqual(row[1], "source_problem")
        self.assertEqual(row[2], "教材 第12章 习题12-1")
        self.assertEqual(row[3], "由环路定理可得。")
        self.assertEqual(row[4], "教材原解：取任意闭合回路积分。")
        self.assertEqual(row[5], "source")

    def test_generated_explanation_is_labelled(self):
        result = self.apply({
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [formal(
                "p1", ["dmath-ch06-kp-001"], source_answer="答案：0",
                solution="AI 详细推导：……", solution_origin="generated",
            )],
        })
        problem_id = self.query(
            "SELECT problem_id FROM problems WHERE ingest_batch_id=?",
            (result["batch_id"],),
        )[0][0]
        self.assertEqual(
            self.column("problems", problem_id, "solution_origin", "problem_id"),
            "generated",
        )
        self.assertEqual(
            self.column("problems", problem_id, "source_answer", "problem_id"),
            "答案：0",
        )

    def test_missing_source_evidence_is_refused(self):
        item = formal("p1", ["dmath-ch06-kp-001"])
        item.pop("source_evidence")
        with self.assertRaises(ValueError) as caught:
            self.apply({"kind": "content-bundle", "chapter": "ch06", "problems": [item]})
        self.assertIn("source_evidence", str(caught.exception))

    def test_micro_quiz_keeps_its_structured_subtype(self):
        result = self.apply({
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [micro(
                "m1", ["dmath-ch06-kp-001"], quiz_type="single_choice",
                options=["是", "否"], answer_key="是",
            )],
        })
        problem_id = self.query(
            "SELECT problem_id FROM problems WHERE ingest_batch_id=?",
            (result["batch_id"],),
        )[0][0]
        row = self.query(
            "SELECT practice_modes, micro_quiz FROM problems WHERE problem_id=?",
            (problem_id,),
        )[0]
        self.assertIn("micro", json.loads(row[0]))
        payload = json.loads(row[1])
        self.assertEqual(payload["quiz_type"], "single_choice")
        self.assertEqual(payload["options"], ["是", "否"])

    # -- figures ----------------------------------------------------------

    def test_figure_bytes_are_copied_and_referenced_by_logical_path(self):
        payload = b"\x89PNG-original-bytes-\x00\x01"
        figure = self.image(name="src.png", payload=payload)
        result = self.apply({
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [formal(
                "p1", ["dmath-ch06-kp-001"], text="如图所示 ![图](figure:f1)",
                figures=[{"key": "f1", "source_path": str(figure)}],
            )],
        })
        problem_id = self.query(
            "SELECT problem_id FROM problems WHERE ingest_batch_id=?",
            (result["batch_id"],),
        )[0][0]
        text = self.column("problems", problem_id, "problem_text", "problem_id")
        paths = json.loads(
            self.column("problems", problem_id, "figure_paths", "problem_id")
        )
        self.assertNotIn("figure:f1", text)
        self.assertEqual(len(paths), 1)
        logical = paths[0]
        self.assertRegex(logical, r"^dmath/ch06/[0-9a-f]{64}\.png$")
        self.assertIn(f"]({logical})", text)
        stored = self.ws / ".lessonkit" / "figures" / logical
        self.assertTrue(stored.is_file())
        self.assertEqual(stored.read_bytes(), payload)

    def test_linked_problem_renders_and_rollback_removes_unreferenced_figure(self):
        figure = self.image(name="unique.png")
        result = self.apply({
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [formal(
                "p1", ["dmath-ch06-kp-001"], text="![图](figure:f1)",
                figures=[{"key": "f1", "source_path": str(figure)}],
            )],
        })
        logical = json.loads(self.query(
            "SELECT figure_paths FROM problems WHERE ingest_batch_id=?",
            (result["batch_id"],),
        )[0][0])[0]
        stored = self.ws / ".lessonkit" / "figures" / logical
        self.assertTrue(stored.is_file())

        rolled = ingest.rollback_batch(self.db_path, result["batch_id"])
        self.assertEqual(rolled["deleted"], 1)
        self.assertFalse(stored.exists())

    def test_rollback_keeps_a_shared_figure(self):
        figure = self.image(name="shared.png")
        first = self.apply({
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [formal(
                "p1", ["dmath-ch06-kp-001"], text="![图](figure:f1)",
                figures=[{"key": "f1", "source_path": str(figure)}],
            )],
        })
        second = self.apply({
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [formal(
                "p2", ["dmath-ch06-kp-001"], text="![图](figure:f2)",
                figures=[{"key": "f2", "source_path": str(figure)}],
            )],
        })
        logical = json.loads(self.query(
            "SELECT figure_paths FROM problems WHERE ingest_batch_id=?",
            (second["batch_id"],),
        )[0][0])[0]
        stored = self.ws / ".lessonkit" / "figures" / logical
        self.assertTrue(stored.is_file())

        ingest.rollback_batch(self.db_path, second["batch_id"])
        self.assertTrue(stored.is_file())
        ingest.rollback_batch(self.db_path, first["batch_id"])
        self.assertFalse(stored.exists())

    # -- append-only discipline ------------------------------------------

    def test_bundle_refuses_to_overwrite_existing_problem(self):
        with self.assertRaises(ValueError) as caught:
            self.apply({
                "kind": "content-bundle",
                "chapter": "ch06",
                "problems": [dict(
                    formal("p1", ["dmath-ch06-kp-001"]),
                    problem_id="dmath-ch06-prob-001",
                )],
            })
        self.assertIn("already exists", str(caught.exception))

    def test_rollback_refuses_when_the_new_kp_is_still_referenced(self):
        bundle = self.apply({
            "kind": "content-bundle",
            "chapter": "ch06",
            "knowledge_points": [{
                "key": "kp-new", "knowledge_item": "电势",
                "knowledge_type": "concept-property", "importance": "core",
            }],
            "problems": [formal("p1", ["kp-new"])],
        })
        kp_id = self.query(
            "SELECT kp_id FROM knowledge_points WHERE ingest_batch_id=?",
            (bundle["batch_id"],),
        )[0][0]
        # keep the problem, delete only its batch membership: the KP is now
        # referenced by a surviving row, so the rollback must refuse.
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE problems SET ingest_batch_id=NULL WHERE problem_id LIKE '%-prob-%'")
        conn.commit()
        conn.close()
        with self.assertRaises(ValueError) as caught:
            ingest.rollback_batch(self.db_path, bundle["batch_id"])
        self.assertIn(kp_id, str(caught.exception))

    def test_unknown_kind_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            self.apply({"kind": "flash-card-patch", "items": []})
        self.assertIn("content-bundle", str(caught.exception))

    # -- bundles that span chapters --------------------------------------

    def two_chapter_manifest(self, figure=None):
        manifest = {
            "kind": "content-bundle",
            "chapter": "ch06",
            "knowledge_points": [
                {"key": "kp-06", "knowledge_item": "第六章概念"},
                {"key": "kp-07", "chapter": "ch07", "knowledge_item": "第七章概念"},
            ],
            "problems": [
                formal("p-06", ["kp-06"], text="第六章题目"),
                formal("p-07", ["kp-07"], chapter="ch07", text="第七章题目"),
            ],
        }
        if figure is not None:
            manifest["problems"].append(formal(
                "p-fig", ["kp-07"], text="带图题目 ![图](figure:f1)",
                chapter="ch07", figures=[{"key": "f1", "source_path": str(figure)}],
            ))
        return manifest

    def test_one_bundle_imports_two_chapters(self):
        figure = self.image("two-chapter.png")
        result = self.apply(self.two_chapter_manifest(figure))

        self.assertTrue(result["ok"])
        self.assertEqual([batch["chapter"] for batch in result["batches"]], ["ch06", "ch07"])
        self.assertEqual(len({batch["batch_id"] for batch in result["batches"]}), 2)
        self.assertNotIn("batch_id", result, "a multi-chapter bundle has no single batch id")
        self.assertEqual(
            [row[0] for row in self.query(
                "SELECT problem_id FROM problems WHERE problem_id LIKE 'dmath-ch0%'"
                " ORDER BY problem_id")],
            ["dmath-ch06-prob-001", "dmath-ch06-prob-002", "dmath-ch07-prob-001",
             "dmath-ch07-prob-002"],
        )
        self.assertEqual(
            self.query("SELECT problem_id, ingest_batch_id FROM problems WHERE"
                       " problem_id LIKE 'dmath-ch07-prob-%' ORDER BY problem_id"),
            [("dmath-ch07-prob-001", result["batches"][1]["batch_id"]),
             ("dmath-ch07-prob-002", result["batches"][1]["batch_id"])],
        )
        # Each chapter's figures land in its own chapter directory.
        self.assertTrue((self.ws / ".lessonkit" / "figures" / "dmath" / "ch07"
                         / f"{figure.stem}").parent.is_dir())
        copied = list((self.ws / ".lessonkit" / "figures" / "dmath" / "ch07").glob("*.png"))
        self.assertEqual(len(copied), 1)
        self.assertFalse((self.ws / ".lessonkit" / "figures" / "dmath" / "ch06").exists())
        self.assertEqual(len(self.query("SELECT batch_id FROM ingest_batches")), 2)

    def test_each_chapter_batch_rolls_back_alone(self):
        result = self.apply(self.two_chapter_manifest())
        first, second = (batch["batch_id"] for batch in result["batches"])

        rolled = ingest.rollback_batch(self.db_path, first)

        self.assertEqual(rolled["counts"]["problems"], 1)
        self.assertEqual(
            [row[0] for row in self.query(
                "SELECT problem_id FROM problems WHERE problem_id LIKE 'dmath-ch07-prob-%'")],
            ["dmath-ch07-prob-001"], "the sibling batch stays")
        states = dict(self.query("SELECT batch_id, rolled_back_at FROM ingest_batches"))
        self.assertIsNotNone(states[first])
        self.assertIsNone(states[second])

    def test_an_item_without_a_chapter_is_refused(self):
        manifest = self.two_chapter_manifest()
        del manifest["chapter"]
        manifest["knowledge_points"][0].pop("chapter", None)
        before = self.count("problems")

        with self.assertRaises(ValueError) as caught:
            self.apply(manifest)

        self.assertIn("knowledge point 1: chapter is required", str(caught.exception))
        self.assertEqual(self.count("problems"), before)
        self.assertEqual(len(self.query("SELECT batch_id FROM ingest_batches")), 0)

    def test_a_bad_chapter_value_is_refused(self):
        manifest = self.two_chapter_manifest()
        manifest["problems"][1]["chapter"] = "第7章"
        with self.assertRaises(ValueError) as caught:
            self.apply(manifest)
        self.assertIn("chapter must be a lowercase ASCII identifier", str(caught.exception))

    def test_an_explicit_id_must_name_the_items_chapter(self):
        manifest = self.two_chapter_manifest()
        manifest["problems"][1]["problem_id"] = "dmath-ch08-prob-001"
        with self.assertRaises(ValueError) as caught:
            self.apply(manifest)
        message = str(caught.exception)
        self.assertIn("must start with dmath-ch07-", message)
        self.assertIn("it belongs to ch08", message)

    def test_a_single_chapter_bundle_keeps_the_legacy_result(self):
        manifest = {
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [formal("p1", [], text="题目")],
        }
        manifest["problems"][0]["kp_ids"] = ["dmath-ch06-kp-001"]
        result = self.apply(manifest)
        self.assertEqual(result["batch_id"], result["batches"][0]["batch_id"])
        self.assertEqual(result["counts"]["problems"], 1)
        self.assertEqual(result["origins"], {"source_problem": 1})

    # -- practice mode and missing answer keys ---------------------------

    def test_an_objective_item_may_enter_without_an_answer_key(self):
        page = ["dmath-ch06-kp-001"]
        manifest = {
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [
                micro("m1", page, answer_key=None, error_reason=None),
                micro("m2", page, quiz_type="single_choice", stem="与 E 同向的是？",
                      options=["甲", "乙", "丙"], answer_key=None, error_reason=None),
                micro("m3", page),
            ],
        }

        result = self.apply(manifest)

        self.assertEqual(result["counts"]["problems"], 3)
        self.assertEqual(result["counts"]["keyless"], 2)
        rows = self.query(
            "SELECT problem_id, practice_modes, micro_quiz FROM problems "
            "WHERE problem_id LIKE '%mq-%' ORDER BY problem_id"
        )
        self.assertEqual([tuple(json.loads(row[1])) for row in rows],
                         [("yes_no",), ("micro",), ("yes_no",)])
        payloads = {row[0]: json.loads(row[2]) for row in rows}
        keyless = [row[0] for row in rows if payloads[row[0]]["answer_key"] is None]
        self.assertEqual(len(keyless), 2)
        self.assertIsNone(payloads[keyless[0]]["error_reason"])
        graded = [row[0] for row in rows if payloads[row[0]]["answer_key"] == "是"]
        self.assertEqual(len(graded), 1)
        batch = self.query(
            "SELECT counts_json FROM ingest_batches WHERE batch_id=?",
            (result["batch_id"],),
        )
        self.assertEqual(json.loads(batch[0][0])["keyless"], 2)

    def test_a_keyed_item_still_needs_its_error_reason(self):
        manifest = {
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [micro("m1", ["dmath-ch06-kp-001"], error_reason=None)],
        }
        with self.assertRaises(ValueError) as caught:
            self.apply(manifest)
        self.assertIn("error_reason is required", str(caught.exception))

    def test_a_keyless_choice_item_still_needs_options(self):
        manifest = {
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [micro("m1", ["dmath-ch06-kp-001"],
                               quiz_type="single_choice", options=None,
                               answer_key=None, error_reason=None)],
        }
        with self.assertRaises(ValueError) as caught:
            self.apply(manifest)
        self.assertIn("choice items need 2-6 options", str(caught.exception))

    def test_a_plain_problem_cannot_declare_a_micro_mode(self):
        manifest = {
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [formal("p1", ["dmath-ch06-kp-001"],
                                practice_modes=["micro"])],
        }
        before = self.count("problems")

        with self.assertRaises(ValueError) as caught:
            self.apply(manifest)

        message = str(caught.exception)
        self.assertIn("practice_modes ['micro']", message)
        self.assertIn("quiz_type", message)
        self.assertEqual(self.count("problems"), before)

    def test_declaring_the_exam_mode_is_a_no_op(self):
        manifest = {
            "kind": "content-bundle",
            "chapter": "ch06",
            "problems": [formal("p1", ["dmath-ch06-kp-001"],
                                practice_modes=["exam"])],
        }
        result = self.apply(manifest)
        self.assertEqual(result["counts"]["problems"], 1)
        self.assertEqual(result["counts"]["keyless"], 0)
        stored = self.query(
            "SELECT practice_modes FROM problems WHERE ingest_batch_id=?",
            (result["batch_id"],),
        )
        self.assertEqual(stored, [(None,)])


if __name__ == "__main__":
    unittest.main()
