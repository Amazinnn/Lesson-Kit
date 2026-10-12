"""On-demand runtime contracts for external Lesson Kit Agents.

These contracts are intentionally discoverable from the installed Python package so
an Agent working inside a learner workspace does not need the Lesson Kit source
checkout.  The turn prompt carries only a small map and tells the Agent to load the
relevant topic before performing a specialized action.
"""

import argparse


TOPICS = ("commands", "attempts", "practice", "actions", "content")


_CONTRACTS = {
    "commands": r"""Lesson Kit command contract

- Read Lesson Kit data proactively when it is relevant to the learner's question. Reading needs no confirmation.
- Mutate Lesson Kit data only when the learner explicitly asks to change content or submit a learning result.
- Use `lesson-kit <command> --help` when argument order or flags are uncertain; do not guess.
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
  "items": [
    {
      "problem_id": "...",
      "answer_text": "<transcribed learner answer>",
      "note": "<grading note>",
      "rating": 1
    }
  ]
}

`rating` is the existing learner self-rating scale (1-5), not an exam score. Omit it if uncertain. `check` validates without writing; `apply` records the batch atomically. To replace an already Agent-recorded attempt use:
`lesson-kit attempts <工作区名> correct <attempt-id> --input <file>`.

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
`problem_text` (required), `problem_type` (required; machine enum: calculation/proof/modeling/explanation/experiment/design/application/counterexample/other; Chinese display label is explanatory only: proof = 证明题), `kp_ids`, `source_kind`, `origin_kind`, `source_evidence` (required), `source_answer`, `solution`, `solution_origin`, `display_title`, `display_summary`, `exam_year`, and `figures`.
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
Patchable fields include `problem_text`, `solution`, `kp_ids`, `problem_type`, `source_kind`, `origin_kind`, `source_evidence`, `source_answer`, `solution_origin`, `display_title`, `display_summary`, `exam_year`, `practice_modes`, `micro_quiz`, and `answer_key`. Problem ids are immutable. Difficulty still uses `lesson-kit difficulty`. Converting an existing problem to yes/no/choice uses `practice_modes` plus the full `micro_quiz` object (`quiz_type`, `options`, `answer_key`, `error_reason`); preserve source option text rather than rewriting it. In-place patching preserves all learning history and is rollbackable by ingest batch.

16. Server validation is authoritative. If any item is invalid the entire submitted manifest is zero-write and the result names the failures. Correct the causes and resubmit the complete manifest; do not silently drop rejected items or claim success. If turn context includes `last_check_outcome`, obey it: after success do not duplicate the same content; after a rejection fix the reported causes before resubmission.
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
