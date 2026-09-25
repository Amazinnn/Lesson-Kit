# practice-set-export Specification

## Purpose
TBD - created by archiving change practice-set-export-and-cli-audit. Update Purpose after archive.
## Requirements
### Requirement: Practice set composition

One `pull` invocation SHALL compose a practice set from any combination of: a
knowledge-point scope (explicit knowledge points, else the active chapter lens),
explicitly named problem ids, conditional filters (source kind, origin kind,
source group, exam year, and the objective difficulty range), and learner-driven
selection (weak knowledge points, due problems, and previously wrong problems).
Conditional filters SHALL restrict the candidate set only. An explicitly named
problem id SHALL be included even when it fails the filters, and learner drivers
SHALL be unioned rather than intersected. Every selected problem SHALL report
why it entered the set — `scope`, `weak`, `due`, `wrong`, or `explicit` — and
unfilled knowledge-point demand SHALL remain reported as a shortage instead of
being filled with invented content. Composing a set SHALL perform zero writes.

#### Scenario: Compose by scope and filters

- **WHEN** the Agent composes a set for one chapter restricted to textbook final-exam problems of one exam year
- **THEN** only problems matching every condition are returned, each carrying its reason

#### Scenario: Add one problem explicitly

- **WHEN** the Agent appends a single problem id that the current filters reject
- **THEN** that problem is in the set with reason `explicit` and the filters still govern the remaining problems

#### Scenario: Compose from wrong problems

- **WHEN** the Agent composes a set from previously wrong problems
- **THEN** the set contains the problems whose progress or latest attempt marks them wrong, each with reason `wrong`

#### Scenario: Shortage stays honest

- **WHEN** the scope holds fewer problems than requested
- **THEN** the result reports the shortage per knowledge point and no problem is invented

### Requirement: Practice manifest

A practice manifest SHALL be UTF-8 JSON carrying the set title, the ordered
problem ids with their reasons, and the composition inputs needed to reproduce
the selection. It SHALL be validated before use — every named problem SHALL
exist and no problem SHALL repeat — and reading a manifest SHALL perform zero
writes. Re-running the same manifest SHALL reproduce the same ordered set. A
manifest is an input, not a stored practice: no practice-set row, table, or
index SHALL be added to the pool.

#### Scenario: Manifest round-trip

- **WHEN** a composed set is written as a manifest and read back
- **THEN** the same ordered problems are selected again and no pool row changes

#### Scenario: Invalid manifest is refused

- **WHEN** a manifest names an unknown problem or names one twice
- **THEN** the command exits nonzero, names the offending problem, and writes nothing

### Requirement: Rendered practice set and solutions

The CLI SHALL render one practice set into two files: a student set and its
solution file, sharing continuous numbering. The student file SHALL contain
problem text only — no answer, no solution, and none of `problem_id`, `kp_id`,
or `source_kind`. The solution file SHALL mirror the numbering exactly and SHALL
write `待补` for a problem whose solution is not
stored. Rendering SHALL be deterministic, and figure references SHALL remain the
stored relative references rather than copied bytes. A single-chapter set SHALL
default to the documented problem-set artifact paths, and a set spanning
chapters SHALL be placeable in a caller-chosen directory and base name.

#### Scenario: Print a single-chapter set

- **WHEN** the Agent prints a composed chapter set with default paths
- **THEN** the two files appear at the documented output paths, the student file leaks no answer or internal identifier, and both files number identically

#### Scenario: Print a set spanning chapters

- **WHEN** the Agent prints a set spanning several chapters into a chosen directory and base name
- **THEN** the two files use that directory and base name and the numbering still matches

#### Scenario: Missing solution

- **WHEN** a selected problem has no stored solution
- **THEN** the solution file writes `待补` at that number and the student file is unaffected

### Requirement: Zero-write practice-set check

`pull <workspace> check --input <file|->` SHALL validate a manifest and preview
the rendered set without writing anything. It SHALL report the selected count,
the shortage per knowledge point, the problems without a stored solution,
duplicate or unknown problems, and any answer or internal identifier that would
leak into the student file. Failures SHALL be itemized and SHALL exit nonzero.

#### Scenario: Check writes nothing

- **WHEN** the Agent checks a valid manifest
- **THEN** the report lists the selected problems and their gaps and neither a table row nor a file is written

#### Scenario: Leakage is caught

- **WHEN** a plan would place an answer or an internal identifier into the student set
- **THEN** the check fails and names the offending item

