"""Bridge job lifecycle tests (TDD, red first)."""

import importlib.util
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


jobs = load_script("wb_jobs", Path("workbench/bridge/jobs.py"))


class JobLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.jobs_dir = Path(self.tmp.name) / "jobs"

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_job_writes_files(self):
        job_id = jobs.create_job(
            self.jobs_dir,
            operation="explain",
            context={"problem_id": "p1", "note": "stuck"},
            instruction="Explain this.",
            output_contract={"sections": ["结论", "逐步拆解", "易错点", "回源指向"]},
        )
        job_dir = self.jobs_dir / job_id
        self.assertTrue((job_dir / "task.json").is_file())
        self.assertTrue((job_dir / "task.md").is_file())
        self.assertTrue((job_dir / "status.json").is_file())
        status = jobs.status(self.jobs_dir, job_id)
        self.assertEqual(status["state"], "queued")
        self.assertEqual(status["operation"], "explain")

    def test_sequential_job_ids(self):
        first = jobs.create_job(self.jobs_dir, "explain", {}, "x")
        second = jobs.create_job(self.jobs_dir, "diagnose", {}, "y")
        self.assertEqual(first, "job-001")
        self.assertEqual(second, "job-002")

    def test_concurrent_job_ids_are_reserved_atomically(self):
        def create(index):
            return jobs.create_job(self.jobs_dir, "explain", {}, str(index))

        with ThreadPoolExecutor(max_workers=8) as executor:
            job_ids = list(executor.map(create, range(20)))

        self.assertEqual(len(job_ids), len(set(job_ids)))
        self.assertTrue(all((self.jobs_dir / job_id / "status.json").is_file()
                            for job_id in job_ids))

    def test_mark_running_then_done(self):
        job_id = jobs.create_job(self.jobs_dir, "explain", {}, "x")
        jobs.mark(self.jobs_dir, job_id, "running")
        self.assertEqual(jobs.status(self.jobs_dir, job_id)["state"], "running")
        jobs.mark(self.jobs_dir, job_id, "done", result_file="r.md")
        status = jobs.status(self.jobs_dir, job_id)
        self.assertEqual(status["state"], "done")
        self.assertEqual(status["result_file"], "r.md")

    def test_fail_with_reason(self):
        job_id = jobs.create_job(self.jobs_dir, "explain", {}, "x")
        jobs.mark(self.jobs_dir, job_id, "failed", error="missing section 易错点")
        status = jobs.status(self.jobs_dir, job_id)
        self.assertEqual(status["state"], "failed")
        self.assertEqual(status["error"], "missing section 易错点")


if __name__ == "__main__":
    unittest.main()
