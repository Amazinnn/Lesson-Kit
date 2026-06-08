# lesson-kit Design: Knowledge Pool & Modular Views

**Date:** 2026-06-08
**Status:** Brainstorming phase — decisions recorded

## Architecture

```
Source Material (PDF/PPT/…)
    │
    ▼
  Extraction Layer ──→ lesson-kit.db     (SQLite)
                          ├─ knowledge_points
                          └─ questions
    │
    ▼
  View Layer ──→ First-Pass Overview / In-Depth Lesson / Problem Set / Exam Paper / …
```

**Core principle:** Extract once, render in any form. Knowledge points and questions are persistent assets stored in SQLite; views are optional consumers.

## Storage: SQLite

**Rationale:** The pool is a long-lived knowledge base, not a temporary scratchpad. It requires real CRUD (create, read, update, delete), cross-chapter queries, and algorithmic access — all of which SQLite provides with zero server overhead.

- One `lesson-kit.db` file per chapter directory, alongside source materials
- Two tables: `knowledge_points` and `questions`
- Git-tracked alongside source PDFs
- Python `sqlite3` (stdlib) for scripting; SQL for manual inspection
- LaTeX formulas stored natively without escaping

## KP Pool Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `kp_id` | string | Unique identifier |
| `knowledge_item` | string | KP name/title |
| `source_location` | string | Source material location (page/section). Low usage frequency but retained. |
| `knowledge_type` | enum | Primary type: concept-property / method-modeling / formula-calculation / algorithm-process / code-implementation / system-timing / lab-implementation / memory-recall. Extensible. |
| `related_kp_ids` | list | Bidirectional links between KPs. Reserved for future knowledge graph use. |
| `importance` | enum | `core` / `supplementary` / `optional` |
| `learning_action` | string | Learning action description (distinguish/memorize/apply/analyze…). Used for review guidance. |
| `difficulty` | int | 1–5 scale |
| `fragile` | bool | Whether this KP is easily confused or error-prone. |
| `created_at` | timestamp | Auto-set on creation |
| `updated_at` | timestamp | Auto-set on creation, update on modification |

### Excluded from KP Pool (view-layer responsibility)

- `quick_absorption` — view decides length and style
- `checkpoint_question` — maintained independently in question pool
- `writing_view_primary` / `rendering_intent` / `forbidden_rendering` / `student_visible_title`
- `estimated_time` — determined by the student
- `minimum_mastery_standard`
- `mcq_viability`

## SQLite Schema

### Table: `knowledge_points`

```sql
CREATE TABLE knowledge_points (
    kp_id           TEXT PRIMARY KEY,
    knowledge_item  TEXT NOT NULL,
    source_location TEXT,
    knowledge_type  TEXT NOT NULL CHECK (knowledge_type IN (
                        'concept-property', 'method-modeling',
                        'formula-calculation', 'algorithm-process',
                        'code-implementation', 'system-timing',
                        'lab-implementation', 'memory-recall'
                    )),
    related_kp_ids  TEXT,  -- JSON array: ["dld-ch02-kp-003", "dld-ch02-kp-007"]
    importance      TEXT NOT NULL CHECK (importance IN (
                        'core', 'supplementary', 'optional'
                    )),
    learning_action TEXT,
    difficulty      INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    fragile         INTEGER DEFAULT 0,  -- boolean: 0 or 1
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
```

```sql
CREATE INDEX idx_kp_type       ON knowledge_points(knowledge_type);
CREATE INDEX idx_kp_importance ON knowledge_points(importance);
CREATE INDEX idx_kp_difficulty ON knowledge_points(difficulty);
CREATE INDEX idx_kp_fragile    ON knowledge_points(fragile);
```

### Table: `questions`

```sql
CREATE TABLE questions (
    q_id               TEXT PRIMARY KEY,
    question_text      TEXT NOT NULL,
    answer_key         TEXT NOT NULL,
    answer_explanation TEXT,
    kp_id              TEXT NOT NULL,
    difficulty         INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    FOREIGN KEY (kp_id) REFERENCES knowledge_points(kp_id)
);
```

```sql
CREATE INDEX idx_q_kp        ON questions(kp_id);
CREATE INDEX idx_q_difficulty ON questions(difficulty);
```

### Design notes

- `related_kp_ids` stored as JSON array TEXT — simple to read/write, queryable via `json_each()` when needed. No junction table overhead until the knowledge graph actually exists.
- `fragile` is on `knowledge_points` only — questions inherit it via JOIN on `kp_id`.
- `kp_id` naming convention: `{course}-{chapter}-kp-{NNN}` (e.g. `dld-ch02-kp-001`).

## Question Pool Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `q_id` | string | Unique question identifier |
| `question_text` | string | Question body + options (merged into one block; no type-level distinction) |
| `answer_key` | string | Correct answer |
| `answer_explanation` | string | One-sentence explanation of the answer |
| `kp_id` | string | Linked knowledge point ID |
| `difficulty` | int | 1–5 scale |

`fragile` is inherited from the linked KP (`kp_id` → KP pool), not duplicated here.

### Excluded from Question Pool

- `source_location` / `source_exercise` — not needed; `kp_id` provides sufficient tracing
- `question_type` — merged into KP pool's `learning_action`

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
