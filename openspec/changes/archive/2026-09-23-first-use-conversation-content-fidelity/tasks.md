# Tasks

## 1. Contract and documentation

- [x] 1.1 Record the first-use evidence and final owner decisions in proposal/design/spec deltas.
- [x] 1.2 Update GLOSSARY, PRODUCT-MANUAL, ACTION-GRAPH, architecture, prompt documentation, and red lines with implemented behavior.

## 2. Content actions and bundle

- [x] 2.1 Add failing tests proving keyword-free append actions execute while action-free conversation writes nothing.
- [x] 2.2 Remove the 3–6 prompt ceiling and add staged-manifest path validation scoped to the conversation jobs directory.
- [x] 2.3 Add a failing 30-item bundle test covering knowledge points, formal/micro problems, figures, one batch id, and all-or-nothing failure.
- [x] 2.4 Implement the minimal `content-bundle` gate/apply/backup/rollback path by composing existing Data/ingest primitives.
- [x] 2.5 Add formal-problem source evidence, source answer, and solution-origin compatibility fields and user-facing labels.
- [x] 2.6 Preserve Micro Quiz and all four practice entries; prove source exercises are not silently converted while explicit micro requests still work.
- [x] 2.7 Delete newly unreferenced bundle figure files on rollback while retaining shared referenced files.

## 3. Rich content

- [x] 3.1 Add shared fixtures for headings, lists, quotes, code, links, math, images, GFM tables, and rejected raw HTML.
- [x] 3.2 Implement renderer parity in browser Agent messages and server linked-problem Markdown with narrow-table overflow.
- [x] 3.3 Render source evidence and source/generated solution labels on practice and knowledge-point surfaces.

## 4. Pi runtime and Windows processes

- [x] 4.1 Add a fake strict-LF Pi RPC fixture covering prompt, streamed events, completion, abort, handshake retry, idle expiry, restart, and shutdown.
- [x] 4.2 Keep one Pi RPC process per conversation for 30 idle minutes with no process-count cap and native-session resume.
- [x] 4.3 Never replay an accepted prompt after a mid-turn crash; preserve partial events and require an explicit retry.
- [x] 4.4 Apply hidden/no-window launch settings to every Windows provider child and test that command construction remains compatible.

## 5. Automated and isolated acceptance

- [x] 5.1 Run focused Python/Node tests, then full Python, all Node, compileall, OpenSpec strict, doctor, and guards.
- [x] 5.2 In a copied physics workspace, import one 30-item mixed content bundle with at least one required original image and inspect both rich-text surfaces.
- [x] 5.3 Run three real Pi 0.85.1 turns through one PID, abort a turn, wait/restart from session, and confirm no visible console.

## 6. Authorized real remediation and closeout

- [x] 6.1 Back up the real physics pool/figures and recheck all five erroneous batches for learning/dependency blockers.
- [x] 6.2 If blocker-free, roll back batch-005 through batch-001, preserve/review the eight knowledge points, and reimport original exercises and images.
- [x] 6.3 Verify accounting, foreign keys, integrity, source/type/image rendering, and rolled-back conversation result cards.
- [x] 6.4 Update current docs, rerun repository checks, archive the OpenSpec change, and leave commit/push to explicit user authorization.

> Acceptance (2026-09-23, executing Agent). Repository checks on the final tree:
> pytest **539**, Node **112**, `compileall` exit 0, `openspec validate --specs
> --strict` **11**, `doctor` all checks passed, `guard extract-problems` and
> `guard problem-set` PASS.
>
> Isolated copy (`%TEMP%/lk-phys-accept/大学物理乙II`, isolated registry, port
> 3092): one 30-item bundle committed as `batch-006` — knowledge_points 3,
> problems 25 (22 `source_problem` + 3 explicitly requested micro adaptations),
> flash_cards 2, figures 8 copied byte for byte; foreign keys and integrity
> clean. Both rich-text surfaces were inspected on the live pages: the
> knowledge-point page and the practice card each rendered the source line, the
> original figure, KaTeX math, and a GFM table (`rich-table-wrap`); the four
> practice entries remained available.
>
> Real Pi 0.85.1 (`pi.cmd` pinned to `deepseek/deepseek-v4-flash`, isolated
> registry): three turns in one conversation reused **one PID (41224)**; the
> cancel of a long turn reached the agent over RPC and stopped it in **0.51 s**
> with the same process still standing; after a server restart the next turn ran
> on a **new PID (17580)** and answered from the resumed native session (it
> recalled the earlier points and the pending exercise 12-5). Every recorded Pi
> process had `MainWindowHandle = 0`. Evidence:
> `%TEMP%/lk-phys-accept/pi-acceptance.json`.
>
> Real remediation (`大学物理乙II`): pre-remediation pool backup
> `pool/backups/c01-pre-remediation-20260923-071933.db`; the five old batches
> re-checked with **zero** learning dependencies; `batch-005`→`batch-001` rolled
> back through the governed CLI (each rollback kept its own
> `c01.db.batch-00N-rollback-backup`); the pool was migrated and 25 textbook
> exercises were reimported as one atomic `batch-006` (1 knowledge point for
> §12-8, 25 problems all `source_problem` with `source_evidence`, 11 figures
> byte-identical to the textbook OCR, 0 micro quizzes). Final accounting: 25
> problems, 9 knowledge points, `foreign_key_check` empty, `integrity_check` ok,
> all eight original knowledge points preserved. The preserved `conv-001`
> reopens with all five old result cards reading 「已回滚」 and exposing no
> rollback button.
>
> Known limit recorded honestly: the copy acceptance captured 8 of the 11
> figure-bearing exercises (its generator missed the three figures embedded in
> an OCR table block); the real reimport contains all 11, so the workspace is
> the more faithful of the two.
