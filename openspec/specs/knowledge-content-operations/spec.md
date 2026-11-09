# knowledge-content-operations Specification

## Purpose
Defines the observable 内容与知识点能力成熟化 behavior for the Lesson Kit course workflow, preserving explicit data ownership, learning evidence and verifiable normal-entry outcomes.
## Requirements
### Requirement: Typed knowledge queries

Knowledge-point queries SHALL filter existing knowledge_type values and search titles, bodies, experience summaries and provenance text. Basic bulk reads SHALL return knowledge-point content and classification. Associated-problem queries SHALL match any selected associated knowledge point and deduplicate problems.

#### Scenario: Only experience contains the keyword

- **WHEN** the requested text occurs only in the experience of a matching knowledge point
- **THEN** the knowledge point is found once

#### Scenario: A problem has two matching associations

- **WHEN** two associated knowledge points match the selected type
- **THEN** the problem appears once

### Requirement: Practice-derived method knowledge

Within the stated course scope, the Agent SHALL support persistent authorization to create reusable methods and models with explicit applicability, prioritize reuse of existing equivalent knowledge points, and append applicable original-problem associations while retaining valid existing associations.

#### Scenario: A model is absent from textbook headings

- **WHEN** practice supports a reusable model with valid conditions
- **THEN** the model can be created through the governed knowledge-point path

#### Scenario: Equivalent content already exists

- **WHEN** the proposed model is substantively equivalent to an existing knowledge point
- **THEN** the existing identity is reused and valid content or associations are extended

#### Scenario: Classification is uncertain

- **WHEN** the user requests classification of a specified chapter and evidence is insufficient for some items
- **THEN** supported classifications are completed only in scope and uncertain items retain their state

#### Scenario: A method changes problem associations

- **WHEN** a method adds a previously absent knowledge-point association
- **THEN** the full objective difficulty group is invalidated through the common content update path; an unchanged association retains its rating

### Requirement: Chapter moves preserve references

A Knowledge-point Chapter Move SHALL support same-course reassignment while preserving stable identity, associated problems, formal relations, experience and learning history. Old identifiers SHALL remain resolvable.

#### Scenario: A practiced knowledge point moves

- **WHEN** a knowledge point with relationships and attempts is reassigned to another chapter
- **THEN** all existing references and history remain usable and chapter reads show the new assignment

### Requirement: Independent valid content changes

Bulk direct edits and governed content input SHALL commit independent valid units, retain invalid units and their dependents, and support corrected retries without duplicate content. Explicit successful-batch undo SHALL be unavailable.

#### Scenario: One item is invalid

- **WHEN** two independent valid edits accompany an invalid edit and its dependent
- **THEN** the two valid edits complete and the other items remain unchanged

#### Scenario: A correction is submitted

- **WHEN** failed items are corrected and resubmitted with completed items
- **THEN** completed entities are reconciled and only necessary changes apply

#### Scenario: Corrected input repeats an auto-ID knowledge point

- **WHEN** an unchanged auto-ID item exactly matches one current knowledge point in its resolved chapter
- **THEN** the existing entity is reported without a new write, its local key can resolve dependent units, and only newly written units enter the batch counts; ambiguous matches are refused

#### Scenario: New dependencies cross chapter order

- **WHEN** valid problems or cards reference new knowledge points in another chapter, including mutually referring chapters
- **THEN** actual knowledge-point writes precede dependencies regardless of chapter ordering and each applied chapter retains its own batch

#### Scenario: Cross-chapter provenance cannot be recorded

- **WHEN** a chapter batch or snapshot fails within a connected cross-chapter dependency component
- **THEN** that uncommitted component and its newly published figures roll back, no dangling dependency survives, and disconnected chapters can complete

#### Scenario: A malformed micro-quiz has a valid neighbour

- **WHEN** a micro-quiz patch contains a non-object item alongside a valid independent item
- **THEN** the malformed item is reported and the valid item can complete

#### Scenario: Partial outcomes reach the conversation

- **WHEN** independent units complete while other submitted units fail
- **THEN** the public receipt, conversation history, next-turn context and result card retain the actual failure reasons and applied counts; a zero-write result is not represented as a successful batch

### Requirement: Content quality precedes targeted use

Content preparation SHALL preserve source meaning and specified scope, distinguish structural validity from semantic verification, and exclude unresolved questionable items from the targeted practice set while allowing independent verified items.

#### Scenario: Chapter numbers are misleading

- **WHEN** a structurally valid association is unsupported by the source content
- **THEN** it is not presented as a verified mapping

#### Scenario: The learner is actively typing

- **WHEN** a content update affects the current question
- **THEN** the current input survives and presentation updates at a natural interaction boundary
