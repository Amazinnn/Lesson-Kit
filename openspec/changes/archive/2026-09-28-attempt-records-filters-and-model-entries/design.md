# Design — Durable records, source filters, and model entries

## Records: one row per answer, linked at rating time

The practice loop has two moments: **submit** (the browser knows the answer
text, the chosen options, and — for objective items — the verdict) and
**rate** (1–5, possibly minutes later in batch mode). The design keeps each
moment honest:

- submit → `POST /attempts` inserts one `problem_attempts` row with status
  `answered` and returns its id; nothing else moves. Progress, schedule, and
  signals still change only through the rating flow, so a submission that is
  never rated cannot distort learning state.
- rate → `/feedback` carries `attempt_id`; the domain validates that the
  attempt belongs to the item (one authority in `feedback._apply`, so the Agent
  path inherits it too), and `feedback_events.attempt_id` — which until now
  only the Agent path used — becomes the join for every reader.

Readers decorate, they do not re-derive: `problem_detail` and the new
`records_overview` left-join the rating onto the attempt. The verdict column is
the browser's objective grading; a 综合题 answer stores `answer_text` with a
NULL verdict because the workbench does not grade formal problems.

**Migration**: the status CHECK cannot grow by `ensure_columns`, so a rebuild
copies every column the old shape actually has (the table evolved:
`answer_text`, then `verdict`/`choices`), then the column adder no-ops. An
un-migrated pool degrades in kind — the row lands with status `new` and no
verdict — because a failed practice write would be worse than a partial one.

## Filters: dimensions, not another query language

Three list dimensions join the existing single-value filters. Within a
dimension the values OR (any of the papers I tick), across dimensions they AND
(final ∧ 2023). `evidence_docs` matches case-insensitive substrings of
`source_evidence` — substring, not equality, because the two real pools write
evidence in two different shapes and because a learner types fragments ("CC98",
"期末模拟") rather than exact keys.

The **document key** is the one new rule: an `.md`-style path wins verbatim, a
教材 row folds into the single key 教材 (its evidence is per-problem and has no
document identity), anything else degrades to its first segment. `pull-facets`
counts rows per value from the pool itself, so the panel never offers a filter
that selects nothing, and the counts double as honest empty-state signals.

The browser popup persists per workspace in sessionStorage and merges with the
existing one-shot `include_ids`: picked search results ride `include_ids`
(union), dimensions ride `filters`. Flash-card pulls are untouched — cards have
no provenance axes worth filtering yet.

## Model entries: a name is not a harness

bridges.json grows an optional `models` list. Entries are resolved against the
discovered harnesses at read time (command, budgets, and launch flags come from
the harness; the entry contributes the display name, the model id, and optional
extra args), so an entry whose harness is missing is skipped rather than
erroring, and an empty list falls back to the historical one-entry-per-harness
picker.

The conversation gains a `model` field. `_run_turn` overrides the harness
dict's model with it, so print-mode providers get `--model` per turn and the Pi
RPC process launches with it on the next turn. `set_model` discards the cached
RPC process immediately — a stale process would silently keep the old model.
The native session id is preserved; if the provider refuses a cross-model
resume (probed at launch), the bridge drops the session once, starts fresh, and
discloses that in the conversation stream — the mirror keeps everything.

A raw model id is accepted for the same harness (it must be one argv token);
an entry name is free text and resolves to its model, so `DeepSeek V4` is a
legal display name.

## Non-goals

- No editing or deleting of attempt records — the ledger is append-only.
- No auto-grading of 综合题 (verdict stays NULL there); grading remains the
  browser's local comparison against the stored answer key.
- The filter popup stays on the practice page; the graph page keeps its own
  state filter.
- No cross-workspace records aggregation; a workspace is one course.
- No hot model swap mid-turn: the running turn finishes on the model it
  started with.
