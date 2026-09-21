"""Gated figure-patch channel and legacy source-image migration."""

import hashlib
import io
import contextlib
import json
import sqlite3
import unittest
from pathlib import Path

from tests.workbench.fixtures import WorkspaceFixture


class FigurePatchTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.ingest import FIGURE_PATCH_KIND, apply_figure_patch

        self.kind = FIGURE_PATCH_KIND
        self.apply = apply_figure_patch
        self.db = self.fixture.ws / "pool" / "dmath.db"
        self.images = Path(self.fixture.tmp.name) / "sources"
        self.images.mkdir()
        self.content = b"figure-bytes-for-tests"
        self.source = self.images / "stale-name.jpg"
        self.source.write_bytes(self.content)
        self.name = hashlib.sha256(self.content).hexdigest() + ".jpg"
        self.logical = f"dmath/ch06/{self.name}"
        self.text = "看图作答。\n\n![](images/old.jpg)"

    def tearDown(self):
        self.fixture.cleanup()

    def manifest(self, text=None, source=None, owner="dmath-ch06-prob-001"):
        return {
            "kind": self.kind, "course": "dmath", "chapter": "ch06",
            "items": [{
                "owner_type": "problem", "owner_id": owner,
                "figure_files": [{"source_path": str(source or self.source)}],
                "text": self.text if text is None else text,
            }],
        }

    def row(self, problem_id="dmath-ch06-prob-001"):
        conn = sqlite3.connect(self.db)
        try:
            return conn.execute(
                "SELECT problem_text, figure_paths, ingest_batch_id "
                "FROM problems WHERE problem_id=?", (problem_id,)
            ).fetchone()
        finally:
            conn.close()

    def test_apply_lands_the_figure_and_updates_the_row(self):
        text = f"看图作答。\n\n![]({self.logical})"
        manifest_path = Path(self.fixture.tmp.name) / "manifest.json"
        manifest_path.write_text(json.dumps(self.manifest(text=text)), encoding="utf-8")
        stamp_before = self.row()[2]

        result = self.apply(self.db, manifest_path)

        self.assertTrue(result["ok"])
        landed = self.fixture.ws / ".lessonkit" / "figures" / "dmath" / "ch06" / self.name
        self.assertTrue(landed.is_file())
        self.assertEqual(landed.read_bytes(), self.content)
        new_text, figure_paths, batch_stamp = self.row()
        self.assertEqual(new_text, text)
        self.assertEqual(json.loads(figure_paths), [self.logical])
        self.assertEqual(batch_stamp, stamp_before)

    def test_gate_rejects_and_writes_nothing(self):
        missing = self.manifest(source=self.images / "nope.jpg")
        unreferenced = self.manifest(text="没有引用的题干")
        unknown = self.manifest(owner="dmath-ch06-prob-999")
        for manifest in (missing, unreferenced, unknown):
            path = Path(self.fixture.tmp.name) / "m.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ValueError):
                self.apply(self.db, path)
        self.assertIsNone(self.row()[1])
        self.assertFalse(
            (self.fixture.ws / ".lessonkit" / "figures" / "dmath" / "ch06").exists())

    def test_a_foreign_course_or_escaping_chapter_is_refused(self):
        outside = Path(self.fixture.tmp.name) / "escaped"
        for course, chapter in (("c01", "ch06"), ("dmath", "../../escaped")):
            manifest = self.manifest(text=f"![]({course}/{chapter}/{self.name})")
            manifest["course"], manifest["chapter"] = course, chapter
            path = Path(self.fixture.tmp.name) / "m.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaises(ValueError):
                self.apply(self.db, path)

        self.assertIsNone(self.row()[1])
        self.assertFalse(outside.exists())
        self.assertFalse((self.fixture.ws / ".lessonkit" / "figures" / "c01").exists())

    def test_destination_conflict_is_rejected(self):
        figures = self.fixture.ws / ".lessonkit" / "figures" / "dmath" / "ch06"
        figures.mkdir(parents=True)
        (figures / self.name).write_bytes(b"different-bytes")
        path = Path(self.fixture.tmp.name) / "m.json"
        path.write_text(json.dumps(
            self.manifest(text=f"![]({self.logical})")), encoding="utf-8")

        with self.assertRaises(ValueError):
            self.apply(self.db, path)

        self.assertEqual((figures / self.name).read_bytes(), b"different-bytes")
        self.assertIsNone(self.row()[1])

    def test_rollback_restores_the_previous_text(self):
        path = Path(self.fixture.tmp.name) / "m.json"
        path.write_text(json.dumps(
            self.manifest(text=f"![]({self.logical})")), encoding="utf-8")
        result = self.apply(self.db, path)
        from workbench.ingest import rollback_batch

        rollback_batch(self.db, result["batch_id"])

        new_text, figure_paths, batch_stamp = self.row()
        self.assertEqual(new_text, "P1")
        self.assertIsNone(figure_paths)
        self.assertIsNone(batch_stamp)
        self.assertTrue(
            (self.fixture.ws / ".lessonkit" / "figures" / "dmath" / "ch06" / self.name)
            .is_file())

    def test_recipe_dispatch_applies_figures(self):
        from workbench.ingest import recipe

        manifest_path = Path(self.fixture.tmp.name) / "m.json"
        manifest_path.write_text(json.dumps(
            self.manifest(text=f"![]({self.logical})")), encoding="utf-8")
        out_dir = Path(self.fixture.tmp.name) / "recipe-out"
        out_dir.mkdir()

        result = recipe("figures", self.db, manifest_path, out_dir,
                        apply_changes=True)

        self.assertTrue(result["applied"])
        self.assertEqual(json.loads(self.row()[1]), [self.logical])


class LegacyMigrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.ingest import build_legacy_figure_manifest, migrate_legacy_figures

        self.build = build_legacy_figure_manifest
        self.migrate = migrate_legacy_figures
        self.db = self.fixture.ws / "pool" / "dmath.db"
        self.content = b"legacy-image-bytes"
        self.name = hashlib.sha256(self.content).hexdigest() + ".jpg"
        self.legacy_name = "3d9f6934d96a760745fd62a416dbb67dddaef0ba82c5be69ba62c25ff1d2266e.jpg"
        self.source_dir = self.fixture.ws / "intermediate" / "dmath" / "extraction" / "ch06" / "00_source" / "images"
        self.source_dir.mkdir(parents=True)
        (self.source_dir / self.legacy_name).write_bytes(self.content)
        conn = sqlite3.connect(self.db)
        try:
            conn.execute(
                "UPDATE problems SET problem_text=? WHERE problem_id='dmath-ch06-prob-001'",
                ("看图作答。\n\n![](images/" + self.legacy_name + ")",),
            )
            conn.commit()
        finally:
            conn.close()

    def tearDown(self):
        self.fixture.cleanup()

    def test_dry_run_plans_without_writing(self):
        plan = self.build(self.db, self.fixture.ws)

        self.assertTrue(plan["ok"])
        manifest = plan["manifests"][0]
        self.assertEqual(manifest["course"], "dmath")
        self.assertEqual(manifest["chapter"], "ch06")
        item = manifest["items"][0]
        self.assertEqual(item["owner_id"], "dmath-ch06-prob-001")
        self.assertIn(f"](dmath/ch06/{self.name})", item["text"])
        self.assertFalse(
            (self.fixture.ws / ".lessonkit" / "figures").exists())

    def test_missing_source_blocks_the_migration(self):
        (self.source_dir / self.legacy_name).unlink()

        plan = self.build(self.db, self.fixture.ws)

        self.assertFalse(plan["ok"])
        self.assertIn("source image not found", plan["errors"][0])

    def test_migrate_applies_through_the_gate(self):
        result = self.migrate(self.db, self.fixture.ws, apply_changes=True)

        self.assertTrue(result["applied"])
        batch = result["results"][0]
        self.assertTrue(batch["ok"])
        landed = self.fixture.ws / ".lessonkit" / "figures" / "dmath" / "ch06" / self.name
        self.assertTrue(landed.is_file())
        conn = sqlite3.connect(self.db)
        try:
            text, figure_paths, _ = conn.execute(
                "SELECT problem_text, figure_paths, ingest_batch_id FROM problems"
                " WHERE problem_id='dmath-ch06-prob-001'"
            ).fetchone()
        finally:
            conn.close()
        self.assertIn(f"](dmath/ch06/{self.name})", text)
        self.assertEqual(json.loads(figure_paths), [f"dmath/ch06/{self.name}"])

    def test_cli_dry_run_reports_the_plan(self):
        from workbench.cli import main as cli_main

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli_main.main(["ingest", "dmath", "migrate-figures"])

        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())["result"]
        self.assertFalse(payload["applied"])
        self.assertEqual(payload["manifests"][0]["items"][0]["owner_id"],
                         "dmath-ch06-prob-001")

    def test_logical_figure_path_renders_through_the_figures_route(self):
        from workbench.server.pages import _image_replace

        line = f"![](dmath/ch06/{self.name})"
        rendered = _image_replace(line, "lesson-kit")

        self.assertEqual(
            rendered,
            f"<img alt='' src='/api/w/lesson-kit/figures/dmath/ch06/{self.name}'>")


if __name__ == "__main__":
    unittest.main()
