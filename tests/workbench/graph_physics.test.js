"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const graph = require("../../workbench/server/static/graph-physics.js");

test("node size stays monotonic and capped", () => {
  assert.equal(graph.nodeRadius(0), 8);
  assert.ok(graph.nodeRadius(4) > graph.nodeRadius(1));
  assert.equal(graph.nodeRadius(10000), 30);
  assert.ok(graph.metricRadius(1) > graph.metricRadius(0));
});

test("wrapped labels enlarge only the collision footprint", () => {
  const radius = graph.nodeRadius(4);
  assert.equal(graph.labelLineCount("十四个字符一行正好十四个"), 1);
  assert.equal(graph.labelLineCount("二十八个字符的标签会折成两行显示出来"), 2);
  assert.ok(
    graph.collisionRadius(radius, "广义鸽巢原理与组合模型".repeat(3))
      > graph.collisionRadius(radius, "短标签"),
  );
});

test("relationship visual weight still follows stored attraction", () => {
  const weak = graph.edgeVisual(0.75);
  const strong = graph.edgeVisual(1.875);
  assert.equal(weak.score, 0);
  assert.equal(strong.score, 1);
  assert.ok(strong.width > weak.width);
  assert.ok(strong.opacity > weak.opacity);
});

test("prerequisite relations create stable top-to-bottom levels", () => {
  const layout = graph.layoutHierarchy(
    [
      { id: "a", title: "A", problem_count: 1 },
      { id: "b", title: "B", problem_count: 1 },
      { id: "c", title: "C", problem_count: 1 },
    ],
    [
      { id: "r1", source: "a", target: "b", relation_type: "prerequisite",
        direction: "directed", attraction: 1.25 },
      { id: "r2", source: "b", target: "c", relation_type: "prerequisite",
        direction: "directed", attraction: 1.25 },
    ],
    800, 600, "structure",
  );
  const byId = new Map(layout.nodes.map((node) => [node.id, node]));
  assert.ok(byId.get("a").y < byId.get("b").y);
  assert.ok(byId.get("b").y < byId.get("c").y);
  assert.deepEqual(
    ["a", "b", "c"].map((id) => byId.get(id).hierarchyLevel),
    [0, 1, 2],
  );
});

test("auxiliary relations do not invent learning hierarchy", () => {
  const layout = graph.layoutHierarchy(
    [
      { id: "a", title: "A", problem_count: 1 },
      { id: "b", title: "B", problem_count: 1 },
    ],
    [
      { id: "r1", source: "a", target: "b", relation_type: "contrasts",
        direction: "symmetric", attraction: 1 },
    ],
    800, 600, "structure",
  );
  assert.equal(layout.nodes[0].hierarchyLevel, 0);
  assert.equal(layout.nodes[1].hierarchyLevel, 0);
  assert.equal(layout.nodes[0].y, layout.nodes[1].y);
});

test("a prerequisite cycle remains finite instead of starting a simulation", () => {
  const layout = graph.layoutHierarchy(
    [
      { id: "a", title: "A" },
      { id: "b", title: "B" },
      { id: "c", title: "C" },
    ],
    [
      { source: "a", target: "b", relation_type: "prerequisite", direction: "directed" },
      { source: "b", target: "c", relation_type: "prerequisite", direction: "directed" },
      { source: "c", target: "a", relation_type: "prerequisite", direction: "directed" },
    ],
    800, 600, "structure",
  );
  assert.equal(new Set(layout.nodes.map((node) => node.hierarchyLevel)).size, 1);
  layout.nodes.forEach((node) => {
    assert.ok(Number.isFinite(node.x));
    assert.ok(Number.isFinite(node.y));
  });
});

test("metric projection reorders only inside the existing levels", () => {
  const layout = graph.layoutHierarchy(
    [
      { id: "a", title: "A", problem_count: 1, importance: "supplementary" },
      { id: "b", title: "B", problem_count: 8, importance: "core" },
      { id: "c", title: "C", problem_count: 2, importance: "supplementary" },
    ],
    [
      { source: "a", target: "c", relation_type: "prerequisite", direction: "directed" },
      { source: "b", target: "c", relation_type: "prerequisite", direction: "directed" },
    ],
    800, 600, "structure",
  );
  const before = new Map(layout.nodes.map((node) => [node.id, {
    level: node.hierarchyLevel,
    y: node.y,
  }]));

  graph.applyHierarchyProjection(layout, "problem_count");
  const byId = new Map(layout.nodes.map((node) => [node.id, node]));
  layout.nodes.forEach((node) => {
    assert.equal(node.hierarchyLevel, before.get(node.id).level);
    assert.equal(node.y, before.get(node.id).y);
  });
  assert.ok(byId.get("b").x < byId.get("a").x);
  assert.ok(byId.get("b").radius > byId.get("a").radius);
});

test("multiple relations between one pair keep deterministic curve slots", () => {
  const layout = graph.layoutHierarchy(
    [{ id: "a" }, { id: "b" }],
    [
      { id: "r2", source: "a", target: "b", relation_type: "applies_to",
        direction: "directed" },
      { id: "r1", source: "a", target: "b", relation_type: "prerequisite",
        direction: "directed" },
      { id: "r3", source: "b", target: "a", relation_type: "prerequisite",
        direction: "directed" },
    ],
    800, 600, "structure",
  );
  assert.deepEqual(
    layout.edges.map((edge) => edge.parallelCount),
    [3, 3, 3],
  );
  assert.deepEqual(
    new Set(layout.edges.map((edge) => edge.parallelIndex)),
    new Set([0, 1, 2]),
  );
});
