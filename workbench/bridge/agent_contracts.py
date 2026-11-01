"""On-demand runtime contracts for external Lesson Kit Agents.

These contracts are intentionally discoverable from the installed Python package so
an Agent working inside a learner workspace does not need the Lesson Kit source
checkout.  The turn prompt carries only a small map and tells the Agent to load the
relevant topic before performing a specialized action.
"""

import argparse


TOPICS = ("commands", "attempts", "practice", "actions", "content", "grading")


_CONTRACTS = {
    'grading': r'''Lesson Kit independent part-grading contract

Read `lesson-kit grading <workspace> get --attempt-id N` and `history --attempt-id N`.
Only explicit subjective submission or an explicit learner review request authorizes grading writes.
Use `apply --input FILE` or `withdraw --input FILE`. JSON fields: attempt_id (integer),
problem_id, part_id, content_revision (integer), expected_revision (0 for create),
operation_id (stable unique readable identity), payload (omit on withdrawal).
Payload fields: answer_conclusion, process_conclusion, extracted_answer, reference_answer,
reference_reasoning, reference_origin, feedback. Conclusions: correct, wrong,
needs_confirmation, unprovided; process additionally supports partially_correct.
Proof permits process only. Preserve original learner response; extraction must come only
from it. Unprovided final results cannot have an extraction. No synthesized overall verdict.
Reference origin is source or agent_derived; never overwrite authored references.
Stale content or expected revisions are refused. Reuse the operation identity for an exact
retry, never for changed input. Withdrawal appends history and removes current conclusions.
`retry --attempt-id N` retries a failed Agent job without another Attempt. Grading does not
create ratings or alter mastery, signals, schedules or original submissions. Ordinary explanation
is read-only; do not use attempts correct to revise subjective grading.
''',
    "commands": r"""Lesson Kit command contract

- Read Lesson Kit data proactively when it is relevant to the learner's question. Reading needs no confirmation.
- Mutate Lesson Kit data only when the learner explicitly asks to change content or submit a learning result.
- Use `lesson-kit <command> --help` when argument order or flags are uncertain; do not guess.
- Keep internal manifests, scratch files and default generated artifacts in the workspace's `.lessonkit/intermediate/`. Write outside `.lessonkit/` only when the learner explicitly requests an export destination; honor that destination. Read course source materials in place.
- Workspace-aware commands put the workspace name immediately after the command, for example:
  `lesson-kit data <工作区名> create kp --input <清单文件>`.
- For a historical learning claim, query `lesson-kit evidence <workspace> kp <kp-id> [--limit 1..20]` (default 8, maximum 20). It is read-only and reports recorded facts; do not infer learning labels from missing evidence.
- Run each Lesson Kit command independently. Do not hide its exit status with pipelines, `|| true`, or a chained `&&`/`;` command.
- If output is too long, redirect the complete output to a file and read that file. If an exit code is needed, inspect it explicitly.
- Claim success only when the command actually exits successfully and its result contains no error. On failure, report the real reason, consult help, and make at most a corrected independent invocation rather than repeating the same broken command.
""",
    "attempts": r"""Lesson Kit attempt contract

Use this contract only when the learner explicitly asks to record, submit, correct, or grade an answer. Ordinary tutoring and reading existing answers are zero-write operations and MUST NOT create attempts or ratings.

Record / check a batch:
`lesson-kit attempts <工作区名> check|apply --input <manifest.json>`

Manifest:
{
  "request_id": "<caller-stable, human-repeatable id>",
  "paper_id": "ps-001",
  "items": [
    {
      "problem_id": "...",
      "answer_text": "<transcribed learner answer>",
      "note": "<grading note>",
      "rating": 1
    }
  ]
}

`paper_id` is optional. Without it the attempt is a free record. With it, every problem must already belong to that saved Paper; `apply` binds the answers to that Paper's progress in the same transaction. A selected Paper is updated in place; another Paper's unfinished progress is updated as its parked checkpoint; a Paper with no unfinished progress gets a new `on_submit` checkpoint without becoming the active practice. An item that already had an answer or stuck mark gets a new attempt appended and re-linked; the old attempt remains. An import without `rating` changes only Paper execution progress, not learning signals, states, progress, or schedule. Completion follows the Paper's existing mode: a legacy Paper may archive when its last pending item is imported; `per_item` / `on_submit` still wait for the learner's explicit submission.

`rating` is the existing learner self-rating scale (1-5), not an exam score. You MAY choose it yourself when the learner asks you to record or evaluate an answer; the learner does not need to supply a number. Omit it if uncertain. `check` validates without writing; `apply` records the batch atomically. To replace an already Agent-recorded attempt use:
`lesson-kit attempts <工作区名> correct <attempt-id> --input <file>`.

Manage evaluations:
`lesson-kit feedback <工作区名> get --event-id <id>`
`lesson-kit feedback <工作区名> list [--item problem|kp|card] [--id ...] [--attempt-id ...]`
`lesson-kit feedback <工作区名> add --item problem|kp|card --id <id> [--rating 1-5] [--note ...] [--attempt-id <id>]`
`lesson-kit feedback <工作区名> update --event-id <id> --expected-rating 1-5|none --expected-note "<current note>" [--rating 1-5] [--note ...]`
`lesson-kit feedback <工作区名> delete --event-id <id> --expected-rating 1-5|none --expected-note "<current note>"`

An evaluation is one `feedback_events` row. Read it first with `get`/`list`; update and delete require the current expected rating and note and refuse a stale write. Update changes only rating/note; delete is a hard delete. Neither replays signals, current states, progress, or schedule; use `attempts correct` only when you need to replace the whole attempt and recompute its effects. You may choose or change the 1-5 rating yourself when the learner asks you to manage an evaluation. Adding an evaluation for an attempt that already has one is refused; update the existing event id instead.

When a problem in the learner's answer is missing from the pool, do not invent it inside the manifest. First create it through the governed content path under an existing knowledge point with truthful source evidence, then append it to the Paper:
`lesson-kit papers <工作区名> append <ps-NNN> --problem <problem-id>`
(`append` is idempotent, adds the problem at the end, and preserves existing progress), then import the attempt. Never edit `.lessonkit/practice-sets/ps-*.json` directly.

Learner answer images stay in their own directories. `lesson-kit attempts <工作区名> sources list` lists allowed directories. Read those files in place when needed; do not copy/upload them and do not store image paths or image bytes in the attempt manifest.
""",
    "practice": r"""Lesson Kit practice-selection contract

Use `lesson-kit pull <工作区名>` when the learner asks to compose a practice set or paper. Discover exact flags with `lesson-kit pull --help` instead of guessing.

Selection map:
- `--kp`: knowledge-point scope. With no explicit wider scope the active chapter lens applies; disabling the chapter lens permits whole-course selection.
- `--problem`: force one named problem into the set; repeatable.
- source filters: `--source-kind`, `--origin-kinds`, `--exam-year`, `--source-evidence`.
- learner-evidence drivers: `--weak`, `--due`, `--wrong`.
- remembered text/source: `--search-stem`, `--search-source`; whitespace-separated terms are AND-matched within that field.
- difficulty filters use the CLI's documented difficulty flags.
- `--plan <file>` writes a reproducible plan, `--check` validates without writing, `--print <dir>` writes student and solution Markdown sheets. Selection and printing do not mutate the learning pool.

When importing a sourced exam problem, `exam_year` is optional. If known it begins with a four-digit year (for example `2023` or `2023-2024秋冬`) and is at most 20 characters. Do not invent it.

`pull --plan` exports a practice manifest and `pull --print` writes Markdown sheets; neither saves a reusable paper in Workbench. When the learner asks to save the paper or make it available in Workbench, run `lesson-kit papers <workspace> save --input <manifest>`. Report a managed save only after exit 0 and a JSON receipt; use its title, count, and `url`. A job artifact or printed sheet alone is not proof that the paper appears in the saved-paper list. Export-only requests remain supported.

To add one missing problem that the learner actually answered to an existing Paper without resetting its progress, run `lesson-kit papers <workspace> append <ps-NNN> --problem <problem-id>`. It appends at the end, preserves every existing item's state, attempts and drafts, and is idempotent. `papers update` remains the membership/order edit that resets unfinished progress and requires the existing preview confirmation; do not use it for the missing-problem repair.
""",
    "actions": r"""Lesson Kit UI action contract

Only emit an action when the learner's request actually calls for it. Ordinary tutoring answers contain no action block.

Practice selection:
```lessonkit-action
{"type":"replace_practice_selection","kp_ids":["知识点ID"]}
```
Use only when the learner explicitly asks to select or arrange practice scope.

Goal form prefill:
```lessonkit-action
{"type":"prefill_goal_form","title":"…","kind":"stage|long_term","start_date":"YYYY-MM-DD或空","deadline":"YYYY-MM-DD或空","description":"…"}
```
Use only when the learner is asking from the goal-form flow; ordinary chat must not prefill it.

Managed Paper handoff:
```lessonkit-action
{"type":"paper_artifact","practice_set_id":"ps-001","title":"…","item_count":12,"summary":"…"}
```
Emit this only after a successful `lesson-kit papers <workspace> save --input <manifest>` command returns exit 0 and a JSON receipt. `practice_set_id`, title, and item count must come from that receipt; do not invent them. Do not include or invent a navigation URL in the action. The Workbench derives its own native destination, and presenting an Artifact must not navigate automatically.

Saved Paper update proposal:
```lessonkit-action
{"type":"paper_update_proposal","practice_set_id":"ps-001","problem_ids":["题目ID"]}
```
Emit this only when the learner explicitly asks to change the question membership or order of one existing saved Paper. Use the explicit Paper id and ordered problem ids. This proposes an update for the learner to review; it does not apply it. Do not run a `papers update` command or edit the saved Paper file directly. The Workbench computes the current impact and waits for the learner's separate approval click. Title/description edits, question-level resets, and ordinary Paper UI operations keep their existing workflows.

After any successful write, summarize the affected objects and user-accessible result in concise Chinese. Do not expose shell commands, SQL, tool logs, hashes, database keys, or implementation-only paths as the learner-facing evidence.
""",
    "content": r"""Lesson Kit content action contract — content-bundle v2 (2026-09-25)

Load this contract before creating or modifying managed learning content. It supersedes remembered older content-bundle conventions.

1. Creation uses a `lessonkit-action` content-bundle, not direct `lesson-kit ingest` or database writes from the conversation. Pure valid additions may auto-apply; modification, deletion, rollback, and difficulty rating still require the learner's explicit request.

2. A large manifest is first written unchanged to the `staged_manifest_dir` supplied in the current turn context. The action then contains only:
```lessonkit-action
{"type":"content-bundle","staged_manifest":"<file name>"}
```
A small manifest may be inline. Inline `kind:"content-bundle"` and `type:"content-bundle"` are both accepted.

3. A content-bundle may contain `knowledge_points`, `problems`, and/or `flash_cards`, with no item ceiling. One manifest may span any number of chapters. Every item supplies `chapter`, or inherits the manifest top-level `chapter`; if neither exists that item is explicitly rejected. An item's chapter must agree with any explicit content id. The server allocates ids per chapter and records one batch per chapter, but validation/backup/write is atomic for the entire manifest: one invalid item means zero writes for the whole manifest.

4. Every content-bundle block in one Agent reply is processed in order. If the learner requested several chapters in one turn, submit them all in that turn (one cross-chapter manifest or several blocks); do not stop after one chapter and wait for “继续”. If a prior turn only completed part of the request, continue the missing part without making the learner repeat the request.

5. Every item has a manifest-local unique `key`. Problem `kp_ids`, flash-card `kp_id`, and figure references use keys to refer to newly-created items. Managed content ids are allocated by the server; do not invent or reuse ids.

6. Knowledge-point fields:
`knowledge_item` (required), `knowledge_type`, `importance`, `source_location`, `body`, `graph_label`, `related_kp_ids`, `fragile`.

7. Problem fields:
`problem_text` (required), `problem_type` (required; machine enum: calculation/proof/modeling/explanation/experiment/design/application/counterexample/other; Chinese display label is explanatory only: proof = 证明题), `kp_ids`, `source_kind`, `origin_kind`, `source_evidence` (required), `source_answer`, `solution`, `solution_origin`, `display_title`, `display_summary`, `exam_year`, `figures`, and `parts` (mixed-problem parts — see item 18).
`problem_type` describes the disciplinary form, not the practice UI. A yes/no or choice problem normally uses `problem_type:"other"`; the practice form is expressed by `quiz_type`, `options`, and `answer_key`.

8. Practice forms:
Every new micro quiz and in-place micro conversion MUST map to exactly one knowledge point in `kp_ids`.
- ordinary/open problem: omit `quiz_type`; learner self-rates.
- yes/no: `quiz_type:"yes_no"`; options may be omitted (是/否 default).
- single choice: `quiz_type:"single_choice"`, 2–6 options.
- multiple choice: `quiz_type:"multiple_choice"`, 2–6 options.
Objective source problems are still imported when the source has no known answer key: omit `answer_key` or set it to null. Such problems are not auto-graded and remain learner-self-rated. When an answer key exists, include it; `error_reason` is required when an answer key is present and optional otherwise. Do not convert a keyless objective source problem into an open problem merely because the key is unavailable. A `yes_no` answer key is one scalar option string (`是` or `否`); a `single_choice` answer key is one scalar option string contained in `options`; a `multiple_choice` answer key is a non-empty list of option strings drawn from `options`.

9. Source fidelity: textbook/exam source problems preserve the original wording, numbers, options, answer form, and disciplinary problem type. Use `origin_kind:"source_problem"`. Only convert/adapt when the source itself is objective or the learner explicitly asks for an adaptation; adapted problems use `origin_kind:"adapted_problem"`, generated grounded objective problems use `generated_grounded`. OCR mistakes may be corrected against the source page; otherwise do not silently rewrite source text.

10. Figures: in `problem_text`, reference `![](figure:f1)` and declare `figures:[{"key":"f1","source_path":"<local path>"}]`. The server copies original bytes into its managed figure directory without cropping or conversion. A declared-but-unused figure or a missing required figure rejects the whole manifest.

11. Put a short source answer in `source_answer`. Put a detailed worked explanation in `solution`. AI-generated explanation uses `solution_origin:"generated"`; an original source explanation uses `solution_origin:"source"`.

12. Flash-card fields: `kp_id`, `front` (<=100 chars), `back` (<=300 chars), `source_evidence` (required), optional `topic_label`. `directions` is either `["forward"]` (default) or `["forward","reverse"]`.

13. Content creation does not carry difficulty fields and does not automatically suggest or queue difficulty ratings. Only when the learner explicitly requests ratings should the Agent use `lesson-kit difficulty` and check before apply.

14. Value/length rules: source problem stems have no artificial length ceiling. `options` contains 2–6 distinct strings; when `answer_key` exists it must point to allowed option(s); yes/no uses the default 是/否 pair. `display_title` <=80 chars, `display_summary` <=200 chars. Use the multiplication sign `×`. Body text may contain headings, lists, quotes, code, links, images, inline math, and GFM tables.

15. Existing problems are modified in place with a `problem-patch`; do not delete and re-import them merely to add an answer key, source metadata, objective-practice fields, or extracted options. Shape:
{"kind":"problem-patch","items":[{"problem_id":"…", ...fields to change...}]}
Patchable fields include `problem_text`, `solution`, `kp_ids`, `problem_type`, `source_kind`, `origin_kind`, `source_evidence`, `source_answer`, `solution_origin`, `display_title`, `display_summary`, `exam_year`, `practice_modes`, `micro_quiz`, `parts`, and `answer_key`. Problem ids are immutable. Difficulty still uses `lesson-kit difficulty`. Converting an existing problem to yes/no/choice uses `practice_modes` plus the full `micro_quiz` object (`quiz_type`, `options`, `answer_key`, `error_reason`); preserve source option text rather than rewriting it. In-place patching preserves all learning history and is rollbackable by ingest batch.

16. Server validation is authoritative. If any item is invalid the entire submitted manifest is zero-write and the result names the failures. Correct the causes and resubmit the complete manifest; do not silently drop rejected items or claim success. If turn context includes `last_check_outcome`, obey it: after success do not duplicate the same content; after a rejection fix the reported causes before resubmission.

17. When repairing a Paper that is missing a problem the learner actually answered on paper, create that problem as ordinary governed content under an existing knowledge point with truthful `source_evidence`, append it to the Paper with `lesson-kit papers <workspace> append <ps-NNN> --problem <id>`, then import the attempt. Do not invent the problem, its knowledge point, or its source, and do not edit the saved Paper JSON directly.

18. Problem parts (综合题小问): a problem MAY declare `parts`, an ordered list whose saved order is authoritative — practice renders it as saved and never reorders or splits it. One problem may mix judgment, choice, calculation and proof parts. Each part:
- required: `id` (lowercase `[a-z][a-z0-9_-]{0,63}`, unique inside the problem), `prompt` (non-empty), `type` in yes_no / single_choice / multiple_choice / calculation / proof / open_response;
- `reference_answer` and `reference_reasoning`: optional text; a proof part uses reasoning only and must not carry `short_answer` or `reference_answer`;
- `short_answer`: optional boolean marking that a concise final result can be extracted; a missing learner result stays "unprovided", never wrong;
- objective parts (yes_no / single_choice / multiple_choice) require distinct `options` (yes_no defaults to 是/否; others need at least two) and an optional `answer_key` naming them — one scalar for yes_no / single_choice, a list for multiple_choice;
- a problem without `parts` remains answerable as one legacy whole problem.

Author `parts` inside a content-bundle problem, or add/replace them with a `problem-patch` on an existing problem. Do not also declare `quiz_type` / `micro_quiz` on a problem that has `parts`. Later parts edits follow existing content-revision rules (only affected unfinished practice is invalidated) and never rewrite historical submissions. Pools created before this contract need the additive migration (`python pool/scripts/migrate-progress.py --db pool/<course>.db`) before `parts` can be stored.
""",
}


def topics():
    return list(TOPICS)


def get(topic):
    try:
        return _CONTRACTS[topic].strip() + "\n"
    except KeyError as exc:
        raise ValueError(
            f"unknown Agent contract topic: {topic}; available: {', '.join(TOPICS)}"
        ) from exc


def _parser():
    parser = argparse.ArgumentParser(
        prog="python -m workbench.bridge.agent_contracts",
        description="print one read-only Lesson Kit Agent contract on demand",
    )
    parser.add_argument(
        "topic", choices=("list", *TOPICS),
        help="contract topic, or list to discover available topics",
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.topic == "list":
        print("\n".join(TOPICS))
        return 0
    print(get(args.topic), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
