# Graph Worker execution repair — 2026-10-13

The graph page now parser-loads the semantic core before the Worker adapter. The adapter does not expose the synchronous core when browser Worker support or core loading is unavailable. A Worker construction or execution error terminates that runtime, prevents further solver posts and solver frames, and remains visible in the graph status surface.

The graph interface, semantic layout, relation model, authored content, learning records, and memory-only coordinates are unchanged. Focused Node adapter/UI tests, the graph route test, the associated Python graph test, and strict OpenSpec validation cover the repair.
