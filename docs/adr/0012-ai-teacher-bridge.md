# ADR 0012: AI Teacher Bridge

## Status

Accepted.

## Context

Past attempts at AI-assisted study failed on both sides: generic web AI chat
generated shallow questions that merely mirrored original problem structure
(no induction, transfer, or generalization), and long-lived prompt personas
("teacher mode") did not survive conversation resets. The workbench must not
become a local chat that reads files. The confirmed direction: the workbench
provides no harness engineering — AI is reached through an external agent CLI
(Claude Code and similar), with the pool as the durable cross-session memory.

## Decision

A **bridge** layer connects the workbench to external agent CLIs:

- The workbench has **no AI kernel**. AI operations are tasks: a task file
  (operation, target, context from the pool, output contract) plus a rendered
  instruction file, executed asynchronously by a configured provider CLI with
  the workspace folder as working directory.
- **Output-contract validation** is mandatory: a result is trusted only when
  the file is written, required sections are present, a source reference
  exists, and the Markdown parses. Failures are observable with reasons.
- The v1 operation is `explain` only (defense simulation and gap-filling
  generation are later operations on the same protocol).
- Every task carries a **teacher conduct contract**: establish what the
  learner already knows first, explain in focused concise chunks, verify
  understanding with a question, never guess — verify against the workspace
  pool and source material — and cite the source location. This encodes the
  lessons of the CFP-Study CLAUDE.md case (Socratic baseline, comprehension
  check, no-guessing/cite-source protocol) as a contract rather than a persona
  prompt.

## Consequences

The full learning loop runs with zero AI dependency; AI quality is governed by
architecture (task context from the pool, contracts, validation) rather than
by prompt engineering. Cross-conversation memory is the pool itself. The bridge
is the smallest surface that still keeps the door open to defense and
generation later.
