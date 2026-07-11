# Command: Generate Problem Candidates

## One-Line Purpose

Generate source-grounded practice candidates for initial checks or weak-point
remediation, pass them through independent structure and semantic gates, then
practice or explicitly import them.

## Entry Conditions

Use this command when:

- the chapter already has knowledge points in `pool/{course}.db`;
- source material has too few suitable problems;
- the learner needs `first_pass_check` or `remediation` practice.

Do not use this command for:

- exam simulation, mock papers, or automated exam-style prediction;
- ungrounded free-form question generation;
- extracting real textbook or exam questions, which belongs to
  `pipeline/commands/extract-problems.md`.

## Required Load List

```text
CONTEXT.md
FILE_CONTRACT.md
pipeline/templates/candidate-insert-manifest.md
pipeline/templates/candidate-audit-report.md
skills/problem-model-space/SKILL.md
```

## Defaults

- First-pass check: two candidates per requested KP, normally single-KP.
- Remediation: six candidates per requested signal; multi-KP candidates are
  allowed when the signal describes confusion between linked KPs.
- User-specified counts override these defaults.
- Scenario policy is `source_anchored`: change the angle, reverse the question,
  split conditions, or compare adjacent concepts without replacing the source's
  core scenario.
- Use `knowledge_relations` and current Focus Map signals as preferred context
  for remediation. They are optional context for first-pass checks.

## Workflow

1. Create the workspace:

```text
intermediate/{course}/problem_generation/{chapter}/
├── 01_inputs/
├── 02_analysis/
└── 04_checks/
```

2. Query the requested KPs. For remediation, also query the Focus Map so the
Agent sees current SQLite learner signals and audited neighbor relations.

```bash
python pool/scripts/query-pool.py --db pool/{course}.db --chapter {course}-{chapter} --view knowledge-guide
python pool/scripts/query-focus-map.py --db pool/{course}.db --course {course} --chapter {chapter} --seed <kp-id>
```

3. Build `02_analysis/candidate-insert-manifest.json` using the candidate
template. Every item must be self-contained for the learner while retaining
non-empty internal source evidence. Do not add `answer`; put answers and
explanations in `solution`.

4. Insert the manifest as draft candidates:

```bash
python pipeline/scripts/insert-candidates.py --db pool/{course}.db --manifest intermediate/{course}/problem_generation/{chapter}/02_analysis/candidate-insert-manifest.json
```

5. A separate Agent pass solves and audits every candidate against its source.
Write `04_checks/candidate-audit-report.json` using the audit template. The
learner is not the reviewer and does not approve candidates before practice.

6. Apply both gates:

```bash
python pipeline/scripts/gate-candidates.py --db pool/{course}.db --audit intermediate/{course}/problem_generation/{chapter}/04_checks/candidate-audit-report.json
```

Only candidates with script structure PASS and Agent semantic audit PASS become
`gate_passed`. A failure becomes `needs_revision`.

7. Choose either or both downstream actions:

```bash
# Practice eligible candidates without importing them.
python pool/scripts/practice-candidates.py --db pool/{course}.db --candidate {course}-{chapter}-cand-001

# Explicitly import eligible candidates into the durable problems table.
python pipeline/scripts/import-candidates.py --db pool/{course}.db --candidate {course}-{chapter}-cand-001
```

Import does not require prior practice. If practice exists, import migrates one
summary attempt and the final candidate state. Exact or near-duplicate stems
for the same KPs are blocked.

8. Validate the course pool:

```bash
python pipeline/scripts/validate-pool.py --db pool/{course}.db --course {course} --chapter {chapter}
```

## Output Checklist

```text
intermediate/{course}/problem_generation/{chapter}/02_analysis/candidate-insert-manifest.json
intermediate/{course}/problem_generation/{chapter}/04_checks/candidate-audit-report.json
candidate_problems rows with explicit lifecycle state
candidate_attempts rows when practiced
learner_signals rows after wrong or stuck attempts
problems rows only after explicit eligible import
```
