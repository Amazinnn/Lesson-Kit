## ADDED Requirements

### Requirement: Paper practice presentation state remains independent

Each ordinary-problem Paper's unfinished run SHALL independently retain Answer Reveal Timing, ordered items, position, inputs, stuck marks, submission locks, reference-view facts and self-ratings. Switching Paper, pausing, refreshing or restarting browser/service SHALL restore confirmed state without clearing another Paper. Timing SHALL remain fixed until completion. Completed answer sheets SHALL remain associated with original runs rather than reconstructed from new runs or current drafts. Existing stale content/container validation SHALL continue; restoration SHALL NOT silently remap unavailable problems or override an approved reset.

#### Scenario: Switch Papers and reload
- **WHEN** the learner partly fills A in whole-Paper mode, answers B in per-item mode, reloads and returns to A
- **THEN** both retain separate choices, positions, inputs, locks, marks and ratings without new runs or implicit submission

#### Scenario: Container changes after saving input
- **WHEN** a content or structure revision invalidates a saved practice write
- **THEN** existing stale-write/reset rules apply and the UI reports readiness without silently losing input or claiming successful submission

#### Scenario: A repeated Paper has two answer sheets
- **WHEN** a completed Paper is started again
- **THEN** new progress cannot overwrite the previous answer sheet or self-ratings
