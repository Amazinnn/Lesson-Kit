# Agent UI v1 — Design Baseline

Status: **accepted v1 baseline**  
Decision date: 2026-10-15

This note freezes the first implementable Agent UI shape. It is intentionally a baseline, not a claim that the interface is final.

## Core invariant

- The **central Lesson Kit page remains primary**.
- The **right Agent rail remains conversation-first**.
- Tool progress, approvals, long-running work and artifacts appear only when runtime state requires them.
- Transient work UI must not become permanent chrome.
- Agent surfaces reuse Lesson Kit's existing **Soft Mondrian** palette and tokens. The Agent rail does **not** establish an independent dark theme.

## Presentation states

| Runtime need | Primary presentation |
| --- | --- |
| ordinary conversation / idle | Agent rail only |
| short tool call | inline Tool Call Card; optional replaceable Activity Float |
| tool failure | semantic failure Tool Call Card; raw diagnostics folded; recovery actions visible |
| sustained multi-step work | Bottom Dock for current milestones while conversation remains usable |
| completed handoff-worthy result | Agent Artifact card; Adaptive Split may preview the latest artifact |
| risk / low-reversibility action requiring consent | Approval Gate temporarily replaces the normal composer |

Automatic auxiliary-surface selection is state-driven. If the user has explicitly collapsed auxiliary work, long-running work and artifacts must not force the surface back open.

## Surface rules

### Activity Float
A small replaceable top-right activity surface for short-lived work. It is not a task dashboard and does not accumulate historical cards.

### Bottom Dock
A temporary lower surface in the central view for sustained work. It shows current milestones and the latest status, not raw provider events. The Agent rail remains available during the task.

### Adaptive Split
A temporary split of the central workspace used to preview the latest Agent Artifact without taking over navigation. The current Lesson Kit page remains present; opening the artifact's canonical page is an explicit user action.

### Approval Gate
A decision surface for an action that needs explicit user consent. While active, it replaces the normal composer with the reason, impact and approve/deny actions. It is not a generic confirmation for every tool call.

## Tool and artifact distinction

A **Tool Call Card** represents execution activity. It shows a semantic label, concise outcome and state; raw parameters/logs are folded behind explicit inspection.

An **Agent Artifact** represents a result worth handing off or revisiting, such as a generated practice paper. Artifact completion does not automatically navigate away from the user's current page.

## Visual baseline

Use the existing `workbench.css` tokens and Soft Mondrian semantics:

- warm paper / paper-shade surfaces;
- ink structural lines;
- blue for primary actions and active information;
- yellow for warnings / approval emphasis;
- red for failures or destructive-risk emphasis;
- existing success green for successful execution state.

Status must never rely on color alone; retain text and/or geometry cues.

## Explicit non-goals for v1

- no independent dark Agent theme;
- no permanent tool dashboard;
- no raw protocol-event wall;
- no hidden chain-of-thought exposure;
- no automatic page navigation when an artifact finishes;
- no approval prompt for ordinary reversible tool activity.
