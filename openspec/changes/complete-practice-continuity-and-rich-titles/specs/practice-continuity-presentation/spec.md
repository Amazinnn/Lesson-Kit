## Purpose

Defines the observable 未完成练习与标题呈现 behavior for the Lesson Kit course workflow, preserving explicit data ownership, learning evidence and verifiable normal-entry outcomes.

## ADDED Requirements

### Requirement: Unfinished practice is retained by execution

Every unfinished Paper execution SHALL be discoverable at practice start without a count or age eviction limit. Reopening a Paper SHALL continue the same unfinished execution by default. Explicit clear SHALL remove only that execution and its drafts.

#### Scenario: One unfinished execution is cleared

- **WHEN** the learner clears unfinished Paper A while B is also unfinished
- **THEN** A leaves the continuation list while original A, history and B remain usable

#### Scenario: A late draft arrives

- **WHEN** an old client sends a draft after its execution was cleared
- **THEN** it cannot resurrect the cleared execution

### Requirement: Titles render safely and preserve source

All content-title display surfaces SHALL support the existing safe Markdown and LaTeX feature set. Editing, renaming, cancellation and unchanged saving SHALL preserve the authored source rather than rendered DOM text.

#### Scenario: A formula title is renamed without edits

- **WHEN** the user opens a formula-bearing title and saves unchanged
- **THEN** the exact original source is retained

#### Scenario: The title is displayed in multiple places

- **WHEN** a title appears in a list, detail and resumed practice
- **THEN** the same safe rich content is rendered consistently

### Requirement: Practice resumes the intended context

Default startup SHALL restore the last course and recoverable learning position and explicit targets SHALL take precedence. Unaffected practice SHALL continue during content edits without input loss.

#### Scenario: An explicit target is supplied

- **WHEN** the launcher receives a different explicit course
- **THEN** the explicit course opens instead of the last used course
