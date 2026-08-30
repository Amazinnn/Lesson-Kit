# Protect goal-store integrity

- Refuse mutations when the existing goal file is malformed instead of silently replacing it.
- Serialize concurrent in-process goal mutations so IDs and writes cannot be lost.
- Flush changes to a temporary file and atomically replace the goal file.
