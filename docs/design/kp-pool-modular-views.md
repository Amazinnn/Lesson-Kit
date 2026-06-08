# lesson-kit Design: Knowledge Pool & Modular Views

**Date:** 2026-06-08
**Status:** Brainstorming phase — decisions recorded

## Architecture

```
Source Material (PDF/PPT/…)
    │
    ▼
  Extraction Layer ──→ pool/knowledge/    Knowledge Point Pool
                      pool/questions/     Question Pool
    │
    ▼
  View Layer ──→ First-Pass Overview / In-Depth Lesson / Problem Set / Exam Paper / …
```

**Core principle:** Extract once, render in any form. Knowledge points and questions are persistent assets; views are optional consumers.

## KP Pool Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `kp_id` | string | Unique identifier |
| `knowledge_item` | string | KP name/title |
| `source_location` | string | Source material location (page/section). Low usage frequency but retained. |
| `knowledge_type` | enum | Primary type: concept-property / method-modeling / formula-calculation / algorithm-process / code-implementation / system-timing / lab-implementation / memory-recall. Extensible. |
| `secondary_knowledge_type` | enum | Auxiliary classification index (analogous to non-PK MySQL index). Optional. |
| `related_kp_ids` | list | Bidirectional links between KPs. Reserved for future knowledge graph use. |
| `importance` | enum | `core` / `supplementary` / `optional` |
| `learning_action` | string | Learning action description (distinguish/memorize/apply/analyze…). Used for review guidance. |
| `difficulty` | int | 1–5 scale |
| `fragile` | bool | Whether this KP is easily confused or error-prone. |

### Excluded from KP Pool (view-layer responsibility)

- `quick_absorption` — view decides length and style
- `checkpoint_question` — maintained independently in question pool
- `writing_view_primary` / `rendering_intent` / `forbidden_rendering` / `student_visible_title`
- `estimated_time` — determined by the student
- `minimum_mastery_standard`
- `mcq_viability`

## Question Pool (to be designed)

- Questions maintained independently from KPs.
- KP references questions via `kp_id`.

## Learning Cache Package (Spark)

Separate design, recorded in `memory/learning-cache-package.md`.
Purpose: carry learning state across breaks in time, space, or focus.

## Architectural Changes from V17

V17 was a fixed 3-stage pipeline: First-Pass → Lesson → Exam Training.
lesson-kit replaces this with:

```
Source → Extraction → Pool Layer (KP + Questions) → View Layer
```

- Pool layer is persistent (checked into repo alongside source materials).
- Views are generated on demand from the pool.
- No fixed set of view types; no limit on number of views.
