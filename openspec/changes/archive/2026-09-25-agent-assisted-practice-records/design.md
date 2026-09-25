# Design — Agent-assisted practice records

## Existing facilities and gap

`problem_attempts` already stores answer text, status, and note. The feedback
Domain maps a 1–5 rating to events, knowledge-point signals, current states,
progress, and scheduling. The public `practice` CLI records one categorical
result (`correct/wrong/stuck/skip`) and maps it to a fixed schedule quality;
the `feedback` CLI takes a separate 1–5 rating. Neither command atomically
submits a transcribed open answer with its own learning rating. No attempt
image attachment or Agent-oriented correction contract exists.

Reuse these rules within Shell → Domain → Data. Keep ordinary browser practice
and explicit self-rating compatible. The new path is invoked when the learner
asks the Agent to record or grade work; merely reading a draft or local image
does not write anything.

## Public CLI

```text
lesson-kit attempts <workspace> list --problem <problem-id>
lesson-kit attempts <workspace> get <attempt-id>
lesson-kit attempts <workspace> check --input <file|->
lesson-kit attempts <workspace> apply --input <file|->
lesson-kit attempts <workspace> correct <attempt-id> --input <file|->
lesson-kit attempts <workspace> sources add --path <directory>
lesson-kit attempts <workspace> sources list
lesson-kit attempts <workspace> sources remove --path <directory>
```

List/get are read-only JSON. A record manifest is a UTF-8 JSON object:

```json
{
  "request_id": "conv-001-turn-004-record",
  "items": [
    {
      "problem_id": "c01-ch12-prob-001",
      "answer_text": "Transcribed working and final answer",
      "note": "Feedback on the reasoning and the point of difficulty",
      "rating": 3
    }
  ]
}
```

`items` contains one or more distinct attempt submissions. `rating` is
optional and, when present, must be an integer 1–5; it expresses the existing
learning-rating semantics, not exam percentage points. `answer_text` and
`note` are text, and at least one must be non-empty. No answer-image bytes,
file path, image reference, exam mark, or grader-identity field is accepted.
`request_id` is a readable caller-stable idempotency key: applying identical
content with the same id returns the original result; different content with
that id fails. A new id makes a new attempt even for the same problem.

`check` validates every item and previews the expected attempt count and
rating effects with zero writes. `apply` validates under the write transaction,
then inserts attempts and linked feedback and updates existing Domain-derived
projections. One invalid item leaves every table unchanged. Output reports
attempt ids, which items were ungraded, and changed due dates. CLI errors use
nonzero exit codes and itemized JSON messages, following current conventions.

`correct` takes a single JSON object containing the replacement `answer_text`,
`note`, and optional `rating`, plus a new `request_id`. The attempt id is the
positional CLI argument. The command validates and atomically replaces that
attempt and its linked feedback effect; it neither creates a new attempt nor
keeps a correction-history entry. Ordinary `apply` never overwrites attempts.

## Atomic effects and correction guard

Use `status=new` for an ungraded submitted attempt, without altering progress,
signals, current state, feedback events, or schedule. A rated attempt receives
the existing status projection (1–2 wrong, 3–4 reviewing, 5 mastered) and
calls the existing 1–5 feedback rules exactly once in the same transaction.
Do not call the categorical `practice` result mapping, which would turn
`correct/wrong` into fixed 4/2 schedule inputs.

Associate new attempt feedback with its attempt id. Store the pre-effect and
post-effect snapshots needed to correct only this operation's changes without
replaying unrelated learning history. Correction first checks that the current
affected problem/KP projections still equal the operation's post-effect
snapshot. A newer attempt, feedback, graph-state edit, or other change that
affects those projections causes a zero-write conflict with an actionable
message to record a fresh attempt. For an eligible correction, restore the
pre-effect snapshot, update/delete the linked feedback event, replace the
attempt, and apply the new rating in one transaction; update its post-effect
snapshot. This keeps the attempt id stable and avoids duplicate evidence.
Legacy attempts and feedback without an operation link remain readable and
are not retroactively correctable through this command.

## Images and focused context

`sources add/list/remove` manage a per-workspace list of learner-chosen
directories. An explicitly configured directory may be outside the workspace
and is only a read source. The Agent can also use its ordinary workspace file
access and existing CLI to inspect problems and prior attempts. Directory
configuration stores directory paths, never per-image paths or bytes. There is
no background monitor or image scan index; exact cross-scan deduplication is
not promised.

When the learner sends a message from the practice page, the browser sends the
active problem id and bounded, ephemeral text draft, selected choices, note,
and currently visible image references. The server still rebuilds authoritative
problem facts from SQLite; it does not trust browser-supplied content as a pool
fact or send the whole DOM. The Agent may prioritize this focused context and
read other permitted workspace files. Neither the draft nor answer images are
saved by the bridge merely because a message was sent. The record CLI receives
the Agent's transcription and feedback, not the image files.

## Compatibility and delivery

Keep existing learner self-rating UI, `practice`/`feedback` commands, and
provider-native conversation behavior. Use an additive schema migration; no
automatic backfill or mutation of existing attempts. Add no dependency and no
exam-style scoring or rater source field. The new CLI is a data interface, not
an instruction for how the Agent should interpret handwriting or assign a
rating.

Implementation acceptance runs first in isolated workspaces and covers
multi-page answers, two problems on one page, draft-only discussion, rated and
ungraded submissions, request retries, correction with/without later effects,
and failures that leave every learning table unchanged. Full repository tests
and real-environment acceptance belong to the receiving implementation Agent.
