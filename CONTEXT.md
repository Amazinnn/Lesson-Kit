# lesson-kit

lesson-kit turns academic source material into reusable learning assets and
student-facing views.

> **Superseded (2026-08-29):** authoritative term definitions now live in
> `docs/GLOSSARY.md` (bilingual, covers the workbench era). This file remains
> as pipeline-era history; entries that are still valid were migrated into the
> GLOSSARY. Do not add new entries here.

## Language

**Knowledge Pool**:
The course-level SQLite store that contains extracted knowledge points,
durable problems, and learning state.
_Avoid_: Chapter database, zip version

**Knowledge Point**:
A reusable unit of course knowledge extracted from source material and stored
in the pool.
_Avoid_: Card, notelet

**Course Learning Network**:
The course-scoped knowledge-point network made from audited knowledge points,
audited low-level relations, and query-time graph findings.
_Avoid_: Generic life map, final ontology

**Knowledge Relation**:
An audited point-to-point edge between two knowledge points, stored in
`knowledge_relations`. It is the low-level graph fact layer.
_Avoid_: Hidden relation, algorithmic discovery

**Graph Finding**:
A query-time discovery produced from the Course Learning Network, such as a
shortest path, shared neighbor, bridge node, or dense section. It is not stored
as a durable relation unless later audited.
_Avoid_: Source relation, extracted fact

**Signal Map**:
A lightweight learner-feedback layer that marks weak nodes, confusion,
transfer failures, missing prerequisites, or suspected relation gaps.
_Avoid_: Relation manifest, problem record

**Learner Signal**:
The current SQLite record for one learner-attention signal targeting a
knowledge node or audited relation. Repeated wrong or stuck attempts strengthen
it; later mastery does not erase it automatically.
_Avoid_: Attempt history, permanent Knowledge Relation, JSON-only signal

**Focus Map View**:
A compact JSON subgraph around seed knowledge points, optional target paths,
shared neighbors, simple clusters, and learner signals.
_Avoid_: Full graph preview, generated lesson

**Graph Label**:
A short, audited label for a knowledge point when it appears as a node in a
map-like graph.
_Avoid_: Generated nickname, UI-only truncation

**Problem**:
A durable practice item stored as its own learning asset. A problem has text,
linked knowledge points, a source kind, a problem type, and optional solution
text.
_Avoid_: Exercise, question, task

**Problem Candidate**:
A source-grounded practice item that has not yet entered the durable problem
pool. It may be practiced after both candidate gates pass, and it becomes a
Problem only through explicit import.
_Avoid_: Generated problem, draft Problem, trusted AI question

**Candidate Practice Session**:
A learner-facing practice run over gate-passed Problem Candidates. It records
candidate attempts and learner signals without requiring the learner to audit
or approve the candidates.
_Avoid_: Candidate review, Problem-Set View, acceptance session

**Problem Origin**:
The candidate-level provenance class: source problem, adapted problem, or
source-grounded generated problem. It is separate from Source Kind and is not
added to the durable `problems` table in the MVP.
_Avoid_: Source Kind, AI tag, author

**Interaction Type**:
The way a Problem Candidate accepts an answer: single choice, true/false, or
free response. It is independent of whether the item was sourced or generated.
_Avoid_: Problem Type, source format

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
