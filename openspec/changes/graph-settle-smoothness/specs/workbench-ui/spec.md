> **范围说明（事后修订）**：本 change 最初还包含了「座位在引导网格上」「层级带随 α 收紧」
> 「电荷用四叉树」「阻尼代替速度上限」「舞台降级为坐标盒」五项。它们后来被
> `graph-free-force-field` 整体取代（那里移除了层级带、把座位改为按连通性生成），
> 为避免同一件事在两份 delta 里各说一遍且互相矛盾，本文件只保留**仍然成立**的那一条。
> 其余五项的去向见 `graph-free-force-field/specs/workbench-ui/spec.md`。

## ADDED Requirements

### Requirement: A restored layout is adopted, not re-solved

When the cached layout seed matches the visible graph exactly, the workbench SHALL place
the points at their cached coordinates and stop, rather than re-solving from them. A
partially matching seed SHALL still be solved. Clearing or failing to read the cache
SHALL only cost the previous layout.

#### Scenario: Reopening the graph

- **WHEN** the learner reopens the graph page with a matching cache
- **THEN** the layout appears at the cached coordinates without further motion

#### Scenario: A partial cache

- **WHEN** only some points have cached coordinates
- **THEN** those points start where they were and the solve runs

#### Scenario: The graph changed

- **WHEN** node ids or relation endpoints, types or directions differ from the cache
- **THEN** the cache does not apply and the graph is solved from scratch
