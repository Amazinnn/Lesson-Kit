# Graph Worker execution repair — 2026-10-13

The graph page now parser-loads the semantic core before the Worker adapter. The adapter does not expose the synchronous core when browser Worker support or core loading is unavailable. A Worker construction or execution error terminates that runtime, prevents further solver posts and solver frames, and remains visible in the graph status surface.

The graph interface, semantic layout, relation model, authored content, learning records, and memory-only coordinates are unchanged. Focused Node adapter/UI tests, the graph route test, the associated Python graph test, and strict OpenSpec validation cover the repair.

Independent acceptance at `4e248ab`: 972 Python, 151 Node, 24 strict OpenSpec
items, compile and extraction guard passed. Six automated actual fixture-page
Edge scenarios covered normal Worker steps/settle and controls, unsupported
Worker, missing core/adapter, Worker load and runtime errors. SQL and database
bytes stayed identical in every case. This is automated fixture acceptance,
not manual visual or real LLM acceptance. Source CI `38352113247` passed on
Python 3.11/3.12. OpenSpec CLI archived `2026-10-13-graph-worker-execution`,
synchronized the live graph requirement, and strict all validation passed 23/23.
Final archive-head and actual merge CI remain root publication gates.
