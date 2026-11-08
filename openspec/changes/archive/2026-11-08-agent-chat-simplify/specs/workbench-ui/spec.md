## MODIFIED Requirements

### Requirement: Provider activity cards show evidenced outcomes
The UI SHALL render normalized provider activities as semantic action cards with their actual status and outcome. Activity cards SHALL NOT display impact statements — neither a claimed known impact nor an unknown-impact label — and SHALL NOT infer effects from an action's name; evidenced failure SHALL surface through the card's actual status and concise failure summary instead. Diagnostics SHALL be folded and redacted, with a concise summary limited to 240 characters. The UI SHALL expose only backend-supported recovery controls and SHALL NOT present selective retry when no such operation exists. Existing approval behavior remains governed by its current capability contracts.

#### Scenario: A tool reports a result and an error
- **WHEN** normalized activity evidence contains a semantic action, terminal status, output, and diagnostic text
- **THEN** the card shows the action, actual status and evidenced result, while the redacted diagnostic stays folded

#### Scenario: Impact is not known
- **WHEN** an activity carries or lacks backend impact evidence
- **THEN** the card renders no impact line in either case and does not infer success from a command string

#### Scenario: Selective recovery is unavailable
- **WHEN** a failed activity has no supported scoped retry operation
- **THEN** the UI offers no selective retry and may offer only an existing safe read-only or new-instruction affordance

### Requirement: Running-send preference and pending controls are explicit

The workspace's existing browser settings SHALL store the default action for a
message submitted while a turn is running, with queue as the default. The
composer SHALL use the workspace running-send preference for new submissions
and SHALL NOT expose a per-message send-mode selector. A single compact
pending-message list immediately above the composer SHALL show only accepted
queued messages in confirmed execution order, with reorder, send-now, edit and
remove controls before execution, and one continue action when retained work is
paused. Interrupt handoffs SHALL NOT appear as queue entries. Pending edits
SHALL use the expected revision read with the message. The controls SHALL make
clear that an accepted pending message has not begun provider execution. A
paused queue SHALL protect only retained queued messages: when no pending
approvals remain and no messages are retained, the pause SHALL NOT hold a new
submission, which follows the running-send preference directly.

#### Scenario: Change the default running-send action

- **WHEN** the learner changes the running-send preference in workspace settings
- **THEN** the choice survives normal browser reopening and changes only future submissions

#### Scenario: Use an explicit running-send action

- **WHEN** a turn is running and the learner submits a message using the configured queue or interrupt-and-send preference
- **THEN** that explicit action applies to the submission without changing the stored default preference

#### Scenario: Inspect and edit a pending message

- **WHEN** the learner opens an accepted message that has not started
- **THEN** its current text and order are shown, and a valid edit preserves the originally captured context

#### Scenario: Stale pending control

- **WHEN** the pending message has started or its revision changed before the learner edits or removes it
- **THEN** the UI reports that the pending state changed and refreshes the list without modifying the running message

#### Scenario: Continue paused work

- **WHEN** the conversation has retained paused messages and no provider turn is running
- **THEN** the learner can explicitly continue the queue and see the next retained message begin

#### Scenario: Interrupt result keeps older work paused

- **WHEN** D interrupts A while B and C are queued and D finishes
- **THEN** B and C remain visible as paused until the learner explicitly continues them

#### Scenario: Compact queued messages

- **WHEN** B and C are accepted with queue while A runs
- **THEN** the composer remains usable beneath one list with one compact row per message in execution order; no duplicate pending cards appear in history

#### Scenario: An empty queue is hidden

- **WHEN** no queued messages remain, including when an interrupt is waiting for stop confirmation
- **THEN** the entire queue list and its queue controls are hidden; any interrupt status is shown independently

#### Scenario: Reorder with accessible controls

- **WHEN** the learner moves C above B by dragging or the keyboard equivalent and the server accepts the expected order
- **THEN** the list and dispatch order both become C then B without changing their identities, text or captured contexts

#### Scenario: Queue reorder conflicts

- **WHEN** the queue changes before the server accepts a reorder
- **THEN** the UI refreshes the authoritative order and explains the conflict without silently persisting the stale order

#### Scenario: Send a queued message now

- **WHEN** the learner chooses send-now on queued C while A runs and B precedes C
- **THEN** C leaves the ordinary queue and uses direct interrupt-and-send with its existing identity, current text and original context; B stays paused

#### Scenario: Read long or numerous pending messages

- **WHEN** queued text is long or more than four messages are queued
- **THEN** rows offer full-text reading/editing, the list scrolls within at most four row heights, the composer stays visible, and icon actions have readable accessible names

#### Scenario: Send directly after the last approval with an empty queue

- **WHEN** every Paper approval has been resolved, no queued messages are retained, and the learner submits a new message while no turn is running
- **THEN** the message starts immediately under the running-send preference instead of joining a paused queue

### Requirement: Existing approval controls remain truthful and scoped
Governed Paper-reset and rollback confirmations SHALL show their exact impact and remain bound to the intended workspace/conversation/message/revision; cancellation or stale approval SHALL perform no write. Paper approval SHALL identify the existing Paper, proposed item membership/order change, and affected unfinished completion/draft counts from the existing backend preview. The Agent SHALL propose rather than apply this Paper update; a learner click SHALL cause the page to request the existing validated update. A preview snapshot or chat reply alone SHALL NOT constitute that click. This change adds no generic approval gate to ordinary tools.

Paper approval SHALL coexist with the ordinary composer. A pending Paper approval SHALL be presented exactly once, in the composer-side approval card that carries the decision actions; the message flow SHALL NOT duplicate it and SHALL retain only resolved approval history cards. New messages explicitly submitted with queue SHALL be retained in the paused queue with their submission-time contexts. Interrupt-and-send and send-now SHALL be rejected without queue fallback or message loss; neither operation SHALL bypass the pending approval. Pending approval SHALL prevent queue continuation. Approval or cancellation SHALL leave the queue paused only while retained messages exist; when no approvals remain pending and no messages are retained, the queue SHALL NOT stay paused and new submissions follow the running-send preference. Existing rollback SHALL retain its composer-replacement interaction.

If the Paper or progress snapshot changed before approval, the UI SHALL perform no update, display a refreshed impact for the same proposed update and require a new approval click without requiring another Agent turn. Reload/reopen SHALL restore the pending approval and paused queue without automatic writes or provider execution. Missing/invalid targets SHALL produce actionable feedback without creating a replacement Paper. Duplicate approval attempts SHALL NOT reset progress twice.

#### Scenario: Cancel an existing Paper reset approval
- **WHEN** the learner cancels a governed Paper-reset approval or switches conversations before deciding
- **THEN** no Paper write occurs and the existing approval callback cannot act on the new conversation

#### Scenario: Approve the displayed Paper update
- **WHEN** the learner approves the current displayed Paper impact
- **THEN** the page requests the exact proposed update with its current confirmation; Paper ID, questions, historical attempts/ratings and other Papers remain unchanged, while only the target Paper's affected unfinished progress/drafts reset

#### Scenario: Pending approval appears once
- **WHEN** a Paper update awaits the learner's decision
- **THEN** only the composer-side approval card offers approve/cancel actions and the message flow shows no duplicate pending card alongside it

#### Scenario: Continue composing while approval is pending
- **WHEN** B/C are already queued and the learner explicitly queues another message while a Paper update awaits approval
- **THEN** the composer stays usable and the new message joins the paused queue; no queued provider runs and Continue cannot bypass the approval

#### Scenario: Resolve approval before continuing the queue
- **WHEN** the learner approves or cancels the pending Paper update
- **THEN** the queue stays paused only while retained messages exist; if no messages are retained the pause lifts and the next new submission follows the running-send preference

#### Scenario: Practice advances before approval
- **WHEN** the learner answers more questions or the Paper changes before the approval request is validated
- **THEN** no update/reset occurs from the old confirmation, the latest impact is displayed for another click, and no additional Agent request is required

#### Scenario: Restore a pending Paper approval
- **WHEN** the learner reloads or reopens the owning conversation after a Paper approval was persisted
- **THEN** the pending decision and paused queue reappear, with no automatic update or provider launch and with impact revalidation before execution

#### Scenario: Navigate or switch conversations during approval
- **WHEN** middle navigation or a conversation switch occurs while approval is pending
- **THEN** middle navigation preserves the decision; switching conversations makes old callbacks inert, and any restored approval remains bound to its original workspace/conversation/turn/Paper/revision

#### Scenario: Repeat an approval request
- **WHEN** an approval is double-clicked or its response is lost and the decision is submitted again
- **THEN** the operation is not executed a second time and the UI does not claim a second reset

#### Scenario: Interrupt cannot bypass approval or silently queue

- **WHEN** the learner chooses interrupt-and-send or send-now while a Paper update awaits approval
- **THEN** the UI explains that approval must be resolved first, retains the composer text or original queued item, and neither starts a provider nor silently enqueues an interrupt message

## ADDED Requirements

### Requirement: Long cards collapse with a fade expander

An Agent-side card whose rendered content exceeds a generous fixed height (approximately 320px) SHALL offer fade truncation: the overflowing bottom edge fades out and a small floating expander control with an up/down chevron floats over the faded region. AI message bubbles SHALL default to fully expanded with collapse available; tool-call outputs, Paper approval details and send-recovery cards SHALL default to collapsed. The expander SHALL keep a reachable hit area of at least 44×44 CSS px, keep its focus ring visible and unclipped, expose its state through `aria-expanded`, and never navigate, submit or modify records. Collapsing and expanding SHALL preserve drafts, selection and reading position.

#### Scenario: Expand a long assistant answer
- **WHEN** an AI message bubble exceeds the height threshold
- **THEN** it stays fully expanded by default with a chevron that collapses it, and collapsing preserves the reading position

#### Scenario: Tool output is collapsed by default
- **WHEN** a tool-call card's output block exceeds the height threshold
- **THEN** the card shows the faded truncation with the expander collapsed until the learner expands it

#### Scenario: Keyboard reaches the expander
- **WHEN** the learner focuses the expander control by keyboard
- **THEN** the focus ring is visible and unclipped, activation toggles `aria-expanded` and the fade, and the control's hit area is at least 44×44 CSS px
