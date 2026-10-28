## MODIFIED Requirements

### Requirement: Bundled Lesson Kit drill skill

Lesson Kit SHALL distribute the material-bounded drill skill and its local
terminology together as a Bundled Lesson Kit Skill in its installed package.
Every new Pi process launched by the Lesson Kit Bridge, in print or RPC mode,
SHALL receive exactly one argument loading that bundled skill when enabled, including when
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
- **THEN** it keeps its current resources until its accepted turn ends; the next dispatched turn refreshes managed discovery and retains the native session
- **AND** active work is not interrupted to reload the skill

## ADDED Requirements
### Requirement: Teaching instructions preserve authorized ongoing work
The prompt SHALL prioritize explicit messages, task continuation, explicit referents and only then page defaults. It SHALL supply global requirements, continuity excerpts, Skill catalogs and page data in separate labelled sections. It SHALL require actual tool success before reporting saved content. Persistent instructions in available conversation history SHALL remain applicable until revoked, and skill/excerpt content SHALL not masquerade as new user authorization.
#### Scenario: Task crosses knowledge points
- **WHEN** an authorized task needs other knowledge points
- **THEN** the Agent is instructed to read appropriate data proactively without requesting read permission or restricting itself to page focus
