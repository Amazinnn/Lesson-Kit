# WebGL2 graph rendering boundary — 2026-10-13

The graph page now loads its semantic core, renderer, and Worker adapter in an explicit order. WebGL2 remains the single relation-rendering path; DOM nodes and physics-provided relation geometry keep their existing behavior. If renderer startup fails, the current Worker run stops and partially initialized renderer resources are released through the graph status path.

No graph algorithm, graph data, persistence, API, or dependency changes are included.
