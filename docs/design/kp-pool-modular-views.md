# lesson-kit Design: Knowledge Pool & Modular Views

**Date:** 2026-06-08
**Status:** Schema finalized — knowledge_points table locked. Question pools split into three logical pools (design intent recorded, implementation deferred). Extraction pipeline and view layer design in progress.

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

## Progress Tables

### Table: `kp_progress`

Tracks the student's absorption → feedback → forgetting cycle per knowledge point.
One record per KP — overwritten on state change (UPDATE, not INSERT).

```sql
CREATE TABLE kp_progress (
    kp_id           TEXT PRIMARY KEY REFERENCES knowledge_points(kp_id),
    mastery_state   TEXT NOT NULL DEFAULT 'new'
                    CHECK (mastery_state IN (
                        'new', 'confused', 'grasping', 'stable', 'faded'
                    )),
    self_assessment TEXT  -- optional student note
);
```

### Table: `question_progress`

One table, two purposes: log every interaction (INSERT-only), carry current mastery state.
Query the latest row per `q_id` for current state.

```sql
CREATE TABLE question_progress (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    q_id          TEXT NOT NULL REFERENCES questions(q_id),
    note          TEXT NOT NULL,  -- freeform: what the student did / observed / got wrong
    mastery_state TEXT NOT NULL DEFAULT 'new'
                  CHECK (mastery_state IN (
                      'new', 'confused', 'misleaded', 'familiar', 'mastered'
                  )),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_qp_q_id ON question_progress(q_id);
```

### Design notes

- `related_kp_ids` stored as JSON array TEXT — simple to read/write, queryable via `json_each()` when needed. No junction table overhead until the knowledge graph actually exists.
- `fragile` is on `knowledge_points` only — questions inherit it via JOIN on `kp_id`.
- `kp_id` naming convention: `{course}-{chapter}-kp-{NNN}` (e.g. `dld-ch02-kp-001`).

## Question Pools (Design Intent)

The original single `questions` table is being split into three logical pools. This is a **design intent** — the schema is not yet implemented. Current `questions` table is created but left empty (chapter-companion MCQs are generated at view-render time, not stored in the pool).

### Pool 1: Chapter Companion Questions (章节伴生题)

**Storage: NOT in pool.** Generated at view-render time by the `scene-judgment-mcq` skill.

- Scene-judgment MCQs for first-pass overviews
- Lightweight, single-choice, 4 options
- Purpose: send student back to source material
- Each MCQ is linked to one KP but ephemeral — re-generated each view render

### Pool 2: Textbook Exercise Pool (课后习题池)

**Storage: SQLite table `textbook_exercises`** (future)

| Field | Type | Description |
|-------|------|-------------|
| `ex_id` | string | Unique exercise identifier |
| `exercise_text` | string | Exercise body (including sub-questions) |
| `answer` | string | Answer / solution |
| `solution` | string | Step-by-step solution (optional) |
| `kp_ids` | string | JSON array of linked KP IDs |
| `source_location` | string | Original exercise number in textbook (e.g., "Exercise 2.3") |
| `difficulty` | int | 1–5 |
| `exercise_type` | string | calculation / proof / design / analysis / ... |

### Pool 3: Exam Question Pool (历年卷题目池)

**Storage: SQLite table `exam_questions`** (future)

| Field | Type | Description |
|-------|------|-------------|
| `exam_q_id` | string | Unique exam question identifier |
| `question_text` | string | Question body |
| `answer` | string | Answer |
| `solution` | string | Step-by-step solution (optional) |
| `kp_ids` | string | JSON array of linked KP IDs |
| `exam_year` | int | Exam year |
| `exam_type` | string | midterm / final / makeup / ... |
| `difficulty` | int | 1–5 |

### Why split instead of one table?

Different question types have different:
- **Granularity**: companion MCQs are per-KP micro-questions; textbook exercises can span multiple KPs; exam questions often test cross-chapter integration
- **Lifecycle**: companion MCQs are ephemeral (generated per view); textbook exercises are persistent reference; exam questions are curated collections
- **Metadata**: textbook exercises need source numbering; exam questions need year/type; companion MCQs need none of this

When implementations begins, each pool gets its own CREATE TABLE, INSERT scripts, and query views.

## Original Question Pool Definition (kept for reference; superseded by 3-pool design above)

The following `questions` table remains in the current schema for backward compatibility during development. It will be replaced by the three-pool design when question pools are implemented.

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
