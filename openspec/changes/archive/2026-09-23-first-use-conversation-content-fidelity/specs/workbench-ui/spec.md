## ADDED Requirements

### Requirement: Rich-text surfaces share one safe feature set

Agent messages and server-rendered linked-problem text SHALL both support
headings, ordered/unordered lists, blockquotes, emphasis, code, links, images,
inline/display math, and GFM tables. Table cells SHALL use the same escaping and
inline rules, and tables SHALL scroll locally on narrow surfaces. Raw HTML
SHALL remain escaped/rejected.

#### Scenario: Pi answers with a table

- **WHEN** a Pi answer contains a Markdown header row, delimiter row, and body rows
- **THEN** the conversation renders a table rather than literal pipe text

#### Scenario: Linked problem contains rich content

- **WHEN** a linked problem contains table, math, and image Markdown
- **THEN** the knowledge-point row renders all three with the same safe semantics

### Requirement: Content results expose type, source, and rollback state

An automatically executed append action SHALL render a result card containing
the final asset types/counts, affected workspace, source summary, figure count,
batch id, backup, and current rollback state. Formal/linked problems SHALL show
concise source evidence. Solution reveal SHALL distinguish source answer,
source solution, and `AI 生成解析`.

#### Scenario: Source problem enters automatically

- **WHEN** an Agent action imports formal source problems
- **THEN** the result card states that type and every rendered problem shows its source evidence

#### Scenario: Reopen a rolled-back result

- **WHEN** a conversation is reopened after its batch was rolled back
- **THEN** the card shows `已回滚` and exposes no rollback button

