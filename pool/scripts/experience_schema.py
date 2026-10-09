"""Schema migration for optional knowledge-point practice experience."""


def ensure_experience_schema(conn):
    changes = []
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='kp_experiences'"
    ).fetchone():
        conn.execute(
            """
            CREATE TABLE kp_experiences (
                kp_id TEXT PRIMARY KEY REFERENCES knowledge_points(kp_id) ON DELETE CASCADE,
                content TEXT NOT NULL CHECK (length(trim(content)) > 0),
                revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
                updated_by TEXT NOT NULL CHECK (updated_by IN ('user', 'agent')),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        changes.append("kp_experiences")
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='kp_experience_problems'"
    ).fetchone():
        conn.execute(
            """
            CREATE TABLE kp_experience_problems (
                kp_id TEXT NOT NULL REFERENCES kp_experiences(kp_id) ON DELETE CASCADE,
                problem_id TEXT NOT NULL REFERENCES problems(problem_id) ON DELETE CASCADE,
                position INTEGER NOT NULL DEFAULT 0 CHECK (position >= 0),
                PRIMARY KEY (kp_id, problem_id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX idx_kp_experience_problems_problem "
            "ON kp_experience_problems(problem_id)"
        )
        changes.append("kp_experience_problems")
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='trigger' "
        "AND name='trg_kp_experience_problem_membership'"
    ).fetchone():
        # The reference list is a subset of the formal problem.kp_ids relation.
        # Enforce that at the schema boundary too: any mutation path that removes
        # a knowledge point from a problem also removes the now-invalid reference.
        conn.execute(
            """
            CREATE TRIGGER trg_kp_experience_problem_membership
            AFTER UPDATE OF kp_ids ON problems
            BEGIN
                DELETE FROM kp_experience_problems
                WHERE problem_id = NEW.problem_id
                  AND NOT EXISTS (
                      SELECT 1 FROM json_each(COALESCE(NEW.kp_ids, '[]'))
                      WHERE json_each.value = kp_experience_problems.kp_id
                  );
            END
            """
        )
        changes.append("trg_kp_experience_problem_membership")
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='trigger' "
        "AND name='trg_kp_experience_problem_delete'"
    ).fetchone():
        # Pool connections historically run with foreign_keys off, so cleanup
        # cannot rely on ON DELETE CASCADE alone.
        conn.execute(
            """
            CREATE TRIGGER trg_kp_experience_problem_delete
            AFTER DELETE ON problems
            BEGIN
                DELETE FROM kp_experience_problems WHERE problem_id = OLD.problem_id;
            END
            """
        )
        changes.append("trg_kp_experience_problem_delete")
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='trigger' "
        "AND name='trg_kp_experience_kp_delete'"
    ).fetchone():
        conn.execute(
            """
            CREATE TRIGGER trg_kp_experience_kp_delete
            BEFORE DELETE ON knowledge_points
            BEGIN
                DELETE FROM kp_experience_problems WHERE kp_id = OLD.kp_id;
                DELETE FROM kp_experiences WHERE kp_id = OLD.kp_id;
            END
            """
        )
        changes.append("trg_kp_experience_kp_delete")
    return changes
