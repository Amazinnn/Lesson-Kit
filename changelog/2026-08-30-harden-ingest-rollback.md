# Harden ingest rollback dependencies

- Treat problem learning-state rows as rollback blockers so content cannot be orphaned.
- Acquire the SQLite write lock before dependency checks and keep it through backup and deletion.
- Extend rollback coverage to every current problem-learning dependency table.
