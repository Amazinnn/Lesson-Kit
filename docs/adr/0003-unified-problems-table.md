# Unified Problems Table

Durable practice items live in one `problems` table and are logically split by
`source_kind`. Separate physical tables for textbook, quiz, midterm, and final
problems were rejected because the v1 fields are the same and the core identity
of a problem is the problem itself, not its source location.
