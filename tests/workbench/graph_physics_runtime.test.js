"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const publicPhysics = require("../../workbench/server/static/graph-physics.js");
const localPhysics = require("../../workbench/server/static/graph-physics-local.js");

function node(id, extra) {
  return Object.assign({
    id: id,
    title: id,
    state: "new",
    kind: "core",
    importance: .5,
    problems: 1,
  }, extra || {});
}

function edge(s, t, type, strength) {
  return {
    s: s,
    t: t,
    type: type || "prereq",
    strength: strength === undefined ? 1.25 : strength,
  };
}

function settle(api) {
  const sim = api.create(
    [node("a"), node("b"), node("c"), node("d")],
    [edge("a", "b"), edge("b", "c"), edge("c", "d"), edge("a", "d", "related")],
    { stageWidth: 1800, stageHeight: 1550, gravity: 30 }
  );
  for (let i = 0; i < 500 && sim.graph.alpha > 0; i += 1) sim.tick();
  return {
    alpha: sim.graph.alpha,
    congestion: sim.congestion(),
    nodes: sim.nodes.map((item) => ({
      id: item.id,
      x: item.x,
      y: item.y,
      size: item.size,
    })),
  };
}

test("graph physics local runtime preserves the public solver contract", () => {
  assert.deepEqual(
    Object.keys(localPhysics).sort(),
    Object.keys(publicPhysics).sort(),
    "the isolated local runtime starts as the exact public solver contract"
  );
  assert.deepEqual(settle(localPhysics), settle(publicPhysics));
});
