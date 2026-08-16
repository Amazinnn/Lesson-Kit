# ADR 0009: Workbench Layered Architecture

## Status

Accepted.

## Context

lesson-kit's creation side (extraction pipeline, pool, gates) is complete and
validated, but its consumption side is nearly unused: 303 durable problems with
only 2 recorded attempts. The learner needs a daily practice surface. Building
it as a monolithic app would entangle AI capabilities with the deterministic
learning loop, making the tool depend on model availability and hiding the
rules that actually drive learning.

## Decision

Structure the workbench in five layers with one-way dependencies:

1. **Shell** — web workbench and super CLI (`wb`), two thin entry points over a
   single service layer. The shell is stateless: all business state lives in
   the pool.
2. **Learning model** — weakness ordering, problem pull, feedback→signal
   mapping, forgetting-curve scheduling. Pure rules, zero AI dependency,
   unit-testable.
3. **Content** — view rendering (guide, problem set, graph, KP detail,
   explain). Data-first: renders from the pool; Markdown artifacts become
   print/export outputs.
4. **Data** — per-workspace SQLite pool plus `.lessonkit/state.yaml`.
5. **Intelligence** — attached beside the stack, never in the main path: the AI
   bridge to an external agent CLI (tasks + output contracts + validation).

Two governing principles:

- **Decision layering**: the kernel decides WHAT to teach (deterministic rules
  over signals, schedule, and pool data); AI decides HOW to teach (explain,
  later defense and gap-filling generation). With AI absent, the full loop
  runs unchanged.
- **One-way dependency**: shell → learning model → data; content reads data;
  intelligence is requested by the shell/model, never drives them.

## Consequences

The deterministic core stays fast, testable, and reliable without any model
dependency. AI capabilities are add-ons behind a stable task/contract
interface. The cost is a slightly larger surface (web shell + CLI share one
core), managed by keeping the shell thin and the model layer pure.
