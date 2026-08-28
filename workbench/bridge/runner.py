"""AI task orchestration: create job, run provider, validate, mark done/failed."""

from workbench import registry
from workbench.bridge import contracts, jobs, providers, teacher


def _task(pool, operation, problem_id, note=None, user_answer=None, stuck_step=None):
    problem = pool.problem(problem_id)
    if problem is None:
        raise ValueError(f"unknown problem: {problem_id}")
    context = {
        "problem_text": problem["problem_text"],
        "solution": problem.get("solution") or "",
        "kp_ids": problem["kp_ids"],
        "learner_note": note or "",
        "weak_signals": [
            s for s in pool.signals() if s["target_id"] in problem["kp_ids"]
        ],
        "recent_attempts": pool.attempts(problem_id)[-3:],
    }
    if user_answer:
        context["user_answer"] = user_answer
    if stuck_step:
        context["stuck_step"] = stuck_step

    output_path = pool.explain_dir() / f"{problem_id}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sections = (
        teacher.EXPLAIN_SECTIONS if operation == "explain"
        else teacher.DIAGNOSE_SECTIONS
    )
    instruction = teacher.render(operation, context, str(output_path))
    output_contract = {"sections": sections}
    return context, instruction, output_contract, output_path


def create_ai_task(pool, operation, problem_id, note=None, user_answer=None,
                   stuck_step=None):
    """Reserve and persist a queued task before a worker is started."""
    context, instruction, output_contract, _output_path = _task(
        pool, operation, problem_id, note, user_answer, stuck_step
    )
    jobs_dir = pool.jobs_dir()
    return jobs.create_job(
        jobs_dir, operation, context, instruction, output_contract
    )


def run_ai_task(pool, workspace_path, operation, problem_id, provider_name=None,
                note=None, user_answer=None, stuck_step=None, job_id=None):
    """Run an explain/diagnose task; optionally use an already queued job."""
    context, instruction, output_contract, output_path = _task(
        pool, operation, problem_id, note, user_answer, stuck_step
    )
    jobs_dir = pool.jobs_dir()
    if job_id is None:
        job_id = jobs.create_job(
            jobs_dir, operation, context, instruction, output_contract
        )
    else:
        queued = jobs.status(jobs_dir, job_id)
        if queued.get("state") != "queued" or queued.get("operation") != operation:
            raise ValueError(f"job is not queued for {operation}: {job_id}")

    provider = _resolve_provider(provider_name)
    if provider is None:
        jobs.mark(jobs_dir, job_id, "failed",
                  error="no provider configured (use wb bridge add)")
        return job_id

    jobs.mark(jobs_dir, job_id, "running")
    log_path = jobs_dir / job_id / "stdout.log"
    code = providers.run_provider(
        provider, workspace_path, log_path,
        env={
            "LESSONKIT_JOB_DIR": str(jobs_dir / job_id),
            "LESSONKIT_OUTPUT_PATH": str(output_path),
        },
    )
    if code == "timeout":
        jobs.mark(jobs_dir, job_id, "failed", error="provider timed out")
        return job_id
    if code != 0:
        jobs.mark(jobs_dir, job_id, "failed", error=f"provider exited {code}")
        return job_id

    result_text = (
        output_path.read_text(encoding="utf-8") if output_path.is_file() else ""
    )
    ok, reasons = contracts.validate(operation, result_text)
    if ok:
        jobs.mark(jobs_dir, job_id, "done", result_file=str(output_path))
    else:
        jobs.mark(jobs_dir, job_id, "failed", error="; ".join(reasons))
    return job_id


def _resolve_provider(provider_name):
    providers_cfg = registry.load_bridges()["providers"]
    if provider_name:
        return providers_cfg.get(provider_name)
    if providers_cfg:
        return next(iter(providers_cfg.values()))
    return None
