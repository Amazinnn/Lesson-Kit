## MODIFIED Requirements

### Requirement: Content results expose type, source, and rollback state

An automatically executed append action SHALL render a result card containing
the final asset types/counts, affected workspace, source summary, figure count,
batch id, backup, and current rollback state. Formal/linked problems SHALL show
concise source evidence. Solution reveal SHALL preserve source answers and useful
normal explanations without a standalone `AI 生成解析` panel. Identical detailed
solution text already shown as the answer or quiz explanation SHALL appear once.
Stored solution content and provenance SHALL NOT be deleted by this presentation change.

#### Scenario: Source problem enters automatically
- **WHEN** an Agent action imports formal source problems
- **THEN** the result card states that type and every rendered problem shows its source evidence

#### Scenario: Reopen a rolled-back result
- **WHEN** a conversation is reopened after its batch was rolled back
- **THEN** the card shows `已回滚` and exposes no rollback button

#### Scenario: Generated explanation repeats the normal explanation
- **WHEN** detailed solution text repeats the displayed quiz explanation or source answer
- **THEN** the text is not repeated in another panel, no standalone AI explanation label appears, and stored fields remain intact
