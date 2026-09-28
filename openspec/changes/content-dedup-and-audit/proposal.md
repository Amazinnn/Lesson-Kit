## Why

The 2026-09-26 repair of the ADS workspace pool (`ads-pool-content-repair`)
had to be carried out largely with external scripts, because the tool cannot
see or prevent the defects that made that 896-row bank unusable:

- **Nothing compares content.** The ingest gates refuse a duplicate key, a taken
  problem id, and a colliding figure destination, but no path compares the
  problem text itself. The same question arriving from two source files is
  stored twice, silently. The ADS bank holds 14 byte-identical duplicate groups
  (18 surplus rows, including cross-chapter duplicates) and roughly 134
  near-duplicate rows; no gate, command, or report could have listed them, so
  the duplicate census had to be written as an external script against a raw
  dump of the pool.
- **No read-only content audit.** Nothing can answer "how many fragment rows,
  option-less choice items, unmarked objective items, unresolved figure
  references, or unreferenced figure files does this pool hold". That number is
  what sizes a repair and what proves, later, that nothing regressed. The
  existing formal-problem audit serves a different purpose (mapping exam points
  to pool items), and `doctor` checks the environment, not content.
- **The in-place edit path is weaker than the ingest path.** `micro-quiz-content`
  requires the same contract to be enforced "for the parts the patch touches",
  but `plan_problem_patch` applies neither `LABEL_FIELD_LIMITS` nor the markup
  safety check. A patch can therefore store what ingest would refuse — an
  over-long `display_title` that blows up the practice header, or an HTML tag
  outside `<sup>`/`<sub>`. The repair has to pre-validate its own manifests to
  work around this.

## What Changes

- **Content identity dedup at ingest.** A content bundle SHALL compute a
  normalized identity per problem item and refuse an item whose identity
  already exists in the target course scope or earlier in the same manifest,
  reporting the colliding problem id. Normalization SHALL cover exactly the
  variants the ADS import produced — case, whitespace, punctuation, `$…$`
  rendering variants, and export noise such as `(3分)` / 作者 / 单位 lines — and
  SHALL NOT truncate the stem. Similar-but-different stems SHALL NOT collide:
  `docs/FUTURE-DEVELOPMENT-NOTES.md` requires keeping them.
- **Read-only pool content audit.** One command reports, per selected scope,
  duplicate content groups, fragment rows, objective items carrying no practice
  mode, problems without a display title, figure references that do not resolve
  to a file, and figure files that no item references. It writes nothing, is
  machine-readable, and exits non-zero when a requested check reports findings,
  so a repair pass and a later regression check can be gated on it.
- **Patch validation parity** (conformance fix, no requirement change):
  `plan_problem_patch` applies the label bounds and markup safety check the
  ingest gate already applies, restoring the behaviour
  `micro-quiz-content`'s patch clause already requires.
- **No stem length bound for objective items.** The 800-character ceiling
  (2026-09-25, raised from 200 for the same reason) still diverted real
  判断题/单选题 into 综合题: the ADS repair found 14 objective rows over it, seven
  of them long multi-assertion items whose options are inlined in the stem.
  Length is not an answering-form property, so the ceiling is removed from the
  micro-quiz contract, the ingest gate, the patch path, and the bridge contract
  text; the option-count bound (2–6) and the one-knowledge-point rule stay.
- No schema change: a derived answer key's origin is recorded in the existing
  `source_answer` field, so the repair needs no new column.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-content-governance`: adds two requirements — ingest-time content
  identity dedup, and the read-only pool content audit.
- `micro-quiz-content`: the stem length bound is removed from the content
  contract (a long objective item stays a micro quiz), and the
  contract-violation scenario no longer lists a length violation.

## Impact

- **Code**: `workbench/ingest/__init__.py` (content-bundle gate: identity check
  and itemized refusal reasons), a new pure-rules module for normalization and
  identity next to the existing `workbench/domain/` rules,
  `workbench/data/` (audit queries and the fragment/figure checks),
  `workbench/cli/main.py` (the audit command and its exit code).
- **Docs**: `docs/FUTURE-DEVELOPMENT-NOTES.md` (dedup moves from deferred to
  specified), `docs/GLOSSARY.md` (content identity, content audit),
  `docs/PRODUCT-MANUAL.md` (the audit command and what each finding means),
  `FILE_CONTRACT.md` (the new refusal reason).
- **Tests**: dedup (same item across sources, same item twice in one manifest,
  rendering variants collide, similar items both pass, nothing written on
  refusal) and audit (findings reported with ids, zero writes, exit code,
  clean pool).
- **Data**: none — this change adds no migration and rewrites no row. The ADS
  pool repair that motivated it is `ads-pool-content-repair`.
- **Compatibility**: a manifest that used to store a duplicate now fails its
  gate; that is the intent, and it is reported per item with the colliding id.
