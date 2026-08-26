## Context

See `proposal.md` for motivation. This document is a live design record for the planning discussion. It intentionally distinguishes verified evidence from decisions; no production implementation is authorized while the decision queue remains open.

The existing architecture and record boundary remain fixed: Shell depends on Domain, Domain on Data; Content reads products and Bridge stays adjacent. Navigation, drafts, graph motion, and other browsing actions are not learning records. Only explicit learning conclusions or content edits may write durable state.

## Goals / Non-Goals

**Goals:**

- Make the workbench readable enough for routine study without exposing storage or scheduling internals as primary content.
- Preserve the learning mechanisms that have a demonstrated purpose while simplifying their presentation.
- Separate legitimate mathematical markup from damaged OCR material.
- Define independent, composable content operations without weakening pool gates or provenance.
- Recover the original purpose of course graphs and focused mathematical views before changing graph behavior.

**Non-Goals:**

- No production code, schema migration, task list, or implementation sequencing during this discussion stage.
- No new study modes, AI capabilities, UI framework, graph dependency, OCR engine, or remote service.
- No silent change to `pipeline/`, `pool/scripts/`, `lessonkit.py`, public routes, or learning-write semantics.
- No assumption that every audit finding must become a feature; deletion and reuse remain preferred.

## Verified Evidence

### Graph readability

- The live graph already uses a real force simulation with springs, pairwise repulsion, circular collision, center gravity, damping, reheating, and a stability threshold.
- Existing semantic strength changes spring target distance, and formal problem count changes node radius.
- The simulation optimizes node separation but has no explicit objective for edge crossings, parallel-edge separation, label collisions, or preserving recognizable clusters. Center gravity can therefore produce a compact but visually tangled graph.
- Existing project documents distinguish a complete course graph from a query-time Focus Map. Graph findings such as paths, common neighbors, clusters, and spanning trees are intended to be computed on demand rather than persisted as semantic relations.

### Learning-state presentation

- Signals and scheduling are not decorative fields. The original rationale is weak-point-first ordering: explicit ratings or notes create evidence, and due state affects background ordering without locking content.
- The current knowledge-point page exposes internal vocabulary and raw values directly, including `signal_type`, `weight`, `state`, `repetitions`, `ease`, and `due_at`.
- The graph dashboard repeats part of the same evidence as “学习信号” and “下次复习”. These mechanisms can remain correct while their current presentation is unnecessary or unintelligible.
- The implementation currently maintains three overlapping concepts: `learning_current_state` (`needs_work` / `review` / `mastered`), scheduler state (`learning` / `review` / `relearning`), and problem progress (`new` / `wrong` / `stuck` / `reviewing` / `mastered`).
- `learning_current_state` is overwritten directly from the latest 1–5 self-rating, so one rating of 5 becomes `mastered`. This conflicts with ADR 0008's conservative rule that later mastery does not erase weak evidence and that the system must not infer mastery from one successful attempt.
- Existing evidence is mixed by nature: machine-gradable outcomes can be observed directly, open responses require reveal-then-self-rate, repeated wrong/stuck results strengthen signals, and spaced results update an SM-2-style schedule. A truthful user-facing state must not present all of these as one equally objective measurement.

### Problem markup and OCR

- Raw `<sup>` and `<sub>` fragments occur throughout extracted source, intermediate manifests, and rendered outputs; an initial repository count found 128 matching lines in the scoped discrete-mathematics artifacts and pool sources.
- Some fragments are legitimate presentational markup, for example a superscript marker. Others are visibly damaged extraction, for example a subscript tag interrupting an ordinary word.
- The safe Markdown renderer escapes raw HTML by design, so legitimate tags appear literally. Allowing arbitrary HTML would also render malformed or unsafe source. The defect therefore spans both renderer policy and upstream content hygiene.

### Daily-use gaps outside the reported examples

- A unified-rating practice session is held in `sessionStorage`, but reload/navigation does not restore its visible mode and queue. Starting again clears accumulated unrated work, conflicting with the existing interruption-recovery contract.
- Below 1024px the AI column is collapsed without a reopen path; at 720px both sidebars disappear without replacement navigation.
- Several practice request failures and invalid ratings have no visible error state and can leave an empty main pane.
- The unavailable-provider message is written into a hidden chat view, leaving the visible provider picker unexplained.
- Practice and unified review still lead with raw problem IDs even though display metadata is available.
- Knowledge-point linked problems are labeled as a practice entry but do not provide an actionable handoff into a selected practice scope.
- Dynamic textareas and repeated batch controls lack reliable accessible names; batch controls also reuse IDs.

## Decisions

### D1. Keep learning mechanics in the background

The student-facing UI will not show raw signal types, weights, weakness scores, scheduler state, repetitions, ease, or other implementation parameters. The primary surface will show only concise information that supports a study action. The complete evidence and scheduler data remain available to deterministic ordering, the CLI, and the Agent.

An excellent future graph expression of learning evidence is not prohibited, but no parameter dashboard or placeholder control will be added in this change. Any later visualization must first demonstrate that it makes a meaningful relationship easier to understand.

**Rationale:** the mechanisms serve weak-point ordering and forgetting reminders, but their current raw presentation asks the learner to interpret the implementation instead of studying.

**Rejected for now:** a default parameter dashboard; an expandable raw-data inspector in the student UI; deleting the underlying signal or scheduling mechanisms.

### D2. Treat mastery estimation as an experimental algorithm

Whether and to what degree an item is mastered will not be defined by renaming three UI enums or by a permanent hand-written threshold in the page layer. It is a distinct algorithmic problem whose inputs can include machine-graded results, self-ratings with explicit provenance, repeated wrong/stuck evidence, elapsed time, and spaced-review outcomes.

The first evaluator should aim for a broadly reasonable and explainable result, not an optimal or academically final mastery model. Its behavior must be replaceable so later experiments can compare another evaluator without changing practice, storage, or presentation contracts.

“Replaceable” means a narrow Domain-level evaluation boundary with pure inputs and outputs plus deterministic tests. It does not justify a generic plugin framework, dynamic package loading, a new dependency system, or premature configuration UI.

The current code can support this direction: attempts, feedback, signals, current state, and scheduling already exist as separate inputs, and Domain rules are pure Python. The present direct `latest rating -> current state` mapping is the behavior to isolate rather than an interface to preserve as the final model.

The learner-facing vocabulary and thresholds remain undecided until the experimental authority and evidence semantics are resolved. In particular, this decision does not yet approve either “已掌握” or “近期稳定” as a final label.

## Decision Queue

Questions are resolved one at a time because each answer changes the later specification or task breakdown.

1. Experimental authority: initially run mastery estimation in read-only shadow mode, let it affect ordering only, or let it replace current state immediately.
2. Meaning of learner-facing state: after choosing experimental authority, define how system evidence and learner intent become concise, truthful actions or labels.
3. Graph reading model: always show the complete graph with visual de-cluttering, make focused neighborhoods the default with an explicit full-graph mode, or use another hierarchy.
4. Mathematical markup boundary: which limited source constructs are trusted at render time, and which must be normalized or rejected before pool insertion.
5. Content CLI composition: define operation boundaries, intermediate contracts, provenance, gates, and orchestration without forcing one end-to-end route.
6. Remaining daily-use gaps: decide which verified regressions belong in this readiness change and which should be separate follow-ups.

## Risks / Trade-offs

- **A concise UI can hide useful evidence needed for diagnosis.** -> Decide separately what is primary, on-demand, and Agent-only rather than deleting data mechanisms reflexively.
- **An experimental mastery estimate can become false authority.** -> Keep provenance explicit, compare predictions against later outcomes, and grant write or ordering authority only through a separate decision.
- **Graph de-cluttering can hide legitimate topology.** -> Keep semantic data unchanged and distinguish a reading projection from stored relations.
- **Permitting raw HTML can turn extraction damage into misleading mathematics.** -> Use a narrow allowlist only if it is paired with source validation; never trust arbitrary HTML.
- **Composable commands can bypass quality gates if composition is unconstrained.** -> Separate operations while preserving explicit artifacts, validation, and promotion boundaries.
- **Combining all audit findings can create another oversized change.** -> Resolve and implement independent capability changes separately after the design is approved.
