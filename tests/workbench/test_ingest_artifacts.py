"""JSON artifact file operations keep the historical ingest entry points."""

import json
import tempfile
import unittest
from pathlib import Path

from workbench import ingest
from workbench.ingest import artifacts


class IngestArtifactTests(unittest.TestCase):
    def test_round_trip_creates_parent_and_preserves_utf8(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "nested" / "task.json"
            payload = {"kind": "content-bundle", "title": "电场练习"}

            self.assertIs(ingest.write_artifact, artifacts.write_artifact)
            self.assertEqual(ingest.write_artifact(path, payload), payload)
            self.assertEqual(ingest.read_artifact(path), payload)
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))

    def test_artifacts_must_be_json_objects(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "list.json"
            path.write_text(json.dumps([1, 2]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON object"):
                ingest.read_artifact(path)
            with self.assertRaisesRegex(ValueError, "JSON object"):
                ingest.write_artifact(path, [1, 2])

    def test_staged_manifest_reads_only_relative_json_inside_folder(self):
        with tempfile.TemporaryDirectory() as temporary:
            jobs = Path(temporary) / "jobs"
            staged = jobs / "turn-001" / "manifest.json"
            staged.parent.mkdir(parents=True)
            staged.write_text('{"kind":"content-bundle"}', encoding="utf-8")

            self.assertIs(ingest.read_staged_manifest, artifacts.read_staged_manifest)
            self.assertEqual(
                ingest.read_staged_manifest(jobs, "turn-001/manifest.json"),
                {"kind": "content-bundle"},
            )
            for reference in ("../outside.json", str(staged), "manifest.txt"):
                with self.subTest(reference=reference), self.assertRaises(ValueError):
                    ingest.read_staged_manifest(jobs, reference)

    def test_staged_manifest_requires_an_existing_object_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            jobs = Path(temporary)
            with self.assertRaisesRegex(ValueError, "not found"):
                ingest.read_staged_manifest(jobs, "missing.json")
            (jobs / "list.json").write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON object"):
                ingest.read_staged_manifest(jobs, "list.json")


if __name__ == "__main__":
    unittest.main()
