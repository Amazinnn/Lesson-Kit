## 1. Specification and Baseline

- [x] 1.1 Synchronize the approved ingestion, daily-use UI, graph, and mastery decisions into OpenSpec and project design documents.
- [x] 1.2 Strictly validate the change and record the 303-problem empty-solution baseline before implementation.

## 2. Content Ingestion and Formal Gate

- [x] 2.1 Add failing tests for atomic ingest commands, explicit provider selection, resumable UTF-8 artifacts, and zero-write recipes.
- [x] 2.2 Implement workbench-only `prepare`, `run`, `gate`, `apply`, `render`, and `recipe` orchestration with no provider fallback.
- [x] 2.3 Add failing tests for limited safe sup/sub markup, damaged OCR, missing solutions, incomplete/non-PASS audits, rollback, and complete-batch apply.
- [x] 2.4 Implement deterministic problem gates, independent audit contracts, recoverable copy creation, and transactional formal-problem apply.
- [x] 2.5 Generate solution artifacts for all current formal problems in bounded independent Agent batches.
- [x] 2.6 Audit every solution and final knowledge-point mapping in fresh independent Agent sessions; repair rejected solutions and qualify the three approved knowledge points plus all thirteen mapping corrections through the same gate.
- [x] 2.7 From one recoverable database copy, apply the 303 qualified solutions, three approved knowledge points, and thirteen qualified mapping corrections in one transaction; rebuild views and verify 303 reveal-ready formal problems and 31 knowledge points.

## 3. Daily-use Reliability

- [x] 3.1 Add failing production-script and route tests for practice restoration, knowledge-point-scoped practice, visible failures, titles, unique accessible labels, and no raw student-facing parameters.
- [x] 3.2 Restore tab-scoped practice mode/current/seen/unified queue without changing existing storage-key meanings or learning-write semantics.
- [x] 3.3 Add the single knowledge-point practice handoff, titled cards, inline validation/request failures, and concise action reminders.
- [x] 3.4 Add responsive navigation and Agent drawers with two compact top-bar icon controls and no hidden-only provider failure state.
- [x] 3.5 Reduce the graph dashboard to name, action reminder, and knowledge-point link; remove visible manual state, signal, and scheduling controls while retaining compatibility APIs.

## 4. Graph Readability

- [x] 4.1 Add failing pure Node tests for components, six deterministic starts, lexicographic scoring, packing, crossings, label collisions, focus distances, drag reheat, and reduced motion.
- [x] 4.2 Implement component discovery, deterministic candidate layout/selection, isolate placement, and component packing using the existing physics engine.
- [x] 4.3 Render residual close edges as shallow curves and implement one-hop/two-hop focus with background reset.
- [x] 4.4 Verify the real 28-node graph reduces crossings against the recorded single-start baseline while preserving drag, zoom, search, filter, and labels.

## 5. Mastery v0 Experiment

- [x] 5.1 Add failing pure Domain tests for evidence strength, negative precedence, due status, cross-date thresholds, cross-problem propagation, single-problem fallback, candidate scope, and neutral events.
- [x] 5.2 Implement the pure versioned `v0` evaluator and read-only data projection.
- [x] 5.3 Add the `wb experiment <workspace> mastery` text/JSON shell without UI integration or ordering authority.
- [x] 5.4 Prove database contents and row counts are identical before and after experiment execution.

## 6. Verification and Delivery

- [x] 6.1 Run focused and full pytest, JavaScript syntax checks, strict OpenSpec validation, doctor, and both pool guards.
- [x] 6.2 Perform responsive workbench acceptance at 375px, 1024px, and 1440px for practice recovery, knowledge-point handoff, Agent drawers, graph readability/focus, and safe problem markup.
- [x] 6.3 Update the dated changelog with final behavior and evidence, archive the OpenSpec change, and verify no active change remains.
- [x] 6.4 Obtain independent code/contract review, resolve material findings, and push the verified main branch.
