# WebGL2 graph rendering boundary — 2026-10-13

The graph page now loads its semantic core, renderer, and Worker adapter in an explicit order. WebGL2 remains the single relation-rendering path; DOM nodes and physics-provided relation geometry keep their existing behavior. If renderer startup fails, the current Worker run stops and partially initialized renderer resources are released through the graph status path.

Relation paints now follow the Workbench's solver, dirty, and viewport signals. Ordinary-motion paints coalesce and park after drawing; reduced motion waits for the stable layout and paints it synchronously without a renderer animation frame.

No graph algorithm, graph data, persistence, API, or dependency changes are included.

Independent final-source acceptance at `949fc81`: 972 Python, 163 Node,
24 strict OpenSpec checks, compile and extraction guard passed. Four actual
Edge/WebGL2 fixture-page cases passed with raw DB bytes and SQL unchanged.
Settled renderer counters stayed 121 to 121 over 300 ms; reduced motion drew
once with zero renderer RAF, stayed 1 to 1 at idle, and painted once more on
projection change. Interactions and failure cleanup remained valid. The prior
`0d11520` browser blocker is historical and fixed. OpenSpec CLI archived
`2026-10-13-graph-webgl-rendering`, synchronized live requirements, and strict
all validation passed 23/23. Final archive-head and actual merge CI remain
root-owned gates; no manual visual or real LLM acceptance is claimed.
