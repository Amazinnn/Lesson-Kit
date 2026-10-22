## ADDED Requirements

### Requirement: Bundled Lesson Kit drill skill

Lesson Kit SHALL distribute the material-bounded drill skill and its local
terminology together as a Bundled Lesson Kit Skill in its installed package.
Every new Pi process launched by the Lesson Kit Bridge, in print or RPC mode,
SHALL receive exactly one argument loading that bundled skill, including when
model-specific or pinned conversation arguments are selected. The Bridge SHALL
preserve other skills, flags, native configuration, authentication and session
continuity. It SHALL NOT install files in course folders or Pi global
configuration, or rewrite provider configuration or conversation records.

#### Scenario: Installed package launches Pi

- **WHEN** an installed wheel launches Pi through the Bridge
- **THEN** the skill and terminology are available from package resources
- **AND** an absolute skill argument loads the packaged directory without manual copying

#### Scenario: Legacy managed skill argument

- **WHEN** selected Pi arguments contain the exact previously managed Lesson Kit skill directory or the bundled directory
- **THEN** the launch replaces duplicate managed skill arguments with one bundled argument
- **AND** unrelated skill paths, other flags and stored configuration remain unchanged

#### Scenario: Preserve existing process resources

- **WHEN** a Pi conversation process is already running during an upgrade
- **THEN** it keeps its current resources until a new conversation or normal idle recycling
- **AND** active work is not interrupted to reload the skill
