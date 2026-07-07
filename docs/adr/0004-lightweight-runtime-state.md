# ADR 0004: Lightweight Runtime State

## Status

Accepted.

## Context

Lesson-Kit already has durable domain artifacts: source extraction files,
manifests, SQLite pools, and rendered views. The weak point is workflow
recovery. After interruption, an agent has to infer progress from directories,
chat history, and partially written reports.

Reference harnesses show different strengths:

- Superpowers has strong role and review methodology.
- OpenSpec has a clear action-oriented command surface.
- Comet has resumable state, guard scripts, and phase recovery.

Lesson-Kit is a learning-material production pipeline, so its first runtime
need is not a software-development lifecycle clone. It needs a small,
repo-local checkpoint and guard layer around the existing file contract.

## Decision

Add `.lessonkit/state.yaml` and a root `lessonkit.py` CLI.

The CLI owns runtime state writes and provides:

- `init`
- `status`
- `set`
- `guard`
- `resume`

The v1 state file uses a constrained YAML subset and Python standard library
only. We will not introduce PyYAML, packaging metadata, dashboarding, eval
harnesses, role bundles, or extension systems in this step.

`lessonkit.py guard` maps current commands to `FILE_CONTRACT.md`:

- `extract-chapter`
- `extract-problems`
- `problem-set`

With `--apply`, guard writes pass/blocked status back to
`.lessonkit/state.yaml`.

## Consequences

Agents have a deterministic recovery point before reading directories or
guessing from chat history.

The SQLite pool remains the runtime source of truth for learning data. The
state file only records workflow coordination.

The constrained YAML parser is intentionally narrow. If runtime state grows
into nested structures or user-authored configuration, Lesson-Kit should either
add a real YAML dependency with explicit packaging or move machine-owned state
to JSON.
