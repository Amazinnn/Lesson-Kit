# ADR 0011: Flexible Feedback

## Status

Accepted.

## Context

Fixed feedback forms (checkbox grids, forced "again/hard/good/easy" buttons)
contradict the learner's practice style: feedback should be given when
conditions are suitable, not demanded. But weak-point tracking needs signal
input to drive the pain-point-first ordering (ADR 0010) and the AI teacher.

## Decision

Feedback is optional and free-form, with two accepted forms — alone or
together:

- **1–5 self-rating** of mastery; mapped to signal weight changes (1–2 → high,
  3 → medium, 4 → low, 5 → lower weight without clearing; repeated evidence
  increments `evidence_count`).
- **Natural-language note** describing the weak point; mapped by keyword rules
  to a signal type (`weak_node`, `confusion`, `missing_prerequisite`,
  `transfer_failure`, `relation_gap`), with the original text preserved
  verbatim on the signal and in the event log. No keyword match falls back to
  `weak_node`.

Data model: `learner_signals` keeps its "current state" semantics (ADR 0008);
a new append-only `feedback_events` table logs every feedback event for later
"AI teacher memory" and statistics. Signals never auto-clear (conservative,
per ADR 0008): a 5 rating lowers weight but does not erase the signal.

No feedback at all is always a valid outcome of a session.

## Consequences

Feedback flows in when the learner has something to say, which is exactly the
signal quality the loop needs. Mapping is simple and deterministic in v1
(keyword rules); misclassification is acceptable because the note text is
preserved and visible to the learner and to the AI teacher later.
