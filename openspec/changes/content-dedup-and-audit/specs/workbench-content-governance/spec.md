## ADDED Requirements

### Requirement: Content identity dedup at ingest

Content that is the same problem as an item already in the pool, or as an item
earlier in the same manifest, SHALL be refused rather than stored a second
time. The gate SHALL derive a normalized content identity from the problem
text — case folded, whitespace collapsed, punctuation dropped, math delimiters
and rendering variants canonicalized, and export noise such as score, author,
and unit lines removed — and SHALL NOT truncate it, because a truncated key
cannot separate a duplicate from a similar item that diverges later in the
stem. Two items whose identities match SHALL be a duplicate regardless of their
keys, their source files, or their chapters, and the refusal SHALL name the
colliding problem id together with its source evidence so the caller can see
which row already covers the content. Two stems that differ beyond those
variants SHALL NOT collide: similar-but-different items are deliberately kept.
A duplicate refusal SHALL follow the existing all-or-nothing rule — every reason
reported per item, nothing written, no batch recorded.

#### Scenario: The same item arrives from a second source file

- **WHEN** a manifest item's normalized identity equals an existing problem's identity in the same course scope
- **THEN** the gate refuses that item with a reason naming the existing problem id and nothing is written

#### Scenario: The same item appears twice in one manifest

- **WHEN** two items of one manifest share a normalized identity
- **THEN** the gate reports an itemized reason for each and the manifest is not applied

#### Scenario: Rendering variants still collide

- **WHEN** an item and an existing problem differ only in whitespace, punctuation, `$…$` rendering, or export noise
- **THEN** they are treated as the same problem and the second one is refused

#### Scenario: Similar items are kept

- **WHEN** two stems differ beyond the normalized variants
- **THEN** both are accepted, and neither is reported as a duplicate

#### Scenario: A duplicate never half-writes

- **WHEN** a manifest mixes a duplicate with otherwise valid new items
- **THEN** the duplicate is reported and no item of that manifest reaches the pool

### Requirement: Read-only pool content audit

The workbench SHALL provide a read-only audit over the workspace's pool that
reports content-hygiene findings for the selected scope: duplicate content
groups with their identity and member problem ids; fragment rows (a row whose
text is the continuation of another row, such as a stem that begins with a
connective or a row holding only an option label); objective items that carry
no practice mode; problems without a display title; figure references that do
not resolve to a file; and figure files that no item references. The audit
SHALL write nothing, SHALL be machine-readable, and SHALL exit non-zero when a
requested check reports findings, so a repair pass and a later regression check
can be gated on it.

#### Scenario: A pool with findings is reported

- **WHEN** the audit runs over a pool holding a duplicate group and an objective item without a practice mode
- **THEN** both findings are reported with their problem ids and the command exits non-zero

#### Scenario: A clean pool reports nothing

- **WHEN** the audit runs over a pool with no findings for the selected checks
- **THEN** it reports an empty finding set and exits zero

#### Scenario: The audit changes nothing

- **WHEN** the audit runs over any pool
- **THEN** row counts, row contents, and the recorded batch list are identical before and after

#### Scenario: The audit sizes and verifies a repair

- **WHEN** the audit runs with all checks before a content repair, and again after
- **THEN** its findings can be grouped by chapter and defect class both times, so the repair can be planned from the first run and verified against the second
