# Tasks

## 1. Contract

- [x] 1.1 Add Pi activity and UI deltas; validate strictly.

## 2. Normalization

- [x] 2.1 Add failing tests for read/write/search/shell/Lesson Kit labels and redaction.
- [x] 2.2 Implement the minimal Pi-specific classifier and bounded output.
- [x] 2.3 Keep only concrete Pi activities in successful mirrors.

## 3. UI

- [x] 3.1 Add failing interaction tests for independent rows, updates, text segmentation, and folded output.
- [x] 3.2 Implement Pi-only activity messages and styles; preserve Codex/Claude plans.
- [x] 3.3 Verify successful restoration and failed/cancelled boundaries.

## 4. Acceptance

- [x] 4.1 Run all automated checks.
- [x] 4.2 Run one real Pi turn in an isolated scratch workspace covering read, write, Lesson Kit CLI, and final text.
- [x] 4.3 Archive the completed change.

> Handoff boundary (2026-09-22): implementation and deterministic provider/UI
> fixtures are complete. A real Pi 0.85.1 scratch turn read the marker, wrote a
> scratch output, ran `lesson-kit pull`, and produced a successful mirror, but
> exposed two acceptance defects: CLI detection matched a workspace-path
> substring, and prefixed secret variable names escaped masking. Both defects
> now have passing focused regressions; the real Pi turn must be repeated before
> checking 4.2 or archiving. The first scratch directory was deleted because its
> pre-fix event file contained an unmasked environment secret.
>
> Acceptance (2026-09-22, next Agent): fresh isolated scratch
> (`%TEMP%/lk-pi-accept2/lesson-kit-scratch`, `LESSONKIT_WB_HOME` isolated, server
> on 3091, the real `bridges.json` pinning `pi -> deepseek/deepseek-v4-flash`).
> Two real Pi 0.85.1 turns typed into the UI composer:
> - Conversation 1 (before the pull fix) mirrored six concrete activities and
>   validated both earlier fixes live: `echo path=…\lesson-kit-scratch` was
>   labelled 运行命令 (not 操作 Lesson Kit), `lesson-kit pull …` was labelled
>   操作 Lesson Kit, and the stored detail read
>   `echo DEEPSEEK_API_KEY=[REDACTED] token=[REDACTED] Bearer [REDACTED]`.
>   No event, mirror, or transcript file contained the raw marker values. The
>   pull call failed with a real CLI crash that was then fixed (see
>   `problem-difficulty-and-provenance`).
> - Conversation 2 (fixed code) completed every activity as 已完成, including a
>   successful `lesson-kit pull lesson-kit-scratch --n 2` whose folded output
>   held the returned problem ids. One DOM row per tool call (3–6 in-place
>   updates each, no duplicates), output folded behind 「查看输出」 and expanding
>   on click, no hidden reasoning or protocol noise, and reopening both
>   conversations from the session list restored the same merged activities
>   (failed state preserved for conversation 1) plus the final answer.
> Repository checks on the final tree: pytest 495 / Node 109 / compileall /
> strict 11 / doctor / both guards PASS.
