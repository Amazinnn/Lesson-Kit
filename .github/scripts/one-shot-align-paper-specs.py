from pathlib import Path


def replace_requirement(text: str, name: str, replacement: str) -> str:
    heading = f"### Requirement: {name}\n"
    start = text.find(heading)
    if start < 0:
        raise SystemExit(f"missing requirement: {name}")
    next_start = text.find("\n### Requirement:", start + len(heading))
    if next_start < 0:
        next_start = len(text)
    return text[:start] + replacement.strip() + "\n" + text[next_start:]


review_path = Path("openspec/specs/review-workbench/spec.md")
review = review_path.read_text(encoding="utf-8")
old_purpose = """## Purpose

The review workbench is the consumption side of lesson-kit: a browser workbench
and shared CLI that turn the SQLite pool into weak-point-first daily practice,
with flexible feedback and a forgetting curve used as background guidance only.
"""
new_purpose = """## Purpose

The review workbench is the consumption side of lesson-kit: a browser workbench
and shared CLI that turn the SQLite pool into **Paper assembly** and Paper-backed
Practice Runs. Weakness evidence, due state, scope, and source filters guide how a
Paper is assembled; once a Practice Run starts, its ordered Paper items are fixed.
Flexible feedback and forgetting-curve scheduling remain background guidance only.
"""
if review.count(old_purpose) != 1:
    raise SystemExit("review purpose drifted")
review = review.replace(old_purpose, new_purpose, 1)

review = replace_requirement(review, "Problem pull engine", r'''### Requirement: Paper assembly engine

The pull engine SHALL assemble the ordered problem portion of a Paper from an
explicit knowledge-point scope, conditional source/difficulty filters, and
learner evidence such as weak, due, or previously wrong items. Assembly SHALL be
a read operation with zero learning writes. When durable problems are exhausted,
it SHALL report the shortage per knowledge point instead of inventing content.
Every selected problem SHALL carry the reason it entered the Paper.

Exact problem ids MAY be supplied by an Agent or CLI authoring workflow to pin a
known problem while composing a Paper. That exact-id capability is an authoring
primitive, not a learner-facing practice control: the browser SHALL NOT expose a
per-problem picker that injects named problems into an active Practice Run.

#### Scenario: Assemble a Paper for one weak knowledge point

- **WHEN** the learner uses one weak knowledge point as the requested practice scope
- **THEN** the engine assembles durable problems for a Paper constrained to that scope and reports the selection reasons before execution begins

#### Scenario: Pool shortage is reported

- **WHEN** a knowledge point has fewer durable problems than requested for the Paper
- **THEN** the assembly result lists the shortfall per knowledge point and points to the Check pipeline instead of fabricating problems

#### Scenario: Agent pins an exact problem while authoring

- **WHEN** an Agent or CLI authoring workflow names an exact durable problem id
- **THEN** that problem may be included with reason `explicit` without creating a learner-side manual-pick affordance

#### Scenario: Learner evidence guides assembly

- **WHEN** Paper assembly is driven by weak knowledge points, due problems, or previously wrong problems
- **THEN** the returned problems reflect that evidence and each carries the matching reason
''')

review = replace_requirement(review, "Practice session", r'''### Requirement: Paper-backed Practice Run

A Practice Run SHALL execute one already determined Paper. The run SHALL preserve
the Paper's ordered item identities for its lifetime: viewing, answering,
skipping, rating, scheduling updates, or Agent discussion SHALL NOT dynamically
pull extra items into the running Paper. At most one active run exists per
workspace execution resource.

A Paper is not defined by one product-level content-mode choice. Existing
`practice_mode` fields and card/problem rendering branches MAY remain as v1
compatibility metadata while mixed-format execution is migrated, but they SHALL
NOT restore the retired model in which selecting a mode creates a dynamic queue.
The learner's rating preference controls feedback timing only. Merely displaying,
drafting, revealing, skipping, or ending work SHALL NOT manufacture a learning
record; existing explicit attempt/verdict/rating rules remain authoritative.
Scheduling SHALL never lock an item.

#### Scenario: Start from an assembled Paper

- **WHEN** a Paper's ordered items are fixed and the learner starts it
- **THEN** those exact items become the Practice Run and no later scope or scheduler change mutates the run

#### Scenario: Skip an item without a learning record

- **WHEN** the learner skips the current Paper item without an explicit recorded conclusion
- **THEN** execution advances according to the existing skip rules and no learner-state row is manufactured

#### Scenario: Explicit rating records a learning conclusion

- **WHEN** the learner submits a 1–5 self-rating for a completed problem
- **THEN** feedback, derived learner state, and schedule are persisted once

#### Scenario: Off-mode verdict remains compatible

- **WHEN** a Paper item is objective and the run uses the compatibility rating mode `off`
- **THEN** its recorded verdict derives the existing learning conclusion exactly once without synthesizing a rating event

#### Scenario: Agent records only at the learner's request

- **WHEN** the learner asks the Agent to record the active answer
- **THEN** only the explicit attempt CLI call writes it; viewing or discussing the draft alone does not
''')

review = replace_requirement(review, "Durable practice run archive", r'''### Requirement: Durable practice run archive

The single active-practice resource SHALL remain the execution authority for one
Paper-backed Practice Run. Every newly created execution SHALL use the product
source semantic `paper`; historical `quick`, `practice_set`, or `agent` source
values MAY remain readable as migration data, and replaying such history SHALL
create a new Paper-sourced execution from the archived fixed items.

When a run completes or is explicitly replaced or cleared, the workbench SHALL
append one minimal `practice_runs` snapshot before deleting active execution
state. The snapshot SHALL preserve Paper source identity/reference/label, ordered
item identities and final states, rating compatibility metadata, and timestamps
only. It SHALL NOT replace, duplicate, edit, or delete `problem_attempts` or
`feedback_events`.

#### Scenario: Completing the last item archives the run

- **WHEN** the final pending item of an active Paper is answered or marked stuck
- **THEN** one completed Paper run snapshot is appended and the active singleton is cleared

#### Scenario: Replacing an unfinished run keeps both histories honest

- **WHEN** the learner explicitly replaces an unfinished Paper run
- **THEN** the old run is archived as abandoned, its existing attempts remain unchanged, and the new Paper starts independently

#### Scenario: Replay legacy history through the Paper boundary

- **WHEN** a historical run labelled `quick`, `practice_set`, or `agent` is replayed
- **THEN** its archived item order is reused but the new active execution stores the Paper source semantic
''')

review = replace_requirement(review, "Reverse review from wrong results", r'''### Requirement: Re-assembly after wrong results

A wrong or stuck result MAY offer a follow-up action that assembles a **new
Paper** from the relevant knowledge scope or learning evidence. The completed or
running Paper SHALL never be extended in place, and the follow-up SHALL not
silently inherit an old seen-id queue as its execution identity.

#### Scenario: Build a follow-up Paper after a wrong answer

- **WHEN** a problem is answered wrong or stuck and the learner chooses to practise similar material
- **THEN** Lesson Kit assembles a new Paper from the relevant scope/evidence and starts it only after its item list is determined
''')

review = replace_requirement(review, "Forgetting-curve scheduling as background", r'''### Requirement: Forgetting-curve scheduling as background

The system SHALL maintain per-item scheduling state (repetitions, ease,
interval, due date) updated on recorded practice results. Scheduling SHALL
influence ordering, suggestions, and Paper Assembly only; it SHALL never hide,
lock, refuse, or inject items into an already running Paper. Due items SHALL NOT
be surfaced as a standing due list or through a separate review page.

Due knowledge points MAY appear as on-demand practice suggestions with at most
one human-readable reason phrase. Acting on such a suggestion SHALL establish or
prefill a Paper-assembly scope; it SHALL NOT add a knowledge point or problem to
a staged execution queue.

#### Scenario: Due items are suggested for Paper assembly

- **WHEN** due schedule rows exist for knowledge points outside the learner's current assembly scope
- **THEN** the practice departure surface can suggest those points with one human reason phrase and an action to assemble from them, never raw scheduler parameters

#### Scenario: Schedule state updates after practice

- **WHEN** a problem result is recorded
- **THEN** its repetitions, ease, interval, and due date are updated in the scheduling table without mutating the running Paper
''')

review = replace_requirement(review, "Session interruption recovery", r'''### Requirement: Practice Run interruption recovery

Recorded learning conclusions SHALL remain durable in the pool. The active
Paper execution checkpoint — Paper source identity, fixed ordered items, cursor,
and item completion states — SHALL be recoverable through the single active
practice resource after refresh or navigation. Browser-only draft answer text,
unsent notes, transient reveal state, and other unsubmitted interaction state MAY
remain tab-scoped and SHALL NOT manufacture durable learning records when lost.

#### Scenario: Resume the same Paper after refresh

- **WHEN** the learner refreshes or leaves and returns while a Practice Run is active
- **THEN** the same fixed Paper items and execution progress are restored rather than re-running Paper Assembly

#### Scenario: Recorded results survive browser closure

- **WHEN** the learner closes the browser after recording results and later reopens the workspace
- **THEN** those results remain in the pool and any surviving active Paper checkpoint remains the execution authority

#### Scenario: Unsubmitted browser state creates no record

- **WHEN** a tab ends with an unsent draft, note, reveal state, or pending unsubmitted rating
- **THEN** no attempt, feedback, signal, progress, or schedule row is fabricated from that transient state
''')

review = replace_requirement(review, "Scoped include filter", r'''### Requirement: Browser manual include filter is retired

`include_ids` SHALL NOT be a learner-facing browser practice capability. Browser
`POST /pull` callers that send it SHALL be refused rather than silently changing
which concrete problems enter a Practice Run. Exact problem selection remains
available only through the explicit Agent/CLI Paper-authoring primitive (for
example `--problem`) and SHALL occur before the Paper starts.

Low-level or historical CLI compatibility code MAY continue to understand a
scoped include filter during migration, but live product documentation and new
UI behavior SHALL NOT treat it as a practice control.

#### Scenario: Stale browser caller sends include ids

- **WHEN** a browser practice pull carries `include_ids`
- **THEN** the request is rejected with an explicit migration message and no Practice Run is changed

#### Scenario: Agent pins a problem through Paper authoring

- **WHEN** an Agent needs one known problem in a Paper
- **THEN** it uses the exact-problem authoring path before execution rather than the retired browser include filter
''')

review = replace_requirement(review, "Chapter lens scoping", r'''### Requirement: Chapter lens scoping

The chapter lens SHALL scope reading surfaces — knowledge-point list/detail,
knowledge graph, and practice suggestions — and MAY provide the default scope for
Paper Assembly. It SHALL NOT define or mutate the contents of a running Paper.
An explicitly chosen Paper-assembly scope MAY span chapters and SHALL survive
chapter-lens changes in the same tab until the learner changes that scope.

#### Scenario: Lens narrows default assembly suggestions

- **WHEN** one chapter is active and the learner has not established another explicit assembly scope
- **THEN** practice suggestions and default Paper Assembly use that chapter without creating an executable knowledge-point queue

#### Scenario: Explicit scope survives lens changes

- **WHEN** the learner has explicitly selected knowledge points across chapters and changes the reading lens
- **THEN** the selected assembly scope remains unchanged while the reading surfaces follow the new lens
''')

review = replace_requirement(review, "Source filter panel on the practice page", r'''### Requirement: Source filter panel on the practice page

The practice departure page SHALL offer a floating source-filter panel with one
checkbox group per filter dimension, using values and counts derived from the
pool. Active dimension selections SHALL persist per workspace for the browser
session and SHALL constrain the next Paper Assembly together with its scope.
Dimension semantics remain OR within a dimension and AND across dimensions.

The panel SHALL NOT provide search-result checkboxes, a picked-problem set, or
any other per-problem learner control. Stem/source keyword search endpoints MAY
remain available for read-only discovery and Agent/authoring workflows, but a
search hit SHALL NOT be injected into learner practice through `include_ids`.

#### Scenario: Filter dimensions reach Paper Assembly

- **WHEN** the learner selects a document, year, and origin before assembling a Paper
- **THEN** those dimensions constrain the assembly and the Paper is fixed before a Practice Run begins

#### Scenario: No per-problem picking in the filter panel

- **WHEN** the learner opens the source-filter panel
- **THEN** the panel exposes dimension filters but no checkbox or action that adds a specific search result to practice

#### Scenario: Clearing filters changes no running Paper

- **WHEN** the learner clears source filters while a Practice Run already exists
- **THEN** the active Paper items remain unchanged and the cleared filters affect only later assembly
''')

for retired in (
    "practice page's staged-list flow",
    "starts practice for a selected weak knowledge point",
    "practice the same knowledge points again",
    "### Requirement: Scoped include filter",
):
    if retired in review:
        raise SystemExit(f"review spec still contains retired model text: {retired}")
review_path.write_text(review, encoding="utf-8")


ui_path = Path("openspec/specs/workbench-ui/spec.md")
ui = ui_path.read_text(encoding="utf-8")

ui = replace_requirement(ui, "Practice page", r'''### Requirement: Practice page

The practice page SHALL be the departure surface for deciding what to practise
and for resuming/running the current Paper. With no active Practice Run it MAY
show scope, source/difficulty filters, suggestions, saved/recent Papers, rating
preference, and other assembly inputs; these inputs constrain Paper Assembly and
are not themselves an executable queue. Starting from a knowledge scope SHALL
first determine a Paper's ordered items, then start the Practice Run from that
fixed Paper.

The learner-facing page SHALL NOT expose per-problem manual selection. Existing
content-mode controls MAY remain temporarily as compatibility inputs while the
mixed-format Paper UI is migrated, but they SHALL NOT define the product identity
of a Paper or authorize dynamic pulling after execution begins. During an active
run, the middle column MAY collapse arrangement controls so the fixed Paper's
answering flow is primary; ending the run returns to the departure surface.

#### Scenario: Start from an explicit scope

- **WHEN** the learner chooses a knowledge scope and starts practice
- **THEN** Lesson Kit assembles a Paper from that scope before execution and the resulting Practice Run keeps that ordered item list fixed

#### Scenario: Resume an active Paper

- **WHEN** the learner returns to practice with an unfinished active run
- **THEN** the same Paper and progress are offered for resume without re-running assembly

#### Scenario: Filters do not mutate a running Paper

- **WHEN** source, difficulty, or suggestion inputs change while a Paper is already running
- **THEN** the current run is unchanged and those inputs apply only to a later Paper Assembly

#### Scenario: No manual problem picker

- **WHEN** the learner opens the practice departure controls
- **THEN** scope and filter controls may be present but no control can hand-pick a concrete problem into the Practice Run
''')

ui = replace_requirement(ui, "Session-end unified self-rating", r'''### Requirement: Session-end unified self-rating

The session-end view SHALL present completed, unrated Paper items only when the
run uses unified self-rating. Each eligible item SHALL show the learner answer
and solution with a 1–5 input and optional note. Submitting a score SHALL use the
ordinary feedback behavior once and remove the scored item; skipped and
unfinished items SHALL not be fabricated as completed ratings.

A practice-similar action MAY use the finished Paper's results and knowledge
scope as inputs to **assemble a new Paper**. It SHALL NOT reopen, extend, or
mutate the completed Practice Run.

#### Scenario: Rate completed items at run end

- **WHEN** the learner submits a score for one completed Paper item
- **THEN** feedback is recorded once and that item is removed while other unrated completed items remain

#### Scenario: Practice similar after the run

- **WHEN** the learner chooses the practice-similar action
- **THEN** Lesson Kit starts a new Paper Assembly from relevant scope/evidence and does not reuse the prior run as a mutable queue
''')

ui = replace_requirement(ui, "Knowledge point display page", r'''### Requirement: Knowledge point display page

The knowledge-point page SHALL render the body as its primary reading content and
provide one prominent `练习此知识点` action. Activating it SHALL transfer that
knowledge point as a Paper-assembly scope and open the practice departure flow;
it SHALL NOT directly create a dynamic, non-repeating Practice Session.

Linked formal problems SHALL remain reading-only and SHALL be listed directly
under the knowledge point with no stored topic/group layer. Each row SHALL show
`display_title` and the complete safe-rendered problem statement without summary
text, truncation, ellipsis, raw ids, or per-problem practice controls. Raw signal
and scheduler parameters SHALL not be shown.

#### Scenario: Practise one knowledge point

- **WHEN** a learner activates `练习此知识点`
- **THEN** practice opens with that knowledge point as the Paper-assembly scope and concrete items are chosen by assembly rather than by direct per-problem controls

#### Scenario: Browse linked problems directly

- **WHEN** a knowledge point has several linked formal problems
- **THEN** the page lists those problems directly without a synthetic topic/group heading or an independent practice button per problem

#### Scenario: Read a complete linked problem

- **WHEN** the learner opens a knowledge-point page with linked problems
- **THEN** each row shows the title and complete rendered statement without summary, truncation, raw id, or manual-add action

#### Scenario: Missing display title

- **WHEN** a linked problem lacks a display title
- **THEN** the row uses the fixed readable fallback `未命名题目` rather than a raw id or statement fragment

#### Scenario: Navigate a wiki link

- **WHEN** rendered knowledge content contains a valid workspace knowledge-point wiki link
- **THEN** activating it opens that formal knowledge-point route

#### Scenario: Hide implementation state

- **WHEN** the knowledge-point page contains signals or schedule data
- **THEN** it shows only the applicable concise action reminder and not raw signal, score, ease, repetition, scheduler, or mastery-state controls
''')

ui = replace_requirement(ui, "Practice page staged list and on-demand suggestions", r'''### Requirement: Practice page suggestions and assembly entry

The practice page SHALL NOT maintain a Staged Practice List as a second product
object between knowledge scope and Paper. The learner's explicit knowledge-point
selection is Paper-assembly scope and may be summarized compactly; removing a
scope item SHALL update that selection everywhere it is represented.

The page MAY offer one on-demand suggestion entry sourced from the daily plan and
due scheduling state, deduplicated to one row per knowledge point with at most
one human-readable reason phrase. A suggestion action SHALL mean `据此组卷` (or
equivalent assembly intent): it can establish/prefill a Paper scope, but it
SHALL NOT join a knowledge point to an executable queue or inject concrete
problems into an active Practice Run. Raw scheduler parameters remain hidden.
The time view MAY remain beside the departure controls.

#### Scenario: A due knowledge point appears as an assembly suggestion

- **WHEN** a knowledge point is overdue and not already in the explicit assembly scope
- **THEN** the suggestion surface may show it with one reason phrase and an action to assemble from it, without a staged-list join action

#### Scenario: Remove a scope item

- **WHEN** the learner removes one knowledge point from the practice departure scope summary
- **THEN** that point is deselected in the knowledge list, graph, and scope tray without altering any running Paper

#### Scenario: Nothing selected and nothing suggested

- **WHEN** no assembly scope, saved/recent Paper, or suggestion is available
- **THEN** the practice departure page shows an honest compact empty state rather than inventing a staged practice queue
''')

ui = replace_requirement(ui, "Cross-page practice-scope tray", r'''### Requirement: Cross-page practice-scope tray

Every workspace page SHALL expose one compact Paper-assembly scope control at the
upper-right of the middle column. Activating it SHALL open a tray that lists the
complete names of explicitly selected knowledge points, allows an item to be
removed, and offers one action to enter the practice departure page with that
scope. The tray SHALL reuse existing tab-local selection and SHALL NOT create
server-side learning or execution state.

The tray action SHALL NOT directly start a Practice Run. Scope answers what the
learner wants to practise; the practice page/Agent determines the concrete Paper
before execution. Open/collapsed state may remain browser-only.

#### Scenario: Inspect a long scope

- **WHEN** the learner opens the tray with more selected knowledge points than fit in its bounded list area
- **THEN** every selected name remains available through vertical scrolling without expanding the page header

#### Scenario: Remove a selected point from the tray

- **WHEN** the learner removes one knowledge point in the tray
- **THEN** it disappears from the tray and is deselected in other scope representations without changing a running Paper

#### Scenario: Enter practice from the tray

- **WHEN** at least one knowledge point is selected and the learner activates the tray action
- **THEN** the practice departure page opens with the same Paper-assembly scope and no Practice Run begins until a Paper is determined
''')

ui = replace_requirement(ui, "Flash card stacked presentation", r'''### Requirement: Flash card item stacked presentation

A flash-card item inside a Paper SHALL render as two fully overlapped card faces:
the prompt face on top and the other face hidden behind it until the explicit
reveal action. Revealing SHALL preserve the current stacked-card motion and
reduced-motion terminal state.

Direction is item/assembly metadata, not a separate executable Practice Session.
A card-only compatibility flow MAY apply one forward/reverse preference to all
cards when assembling its Paper; once a card item is in a running Paper, its
direction SHALL remain fixed for that item and no swap control SHALL mutate it in
place.

#### Scenario: Reveal the hidden face

- **WHEN** the learner activates reveal on an unrevealed flash-card item
- **THEN** the prompt and answer faces reach the existing readable revealed presentation

#### Scenario: Direction is fixed after Paper assembly

- **WHEN** a flash-card item enters a Practice Run with reverse direction
- **THEN** that item prompts from the back and its direction does not change during the run

#### Scenario: Reduced motion reveal

- **WHEN** reduced motion is requested and the learner reveals a card
- **THEN** both faces are shown in their final positions without animation frames
''')

for retired in (
    "Practice page staged list and on-demand suggestions",
    "continuous non-repeating practice session scoped to that knowledge point",
    "find problems and let the learner pick",
    "staged practice list",
):
    if retired in ui:
        raise SystemExit(f"workbench-ui still contains retired model text: {retired}")
ui_path.write_text(ui, encoding="utf-8")

Path(".github/workflows/one-shot-align-paper-specs.yml").unlink(missing_ok=True)
Path(".github/scripts/one-shot-align-paper-specs.py").unlink()
