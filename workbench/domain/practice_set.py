"""Rendering one practice set: pure text rules, no IO.

The student sheet carries problem text and nothing else — no answer, no
solution, no internal identifier — and the solution sheet numbers exactly like
it, so a printed set and its answers line up line for line. A problem without a
stored solution is marked 待补 rather than left blank, matching the problem-set
view contract.
"""

PLACEHOLDER = "待补"
SOLUTION_SCAN_MIN = 24


def render_practice_set(problems, title):
    """The student sheet: continuous numbering, problem text only."""
    lines = [f"# {title}", "", "## 题目", ""]
    for index, problem in enumerate(problems, start=1):
        lines.extend([f"### {index}", "", _field(problem, "problem_text"), ""])
    return "\n".join(lines).rstrip() + "\n"


def render_solutions(problems, title):
    """The solution sheet: same numbering, 待补 where no solution is stored."""
    lines = [f"# {title} · 解答", "", "## 解答", ""]
    for index, problem in enumerate(problems, start=1):
        solution = _field(problem, "solution")
        lines.extend([f"### {index}", "", solution if solution.strip() else PLACEHOLDER, ""])
    return "\n".join(lines).rstrip() + "\n"


def leaks(problems, student_text):
    """Internal identifiers (and long solution text) that must not reach students.

    The renderer cannot emit them by construction; this is the cheap sanity scan
    a caller runs before writing a sheet, so a future renderer change is caught
    instead of printed. Short solutions are skipped: a two-character answer
    legitimately appears inside problem text.
    """
    found = []
    for index, problem in enumerate(problems, start=1):
        tokens = [problem.get("problem_id"), *(problem.get("kp_ids") or [])]
        for token in tokens:
            if token and str(token) in student_text:
                found.append({
                    "index": index, "problem_id": problem.get("problem_id"),
                    "token": str(token),
                })
        solution = _field(problem, "solution").strip()
        if len(solution) >= SOLUTION_SCAN_MIN and solution in student_text:
            found.append({
                "index": index, "problem_id": problem.get("problem_id"),
                "token": "solution text",
            })
    return found


def _field(problem, name):
    value = problem.get(name)
    return value if isinstance(value, str) else ""
