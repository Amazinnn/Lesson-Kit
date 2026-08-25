"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const physics = require("../../workbench/server/static/graph-physics.js");

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

test("node radius grows monotonically with formal problem count and is capped", () => {
  assert.equal(physics.nodeRadius(0), 8);
  assert.ok(physics.nodeRadius(4) > physics.nodeRadius(1));
  assert.equal(physics.nodeRadius(10000), 30);
});

test("readable external labels reserve collision space around their node", () => {
  const simulation = physics.createSimulation(
    [{ id: "a", title: "广义鸽巢原理与组合模型".repeat(3), problem_count: 1 }],
    [], 500, 320,
  );
  assert.ok(simulation.nodes[0].collisionRadius >= 70);
});

test("settled nodes preserve collision space for their labels", () => {
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
      assert.ok(distance(a, b) >= a.collisionRadius + b.collisionRadius + 7);
    }
  }
});

test("stronger attraction has a shorter spring target", () => {
  assert.ok(physics.targetDistance(1.25) < physics.targetDistance(0.75));
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
