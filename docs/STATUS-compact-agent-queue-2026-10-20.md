# Compact Agent queue delivery - 2026-10-20

Approved scope: `d3762157`, `compact-agent-queue-and-direct-interrupt`. Production follows the accepted interaction/layout preview and uses the existing Soft Mondrian paper/ink and blue/yellow tokens.

The queue is one compact list directly above the input, with a four-row scroller, full-text editing, pointer/keyboard ordering, same-turn send-now and removal. Unknown/rejected sends share one collapsed counted recovery summary; accepted failed/cancelled turns retain inline history retry. Unchanged rows survive polling. Queue edit conflicts retain unsaved text in the current page recovery entry, protect a newer composer draft, and make no automatic send.

Bridge owns confirmed `queue_order` and serial stop/worker-release handoff. Interrupt messages never enter the ordinary queue. Retained peers stay paused, and approval cannot be bypassed. Existing conversation JSON remains the durable authority. There is no SQLite migration, new dependency or provider-protocol change.

Code: backend `9455cc66`, `f0080208`; route inventory `765fb909`; UI `409712ad`, `147f298a`, `5f900195`. Independent backend and frontend task reviews approved after closing idempotence-after-edit, empty-backlog continuation, uncertain-send routing (including omitted legacy fields), and edit-versus-dispatch draft recovery findings.

Contract reconciliation covers GLOSSARY, FILE_CONTRACT, ARCHITECTURE, PRODUCT-MANUAL and affected ACTION-GRAPH entries. DATA_MODEL has no affected pool fields.

Verified at code 24ec1715: full Python suite 1117 passed in 343.12s; all Node tests 250 passed; compileall, strict OpenSpec all26/26 and specs19/19, and dmath/ch06 extraction guard passed. The checkout has no generated output for the conditional problem-set guard. Final review fixes preserve newer editors on late save, restore cancelled-turn inline retry and dispatch queued retries in confirmed shared order. Independent incremental review approved all fixes and the final test-only fixture margin adjustment. Measured fake-provider startup exceeded the former 0.3s idle fixture budget; fixture durations now preserve their tested inequalities without changing production watchdogs.

Isolated browser acceptance used a read-only SQLite backup of the main dmath pool (28 tables,466 rows, matching counts), a separate temp registry/workspace, fake provider and port3094. Desktop and390px layouts retain the input and internal scrolling. Browser checks passed pointer/keyboard reorder; edits/focus across polling; deletion; C promotion preserving turn identity and current text while stopping A, keeping B paused and preserving the newer composer draft; interrupt-only with queue never visible; ordinary sending afterwards; collapsed counted unknown/rejected recovery across reload; inline failure;409 reorder refresh; saved-action reconciliation; and edit-conflict recovery without changing the running turn.

No live-provider execution is claimed. The real3081 service remains unchanged until acceptance. Integration/runtime receipts will be recorded under the user-level deployment directory; no course-data migration is required.

Final isolated HTTP order regression: failed F, running A, queued B then retry R; confirmed B/R order was honored after A, B completed before R, and the queue ended empty.
