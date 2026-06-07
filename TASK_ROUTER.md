# Task Router

Choose one governing command. Do not let older task names, local skills, or reference files govern the task.

| Task signal from user | Governing command | Required first files | Required export gates |
|---|---|---|---|
| “I just got the textbook”, “help me read this chapter first”, “make a first-pass reading interface”, “I need grounded source-first reading” | `commands/create-source-guided-first-pass-pack.md` | source scope, knowledge-point inventory, structure plan, coverage check | first-pass lesson gate, source grounding, section order, question specificity, no-summary-substitution, format gate |
| “Generate the full chapter package”, “lesson + exercises + answers” | `commands/full-study-pack.md` | source inventory, knowledge inventory, subject check, structure plan | lesson, problem-set, answer-key, format gates |
| “Generate/revise lesson from PDF/textbook”, “use my feedback to improve lesson” | `commands/lesson-from-textbook-or-feedback.md` | source inventory, knowledge inventory, body-detail extraction when textbook/PDF, feedback record when feedback exists | pre-writing gate, lesson export gate, format gate |
| “Analyze my feedback first”, “diagnose what I do not know” | `commands/feedback-diagnosis-only.md` | exercise feedback record | feedback diagnosis check in pre-writing gate |
| “Create problem set”, “make exercises mapped to knowledge” | `commands/problem-set-from-knowledge.md` | knowledge architecture, problem model space, exercise inventory when source problems exist | problem-set export gate, source consistency gate, format gate |
| “Write answers”, “make answer key” | `commands/answer-key.md` | final problem set, answer-key plan, answer-key sync plan | answer-key export gate |
| “Make printable exercise sheets / add blank writing space” | `commands/printable-exercise-pack.md` | exercise-set format plan, selected problem list | printable exercise gate |
| “Update the workflow from this discussion” | `commands/update-workflow-from-session-learning.md` | session learning notes, rule change plan | workflow update gate or manual review |

## Routing Rules

- If the user has not yet read the source and asks how to approach it, use `create-source-guided-first-pass-pack.md`.
- A first-pass lesson is not a lesson note, not a summary, not a problem set, and not an answer key. It is a source-reading interface with controlled teaching support.
- If textbook/PDF/PPT, thinking questions, worked examples, or feedback affect a final lesson, use `lesson-from-textbook-or-feedback.md` for lesson work.
- If the user asks for a full learning loop package, use `full-study-pack.md`; it orchestrates the lesson, problem-set, and answer-key commands.
- If the task is small conceptual Q&A, do not force a full four-layer workflow unless the user explicitly requests strict workflow treatment.
- If the task involves printable handwriting blanks, run the printable gate even when the exercise set itself was created by another command.
