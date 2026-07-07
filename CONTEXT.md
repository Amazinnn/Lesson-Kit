# lesson-kit

lesson-kit turns academic source material into reusable learning assets and
student-facing views.

## Language

**Knowledge Pool**:
The course-level SQLite store that contains extracted knowledge points,
durable problems, and learning state.
_Avoid_: Chapter database, zip version

**Knowledge Point**:
A reusable unit of course knowledge extracted from source material and stored
in the pool.
_Avoid_: Card, notelet

**Graph Label**:
A short, audited label for a knowledge point when it appears as a node in a
map-like graph.
_Avoid_: Generated nickname, UI-only truncation

**Problem**:
A durable practice item stored as its own learning asset. A problem has text,
linked knowledge points, a source kind, a problem type, and optional solution
text.
_Avoid_: Exercise, question, task

**Problem Progress**:
The current learning state of a durable problem during practice and review.
_Avoid_: Question progress, answer status

**Problem Attempt**:
One recorded interaction with a durable problem, preserving the state and note
at that moment.
_Avoid_: Current status, companion-check result

**Companion Check**:
A temporary view-generated self-check question. It is not part of the durable
problem pool.
_Avoid_: Problem, source problem

**Source Kind**:
The broad origin category for a problem, such as textbook, quiz, midterm,
final, makeup, or other.
_Avoid_: Source label, exam year

**Knowledge Guide View**:
The first student-facing view, rendered from knowledge points as a readable
guide to the chapter's knowledge structure.
_Avoid_: First-pass, speedrun lesson

**Problem-Set View**:
A student-facing practice set rendered from durable problems, with a matching
solution file.
_Avoid_: Problem pool, answer key command

**Knowledge Graph Preview**:
A map-like view of chapter knowledge points and their relationships, enriched
with learning-state summaries.
_Avoid_: Obsidian clone, database editor

**Editable Graph View**:
A local maintenance and prototype view that can update knowledge-point body
text, fragile notes, and problem progress while exploring the future learning
workflow UI.
_Avoid_: Public web app, final production app, full CRUD cockpit

**Runtime State**:
The repo-local `.lessonkit/state.yaml` checkpoint that records the active
course, chapter, command, phase, required artifacts, last guard result, blocker,
and next action.
_Avoid_: Pool data, source of truth

**Phase Guard**:
A script-enforced check that determines whether a workflow command's required
artifacts and check files are complete enough to advance.
_Avoid_: Informal review, final claim
