## Why

The workbench already stores text attempts and maps 1–5 feedback to learning
state, but handwritten open problems require the learner to transcribe and rate
them manually. The existing `practice` and `feedback` CLI commands cannot
atomically submit an Agent-transcribed answer, grading note, and learning rating.

## What Changes

- Add a workspace-scoped `lesson-kit attempts` CLI for reading, checking,
  atomically applying, and correcting problem attempts.
- Let the learner configure directories where the Agent may look for answer
  images. The Agent reads those files with its existing workspace/file tools;
  Lesson Kit stores neither answer images nor per-image paths or scan indexes.
- Include the current practice draft, selected options, and currently displayed
  images in the focused Agent turn context. Reading that context does not create
  a learning record.
- Permit an Agent to submit an optional 1–5 learning rating with its
  transcription and grading note. Rated submissions reuse the existing signal,
  current-state, progress, and schedule rules; ungraded submissions remain
  durable attempts without changing those projections.
- Correcting a specified recent attempt replaces its recorded conclusion and
  recomputes its effects. Ordinary conversations continue to write no learning
  records unless the learner requests recording or grading.

## Capabilities

### New Capabilities

- `agent-assisted-practice-records`: the Agent-facing CLI transaction, attempt
  history, explicit correction, and answer-image directory configuration.

### Modified Capabilities

- `review-workbench`: Agent-recorded and ungraded attempts extend the current
  practice/feedback rules without changing normal student self-rating.
- `ai-teacher-bridge`: learner-requested recording may use the new CLI while
  ordinary conversation remains free of learning writes.
- `workbench-ui`: focused practice drafts and visible images become ephemeral
  turn context.

## Impact

Additive pool schema, Data/Domain recording orchestration, CLI, focused page
context, and current terminology/product documentation. Reuse the existing
SQLite pool, feedback rules, and stdlib-only architecture. No image archive,
image index, exam-percentage grade, or separate grader identity is introduced.
