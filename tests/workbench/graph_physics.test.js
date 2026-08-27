"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const physics = require("../../workbench/server/static/graph-physics.js");

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

const REAL_28_NODES = Array.from({ length: 28 }, (_, index) => ({
  id: "kp-" + (index + 1), title: "Counting concept " + (index + 1), problem_count: 0,
}));
const REAL_28_EDGES = [
  [1, 2], [1, 9], [2, 3], [1, 3], [3, 4], [1, 5], [2, 5], [6, 7], [6, 8],
  [9, 10], [9, 12], [10, 11], [10, 13], [12, 13], [13, 14], [13, 15],
  [14, 15], [14, 16], [15, 16], [15, 17], [13, 16], [13, 17], [9, 18],
  [1, 18], [12, 19], [13, 19], [10, 20], [14, 20], [20, 21], [9, 22],
].map(([source, target]) => ({ source: "kp-" + source, target: "kp-" + target, attraction: 1 }));

function assertInBounds(nodes, width, height) {
  nodes.forEach((node) => {
    assert.ok(node.x - node.collisionRadius >= 0, node.id + " exceeds left bound");
    assert.ok(node.x + node.collisionRadius <= width, node.id + " exceeds right bound");
    assert.ok(node.y - node.collisionRadius >= 0, node.id + " exceeds top bound");
    assert.ok(node.y + node.collisionRadius <= height, node.id + " exceeds bottom bound");
  });
}

function assertNoLabelOverlaps(nodes) {
  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      assert.ok(distance(nodes[i], nodes[j]) >= nodes[i].collisionRadius + nodes[j].collisionRadius,
        nodes[i].id + " overlaps " + nodes[j].id);
    }
  }
}

function assertNoCrossComponentLabelOverlaps(nodes) {
  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      if (nodes[i]._layoutComponent === nodes[j]._layoutComponent) continue;
      assert.ok(distance(nodes[i], nodes[j]) >= nodes[i].collisionRadius + nodes[j].collisionRadius,
        nodes[i].id + " overlaps " + nodes[j].id);
    }
  }
}

test("node radius grows monotonically with formal problem count and is capped", () => {
  assert.equal(physics.nodeRadius(0), 8);
  assert.ok(physics.nodeRadius(4) > physics.nodeRadius(1));
  assert.equal(physics.nodeRadius(10000), 30);
});

test("external labels do not enlarge physical collision radius", () => {
  const simulation = physics.createSimulation(
    [{ id: "a", title: "广义鸽巢原理与组合模型".repeat(3), problem_count: 1 }],
    [], 500, 320,
  );
  assert.equal(simulation.nodes[0].collisionRadius, simulation.nodes[0].radius);
});

test("settled nodes preserve 24 pixels of circle clearance", () => {
  const nodes = Array.from({ length: 12 }, (_, index) => ({
    id: String(index), title: "广义鸽巢原理与组合模型" + index, problem_count: 4,
  }));
  const edges = nodes.slice(1).map((node) => ({
    source: "0", target: node.id, attraction: 1.25,
  }));
  const simulation = physics.createSimulation(nodes, edges, 800, 600);
  physics.settle(simulation, 2000);
  for (let i = 0; i < simulation.nodes.length; i += 1) {
    for (let j = i + 1; j < simulation.nodes.length; j += 1) {
      const a = simulation.nodes[i];
      const b = simulation.nodes[j];
      assert.ok(distance(a, b) >= a.radius + b.radius + 23.5);
    }
  }
});

test("stronger attraction has a shorter spring target", () => {
  assert.equal(physics.targetDistance(1.875, 10, 20), 102);
  assert.equal(physics.targetDistance(0.75, 10, 20), 174);
  assert.ok(physics.targetDistance(1.25, 10, 20) < physics.targetDistance(0.75, 10, 20));
});

test("a stronger edge settles its pair closer than a weak edge", () => {
  function settledPair(attraction) {
    const simulation = physics.createSimulation(
      [{ id: "a", problem_count: 1 }, { id: "b", problem_count: 1 }],
      [{ source: "a", target: "b", attraction }],
      640, 420,
    );
    physics.settle(simulation, 1800);
    return distance(simulation.nodes[0], simulation.nodes[1]);
  }
  assert.ok(settledPair(1.25) < settledPair(0.75));
});

test("simulation converges and reheat resumes movement", () => {
  const simulation = physics.createSimulation(
    [
      { id: "a", problem_count: 1 },
      { id: "b", problem_count: 4 },
      { id: "c", problem_count: 9 },
    ],
    [
      { source: "a", target: "b", attraction: 1 },
      { source: "b", target: "c", attraction: 1.25 },
    ],
    700, 500,
  );
  const ticks = physics.settle(simulation, 2000);
  assert.ok(ticks < 2000);
  assert.equal(simulation.stable, true);
  physics.reheat(simulation);
  assert.equal(simulation.stable, false);
  assert.ok(simulation.alpha > 0.9);
});

test("filtered data creates a new layout and reduced motion settles synchronously", () => {
  const full = physics.createSimulation(
    [{ id: "a" }, { id: "b" }, { id: "c" }],
    [{ source: "a", target: "b", attraction: 1 }],
    500, 320,
  );
  const filtered = physics.createSimulation(
    [{ id: "a" }, { id: "b" }],
    [{ source: "a", target: "b", attraction: 1 }],
    500, 320,
  );
  assert.equal(full.nodes.length, 3);
  assert.equal(filtered.nodes.length, 2);
  physics.settle(filtered, 2000);
  assert.equal(filtered.stable, true);
});

test("connected components retain isolates and their internal edges", () => {
  const components = physics.connectedComponents(
    [{ id: "a" }, { id: "b" }, { id: "c" }, { id: "d" }, { id: "e" }],
    [
      { source: "b", target: "a", attraction: 1 },
      { source: "c", target: "d", attraction: 1 },
    ],
  );
  assert.deepEqual(components.map((component) => component.nodes.map((node) => node.id)), [
    ["a", "b"], ["c", "d"], ["e"],
  ]);
  assert.deepEqual(components.map((component) => component.edges.length), [1, 1, 0]);
});

test("nontrivial components have six repeatable distinct starting layouts", () => {
  const nodes = [{ id: "a" }, { id: "b" }, { id: "c" }, { id: "d" }];
  const first = physics.candidateLayouts(nodes, 640, 420);
  const second = physics.candidateLayouts(nodes, 640, 420);
  assert.equal(first.length, 6);
  assert.deepEqual(second, first);
  assert.equal(new Set(first.map((layout) => JSON.stringify(layout.nodes))).size, 6);
});

test("layout scoring counts crossing edges and label collisions", () => {
  const crossing = physics.scoreLayout(
    [
      { id: "a", x: 0, y: 0, collisionRadius: 10 },
      { id: "b", x: 100, y: 100, collisionRadius: 10 },
      { id: "c", x: 0, y: 100, collisionRadius: 10 },
      { id: "d", x: 100, y: 0, collisionRadius: 10 },
    ],
    [{ source: "a", target: "b" }, { source: "c", target: "d" }],
  );
  const collision = physics.scoreLayout(
    [
      { id: "a", x: 0, y: 0, collisionRadius: 20 },
      { id: "b", x: 25, y: 0, collisionRadius: 20 },
    ], [],
  );
  assert.equal(crossing.crossings, 1);
  assert.equal(crossing.labelCollisions, 0);
  assert.equal(collision.crossings, 0);
  assert.equal(collision.labelCollisions, 1);
});

test("layout scoring treats collinear and near-overlapping edges as clutter", () => {
  const score = physics.scoreLayout(
    [
      { id: "a", x: 0, y: 0 }, { id: "b", x: 100, y: 0 },
      { id: "c", x: 25, y: 0 }, { id: "d", x: 75, y: 0 },
      { id: "e", x: 25, y: 2 }, { id: "f", x: 75, y: 2 },
    ],
    [
      { source: "a", target: "b" }, { source: "c", target: "d" }, { source: "e", target: "f" },
    ],
  );
  assert.equal(score.crossings, 3);
});

test("best layout selection is lexicographic and stable on ties", () => {
  const candidates = [
    { name: "waste", score: { crossings: 0, labelCollisions: 1, waste: 1 } },
    { name: "collision", score: { crossings: 0, labelCollisions: 0, waste: 999 } },
    { name: "crossing", score: { crossings: 1, labelCollisions: 0, waste: 0 } },
    { name: "tie", score: { crossings: 0, labelCollisions: 0, waste: 999 } },
  ];
  assert.equal(physics.chooseBestLayout(candidates).name, "collision");
});

test("component packing separates regions and gives isolates a deterministic slot", () => {
  const packed = physics.packComponents([
    { nodes: [{ id: "a", x: 0, y: 0, radius: 10 }, { id: "b", x: 40, y: 0, radius: 10 }] },
    { nodes: [{ id: "c", x: 0, y: 0, radius: 10 }] },
    { nodes: [{ id: "d", x: 0, y: 0, radius: 10 }] },
  ], 500, 320);
  const a = packed.find((node) => node.id === "a");
  const c = packed.find((node) => node.id === "c");
  const d = packed.find((node) => node.id === "d");
  assert.ok(distance(a, c) > 40);
  assert.ok(distance(c, d) > 40);
  assert.deepEqual(physics.packComponents([{ nodes: [{ id: "c", x: 0, y: 0, radius: 10 }] }], 500, 320),
    physics.packComponents([{ nodes: [{ id: "c", x: 0, y: 0, radius: 10 }] }], 500, 320));
});

test("packed seeds enter one unbounded unified simulation", () => {
  const graph = physics.layoutGraph(
    [{ id: "a" }, { id: "b" }, { id: "c" }, { id: "d" }],
    [{ source: "a", target: "b", attraction: 1 }, { source: "c", target: "d", attraction: 1 }],
    640, 420, 1600,
  );
  assert.equal(graph.components, undefined);
  assert.equal(graph.seedComponents.length, 2);
  const visible = graph.nodes.find((node) => node.id === "a");
  visible.fx = graph.width + 400;
  visible.fy = graph.height + 300;
  physics.reheat(graph);
  physics.tick(graph);
  assert.ok(visible.x > graph.width);
  assert.ok(visible.y > graph.height);
  visible.fx = null;
  visible.fy = null;
});

test("real 28-node unified graph preserves clearance and improves the recorded crossing start", () => {
  const graph = physics.layoutGraph(REAL_28_NODES, REAL_28_EDGES, 800, 600, 2000);
  physics.settle(graph, 2400);
  for (let i = 0; i < graph.nodes.length; i += 1) {
    for (let j = i + 1; j < graph.nodes.length; j += 1) {
      assert.ok(distance(graph.nodes[i], graph.nodes[j]) >= graph.nodes[i].radius + graph.nodes[j].radius + 23.5);
    }
  }
  assert.ok(physics.scoreLayout(graph.nodes, REAL_28_EDGES).crossings <= 67);
});

test("real graph remains collision free for desktop and narrow seed canvases", () => {
  [[640, 420], [375, 320]].forEach(([width, height]) => {
    const graph = physics.layoutGraph(REAL_28_NODES, REAL_28_EDGES, width, height, 2000);
    physics.settle(graph, 2400);
    for (let i = 0; i < graph.nodes.length; i += 1) {
      for (let j = i + 1; j < graph.nodes.length; j += 1) {
        assert.ok(distance(graph.nodes[i], graph.nodes[j]) >= graph.nodes[i].radius + graph.nodes[j].radius + 23.5);
      }
    }
    assert.equal(graph.stable, true);
  });
});

test("complete graph layout selects deterministic component seeds", () => {
  const nodes = [{ id: "a" }, { id: "b" }, { id: "c" }, { id: "isolate" }];
  const edges = [{ source: "a", target: "b", attraction: 1 }, { source: "b", target: "c", attraction: 1 }];
  const first = physics.layoutGraph(nodes, edges, 640, 420, 1600);
  const second = physics.layoutGraph(nodes, edges, 640, 420, 1600);
  assert.deepEqual(first.nodes.map((node) => ({ id: node.id, x: node.x, y: node.y })),
    second.nodes.map((node) => ({ id: node.id, x: node.x, y: node.y })));
  assert.equal(first.seedComponents.length, 2);
});

test("soft anchors preserve a drag intent without pinning the node", () => {
  const graph = physics.createSimulation(
    [{ id: "a" }, { id: "b" }], [{ source: "a", target: "b", attraction: 1 }], 640, 420,
  );
  const node = graph.nodes[0];
  physics.setSoftAnchor(node, 900, -200);
  physics.reheat(graph, 0.35);
  physics.tick(graph);
  assert.equal(node.fx, null);
  assert.ok(node.anchorX === 900 && node.anchorY === -200);
  assert.ok(distance(node, { x: 900, y: -200 }) < distance({ x: 320, y: 210 }, { x: 900, y: -200 }));
});

test("focus expansion preserves attraction ordering", () => {
  assert.ok(physics.targetDistance(1.25, 10, 10, 1.15)
    < physics.targetDistance(0.75, 10, 10, 1.15));
  assert.ok(physics.targetDistance(1.25, 10, 10, 1.15)
    > physics.targetDistance(1.25, 10, 10, 1));
});

test("settled graphs expose no idle breathing offset", () => {
  assert.equal(typeof physics.breathingOffset, "undefined");
});

test("gravity control changes only the in-memory center force", () => {
  const simulation = physics.createSimulation([{ id: "a" }, { id: "b" }], [], 640, 420);
  physics.setGravity(simulation, 80);
  assert.ok(Math.abs(simulation.gravity - 0.002808) < 1e-12);
  assert.equal(simulation.stable, false);
});

test("gravity range has a stronger center pull than the previous maximum", () => {
  const simulation = physics.createSimulation([{ id: "a" }, { id: "b" }], [], 640, 420);
  physics.setGravity(simulation, 0);
  const low = simulation.gravity;
  physics.setGravity(simulation, 100);
  assert.equal(low, 0);
  assert.ok(simulation.gravity > 0.00117 * 2);
});
