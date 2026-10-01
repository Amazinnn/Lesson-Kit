"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const graph = require("../../workbench/server/static/graph-physics.js");

function node(id, title, extra) {
  return Object.assign({
    id: id,
    title: title || id,
    state: "new",
    kind: "core",
    importance: .5,
    problems: 1,
  }, extra || {});
}

function edge(s, t, type, strength) {
  return { s: s, t: t, type: type || "prereq", strength: strength === undefined ? 1.25 : strength };
}

test("node size stays monotonic and bounded", () => {
  assert.equal(graph.sizeFor(0), 28);
  assert.equal(graph.sizeFor(1), 62);
  assert.ok(graph.sizeFor(.6) > graph.sizeFor(.2));
  assert.equal(graph.sizeFor(2), graph.sizeFor(1), "score clamps at 1");
});

test("relationship strength is a monotone distance preference", () => {
  assert.equal(graph.strength01(1.875), 1);
  assert.equal(graph.strength01(.75), 0);
  assert.ok(graph.baseGapForStrength(.75) > graph.baseGapForStrength(1.875));
  assert.equal(graph.baseGapForStrength(.75), 218);
  assert.equal(graph.baseGapForStrength(1.875), 100);
});

test("the gravity curve saturates instead of crushing the graph", () => {
  assert.equal(graph.compactness01(0), 0);
  assert.equal(graph.compactness01(100), 1);
  // the right half of the slider approaches the compact limit asymptotically
  const atEighty = graph.compactness01(80);
  const atNinety = graph.compactness01(90);
  assert.ok(atNinety > atEighty);
  assert.ok(atNinety - atEighty < .3, "late slider stops buying much compactness");
  assert.ok(graph.spreadFactor(100) < graph.spreadFactor(0));
});

test("prerequisite relations create stable top-to-bottom levels", () => {
  const levels = graph.hierarchyLevels(
    [node("a"), node("b"), node("c")],
    [edge("a", "b"), edge("b", "c")]
  );
  assert.equal(levels.get("a"), 0);
  assert.equal(levels.get("b"), 1);
  assert.equal(levels.get("c"), 2);
});

test("auxiliary relations do not invent hierarchy", () => {
  const levels = graph.hierarchyLevels(
    [node("a"), node("b"), node("c")],
    [edge("a", "b", "related"), edge("b", "c", "apply"), edge("c", "a", "contrast")]
  );
  assert.equal(levels.get("a"), 0);
  assert.equal(levels.get("b"), 0);
  assert.equal(levels.get("c"), 0);
  const symmetric = graph.hierarchyLevels(
    [node("x"), node("y")],
    [{ s: "x", t: "y", type: "prereq", strength: 1.25, direction: "symmetric" }]
  );
  assert.equal(symmetric.get("x"), 0);
  assert.equal(symmetric.get("y"), 0, "a symmetric prerequisite is not structural");
});

test("a prerequisite cycle stays finite and shares one row", () => {
  const levels = graph.hierarchyLevels(
    [node("a"), node("b"), node("c")],
    [edge("a", "b"), edge("b", "a"), edge("b", "c")]
  );
  assert.equal(levels.get("a"), levels.get("b"));
  assert.equal(levels.get("c"), levels.get("a"),
    "everything downstream of a cycle shares its row instead of hanging");
  assert.ok(Number.isFinite(levels.get("a")));
  // a node that feeds the cycle keeps its own level; the cycle row sits below it
  const mixed = graph.hierarchyLevels(
    [node("x"), node("a"), node("b")],
    [edge("x", "a"), edge("a", "b"), edge("b", "a")]
  );
  assert.equal(mixed.get("x"), 0);
  assert.ok(mixed.get("a") > mixed.get("x"));
});

test("the readability floor grows with density and label width", () => {
  const a = node("a", "短");
  const b = node("b", "短");
  a.x = 0; a.y = 0; a.size = graph.sizeFor(.5);
  b.x = 200; b.y = 0; b.size = graph.sizeFor(.5);
  const sparse = new Map();
  const dense = new Map([["a", 5], ["b", 5]]);
  const state = { degreeCount: new Map([["a", 4], ["b", 4]]) };
  const sparseFloor = graph.readabilityFloor(state, a, b, 1, 0, sparse);
  const denseFloor = graph.readabilityFloor(state, a, b, 1, 0, dense);
  assert.ok(denseFloor > sparseFloor, "crowded nodes get more personal space");
  const wide = node("c", "广义鸽巢原理与组合模型与容斥原理的联合应用");
  wide.x = 0; wide.y = 0; wide.size = graph.sizeFor(.5);
  assert.ok(graph.readabilityFloor(state, wide, wide, 1, 0, sparse) > sparseFloor,
    "a wide label widens its footprint");
});

test("the solver separates nodes, keeps the floor, and expands rather than shrinks", () => {
  const nodes = [];
  const edges = [];
  for (let i = 0; i < 24; i += 1) nodes.push(node("n" + i, "知识点 " + i));
  for (let i = 0; i < 23; i += 1) edges.push(edge("n" + i, "n" + (i + 1), i % 3 ? "prereq" : "related"));
  const sim = graph.create(nodes, edges, { stageWidth: 1800, stageHeight: 1550 });
  for (let i = 0; i < 400 && sim.graph.alpha > 0; i += 1) sim.tick();
  assert.equal(sim.graph.alpha, 0, "the solver settles");
  assert.ok(sim.graph.layoutInflation >= 1 && sim.graph.layoutInflation <= 1.5);
  const congestion = sim.congestion();
  assert.equal(congestion.pairs, 0, "settled layouts have no overlapping footprints");
  sim.nodes.forEach((n) => {
    assert.ok(n.x > 0 && n.x < sim.state.stageWidth, "x inside the stage");
    assert.ok(n.y > 0 && n.y < sim.state.stageHeight, "y inside the stage");
  });
});

test("a settled layout is deterministic for the same input", () => {
  function settled() {
    const nodes = [node("a"), node("b"), node("c"), node("d")];
    const edges = [edge("a", "b"), edge("b", "c"), edge("c", "d"), edge("a", "d", "related")];
    const sim = graph.create(nodes, edges, { stageWidth: 1800, stageHeight: 1550 });
    for (let i = 0; i < 400 && sim.graph.alpha > 0; i += 1) sim.tick();
    return sim.nodes.map((n) => n.id + ":" + n.x.toFixed(3) + "," + n.y.toFixed(3)).join("|");
  }
  assert.equal(settled(), settled());
});

test("multiple relations between one pair keep separate ported curves", () => {
  const nodes = [node("a"), node("b"), node("c")];
  const edges = [
    edge("a", "b", "prereq"),
    edge("a", "b", "contrast"),
    edge("a", "c", "related"),
  ];
  const sim = graph.create(nodes, edges, { stageWidth: 1800, stageHeight: 1550 });
  for (let i = 0; i < 300 && sim.graph.alpha > 0; i += 1) sim.tick();
  const active = sim.visibleEdges();
  sim.computePortSlots(active);
  const paths = active.map((e) => sim.edgePath(e));
  assert.equal(new Set(paths).size, paths.length, "every edge gets its own curve");
  const again = sim.visibleEdges().map((e) => sim.edgePath(e));
  assert.deepEqual(again, paths, "port routing is deterministic");
});

test("wide levels wrap into stacked rows instead of one huge ribbon", () => {
  const nodes = [];
  for (let i = 0; i < 40; i += 1) nodes.push(node("n" + i, "知识点编号" + i));
  const levels = graph.hierarchyLevels(nodes, []);
  const size = graph.structureStageSize(nodes, levels, 30);
  assert.ok(size.width <= 2800, "a 40-node level stays inside the band ceiling");
  assert.ok(size.height >= 1550);
  const sim = graph.create(nodes, [], { stageWidth: size.width, stageHeight: size.height });
  const rows = new Set(sim.nodes.map((n) => Math.round(n.guideY)));
  assert.ok(rows.size > 1, "the flat level is wrapped into stacked rows");
  for (let i = 0; i < 700 && sim.graph.alpha > 0; i += 1) sim.tick();
  assert.equal(sim.graph.alpha, 0, "a wrapped layout still settles");
  assert.equal(sim.congestion().pairs, 0, "wrapped guides leave no overlap behind");
  sim.nodes.forEach((n) => {
    const fp = graph.footprint(n);
    assert.ok(n.guideY + fp.bottom < size.height, "every wrap row fits inside the sized stage");
    assert.ok(n.guideX - fp.left > 0 && n.guideX + fp.right < size.width,
      "no guide row is pushed past the stage edge");
  });
});

test("hidden relations stop constraining the layout, by type or by id", () => {
  const nodes = [node("a", "甲"), node("b", "乙"), node("c", "丙")];
  const edges = [
    Object.assign(edge("a", "b", "prereq"), { id: "e1" }),
    Object.assign(edge("b", "c", "legacy"), { id: "e2" }),
  ];
  const sim = graph.create(nodes, edges, { stageWidth: 1800, stageHeight: 1550 });
  assert.equal(sim.visibleEdges().length, 2, "everything is visible by default");
  sim.setEdgeVisibility({ types: { legacy: true } });
  assert.equal(sim.visibleEdges().length, 1, "a hidden type is not a constraint");
  assert.ok(sim.graph.alpha > 0, "toggling relation visibility re-solves the layout");
  sim.setEdgeVisibility({});
  assert.equal(sim.visibleEdges().length, 2, "the type comes back");
  sim.setEdgeVisibility({ ids: new Set(["e1"]) });
  assert.equal(sim.visibleEdges().length, 1, "an id-pruned relation drops out of the layout too");
  assert.equal(sim.visibleEdges()[0].id, "e2");
  sim.setEdgeVisibility({ types: { legacy: true }, ids: new Set(["e1"]) });
  assert.equal(sim.visibleEdges().length, 0, "type and id filters combine");
  const preHidden = graph.create(nodes, edges, {
    stageWidth: 1800, stageHeight: 1550,
    hiddenEdgeTypes: { legacy: true },
    hiddenEdgeIds: new Set(["e1"]),
  });
  assert.equal(preHidden.visibleEdges().length, 0, "create() honours both filters");
});

test("an unwrapped graph keeps the blueprint's single-band stage", () => {
  const nodes = [node("a", "甲"), node("b", "乙"), node("c", "丙")];
  const edges = [edge("a", "b"), edge("b", "c")];
  const levels = graph.hierarchyLevels(nodes, edges);
  const size = graph.structureStageSize(nodes, levels, 30);
  assert.equal(size.width, 1800, "narrow graphs keep the base stage width");
  assert.equal(size.height, 1550, "three levels fit the base stage height");
  const sim = graph.create(nodes, edges, { stageWidth: size.width, stageHeight: size.height });
  assert.deepEqual(
    [...new Set(sim.nodes.map((n) => Math.round(n.guideY)))].sort((a, b) => a - b),
    [125, 285, 446].map((y) => Math.round(y)),
    "one row per level, top to bottom"
  );
});

test("gravity changes the guide spacing but never the safety margin", () => {
  const nodes = [node("a"), node("b")];
  const edges = [edge("a", "b")];
  const sim = graph.create(nodes, edges, { stageWidth: 1800, stageHeight: 1550, gravity: 0 });
  const spreadLoose = sim.layoutSpread();
  sim.setGravity(100);
  const spreadTight = sim.layoutSpread();
  assert.ok(spreadTight < spreadLoose, "higher gravity packs the semantic gaps");
  assert.ok(spreadTight > .8, "packing saturates instead of collapsing");
});
