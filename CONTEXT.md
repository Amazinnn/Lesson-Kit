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

**Problem**:
A durable practice item stored as its own learning asset. A problem has text,
linked knowledge points, a source kind, a problem type, and optional solution
text.
_Avoid_: Exercise, question, task

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
