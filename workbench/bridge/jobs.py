"""Task lifecycle: queued → running → done | failed, under .lessonkit/jobs/."""

import json


def next_job_id(jobs_dir):
    jobs_dir.mkdir(parents=True, exist_ok=True)
    highest = 0
    for entry in jobs_dir.iterdir():
        if entry.is_dir() and entry.name.startswith("job-"):
            try:
                highest = max(highest, int(entry.name[4:]))
            except ValueError:
                continue
    return f"job-{highest + 1:03d}"


def create_job(jobs_dir, operation, context, instruction, output_contract=None):
    """Create a job directory with task.json, task.md, and status.json."""
    job_id = next_job_id(jobs_dir)
    job_dir = jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    task = {
        "operation": operation,
        "context": context,
        "output_contract": output_contract or {},
    }
    (job_dir / "task.json").write_text(
        json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (job_dir / "task.md").write_text(instruction, encoding="utf-8")
    _write_status(job_dir, {"state": "queued", "operation": operation, "job_id": job_id})
    return job_id


def status(jobs_dir, job_id):
    return json.loads((jobs_dir / job_id / "status.json").read_text(encoding="utf-8"))


def mark(jobs_dir, job_id, state, **fields):
    job_dir = jobs_dir / job_id
    data = _read_status(job_dir)
    data.update({"state": state})
    data.update(fields)
    _write_status(job_dir, data)


def _read_status(job_dir):
    path = job_dir / "status.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _write_status(job_dir, data):
    (job_dir / "status.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
