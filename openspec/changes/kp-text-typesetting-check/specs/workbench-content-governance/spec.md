## ADDED Requirements

### Requirement: Knowledge-point body paragraph typesetting check

A knowledge point's `body` is read as a sequence of paragraphs, where a
paragraph is a run of text between blank lines. A paragraph's **visible
characters** are what remain after inline math (`$$…$$`, `$…$`) and backticked
code are removed for the purpose of counting; nothing else is removed, and the
text itself is never altered.

A typesetting check SHALL report a knowledge point when any of its `body`
paragraphs falls outside the band **40 to 300 visible characters**, and SHALL
report each such knowledge point once, naming the number of paragraphs past
each bound together with the longest and shortest measured paragraph.

The check is read-only and advisory:

- it SHALL write nothing and SHALL NOT refuse, reject, or exit non-zero because
  of a typesetting finding;
- it SHALL NOT modify, normalize, reflow, split, trim, or reorder any text;
- it SHALL NOT state a preferred typesetting — no target paragraph length, no
  recommended section vocabulary, no suggested split point, no template;
- it SHALL report measured facts only, each recomputable from the stored text.

A paragraph whose visible character count is zero — a paragraph consisting only
of inline math or only of code — SHALL NOT count as too short. The band
applies to `body` only; `fragile` and `learning_action` are excluded because a
reminder note and an action line are written as short units by design.

The check SHALL be available at two points, sharing one measurement rule and one
report wording: over the content bundle before it is applied, and over the pool
after it is applied. Where no bundle is available to check, the check SHALL say
so in the report rather than reporting nothing, so that a caller can tell "checked
and clean" from "nothing to check".

#### Scenario: A body holding an over-long paragraph is reported with its measurement

- **WHEN** a knowledge point's body holds a paragraph of 1750 visible characters
- **THEN** the report names the knowledge point with one paragraph past the upper bound and the longest measured paragraph, and the run completes as it would for a clean pool

#### Scenario: A body holding a too-short paragraph is reported separately

- **WHEN** a knowledge point's body holds a paragraph of 12 visible characters
- **THEN** the report names the knowledge point under the short-paragraph section with its measured length, and the run completes as it would for a clean pool

#### Scenario: A paragraph of only math or only code is not a short paragraph

- **WHEN** a knowledge point's body holds a paragraph whose entire content is a display formula or a code block, leaving zero visible characters
- **THEN** that paragraph is not counted as too short

#### Scenario: A body violating both bounds appears once

- **WHEN** one knowledge point's body holds both an over-long and a too-short paragraph
- **THEN** it appears once in the over-long section, which comes first, and the row states how many paragraphs are past each bound

#### Scenario: A body inside the band is not reported

- **WHEN** a knowledge point's body holds only paragraphs between 40 and 300 visible characters
- **THEN** it is absent from both sections

#### Scenario: The check states no preferred typesetting

- **WHEN** the check reports any finding
- **THEN** the report contains no target length, no recommended section names, and no suggested split point, and every number in it is recomputable from the stored text

#### Scenario: The check changes nothing

- **WHEN** the check runs over a pool or a content bundle
- **THEN** row counts, row contents, and the recorded batch list are identical before and after

#### Scenario: Nothing to check is stated rather than implied

- **WHEN** the pre-apply check runs over a scope that has no content bundle
- **THEN** the report says that scope had nothing to check, which is distinguishable from a scope that was checked and found clean
