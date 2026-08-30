# Proposal: remove-candidate-store

## Why

candidate_problems was retired from every read path by introduce-check-pipeline
(stop reading; table and CLI kept, marked 待退役). The Check ingest path has
since replaced candidate staging as the only Agent content channel, the
observation period has passed with no consumer, and the owner has ordered the
physical removal. Keeping a dead table, dead CLI verbs, and dead evidence
branches contradicts the physical-deletion design of the pool.

## What Changes

- The candidate_problems table is no longer created in fresh pools, and the
  owner runs the one-time physical DROP on the live pool (with backup).
- The `candidate` entity disappears from `wb data` (CRUD and the
  candidate-only gate/promote verbs); pull output no longer carries a
  candidates field.
- Mastery evaluation loses its retired candidate-evidence branches: evidence
  comes only from formal problems, knowledge-point reviews, cards, and micro
  quizzes.
- pool/scripts other than pool_schema.py are untouched (layered rule); the
  retired pipeline script becomes caller-less.
- The graph-layout meaning of "candidate" (knowledge-figures) is unrelated and
  unchanged.

## Impact

- specs: mastery-evaluation (1 requirement reworded), review-workbench
  (2 requirements reworded), workbench-content-governance (1 requirement
  reworded)
- code: workbench cli/data/domain/ingest candidate paths, pool_schema create
  set, related tests
