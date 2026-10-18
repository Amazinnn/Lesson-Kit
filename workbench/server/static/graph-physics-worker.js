"use strict";

importScripts("/static/graph-physics-core.js");

var sim = null;

function applyControls(controls) {
  if (!sim || !controls) return;
  sim.graph.view = controls.view || sim.graph.view;
  sim.graph.gravity = GraphPhysics.clamp(Number(controls.gravity) || 0, 0, 100);
  sim.graph.drag = controls.dragId ? { id: controls.dragId } : null;
  sim.graph.hiddenEdgeTypes = controls.hiddenEdgeTypes || {};
  sim.graph.hiddenEdgeIds = new Set(controls.hiddenEdgeIds || []);

  (controls.nodes || []).forEach(function (value) {
    var node = sim.byId.get(value.id);
    if (!node) return;
    node.visible = value.visible !== false;
    if (Number.isFinite(value.size)) node.size = value.size;
    if (Number.isFinite(value.targetSize)) node.targetSize = value.targetSize;
    node.anchorX = value.anchorX === null || value.anchorX === undefined ? null : Number(value.anchorX);
    node.anchorY = value.anchorY === null || value.anchorY === undefined ? null : Number(value.anchorY);
    if (controls.dragId === node.id || node.anchorX !== null) {
      if (Number.isFinite(value.x)) node.x = value.x;
      if (Number.isFinite(value.y)) node.y = value.y;
      if (Number.isFinite(value.vx)) node.vx = value.vx;
      if (Number.isFinite(value.vy)) node.vy = value.vy;
    }
  });
}

function snapshot(revision, kind) {
  if (!sim) return;
  postMessage({
    type: "snapshot",
    revision: revision,
    kind: kind,
    nodes: sim.nodes.map(function (node) {
      return {
        id: node.id,
        x: node.x,
        y: node.y,
        vx: node.vx,
        vy: node.vy,
        guideX: node.guideX,
        guideY: node.guideY,
      };
    }),
    graph: {
      alpha: sim.graph.alpha,
      stableFrames: sim.graph.stableFrames,
      settleWatch: sim.graph.settleWatch,
      solveStep: sim.graph.solveStep,
      settled: sim.graph.settled,
      layoutInflation: sim.graph.layoutInflation,
    },
  });
}

self.onmessage = function (event) {
  var message = event.data || {};
  if (message.type === "init") {
    var options = message.options || {};
    options.hiddenEdgeIds = new Set(options.hiddenEdgeIds || []);
    sim = GraphPhysics.create(message.nodes || [], message.edges || [], options);
    snapshot(message.revision, "init");
    return;
  }
  if (!sim) return;
  if (message.type === "reheat") {
    applyControls(message.controls);
    sim.reheat(message.alpha, message.autoFit);
    if (message.settle) {
      // A restored layout is adopted, not re-solved: the coordinates arrived with
      // the controls, the anchors that carried them in are dropped again so the
      // next interaction can still move the nodes, and the solver stops here.
      sim.nodes.forEach(function (node) {
        node.anchorX = null;
        node.anchorY = null;
        node.vx = 0;
        node.vy = 0;
      });
      sim.graph.alpha = 0;
      sim.graph.settled = true;
    }
    snapshot(message.revision, "reheat");
    return;
  }
  if (message.type === "step") {
    applyControls(message.controls);
    var count = Math.max(1, Math.min(8, Number(message.count) || 1));
    for (var i = 0; i < count && sim.graph.alpha > 0; i += 1) sim.tick();
    snapshot(message.revision, "step");
    return;
  }
  if (message.type === "dispose") {
    sim = null;
    close();
  }
};
