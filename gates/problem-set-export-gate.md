# Gate: Problem Set Export Gate

The problem set passes only if every problem maps to knowledge points and training targets; source exercises are preserved when required; homogeneous duplicates are handled according to coverage policy; added problems fill real coverage or transfer gaps; answers are excluded; and formatting follows the selected exercise-set plan.

| Failure | Return to | Forbidden repair |
|---|---|---|
| Problems were picked before modeling the training space | `intermediate/lesson_loop/02_analysis/problem-model-space.md` | Just adding tags after selection |
| Candidate/source exercises were filtered before solving or answer-modeling | `intermediate/lesson_loop/02_analysis/exercise-knowledge-model-map.md` | Justifying selection by surface similarity |
| Coverage gaps or duplicate clusters are unclear | `intermediate/lesson_loop/03_plans/selected-and-added-problem-list.md` | Adding random extra problems |
| Formatting/printability is inconsistent | `intermediate/lesson_loop/03_plans/exercise-set-format-plan.md` | Manual spacing edits without updating the format plan |

Fail if filtering occurred before candidate exercises were sufficiently solved or answer-modeled to compare knowledge target, condition signature, technique, representation, boundary, error lure, and training value.
