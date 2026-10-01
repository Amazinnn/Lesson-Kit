# Tasks

The queue for `design.md`. Nothing here is done; this change only records the
defects. Each task names its **route** (`CONFORMANCE` / `NEW-GAP` / `DOCTRINE` /
`NOT-A-DEFECT`) and the capability that owns it, so the register converts into
scheduled work without re-deriving ownership.

Start with §1: those are bugs against requirements the repository already
carries, so they need no new spec and no doctrine decision.

## 1. Conformance — a requirement exists and is violated

Owner: `workbench-content-governance`, `workbench-ui`.

- [ ] 1.1 Stamp every written content row with its batch id. `ingest_batch_id` is NULL on 937/937 problems and 324/324 knowledge points despite 16 ledger batches, so no batch can be traced or rolled back. `openspec/specs/workbench-content-governance/spec.md:163` requires it, scenario at `:167-168`.
- [ ] 1.2 Escape each text exactly once on the server render path. At authorship `workbench/server/pages.py:796` escaped the whole text and `_math_replace` (`:816-820`) escaped the expression again, so `&` reached KaTeX as `&amp;`; the client path at `workbench/server/static/workbench.js:311,340-345` escaped once and rendered correctly, which is why the same row could be fine in one surface and broken in another. `openspec/specs/workbench-ui/spec.md:1079-1083,1092-1093` requires one consistent math pipeline, escaped-then-rendered. **Re-verified 2026-10-01 against the merged tree: the server path now escapes once (live render check) and the client site was rewritten by the records/graph batches — what remains of this task is 1.3's real-pool regression check.**
- [ ] 1.3 Add a regression check for 1.1–1.2 that runs against a real pool, not a fixture. Both survived a full 8-chapter import in two courses.

## 2. Doctrine — decide before writing any requirement

The four items below live in `pipeline/`, whose behaviour contract `AGENTS.md:38-39`
forbids modifying, and which
`openspec/changes/archive/2026-09-20-optional-problem-difficulty-gate/specs/workbench-content-governance/spec.md:13-14`
already places outside spec scope. None can become a requirement until this is
settled. The options are: deprecate `--upsert` in favour of an explicit
patch path, authorise a scoped exception, or accept the behaviour and document
it. This is a decision, not an implementation task.

- [ ] 2.1 Decide the `pipeline/` question above, then record the decision as an ADR.
- [ ] 2.2 After 2.1: stop `INSERT OR REPLACE` rebuilding the row. `pipeline/scripts/insert-problems.py:256-259` writes 6 columns and `pipeline/scripts/insert-knowledge-points.py:254-259` writes 11, so every other column returns to its default and the run exits 0 — a partial re-ingest silently clears `exam_year`, difficulty ratings, display titles and practice modes. The pattern to copy already exists in the tree: `workbench/data/difficulty.py:48-50` writes a targeted `UPDATE`.
- [ ] 2.3 After 2.1: exit non-zero when rows were dropped. Without `--strict`, `pipeline/scripts/insert-knowledge-points.py:239-246` prints "Continuing with valid rows only" and falls through to `return 0` at `:297`, so any caller checking `$?` sees success. The `c04` course worked around it by passing `--strict` at every call site.
- [ ] 2.4 After 2.1: narrow `COLLAPSED_SUBPART_PATTERN`. `pipeline/scripts/candidate_contract.py:12` (`[^\n][ \t]+[a-j]\s*\)[ \t]+`, used at `:55`) matches the `- a) ` inside ordinary printed maths such as `(b - a) `, and cost 6 of 180 real problems under `--strict`.
- [ ] 2.5 After 2.1: make the post-hoc sweep able to run. `pipeline/scripts/validate-pool.py:151-161` still requires the two tables retired on 2026-08-30, and the early return at `:612-613` then skips every content gate — measured 2026-10-01 on `dmath`/`c01`/`c04`, the whole report is two `missing required table` errors (P0-5). Either drop `candidate_problems`/`candidate_attempts` from the required list, or narrow the early return to the tables the following gates actually read.
- [ ] 2.6 After 2.1, in the same pass as 2.5: widen `PROBLEM_ID_PATTERN` (`:32`) to accept the `-mq-NNN` micro-quiz form — or accept it explicitly — otherwise restoring the sweep reports 42 false positives on the repo's own pool (P0-6).
- [ ] 2.7 After 2.1: state which sweep is the acceptance signal — `lesson-kit data <ws> audit` (live) or `validate-pool.py` (frozen) — so course work stops citing the latter's FAIL as a pool verdict, which it cannot be today (P0-5).

## 3. New gap — ingest integrity and the batch registry

Owner: `workbench-content-governance`. Each needs a requirement authored in a
follow-up change; none is covered today.

- [ ] 3.1 Stable problem ids. Ids are minted by a positional counter, so a rebuild re-mints them from position rather than identity — at authorship **425 of `c04`'s 937 problem ids denoted a different question** (diffed against the 974-row `pool/backups/c04-before-spacingfix-20261001-003817.db`; the pool kept evolving and a 2026-10-01 re-run reads 1063 live / 59 deleted / 148 added / 403 displaced / 512 unchanged — see the design.md audit note), and `problem_attempts` / `problem_progress` / `review_schedule` key on the same strings. The `c04` repair had to re-locate 23 problems by content signature to avoid re-tagging the wrong questions. Consider a content-derived or source-position-derived id, and a gate that refuses a manifest whose ids would move relative to what the pool already holds.
- [ ] 3.2 Gate a problem manifest's `kp_ids` against the knowledge points that exist, in both directions, plus a manifest KP count versus its declared split. In `ncmc`, 81 problems' cross-chapter bindings lived in a side manifest the loader never reads, and two chapters were built from `knowledge_points: []` shells. The equivalent rule already exists for flash cards (`openspec/specs/flash-card/spec.md:19-20,37`); it is not applied to problems or knowledge points.
- [ ] 3.3 One backup file per batch, with a retention policy. All 16 `c04` batches wrote `pool\c04.db.ingest-backup`; it was overwritten each time and no longer exists, so only the last snapshot is recoverable. The requirement records a backup *path* (`:163`) but scopes recoverability to rollback only.
- [ ] 3.4 Enter knowledge-point ingest in the ledger. All 16 `c04` batches are `kind='problem-patch'`; 324 knowledge points were ingested outside the registry entirely.
- [ ] 3.5 A documented manifest schema. The contract is recoverable only from insert-script line numbers, 8 files of one manifest kind carry 9 key sets, and 8 builders in one course implement the same contract three ways. `FILE_CONTRACT.md` does not mention `source_location`, `related_kp_ids`, `fragile` or `graph_label` at all.
- [ ] 3.6 A schema for `source_location`. The `§syllabus-chapter.textbook-section` encoding exists only as human convention, has no validator, and already produced one wrong section reference plus one reference to a section that does not exist.
- [ ] 3.7 A field that distinguishes "the source has no answer" from "extraction failed". Both arrive as `solution: null`, via two encodings (empty value vs absent key) — 245 of 937 rows, and the text side has a `sys.exit` guard while the solution side has none.
- [ ] 3.8 A dedup fingerprint that does not degenerate. The `c04` key was a normalized 50-character prefix while `problem_text` averages 49 characters, so the key was effectively the whole stem; the collapse to 56 groups only reproduces when normalization strips CJK, and a CJK-preserving 50-char prefix yields 905 groups. Stripping CJK is itself the bug — every Chinese-stemmed problem keys on its punctuation. The plan declared 847 unique items and 937 rows landed, with no gate comparing the two.
- [ ] 3.9 Carry difficulty anchors and per-item reasons into the manifest. All 937 `c04` ratings are `cognitive-v1-equal-mean` with no recoverable basis, and the declared anchor set contradicts itself (a note says 14, `count=len(anchors)` is 15).
- [ ] 3.10 Cross-check apply-time accounting against the pool. All 8 `c04` per-batch logs are byte-identical (kp 324 / problems 937 / relations 0), and one recorded 937 while the pool held 974 — the only field that could have surfaced the loss was a constant. Note what the requirement does *not* say: "the reported accounting matches the recorded counts" exists only at `openspec/specs/workbench-content-governance/spec.md:173`, inside the *Roll back a whole batch* scenario, and it compares the reported figure against the recorded one — both derived from the same record, so a wrong count satisfies it. Either compute the counts from the transaction, or refuse to record a batch whose counts were not observed.

## 4. New gap — difficulty rating

Owner: `problem-difficulty`.

- [ ] 4.1 Decide whether `difficulty check/apply` promises coverage. `workbench/data/difficulty.py:9-14` documents itself as validating a *complete* manifest but only checks non-empty plus per-item validity, so a truncated batch passes; the spec is careful to promise nothing (`openspec/specs/problem-difficulty/spec.md:77-80,87-90` scopes its promise to "all **named** ratings"). Either make the code match the docstring or change the docstring, and settle which.
- [ ] 4.2 Re-anchor the rating scale outside the rated set. In `ncmc`, 30 anchor problems were themselves among the 180 being rated, so "zero anchor violations" restated the anchors; one rated item crossed the ceiling it was supposed to define and was ingested anyway.
- [ ] 4.3 Sequence any length-based validator after `content-dedup-and-audit` lands, or state explicitly that it is exempt from that change's "length is not an answering-form property" doctrine (`openspec/changes/content-dedup-and-audit/design.md:126-138`, D9). This is the CJK-measurement gap, `design.md` P1-27.

## 5. New gap — the graph artifact

Owner: `knowledge-figures`, `workbench-ui`. Note that the one item here which
*looked* like a defect is not; see §7.

- [ ] 5.1 Constrain `graph_label`: unique per knowledge point, and not a chapter name. There is no chapters table, so a chapter name in `graph_label` renders a whole chapter under one identical label. `pool/scripts/render-graph-html.py:150`.
- [ ] 5.2 Make the `graph_label` check able to see a bad label. The only check is a character count (`pipeline/scripts/insert-knowledge-points.py:127-128`, `len(graph_label) > 24`), so a label that was already cut to exactly the limit passes: 9 `ncmc` labels end mid-word, all at exactly 24. The cut itself was made by a course-local merge tool, so the repo-side gap is that the gate cannot distinguish a short label from a truncated one.
- [ ] 5.3 Define the graph search corpus. It is `[id, label, graph_label, body, source_location]` (`pool/scripts/render-graph-html.py:1313`) and omits `learning_action`, so text written into that field is unsearchable — 8 terms stopped resolving.
- [ ] 5.4 Make the `fragile` filter mean something. It is `Boolean(node.fragile)` (`pool/scripts/render-graph-html.py:1315`), so a pool where every knowledge point has a non-empty `fragile` makes it a no-op. The field's ingest contract is "string or null, bool rejected" (`pipeline/scripts/insert-knowledge-points.py:154-157`) while the renderer treats it as a flag; settle which.
- [ ] 5.5 Support cross-chapter relations as a first-class concern. Per-chapter extraction left all 940 `related_kp_ids` intra-chapter and 0 cross-chapter; the `c04` cross-chapter graph exists only because 218 edges were designed and applied by hand, and graph verification reads the manifests and never the database.

## 6. Verification debt

- [ ] 6.1 Re-run the unverified numbers in `design.md` before any of them is used to size a fix. Listed there: the fate of the 37 deleted `c04` problems (reconstructed from shard copies, not observed); which of the 143 prefix-dedup skips were true duplicates; the correctness of the 419 hand-written problem → KP assignments; the accuracy of the 935 `【…】` display-title prefixes; and every `ncmc` pool count, which came from sweeps that read the pool but were not independently re-run.
- [ ] 6.2 Add a re-entrancy guard to textbook extraction. `c04` retains `textbook/probe` (14,371 B) and `textbook/probe2` (4,682 B) with nothing marking which attempt succeeded, and `ncmc` retains 19 `*.partial.*` files next to their finals because the hand-written promotion copies rather than moves and refuses to overwrite an existing final.
- [ ] 6.3 Decide what the ingest logs are for. `recipe.json` files hold results (`applied`, `ok`, `batch_id`, `backup_path`) that duplicate the `-step2.txt` stdout, and all 24 log files share a 3-second mtime window that contradicts the ledger's `applied_at` spanning 16:16→22:57, so file timestamps cannot order the run.

## 7. Not defects — do not "fix" these

- [ ] 7.1 Leave `knowledge_relations` empty. `openspec/specs/review-workbench/spec.md:347-348` requires that edges may originate from "formal relations **or existing `related_kp_ids`**", so an empty table is the specified behaviour. Recorded because the first sweep reported it as a defect and an earlier draft of this change would have proposed breaking a live requirement. **Superseded half (2026-10-01):** "edge direction stays discarded" no longer holds — batches `#87`/`#90` deliberately preserve stored direction and one edge per stored relation, so the spec scenario at `:355-358` (collapse to one edge for the unordered pair) is now the stale side; update that scenario in the next change that touches `review-workbench`, and do not treat the multi-edge-preserving model as the violation.
- [ ] 7.2 Note the refuted `c04` hypothesis so it is not re-investigated: ch05–ch08 knowledge points were *not* orphaned by late ingestion. Per-chapter references are 578/672/434/324/225/128/237/172, all non-zero, with zero dangling references, and `kp-baseline.json` is timestamped between the two pre-ingest snapshots. The real orphan population is 22 of 324. The absence of a gate that would have caught it either way is item 3.2.
- [ ] 7.3 Do not "fix" `query_rows`' LIKE. A claim that the prefix lacks a trailing `%` is false — `query_rows` (`pipeline/scripts/validate-pool.py:144-145`) appends it, all ten prefix-LIKE call sites route through it, and the comprehension yields 31 ids on `dmath/ch06`. Recorded so the "missing %" change does not land; the real symptom (four gate groups contributing nothing) is P0-5.

## 8. Handoff

- [ ] 8.1 Hand §3.1, §3.2 and §3.3 to the next change that touches
  `workbench-content-governance`, since all three change what an ingest is
  allowed to accept and write.
- [ ] 8.2 Hand §2 to whoever owns the `pipeline/` layering decision, and do not
  author requirements for those items before that decision exists.
- [ ] 8.3 Re-check §1 and 3.10 against `content-dedup-and-audit` when it lands: its audit
  command is the natural place to surface the accounting and provenance
  violations, and its read-only content audit should not have to re-derive them.
- [ ] 8.4 Hand P0-5/P0-6 to the same `pipeline/` decision as §2: until the sweep
  runs again (2.5/2.6), no course may cite `validate-pool` as evidence of
  anything.
