# Skill: Intermediate Contracts

Use intermediate files as contracts. Each file must state the decision it makes, the next step that must read it, and the blocker it creates when missing.

## Stage-Specific Workspaces

Use the correct stage:

```text
intermediate/first_pass/      source-guided first-pass lesson harness
intermediate/lesson_loop/     lessons, problem sets, answer keys, feedback revision
intermediate/exam_training/   later exam-stage workflows
```

Each stage keeps the same four layers:

- `01_inputs`: preserve source facts and evidence; do not diagnose.
- `02_analysis`: analyze learning type, knowledge, knowledge points, models, or weaknesses; do not write final prose.
- `03_plans`: decide final structure, order, rendering, examples, problem mapping, answer depth, or first-pass lesson layout.
- `04_checks`: record pass/fail, broken rule, return file/layer, forbidden repair, and repair action.

Final writing mainly reads `02_analysis` and `03_plans`. Do not load raw feedback or failed-output notes into final prose unless auditing requires it.

For V15 first-pass lessons, `intermediate/first_pass/` is mandatory. Do not place first-pass files directly under a stage-free intermediate input folder.
