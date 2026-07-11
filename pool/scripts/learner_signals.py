"""Current-state learner signal helpers shared by practice workflows."""

from __future__ import annotations

import hashlib
import sqlite3
from typing import Optional


from pool_schema import (  # type: ignore
    PRACTICE_KINDS,
    SIGNAL_TARGET_TYPES,
    SIGNAL_TYPES,
    ensure_problem_candidate_schema,
)


def signal_id_for(target_type: str, target_id: str, signal_type: str) -> str:
    raw = f"{target_type}\0{target_id}\0{signal_type}".encode("utf-8")
    return f"sig:{hashlib.sha1(raw).hexdigest()[:16]}"


def upsert_learner_signal(
    conn: sqlite3.Connection,
    target_type: str,
    target_id: str,
    signal_type: str,
    note: str = "",
    practice_kind: str = "other",
    practice_ref: Optional[str] = None,
) -> str:
    if target_type not in SIGNAL_TARGET_TYPES:
        raise ValueError(f"invalid signal target_type: {target_type}")
    if not target_id.strip():
        raise ValueError("signal target_id is required")
    if signal_type not in SIGNAL_TYPES:
        raise ValueError(f"invalid signal_type: {signal_type}")
    if practice_kind not in PRACTICE_KINDS:
        raise ValueError(f"invalid practice_kind: {practice_kind}")

    ensure_problem_candidate_schema(conn)
    signal_id = signal_id_for(target_type, target_id, signal_type)
    clean_note = note.strip() or None
    conn.execute(
        """
        INSERT INTO learner_signals (
            signal_id, target_type, target_id, signal_type, weight,
            evidence_count, note, last_practice_kind, last_practice_ref
        ) VALUES (?, ?, ?, ?, 'medium', 1, ?, ?, ?)
        ON CONFLICT(target_type, target_id, signal_type) DO UPDATE SET
            evidence_count = learner_signals.evidence_count + 1,
            weight = CASE
                WHEN learner_signals.evidence_count + 1 >= 2 THEN 'high'
                ELSE 'medium'
            END,
            note = COALESCE(excluded.note, learner_signals.note),
            last_practice_kind = excluded.last_practice_kind,
            last_practice_ref = excluded.last_practice_ref,
            updated_at = datetime('now')
        """,
        (
            signal_id,
            target_type,
            target_id,
            signal_type,
            clean_note,
            practice_kind,
            practice_ref,
        ),
    )
    return signal_id
