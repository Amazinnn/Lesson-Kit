"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const graph = require("../../workbench/server/static/graph-physics.js");

test("node size stays monotonic and bounded", () => {
  assert.equal(graph.nodeRadius(0), 14);
  assert.ok(graph.nodeRadius(4) > graph.nodeRadius(1));
  assert.equal(graph.nodeRadius(10000), 31);
  assert.ok(graph.metricRadius(1) > graph.metricRadius(0));
});

test("wrapped labels enlarge the readability footprint", () => {
  const radius = graph.nodeRadius(4);
  assert.equal(graph.labelLineCount("十四个字符一行正好十四个"), 1);
  assert.equal(graph.labelLineCount("二十八个字符的标签会折成两行显示出来"), 2);
  assert.ok(
    graph.collisionRadius(radius, "广义鸽巢原理与组合模型".repeat(3))
      > graph.collisionRadius(radius, "短标签"),
  );
});

test("relationship visual weight follows stored attraction", () => {
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
  assert.deepEqual(
    ["a", "b", "c"].map((id) => byId.get(id).hierarchyLevel),
    [0, 1, 2],
  );
  assert.ok(byId.get("a").y < byId.get("b").y);
  assert.ok(byId.get("b").y < byId.get("c").y);
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
  layout.nodes.forEach((node) => {
    assert.ok(Number.isFinite(node.x));
    assert.ok(Number.isFinite(node.y));
  });
});

test("a prerequisite cycle remains finite", () => {
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

test("metric projections resize nodes without deleting prerequisite semantics", () => {
  const layout = graph.layoutHierarchy(
    [
      { id: "a", title: "A", problem_count: 1, importance: "supplementary" },
      { id: "b", title: "B", problem_count: 16, importance: "core" },
      { id: "c", title: "C", problem_count: 2, importance: "supplementary" },
    ],
    [
      { source: "a", target: "c", relation_type: "prerequisite", direction: "directed" },
      { source: "b", target: "c", relation_type: "prerequisite", direction: "directed" },
    ],
    800, 600, "structure",
  );
  const before = new Map(layout.nodes.map((node) => [node.id, node.hierarchyLevel]));
  graph.applyHierarchyProjection(layout, "problem_count", 30);
  const byId = new Map(layout.nodes.map((node) => [node.id, node]));
  layout.nodes.forEach((node) => {
    assert.equal(node.hierarchyLevel, before.get(node.id));
    assert.ok(Number.isFinite(node.x));
    assert.ok(Number.isFinite(node.y));
  });
  assert.ok(byId.get("b").radius > byId.get("a").radius);
});

test("stronger relations prefer shorter distances without overriding readability", () => {
  function desired(attraction) {
    const layout = graph.layoutHierarchy(
      [
        { id: "a", title: "短标签", problem_count: 1 },
        { id: "b", title: "另一个短标签", problem_count: 1 },
      ],
      [{ id: "r", source: "a", target: "b", relation_type: "related",
        direction: "symmetric", attraction }],
      800, 600, "structure",
    );
    graph.setCompactness(layout, 100);
    return graph.desiredEdgeLength(layout, layout.edges[0]);
  }
  const weak = desired(0.75);
  const strong = desired(1.875);
  assert.ok(strong < weak);
  assert.ok(strong > 70);
});

test("maximum compactness still leaves connected nodes separated", () => {
  const layout = graph.layoutHierarchy(
    [
      { id: "a", title: "排列与组合", problem_count: 12 },
      { id: "b", title: "二项式系数与恒等式", problem_count: 12 },
      { id: "c", title: "条件概率与全概率公式", problem_count: 12 },
    ],
    [
      { id: "r1", source: "a", target: "b", relation_type: "prerequisite",
        direction: "directed", attraction: 1.875 },
      { id: "r2", source: "a", target: "c", relation_type: "related",
        direction: "symmetric", attraction: 1.875 },
    ],
    800, 600, "structure",
  );
  graph.setCompactness(layout, 100);
  for (let i = 0; i < layout.nodes.length; i += 1) {
    for (let j = i + 1; j < layout.nodes.length; j += 1) {
      assert.ok(Math.hypot(
        layout.nodes[i].x - layout.nodes[j].x,
        layout.nodes[i].y - layout.nodes[j].y,
      ) > 70);
    }
  }
});

test("large graphs finish with finite coordinates using bounded local density work", () => {
  const nodes = Array.from({ length: 320 }, (_, index) => ({
    id: "n" + index,
    title: "知识点 " + index,
    problem_count: index % 17,
    importance: index % 7 === 0 ? "core" : "supplementary",
  }));
  const edges = [];
  for (let index = 1; index < nodes.length; index += 1) {
    edges.push({
      id: "p" + index,
      source: "n" + Math.floor((index - 1) / 2),
      target: "n" + index,
      relation_type: "prerequisite",
      direction: "directed",
      attraction: 1.25,
    });
    if (index > 8 && index % 4 === 0) {
      edges.push({
        id: "r" + index,
        source: "n" + (index - 8),
        target: "n" + index,
        relation_type: "related",
        direction: "symmetric",
        attraction: 1,
      });
    }
  }
  const layout = graph.layoutHierarchy(nodes, edges, 1200, 800, "structure");
  assert.equal(layout.nodes.length, 320);
  layout.nodes.forEach((node) => {
    assert.ok(Number.isFinite(node.x));
    assert.ok(Number.isFinite(node.y));
  });
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
  assert.deepEqual(layout.edges.map((edge) => edge.parallelCount), [3, 3, 3]);
  assert.deepEqual(
    new Set(layout.edges.map((edge) => edge.parallelIndex)),
    new Set([0, 1, 2]),
  );
});
