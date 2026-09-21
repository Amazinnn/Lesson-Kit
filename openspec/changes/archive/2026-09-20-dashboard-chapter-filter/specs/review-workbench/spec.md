## MODIFIED Requirements

### Requirement: Workspace registry

Each lesson-kit folder is a workspace. The registry maps a workspace name to a
folder path, its pool database, and its active course/chapter. A workspace can
be registered, listed, and opened (web shell or CLI), and a registered
workspace SHALL appear in the hub with its pool statistics. Hub statistics
SHALL be counted over the workspace's whole course pool — every chapter present
in that pool — regardless of the active chapter lens.

A workspace SHALL register exactly one pool database, and that database SHALL
live inside the workspace folder. Registration SHALL ignore ingest backups
(`*.db.ingest-backup`, `pool/backups/*`) when choosing the pool, SHALL refuse a
folder whose remaining candidates are several databases unless one of them is the
explicitly named course, and SHALL refuse to register a folder or a database that
another registered workspace already owns. Re-registering the same name for a
different folder SHALL be refused instead of silently replacing the existing
entry. The active chapter SHALL be an identifier (lowercase ASCII letters, digits,
and dashes) or empty, and a value that is not SHALL be refused with the reason.

#### Scenario: Register a folder as a workspace

- **WHEN** the user runs `lesson-kit init <path>` on a folder with lesson-kit structure (a `pool/*.db` file or `lessonkit.py`)
- **THEN** the folder is added to the registry under its folder name and the hub lists it with pool row counts

#### Scenario: List workspaces with statistics

- **WHEN** the hub page is loaded
- **THEN** it shows each registered workspace with its course, chapter, knowledge-point count, problem count, due-item count, and weak-signal count, all counted course-wide

#### Scenario: Hub statistics ignore the chapter lens

- **WHEN** the active chapter lens selects a chapter that holds only part of the pool
- **THEN** the hub card still reports course-wide counts and does not shrink to the selected chapter

#### Scenario: A backup is never adopted as the pool

- **WHEN** a folder holds both a live pool and an ingest backup (or a pre-readiness copy of the pool)
- **THEN** registration selects the live pool and the backup file is left untouched

#### Scenario: Several pools ask which one

- **WHEN** a folder holds more than one candidate pool database and none matches the named course
- **THEN** registration fails and lists the candidates with the command that selects one

#### Scenario: Two workspaces cannot share a pool

- **WHEN** a folder whose pool database is already registered under another workspace name is registered again
- **THEN** the registration is refused and both existing entries stay intact

#### Scenario: A name collision does not silently replace

- **WHEN** `init` runs with a name that is already registered for a different folder
- **THEN** the existing registration is left unchanged and the command fails with the conflict

#### Scenario: An invalid chapter is refused

- **WHEN** a chapter value that is not a lowercase ASCII identifier is passed to `init` or `use`
- **THEN** nothing is stored and the error explains the accepted form

### Requirement: Course and chapter switching

The active chapter SHALL act as a course-wide view lens with two writers over
one registry value: the dashboard chapter switch (the human surface) and
`lesson-kit use <course> <chapter>` (the agent-and-script surface). An empty
chapter SHALL explicitly mean the whole course, with no chapter filter. A
switch SHALL NOT create, move, or delete any data; subsequent page and prefix
queries SHALL resolve against the new lens; and no pool file SHALL be modified.
When several workspaces are registered, the workspace SHALL be selectable
explicitly. An unknown workspace or a missing argument SHALL be reported as an
error without changing stored state. A course value that is not a lowercase
ASCII slug SHALL be rejected with the reason, since it prefixes every content
id.

#### Scenario: Switch the active chapter from the dashboard

- **WHEN** the learner turns the chapter switch on and selects a chapter in the top bar
- **THEN** subsequent views and practice resolve against that chapter and the registry records it as the active chapter

#### Scenario: Turn the lens off

- **WHEN** the learner turns the chapter switch off
- **THEN** views and practice resolve against the whole course pool and the registry records an empty active chapter

#### Scenario: Switch the active chapter

- **WHEN** the user runs `lesson-kit use <new-course> <new-chapter>`
- **THEN** subsequent hub, page, and prefix queries resolve against the new course and chapter, and no pool file was modified

#### Scenario: Switch to the whole course from the CLI

- **WHEN** the user runs `lesson-kit use <new-course> ""`
- **THEN** the registry records an empty active chapter and views resolve against the whole course pool

#### Scenario: Switching never happens silently on error

- **WHEN** the user names a workspace that is not registered or omits an argument
- **THEN** the command fails with a clear message and the registry is unchanged

#### Scenario: A chapter that is not an identifier is refused

- **WHEN** a chapter value that is not a lowercase ASCII identifier is passed to `use`
- **THEN** nothing is stored and the error explains the accepted form

## ADDED Requirements

### Requirement: Chapter list derived from pool content

The workbench SHALL list the chapters of the active course by deriving them from
the content identifiers already in the pool (knowledge points, problems, cards).
It SHALL NOT introduce a chapters table, a chapter registry, or any chapter
registration step. A chapter SHALL appear as soon as content carrying its
identifier exists and SHALL disappear only when that content does.

#### Scenario: Chapters come from content

- **WHEN** the pool contains knowledge points or problems whose identifiers carry two different chapter segments
- **THEN** the chapter switch lists exactly those two chapters for the active course

#### Scenario: A new chapter appears without registration

- **WHEN** a batch of content for a chapter that has no content yet is applied to the pool
- **THEN** the new chapter appears in the switch without any additional command

#### Scenario: An empty pool offers no chapter

- **WHEN** the pool holds no content for the active course
- **THEN** the switch reports no chapters and the whole-course lens remains the only state

### Requirement: Chapter lens scoping

The chapter lens SHALL scope the reading surfaces — the knowledge point list
page, the knowledge point detail page, the knowledge graph page, and the
practice page's suggestion range — and SHALL NOT constrain the practice
selection (the staged list). A selection MAY span chapters and SHALL survive
chapter switching. Ordering rules (weakness first, due reminders as background)
SHALL remain unchanged inside any lens, and no item SHALL ever be locked or
hidden by the lens beyond the reading scope it sets. The pages SHALL name the
lens they are showing, so a whole-course page never claims to be a chapter.

#### Scenario: Views follow the lens

- **WHEN** a chapter is selected
- **THEN** the knowledge point list, the knowledge point detail, the knowledge graph, and the practice suggestions show only that chapter's items

#### Scenario: Selection survives switching

- **WHEN** the learner has staged knowledge points from two chapters and then switches the lens to one of them
- **THEN** the staged list still holds both chapters' knowledge points and practice still draws from the full selection

#### Scenario: Whole-course lens shows everything

- **WHEN** the lens is off
- **THEN** every chapter's items are visible on the reading surfaces

#### Scenario: The pages say which lens is active

- **WHEN** the lens is off, and again when a chapter is selected
- **THEN** the page header names the whole course in the first case and the chapter in the second, and the knowledge-point heading says 全部知识点 or 本章知识点 to match
