# Task Router

Choose one governing path. Do not let older V17 task names or historical zip
packages govern current lesson-kit work.

| Task signal from user | Governing path | First required artifact |
|---|---|---|
| "extract this chapter", "build the KP pool" | `pipeline/commands/extract-chapter.md` | `pool-insert-manifest.json` |
| "extract the exercises/problems", "build the problem pool" | `pipeline/commands/extract-problems.md` | `full-problem-bank.md` |
| "show me the knowledge guide", "print the chapter guide" | `pool/scripts/print-graph.py` | existing `knowledge_points` rows |
| "make a problem set", "practice problems" | `views/problem-set/command.md` | existing `problems` rows |

## Routing Rules

- Run KP extraction before problem extraction.
- Run problem extraction before problem-set rendering.
- Problem-set v1 does not generate new problems; it records gaps.
- The student-facing problem set hides KP IDs and solutions.
- The solution file mirrors problem numbering and marks missing solution text as `待补`.
