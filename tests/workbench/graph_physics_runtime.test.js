"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");

const publicPhysics = require("../../workbench/server/static/graph-physics.js");
const corePhysics = require("../../workbench/server/static/graph-physics-core.js");
const loaderSource = fs.readFileSync(
  require.resolve("../../workbench/server/static/graph-physics.js"),
  "utf8"
);
const coreSource = fs.readFileSync(
  require.resolve("../../workbench/server/static/graph-physics-core.js"),
  "utf8"
);

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

test("graph physics public seam exposes the semantic core contract", () => {
  assert.deepEqual(
    Object.keys(corePhysics).sort(),
    Object.keys(publicPhysics).sort(),
    "the public seam must expose the current core implementation without a second solver"
  );
  assert.deepEqual(settle(corePhysics), settle(publicPhysics));
});

test("browser adapter refuses to publish when the parser-loaded core is missing", () => {
  let writes = 0;
  const browser = vm.createContext({
    Worker: function Worker() {},
    document: {
      readyState: "loading",
      write() { writes += 1; },
    },
  });

  assert.throws(
    () => vm.runInContext(loaderSource, browser),
    /graph physics core failed to load/
  );
  assert.equal(writes, 0, "the adapter does not insert a second script");
  assert.equal(vm.runInContext("typeof GraphPhysics", browser), "undefined");
});

test("browser loader still refuses non-parser loading", () => {
  const browser = vm.createContext({
    document: { readyState: "complete", write() {} },
  });

  assert.throws(
    () => vm.runInContext(loaderSource, browser),
    /must be parser-loaded before workbench\.js/
  );
});
