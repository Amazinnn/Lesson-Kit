"""Read existing pool bodies without schema repair or content writes."""

from contextlib import closing
import sqlite3


def bundle_rows(rows):
    """Local measurement view using the storage engine's scalar TEXT affinity.

    No source mapping changes or external database/file access. Boolean/float
    bodies remain accepted and stored exactly as before.
    """
    result = [dict(row) for row in rows]
    numeric = [row for row in result if isinstance(row.get("body"), (bool, float))]
    if numeric:
        with closing(sqlite3.connect(":memory:")) as conn:
            for row in numeric:
                row["body"] = conn.execute("SELECT CAST(? AS TEXT)", (row["body"],)).fetchone()[0]
    return result


def read_rows(conn, prefix=""):
    """Return id/body mappings, or None when that input is unavailable."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(knowledge_points)")}
    if not {"kp_id", "body"} <= columns:
        return None
    query = "SELECT kp_id, body FROM knowledge_points"
    params = ()
    if prefix:
        query += " WHERE kp_id LIKE ?"
        params = (prefix + "%",)
    query += " ORDER BY kp_id"
    return [{"kp_id": kp_id, "body": body} for kp_id, body in conn.execute(query, params)]
