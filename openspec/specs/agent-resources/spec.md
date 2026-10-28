# agent-resources Specification

## Purpose

Provide learner-controlled global Agent instructions and local copied Skill resources across courses, without changing provider-global configuration or interrupting accepted work.

## Requirements

### Requirement: Global instructions and copied Skills are learner controlled
Settings SHALL support read/save/clear global instructions and list/detail/import/replace/enable/disable/delete Skills. Import SHALL copy a local SKILL.md directory package or Markdown file, retain support files and original bytes, and identify YAML or plain-Markdown metadata. Duplicate identities SHALL require explicit replace. Invalid paths, symlinks and unusable metadata SHALL fail without removing existing resources. Built-in resources SHALL be identifiable and disableable but not deletable. All courses SHALL share the resources, independent of browser localStorage. Changes SHALL apply at the next dispatched turn without changing accepted running work.
#### Scenario: Import and remove a package
- **WHEN** a local package is imported then deleted
- **THEN** managed copies are removed but source and provider-global files remain intact
#### Scenario: Inspect and update
- **WHEN** a duplicate import occurs without explicit replacement
- **THEN** existing bytes survive and a readable conflict is returned
#### Scenario: Global requirements
- **WHEN** instructions are saved or cleared
- **THEN** the next turn in every course sees the new text, while ordinary conversation does not edit it

### Requirement: Enabled Skills are discovered without injecting all bodies
Each turn SHALL receive enabled names, purposes and readable entry paths. The external Agent SHALL read applicable Skill instructions before acting. Native discovery SHALL be reused where available; other providers SHALL receive file-readable entries. Configuration changes SHALL not interrupt a running turn or discard native history. Import SHALL not execute package scripts.
#### Scenario: Multiple Skills
- **WHEN** several Skills are enabled
- **THEN** the catalog is available without injecting every full body, and disabled entries are absent
