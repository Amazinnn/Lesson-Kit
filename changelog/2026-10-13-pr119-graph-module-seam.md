# PR119 graph physics loader repair — 2026-10-13

The browser adapter no longer checks for `GraphPhysics` immediately after
`document.write` inserts the core script. The parser executes that script after
the adapter returns and before the next page script. The stable CommonJS seam,
solver, script order, and explicit refusal of non-parser loading remain intact.

The focused runtime regression delays execution of the inserted core until
after the adapter returns, then verifies that the next script can use it.
Validation: both graph-physics Node test files passed (17 tests); the graph
physics Python test passed (1 test); and the graph-page script-order route test
passed (1 test).
