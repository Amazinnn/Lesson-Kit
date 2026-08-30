"""Pool: workspace-scoped SQLite access and runtime path resolution."""

import json
import sqlite3
from pathlib import Path


class Pool:
    """Read/write access to one workspace's course pool.

    The pool is the only module that touches SQLite. Domain rules receive a
    Pool and stay free of IO.
    """

    def __init__(self, root, db_path, course, chapter):
        self.root = Path(root)
        self.db_path = Path(db_path)
        self.course = course
        self.chapter = chapter
        self._conn = None

    def connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def commit(self):
        self.connect().commit()

    # -- knowledge points -------------------------------------------------

    def kps(self, prefix=None):
        conn = self.connect()
        if prefix:
            rows = conn.execute(
                "SELECT * FROM knowledge_points WHERE kp_id LIKE ? ORDER BY kp_id",
                (prefix + "%",),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM knowledge_points ORDER BY kp_id"
            ).fetchall()
        return [dict(r) for r in rows]

    def kp(self, kp_id):
        row = self.connect().execute(
            "SELECT * FROM knowledge_points WHERE kp_id=?", (kp_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_kp_content(self, kp_id, body, fragile):
        self.connect().execute(
            "UPDATE knowledge_points SET body=?, fragile=? WHERE kp_id=?",
            (body, fragile, kp_id),
        )
        self.commit()

    # -- problems ---------------------------------------------------------

    def problems_for_kps(self, kp_ids, source_kind=None):
        conn = self.connect()
        sql = "SELECT * FROM problems WHERE ("
        sql += " OR ".join("kp_ids LIKE ?" for _ in kp_ids) + ")"
        params = [f'%"{kp_id}"%' for kp_id in kp_ids]
        if source_kind:
            sql += " AND source_kind=?"
            params.append(source_kind)
        rows = conn.execute(sql + " ORDER BY problem_id", params).fetchall()
        requested = set(kp_ids)
        return [
            problem for problem in (self._problem_row(row) for row in rows)
            if requested.intersection(problem["kp_ids"])
        ]

    def problems_all(self):
        rows = self.connect().execute(
            "SELECT * FROM problems ORDER BY problem_id"
        ).fetchall()
        return [self._problem_row(r) for r in rows]

    def problem(self, problem_id):
        row = self.connect().execute(
            "SELECT * FROM problems WHERE problem_id=?", (problem_id,)
        ).fetchone()
        return self._problem_row(row) if row else None

    @staticmethod
    def _problem_row(row):
        item = dict(row)
        item["kp_ids"] = json.loads(item.get("kp_ids") or "[]")
        for field in ("practice_modes", "micro_quiz"):
            raw = item.get(field)
            item[field] = json.loads(raw) if raw else None
        return item

    # -- candidates (retired 2026-08-29 Check pipeline: no active readers;
    #    the table and wb data candidate commands remain for 待退役 tooling)

    @staticmethod
    def _candidate_row(row):
        item = dict(row)
        item["kp_ids"] = json.loads(item.get("kp_ids") or "[]")
        return item

    # -- flash cards -------------------------------------------------------

    def cards_for_kps(self, kp_ids):
        conn = self.connect()
        sql = "SELECT * FROM flash_cards WHERE "
        sql += " OR ".join("kp_id=?" for _ in kp_ids)
        rows = conn.execute(sql + " ORDER BY card_id", list(kp_ids)).fetchall()
        return [dict(r) for r in rows]

    def card(self, card_id):
        row = self.connect().execute(
            "SELECT * FROM flash_cards WHERE card_id=?", (card_id,)
        ).fetchone()
        return dict(row) if row else None

    def next_free_content_ids(self, prefix):
        """Return chapter-scoped next ids for Agent-created cards and quizzes."""
        conn = self.connect()
        card_max = _maximum_readable_suffix(
            conn, "flash_cards", "card_id", f"{prefix}-fc-"
        )
        quiz_max = _maximum_readable_suffix(
            conn, "problems", "problem_id", f"{prefix}-mq-"
        )
        return {
            "flash_card": f"{prefix}-fc-{(card_max or 0) + 1:03d}",
            "micro_quiz": f"{prefix}-mq-{(quiz_max or 0) + 1:03d}",
        }

    # -- learner state ----------------------------------------------------

    def signals(self):
        rows = self.connect().execute(
            "SELECT * FROM learner_signals ORDER BY signal_id"
        ).fetchall()
        return [dict(r) for r in rows]

    def relations(self):
        rows = self.connect().execute(
            "SELECT * FROM knowledge_relations ORDER BY relation_id"
        ).fetchall()
        return [dict(r) for r in rows]

    def attempts(self, problem_id):
        rows = self.connect().execute(
            "SELECT * FROM problem_attempts WHERE problem_id=? ORDER BY id",
            (problem_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def insert_attempt(self, problem_id, status, note=None, answer_text=None):
        self.connect().execute(
            "INSERT INTO problem_attempts (problem_id, status, note, answer_text)"
            " VALUES (?, ?, ?, ?)",
            (problem_id, status, note, answer_text),
        )
        self.commit()

    def upsert_problem_progress(self, problem_id, status, note=None):
        self.connect().execute(
            "INSERT INTO problem_progress (problem_id, status, note, updated_at)"
            " VALUES (?, ?, ?, datetime('now'))"
            " ON CONFLICT(problem_id) DO UPDATE SET status=excluded.status,"
            " note=excluded.note, updated_at=excluded.updated_at",
            (problem_id, status, note),
        )
        self.commit()

    def current_state(self, item_type, item_id):
        row = self.connect().execute(
            "SELECT * FROM learning_current_state WHERE item_type=? AND item_id=?",
            (item_type, item_id),
        ).fetchone()
        return dict(row) if row else None

    def current_states(self):
        rows = self.connect().execute(
            "SELECT * FROM learning_current_state ORDER BY item_type, item_id"
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert_current_state(self, item_type, item_id, state):
        self.connect().execute(
            "INSERT INTO learning_current_state (item_type, item_id, state)"
            " VALUES (?, ?, ?)"
            " ON CONFLICT(item_type, item_id) DO UPDATE SET"
            " state=excluded.state, updated_at=datetime('now')",
            (item_type, item_id, state),
        )
        self.commit()

    def upsert_signal(self, target_type, target_id, signal_type, weight,
                      evidence_count, note=None):
        conn = self.connect()
        conn.execute(
            "INSERT INTO learner_signals (signal_id, target_type, target_id,"
            " signal_type, weight, evidence_count, note)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(signal_id) DO UPDATE SET weight=excluded.weight,"
            " evidence_count=excluded.evidence_count, note=excluded.note",
            (f"{target_id}-sig-{signal_type}", target_type, target_id,
             signal_type, weight, evidence_count, note),
        )
        self.commit()

    # -- schedule ---------------------------------------------------------

    def schedule_get(self, item_type, item_id, direction=""):
        row = self.connect().execute(
            "SELECT * FROM review_schedule WHERE item_type=? AND item_id=?"
            " AND direction=?",
            (item_type, item_id, direction),
        ).fetchone()
        return dict(row) if row else None

    def schedule_upsert(self, row):
        self.connect().execute(
            "INSERT INTO review_schedule (item_type, item_id, direction, state,"
            " repetitions, ease, interval_days, due_at, last_rating,"
            " last_reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(item_type, item_id, direction) DO UPDATE SET"
            " state=excluded.state, repetitions=excluded.repetitions,"
            " ease=excluded.ease, interval_days=excluded.interval_days,"
            " due_at=excluded.due_at, last_rating=excluded.last_rating,"
            " last_reviewed_at=excluded.last_reviewed_at",
            (row["item_type"], row["item_id"], row.get("direction", ""),
             row["state"], row["repetitions"], row["ease"], row["interval_days"],
             row.get("due_at"), row.get("last_rating"), row.get("last_reviewed_at")),
        )
        self.commit()

    def schedule_rows(self):
        rows = self.connect().execute(
            "SELECT * FROM review_schedule ORDER BY due_at"
        ).fetchall()
        return [dict(r) for r in rows]

    # -- feedback events --------------------------------------------------

    def insert_feedback_event(self, item_type, item_id, rating=None, note=None):
        self.connect().execute(
            "INSERT INTO feedback_events (item_type, item_id, rating, note)"
            " VALUES (?, ?, ?, ?)",
            (item_type, item_id, rating, note),
        )
        self.commit()

    def feedback_events(self, item_type=None, item_id=None):
        conn = self.connect()
        if item_type and item_id:
            rows = conn.execute(
                "SELECT * FROM feedback_events WHERE item_type=? AND item_id=?"
                " ORDER BY id",
                (item_type, item_id),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM feedback_events ORDER BY id"
            ).fetchall()
        return [dict(r) for r in rows]

    # -- runtime paths ----------------------------------------------------

    def figures_dir(self):
        return self.root / ".lessonkit" / "figures" / self.course / self.chapter

    def jobs_dir(self):
        return self.root / ".lessonkit" / "jobs"


def _maximum_readable_suffix(conn, table, column, marker):
    """Read numeric suffixes without assuming they stay three digits forever."""
    try:
        rows = conn.execute(f"SELECT {column} FROM {table}").fetchall()
    except sqlite3.OperationalError:
        return None
    numbers = [
        int(value[len(marker):])
        for row in rows
        if (value := row[0]).startswith(marker) and value[len(marker):].isdigit()
    ]
    return max(numbers, default=None)
