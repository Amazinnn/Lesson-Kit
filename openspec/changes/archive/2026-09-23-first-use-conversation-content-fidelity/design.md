# Design — first-use conversation and content fidelity

## Verified first-use evidence

The read-only audit covered `大学物理乙II`, `conv-001`, eight completed Pi
turns, and `pool/c01.db`:

- Prompt text imposed `一次产出 3–6 条`; the ingest gates themselves had no
  six-item limit. `_extract_action` applied only the first valid action block.
- `check_intent` came from a fixed browser regex and mechanically gated
  `check_ingest`; a follow-up such as `继续` was unreliable without a trigger.
- Conversation ingest supported only flash cards and micro quizzes. All 29
  imported exercises became `single_choice` micro quizzes with
  `origin_kind=adapted_problem`; exercise 12-25 was absent.
- The pool contained 8 knowledge points, 29 problems, 5 unrolled-back batches,
  no attempts/feedback/schedule rows, and no figure files. Foreign keys and
  SQLite integrity were clean.
- Agent messages and linked problems already used safe Markdown subsets, but
  neither parser handled tables.
- Every turn called `subprocess.Popen`; `--session` preserved logical context,
  but the OS process restarted and had no Windows no-window flags.
- Installed Pi 0.85.1 documents persistent `--mode rpc` with strict LF JSONL,
  prompt/abort commands, streamed events, and session persistence.

## Micro Quiz scope

Micro Quiz remains a normal problem type beside calculation, proof, modeling,
and the other existing types. The existing `综合题 / 小测 / 判断 / 闪卡`
practice entries remain unchanged, and micro subtypes remain
`yes_no / single_choice / multiple_choice`.

Timeline recorded for future maintainers:

1. On 2026-08-27 the owner proposed AI-generated simple judgement and choice
   practice rather than generated comprehensive subjective problems.
2. The project named and implemented `micro-quiz-content` on 2026-08-28.
3. On 2026-08-29 the former card-like short-question mode was named `micro`
   when `flash_card` was reserved for true key/value memory cards.
4. Check's first phase used flash cards plus micro quizzes because those gates
   existed; formal problem generation/import was deferred.
5. The later prompt incorrectly expanded that first-phase limitation into the
   only conversational problem-import path.

This change corrects step 5. It does not rename, remove, or globally migrate
Micro Quiz.

## Automatic append-only content actions

The browser removes `check_intent` keyword regex gating. A syntactically valid,
governed append-only action returned by the Agent executes automatically. The
system prompt remains responsible for emitting an
action only when the learner requests new content. Ordinary replies containing
no action perform zero writes.

Automatic actions may add knowledge points, formal problems, micro quizzes,
flash cards, and figures. Updating or deleting existing content, rolling back a
batch, and applying difficulty ratings still require an explicit learner
instruction. All managed database/filesystem writes continue through Lesson
Kit gates; raw SQL remains forbidden.

Provider file tools remain unrestricted across the local filesystem in every
conversation, as explicitly chosen by the owner. Such external writes are not
Lesson Kit-managed and are not covered by batch backup or rollback. Lesson Kit
must not claim otherwise; its managed runtime, pool, staged manifests, and
figure destinations remain workspace-scoped.

## Staged atomic content bundle

Large content is not embedded in the answer. The Agent writes a complete
manifest under `.lessonkit/jobs/conv-NNN/`; the structured action references
that file. The staged manifest remains with the conversation until the
conversation is deleted.

One `content-bundle` may contain:

- new knowledge points needed by the imported content;
- formal problems, micro quizzes, and/or flash cards;
- required source figures and the final Markdown text that references them.

There is no fixed item-count ceiling. The server loads the staged file, rejects
paths outside that conversation's jobs directory, validates every id/reference,
source field, problem type, figure byte/path, and destination conflict, creates
one recoverable backup, then applies the database rows and figure copies as one
logical batch. Any invalid item or missing required image yields zero writes.
The Agent repairs the complete staged manifest from itemized errors and reruns
the entire check; bad items are never silently dropped.

The owner explicitly declined a deterministic source-coverage gate. Therefore
“all imported” remains an Agent-written claim and is not guaranteed to catch
omissions such as the observed exercise 12-25. This limitation must be visible
in product/developer documentation.

## Source and solution fidelity

`source_kind`, `origin_kind`, and problem type remain independent:

- importing a textbook exercise without a transformation preserves its text,
  numerical conditions, answer form, and `origin_kind=source_problem`;
- Micro Quiz is used only when the source is already that type or the learner
  explicitly requests a micro adaptation;
- generated simple choice/judgement questions remain allowed and use
  `origin_kind=generated_grounded`.

OCR spelling, formula, and line-break errors may be corrected only by checking
the PDF/original page; wording, values, options, and answer form are otherwise
preserved. New Agent-managed problems require visible `source_evidence`.

Store a source-provided short answer separately from the detailed `solution`.
A source-provided detailed solution is labelled as source material. An AI
explanation is generated only when requested, enters without a separate
semantic audit as chosen by the owner, and is visibly labelled `AI 生成解析`.
Legacy rows remain nullable/compatible.

Natural language selects the content type. Result cards state the final asset
types and counts; no new type-selection panel is added.

## Figures and rollback

Source files may be read from any local path. Supported images are copied byte
for byte into the existing `.lessonkit/figures/{course}/{chapter}/` area; they
are not cropped, enhanced, converted, or redrawn. The pool stores only logical
paths, and final problem Markdown references those paths.

Knowledge points, problems, and their figures share one bundle boundary. A
diagram-dependent problem is not inserted without its image. On rollback, the
database rows/references are restored and every file created only by that batch
is immediately deleted if no surviving row references it. Shared referenced
files remain.

## Rich-text parity

Extend both the browser `richText` renderer and server `_render_markdown` with
the same safe subset: headings, ordered/unordered lists, blockquotes, emphasis,
code, links, images, inline/display math, and GFM tables. Table cells use the
same escaping/inline rules, and tables scroll locally on narrow surfaces. Raw
HTML remains rejected. Reuse shared fixtures; add no Markdown dependency.

Linked problems render full Markdown, stored images, and a concise visible
source line. Solution reveal distinguishes source answer/source solution from
an AI-generated explanation.

## Pi RPC and hidden provider processes

Pi changes from print-per-turn to one `pi --mode rpc` process per conversation:

1. Start it in the conversation workspace with configured model/session data.
2. Frame commands and responses using strict LF-delimited JSONL.
3. Send correlated `prompt` commands while preserving the existing serialized
   turn rule, normalized activities, event files, and 350 ms browser polling.
4. Cancel through RPC `abort`; terminate/kill only when abort fails.
5. Keep the process for 30 idle minutes. There is no simultaneous-process cap.
6. Close on idle expiry, conversation deletion, or server shutdown; resume the
   saved native session when starting again.
7. Retry one launch/handshake failure before the prompt is accepted. Never
   replay a prompt after acceptance because tools may already have caused side
   effects.

All provider child processes, not only Pi RPC, use Windows hidden/no-window
creation flags. A hidden process is an independent requirement from Pi process
reuse; neither may be used as evidence for the other.

## Real workspace remediation

Implementation and complete isolated acceptance precede all real data changes.
After acceptance passes, the executing Agent is authorized to repair the real
physics workspace without a further confirmation:

1. Create and report recoverable pool and figure backups.
2. Recheck batch-001 through batch-005 for attempts, feedback, schedule rows,
   and other dependencies. Stop without mutation if any now exist.
3. Roll back the five erroneous problem batches and delete only their now-
   unreferenced figure files.
4. Preserve and source-review the existing eight knowledge points; add missing
   knowledge points inside the replacement content bundle.
5. Reimport textbook exercises in their original types, with original images,
   source evidence, and source answers. AI explanations remain on demand.
6. Preserve `conv-001`. Reopened result cards query current batch state, show
   `已回滚`, and expose no second rollback action.

The owner chose Agent prose rather than a mechanical coverage report, so this
remediation cannot claim deterministic proof that every source exercise was
included.

## Acceptance boundary

- A 30-item staged bundle produces one batch id and remains all-or-nothing.
- A keyword-free append action executes; a reply without an action writes zero.
- Formal textbook exercises retain their type; explicit micro requests still
  create working micro content and the four practice entries remain unchanged.
- Missing images block the bundle; successful images render beneath the linked
  knowledge point and unreferenced files disappear on rollback.
- Both rich-text surfaces pass identical table/math/image/escaping fixtures.
- Three Pi turns use one PID, abort works, idle restart resumes context, a
  post-acceptance crash is not replayed, and no provider shows a Windows console.
- Development acceptance uses a copied physics workspace. Only after every
  automated and real-copy check passes may the authorized real remediation run.
