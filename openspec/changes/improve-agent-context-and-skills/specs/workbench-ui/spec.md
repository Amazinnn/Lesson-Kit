## ADDED Requirements
### Requirement: Settings expose shared Agent instructions and Skills
Settings SHALL expose a global instructions editor with save/clear, Skill list/detail, import local file or package path, explicit replacement, enable/disable and deletion of managed copies. Built-in source and non-deletability SHALL be visible. Failures SHALL retain edited input and report errors rather than claim success. Global scope and next-turn activation SHALL be stated. No per-conversation Skill selection or online install SHALL be added.
#### Scenario: Manage without changing originals
- **WHEN** a learner imports, inspects, disables or deletes a copied Skill
- **THEN** settings reflects the persisted result while originals remain unchanged
