## Why

Three gaps surfaced when the learner started using the pool they had just repaired:

1. **Their own practice leaves no trace.** The browser practice flow writes
   ratings, progress, and schedule — but never an attempt row. The answer text,
   the chosen options, and the objective 对/错 verdict live only in
   sessionStorage and vanish when the tab closes. Nothing in the database holds
   a verdict at all, and there is no history view: the nav has three pages, and
   `GET /problem/{id}` already returns attempts the browser never renders. Only
   Agent-recorded attempts (`lesson-kit attempts`) were durable.
2. **来源 cannot be filtered.** `source_evidence` — the only field that carries
   document-level identity (one 期中合集 holds 90+ items across nine papers
   sharing a year) — is unfilterable in every surface. The CLI has
   `--source-kind`/`--exam-year`, but the browser sends no source filters at
   all and the API does not even accept `exam_year`. And `source_kind` /
   `exam_year` are never displayed.
3. **The model is welded to the provider label.** The picker showed
   `pi · deepseek/deepseek-v4-flash` because bridges.json pins one model per
   harness; a conversation locked onto it for life and the PATCH endpoint only
   renamed.

Plus two rendering facts found on the way: micro-quiz options are
`escapeHtml`-only (38% of the choice questions in the repaired pool show raw
`$O(\log^2 N)$` in the option, rendered correctly in the reveal right below),
and the live verdict line concatenates `error_reason` into innerHTML unescaped.

## What Changes

- **Every answer persists.** The practice page POSTs one attempt per submission
  (`answer_text`, `choices`, `verdict`); the rating later links back through
  `attempt_id`, so a record reads as one row: what was answered, judged how,
  rated what. The attempts table gains `verdict`/`choices` columns and an
  `answered` status (additive migration; un-migrated pools degrade to a plain
  row, never an error).
- **Two history views.** A server-rendered 做题记录 page in the nav (newest
  first, verdict badge, stars, answer excerpt, per-problem filter), and a
  「历史作答」 collapsible in the practice reveal (already-returned
  `detail.attempts`, now rendered with the linked rating).
- **Multi-dimension source filtering.** `pull.select` gains list-valued
  dimensions (`source_kinds`, `exam_years`, `evidence_docs`): OR within a
  dimension, AND across them, evidence matched case-insensitively. A new
  `GET /pull-facets` derives the dimensions from the pool's actual rows with
  counts; a document-key rule folds both real pools' evidence formats into one
  key per paper. The CLI grows `--source-evidence` (repeatable) and repeatable
  `--source-kind`; the API accepts `filters` and the previously missing
  `exam_year`.
- **A filter popup on the practice page.** One button opens a floating panel:
  checkbox groups per dimension (with counts), a search box that finds problems
  and picks them into `include_ids`, selections persisted per workspace, and an
  active-filter count badge.
- **Named model entries.** bridges.json gains an optional `models` list
  (`{name, provider, model, args?}`); the picker shows the learner's own names
  and falls back to one entry per harness when absent. A conversation records
  its model, launches every turn with it, and an in-chat switcher (a select in
  the chat header) changes it for the next turn — the cached RPC process is
  discarded, the native session is resumed, and a provider that refuses a
  cross-model resume falls back to a fresh session with an honest notice.
- **LaTeX fixes.** Options render through `richText`; the verdict line escapes
  and renders its error reason.

## Capabilities

### Modified Capabilities

- `review-workbench`: durable attempt records, the records page, and the
  list-valued source filters.
- `workbench-ui`: the records page, the filter popup, options/verdict math
  rendering, and the in-chat model switcher.
- `ai-teacher-bridge`: model entries, the per-conversation model, and the
  in-chat switch.

## Impact

`pool/scripts/pool_schema.py` (additive migration), `workbench/data/{pool,
attempts,queries}.py`, `workbench/domain/{pull,facets,feedback}.py`,
`workbench/server/{api,app,pages}.py`, `workbench/server/static/workbench.{js,
css}`, `workbench/bridge/{conversation_providers,conversations}.py`,
`workbench/registry.py`, `workbench/cli/main.py`, `workbench/surface.py`, and
the usual documentation set. No learning-write semantics change: the rating
flow remains the only writer of progress, schedule, and signals.
