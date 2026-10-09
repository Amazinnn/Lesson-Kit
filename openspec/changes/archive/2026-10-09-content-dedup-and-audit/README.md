# 内容去重与只读审查

Add the two capabilities the ADS pool repair had to fake with external scripts:
content identity dedup at ingest, and a read-only pool content audit. Also
restore patch-side validation parity, which `micro-quiz-content` already
requires.

- Renaming note: the change adds no schema field and rewrites no row.
- Terms introduced here (content identity, content audit) belong in
  `docs/GLOSSARY.md` when implemented.
