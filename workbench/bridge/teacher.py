"""Render teacher task instructions. The CLI is data-only; conduct lives here."""

CONDUCT_RULES = """\
You are the AI teacher for this workspace.
Before explaining, ask what the learner already knows about the topic.
Explain in focused, concise chunks (about 200 words).
End with a comprehension question that verifies understanding.
Never guess: verify against the workspace pool and the source material, and
cite the source location in every answer.
"""

DIAGNOSE_RULES = """\
This is a diagnose task. Locate the specific error or stuck point in the
learner's own work first, then give the next step as a hint — not the full solution.
End with one follow-up question that checks understanding.
"""

EXPLAIN_SECTIONS = ["结论", "逐步拆解", "易错点", "回源指向"]
DIAGNOSE_SECTIONS = ["定位", "提示", "溯源", "追问"]


def render(operation, context, output_path):
    """Render the task instruction markdown for an explain/diagnose task."""
    sections = EXPLAIN_SECTIONS if operation == "explain" else DIAGNOSE_SECTIONS
    lines = [
        f"# Task: {operation}",
        "",
        CONDUCT_RULES.strip(),
        "",
    ]
    if operation == "diagnose":
        lines.append(DIAGNOSE_RULES.strip())
        lines.append("")
    lines.extend([
        "## Input",
        "",
        f"- problem text: {context.get('problem_text', '')}",
        f"- solution: {context.get('solution', '')}",
        f"- knowledge points: {', '.join(context.get('kp_ids', []))}",
        f"- learner note: {context.get('learner_note', '')}",
        f"- weak signals: {context.get('weak_signals', [])}",
    ])
    attempts = context.get("recent_attempts") or []
    if attempts:
        lines.append(f"- recent attempts: {attempts}")
    if context.get("user_answer"):
        lines.append(f"- learner's own answer: {context['user_answer']}")
    if context.get("stuck_step"):
        lines.append(f"- stuck step marker: {context['stuck_step']}")
    lines.extend([
        "",
        "## Output contract",
        "",
        f"Write the result to: `{output_path}`",
        f"Required sections: {', '.join(sections)}",
        "",
        "The result must be Markdown with exactly these `##` sections in order.",
        "The source reference section must name a concrete source location.",
    ])
    return "\n".join(lines)
