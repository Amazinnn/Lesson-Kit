# Tasks

## 1. Contract

- [x] 1.1 Add deltas for mirror consistency and retired live requirements.
- [x] 1.2 Validate the change strictly.

## 2. Conversation race

- [x] 2.1 Add a deterministic failing concurrent read/write test.
- [x] 2.2 Guard mirror JSON, event JSONL, and transcript I/O with one re-entrant lock.
- [x] 2.3 Run the complete conversation test module (37 passed); full-suite repetition remains in 4.1.

## 3. Current documentation

- [x] 3.1 Remove retired live requirements and the deprecated review-page capability.
- [x] 3.2 Correct current entry/routing/contracts and mark frozen pipeline designs.
- [x] 3.3 Add and pass a current-document consistency test.

## 4. Verification

- [x] 4.1 Run Python, Node, compileall, OpenSpec strict, doctor, and guards.
- [x] 4.2 Archive the completed change.

> Handoff boundary (2026-09-22): 3.1 is intentionally completed by archiving
> this delta after final acceptance. One full run reached 492 Python and 109
> Node passes; doctor and extract-problems guard passed. Two later acceptance
> fixes received focused checks but the full suite was not repeated afterward,
> so 4.1 and archive remain the next Agent's responsibility.
>
> Acceptance (2026-09-22, next Agent): final tree measured after a third
> acceptance fix (see `problem-difficulty-and-provenance`) — pytest **495**,
> Node **109**, `compileall` exit 0, `openspec validate --specs --strict`
> **11 passed**, `doctor` all checks passed, `guard extract-problems` and
> `guard problem-set` PASS, `git diff --check` clean. 3.1 lands through
> `openspec archive` itself: that is what removes the retired `review-page`
> capability and the stale candidate/explain/diagnose requirements from the
> live specs.
>
> Archive deviation (2026-09-22): `review-page` is retired *whole* — its delta
> removed all three requirements, and OpenSpec 1.8 refuses to write a spec with
> zero requirements (`✗ Spec must have at least one requirement`), including
> when the base spec is absent ("3 REMOVED requirement(s) ignored for new spec").
> The capability was therefore retired by deleting `openspec/specs/review-page/`
> directly, and its now-inapplicable REMOVED delta left the change rather than
> blocking the archive forever. The three retired requirements were:
> - `Review page as a reminder surface` — the fourth navigation page was
>   removed; reminders live in the practice page.
> - `Review handoff paths` — the surviving scoped pull behavior already belongs
>   to `review-workbench`.
> - `Directional card session` — directional practice is implemented inside the
>   flash-card mode, not a review page.
> `tests/workbench/test_current_docs.py` asserts the absent directory after
> archiving, and all repository checks were re-run afterwards.
