# ADR 0020: Agent-Native Teaching with Layered Adaptation

## Status

Accepted.

## Context

The first draft of the AI teacher process (a session state machine with enforced
transitions: opened → locate → verify → converged) was rejected as
over-constrained: it hard-codes pedagogical behavior, which the DeepTutor
research (HKUDS, *DeepTutor: Towards Agentic Personalized Tutoring*, arXiv
2604.26962) identifies as brittle and poor-scaling. The learner's position:
the CLI is a data interface, the agent freely explores problems and materials,
a session is not bound to one task, and the learner can open a new session at
any time. The open question was how to keep teaching systematic without
hard-coding — DeepTutor's answer is layered adaptation, not enforcement.

## Decision

Teaching is agent-native; process control is layered, not enforced:

1. **CLI is a data interface.** `wb` exposes only data operations (query, pull,
   record, start bridge tasks, status). Teaching behavior lives in the teaching
   skill and the teacher conduct contract. This mirrors DeepTutor's own design,
   which documents handing its CLI to Claude Code subagents.
2. **Layered adaptation** (from the classic DeepTutor 3-loop framework, Rus et
   al.):
   - *Macro*: a session's purpose is anchored to pool items (problems, KPs);
     anchors can change or be re-anchored.
   - *Meso*: session lifecycle is learner-controlled — start, continue, or
     abandon a session at any time.
   - *Micro*: turn-level conduct (establish baseline, explain concisely, verify
     understanding, never guess, cite source) lives in the teacher contract.
3. **Anti-derailment without locks**: digressions are parked visibly and the
   conversation returns to its anchor; the learner may open a new session for a
   digression. No enforced state transitions, no hidden flow.
4. **Sessions leave traces, not pipes**: at session end a trace artifact
   records anchor, exchanges, and outcomes (DeepTutor's trace-tree idea),
   under `.lessonkit/jobs/<conv-id>/` — recorded for later "AI teacher memory",
   never used to gate future sessions.

## Consequences

The teacher is as flexible as the learner demands, while the systematic part
(conduct contract, trace recording, data interfaces) stays deterministic and
testable. The cost: some pedagogical consistency is delegated to the agent and
must be maintained through the teaching skill rather than enforced in code —
an accepted trade-off per the DeepTutor critique of hard-coded pedagogy.
