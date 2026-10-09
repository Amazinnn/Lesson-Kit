"""Read existing pool bodies without schema repair or content writes."""


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
