## Context

The workbench uses a one-way Shell -> Domain -> Data architecture. Content consumes pool products and the external Agent Bridge remains adjacent. SQLite is the durable source of truth; navigation, drafts, graph motion, and other browsing actions are not learning records. Only explicit learning conclusions or content edits write durable state.

Current evidence establishes four concrete readiness gaps: every one of the 303 formal discrete-mathematics problems has an empty solution; practice state stored in `sessionStorage` is not fully restored into the visible page; the 28-node graph contains disconnected components and many avoidable crossings under one centered simulation; and raw learning/scheduling fields are exposed as if the learner must interpret implementation state.

## Goals / Non-Goals

**Goals:**

- Make the current formal pool usable for reveal-then-rate practice.
- Split content work into resumable atomic commands without weakening formal-content gates.
- Make the existing workbench reliable on refresh and mobile screens while removing implementation vocabulary from the student UI.
- Improve graph readability with deterministic, testable layout choices using the existing zero-dependency physics.
- Provide a useful first mastery experiment with explicit evidence reasons and zero write authority.

**Non-Goals:**

- No OCR engine, generic workflow engine, provider SDK, package/plugin system, mastery probability, mastery UI, remote service, or Graph Findings panel.
- No edits to existing `pipeline/`, `pool/scripts/`, or `lessonkit.py` behavior.
- No new learning log for navigation, drafts, skips, graph interactions, ingestion planning, or experiment execution.
- No claim that the `v0` evaluator is an optimal or final learning-science model.

## Decisions

### D1. Atomic ingestion commands and governed recipes

`wb ingest` exposes `prepare`, `run`, `gate`, `apply`, `render`, and `recipe`. Each stage exchanges an explicit UTF-8 artifact. `prepare` never starts a provider; `run` requires an explicit `codex` or `claude` argument and never falls back. OCR output may be supplied as input material but OCR itself is not part of this core.

Official recipes only sequence the same atomic commands. They are zero-write by default and require `--apply` for one transaction. A caller may resume from any artifact that already satisfies the next stage contract.

### D2. Formal problems require independent double review

A sourced formal problem needs a structure/solution artifact and a separate audit artifact produced in a fresh Agent session. The audit covers source consistency, meaning, formatting, knowledge-point mapping, answer correctness, and solution completeness for every item. Deterministic gating requires complete audit coverage, all-PASS decisions, and non-empty solutions.

The current 303-problem recovery follows the same contract in batches but does not partially update the pool. Only after all items pass do we create a recoverable database copy, apply every solution in one transaction, and rebuild views. Any failed item leaves the active pool unchanged.

### D3. Narrow safe source markup

Source text remains escaped before rendering. Only balanced, non-empty `<sup>` and `<sub>` pairs whose contents are escaped are promoted to elements. Unknown HTML, tags that split ordinary words, malformed/empty tags, and suspicious formula loss fail ingestion. Difficulty stars are presentational and allowed; an Agent audit must still reject semantic loss.

### D4. Student UI shows actions, not internal parameters

Student pages do not show signal types, weights, weakness scores, scheduler state, repetitions, ease, or manual `needs_work/review/mastered` editors. Existing data and compatibility APIs remain available to deterministic ordering and Agent context.

The temporary visible vocabulary is conservative: explicit current weakness evidence yields `重点练习`; otherwise a due item yields `可以复习`; other items remain neutral. The graph dashboard contains only the knowledge-point name, that action reminder, and `打开知识点`.

### D5. Practice is tab-recoverable and explicit

The existing `sessionStorage` keys remain authoritative for the current tab. Page initialization restores mode, current problem, seen IDs, and the unified-rating queue rather than beginning a new session. Closing the tab retains the existing browser-defined session boundary.

Pull, reveal, feedback, and provider failures are rendered in the visible region that initiated them. Invalid ratings stay local and do not send a request. Cards use `display_title`; repeated controls have unique IDs and accessible labels. A knowledge-point page has one `练习此知识点` action that starts a continuous non-repeating session scoped to that knowledge point.

At narrow widths the middle area remains primary and the two side columns become drawers opened from two compact top-bar icon controls.

### D6. Component-aware graph layout

The graph stays complete by default. Connected components run through the existing simulation independently; isolates receive their own deterministic region. Each nontrivial component evaluates six deterministic initial layouts, settles each without animation, and chooses the lexicographically smallest score `(edge crossings, label collisions, spatial waste)`. Components are then packed into the canvas.

Remaining close or overlapping straight edges render as shallow deterministic SVG curves. Selecting a node preserves full emphasis for itself and one-hop neighbors, secondary emphasis for two-hop neighbors, and fades farther nodes plus unrelated edges; background selection resets the graph. Filter, resize, and drag still reheat; reduced-motion chooses and draws a stable layout once. Coordinates remain browser-memory only.

### D7. Mastery evaluation is a pure read-only experiment

`wb experiment <workspace> mastery` calls one versioned Domain `v0` evaluator and presents `evidence_insufficient`, `needs_work`, `due_review`, or `recently_stable` with Chinese explanations and traceable evidence reasons. It returns no probability and has no write or ordering authority.

Strong evidence is an automatic correct/wrong/stuck result. Ratings 1-2 and 4-5 are medium negative/positive evidence; rating 3, notes, and skips are neutral. The latest decisive negative wins, then overdue status. Problem stability needs positive evidence on at least two dates and one strong positive, or at least three positive self-ratings across two dates.

Knowledge-point failure propagates from every linked problem. Stability needs two distinct linked problems across dates; a one-problem knowledge point additionally needs a direct knowledge-point review on another date; a zero-problem knowledge point stays insufficient. Gate-passed candidate attempts may support only knowledge-point evaluation and never appear as formal-problem results.

## Risks / Trade-offs

- Independent Agent passes cost time. This is accepted because empty or wrong solutions make reveal-then-rate unusable; batching reduces coordination without weakening all-or-nothing apply.
- Six graph starts cost browser CPU. The graph is small, layouts are deterministic, and the simulation stops at stability; no dependency or persistent coordinate cache is justified.
- Concise state hides diagnostic detail. Full evidence stays accessible to CLI and Agent context, while the student surface shows only immediate action.
- The first mastery rules are approximate. Keeping them read-only, versioned, pure, and reason-bearing makes replacement cheap without pretending precision.

## Verification Strategy

Each behavior follows a failing test before minimal implementation. Content tests cover artifact contracts, markup, audit completeness, provider selection, rollback, and zero-write recipes. UI/Node tests execute production scripts for restoration, drawers, errors, accessible IDs, titles, graph scoring/focus, and reduced-motion. Domain tests cover evidence precedence and cross-date/cross-problem thresholds while database snapshots prove zero writes. The final gates are full pytest, both JavaScript syntax checks, strict OpenSpec validation, `openspec doctor`, both pool guards, and responsive/manual workbench acceptance.
