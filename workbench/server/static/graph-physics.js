"use strict";

/* Public graph-physics module.
 *
 * The semantic rules live in graph-physics-core.js. Browsers execute that one
 * implementation through a Worker; Node tests export the same core directly.
 * The current renderer is a separate module with one active implementation.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = require("./graph-physics-core.js");
    return;
  }

  var core = root.GraphPhysics;
  if (!core) {
    if (!root.document || root.document.readyState !== "loading"
        || typeof root.document.write !== "function") {
      throw new Error("graph physics core must be parser-loaded before workbench.js");
    }
    root.document.write('<script src="/static/graph-physics-core.js"><\/script>');
    core = root.GraphPhysics;
  }
  if (!core) throw new Error("graph physics core failed to load");

  var renderer = root.GraphRenderer;
  if (!renderer) {
    if (!root.document || root.document.readyState !== "loading"
        || typeof root.document.write !== "function") {
      throw new Error("graph renderer must be parser-loaded before workbench.js");
    }
    root.document.write('<script src="/static/graph-renderer.js"><\/script>');
    renderer = root.GraphRenderer;
  }
  if (!renderer) throw new Error("graph renderer failed to load");
  if (typeof root.Worker !== "function") {
    throw new Error("Lesson Kit knowledge graph requires Web Worker support");
  }

  root.GraphPhysics = factory(root, core, renderer);
}(typeof globalThis === "object" ? globalThis : this, function (root, core, renderer) {
  function controlsFor(state) {
    return {
      view: state.graph.view,
      gravity: state.graph.gravity,
      dragId: state.graph.drag ? state.graph.drag.id : null,
      hiddenEdgeTypes: state.graph.hiddenEdgeTypes || {},
      hiddenEdgeIds: Array.from(state.graph.hiddenEdgeIds || []),
      nodes: state.nodes.map(function (node) {
        return {
          id: node.id,
          visible: node.visible,
          size: node.size,
          targetSize: node.targetSize,
          anchorX: node.anchorX,
          anchorY: node.anchorY,
          x: node.x,
          y: node.y,
          vx: node.vx,
          vy: node.vy,
        };
      }),
    };
  }

  function create(inputNodes, inputEdges, options) {
    var mirror = core.create(inputNodes || [], inputEdges || [], options || {});
    var state = mirror.state;
    var graph = mirror.graph;
    var latest = null;
    var stepPending = false;
    var revision = 0;
    var appliedRevision = -1;
    var controlRevision = 0;
    var rendererInstance = null;
    var worker = new root.Worker("/static/graph-physics-worker.js", {
      name: "lesson-kit-graph-physics",
    });

    function send(type, payload) {
      revision += 1;
      worker.postMessage(Object.assign({ type: type, revision: revision }, payload || {}));
      return revision;
    }

    function applyLatest() {
      if (!latest) return;
      if (latest.revision < appliedRevision || latest.revision < controlRevision) {
        latest = null;
        return;
      }
      appliedRevision = latest.revision;
      (latest.nodes || []).forEach(function (point) {
        var node = state.byId.get(point.id);
        if (!node) return;
        if ((graph.drag && graph.drag.id === node.id) || node.anchorX !== null) return;
        node.x = point.x;
        node.y = point.y;
        node.vx = point.vx;
        node.vy = point.vy;
        node.guideX = point.guideX;
        node.guideY = point.guideY;
      });
      if (latest.graph) {
        graph.alpha = latest.graph.alpha;
        graph.stableFrames = latest.graph.stableFrames;
        graph.settleWatch = latest.graph.settleWatch;
        graph.solveStep = latest.graph.solveStep;
        graph.settled = latest.graph.settled;
        graph.layoutInflation = latest.graph.layoutInflation;
      }
      if (latest.kind === "step") stepPending = false;
      latest = null;
    }

    worker.onmessage = function (event) {
      var message = event.data || {};
      if (message.type !== "snapshot") return;
      if (message.kind === "step") stepPending = false;
      if (message.revision < controlRevision) return;
      latest = message;
    };
    worker.onerror = function (event) {
      stepPending = false;
      if (typeof console !== "undefined" && console.error) {
        console.error("graph physics worker failed", event.message || event);
      }
    };

    controlRevision = send("init", {
      nodes: inputNodes || [],
      edges: inputEdges || [],
      options: {
        stageWidth: state.stageWidth,
        stageHeight: state.stageHeight,
        view: graph.view,
        gravity: graph.gravity,
        hiddenEdgeTypes: graph.hiddenEdgeTypes,
        hiddenEdgeIds: Array.from(graph.hiddenEdgeIds || []),
      },
    });

    function reheat(alpha, autoFit) {
      mirror.reheat(alpha, autoFit);
      controlRevision = send("reheat", {
        alpha: alpha,
        autoFit: autoFit,
        controls: controlsFor(state),
      });
    }

    var runtime = {
      state: state,
      nodes: state.nodes,
      edges: state.edges,
      byId: state.byId,
      graph: graph,
      scoreFor: mirror.scoreFor,
      updateProjection: function () {
        mirror.updateProjection();
      },
      setEdgeVisibility: function (next) {
        next = next || {};
        graph.hiddenEdgeTypes = next.types || {};
        graph.hiddenEdgeIds = next.ids || new Set();
        reheat(.85, true);
      },
      setView: function (view) {
        graph.view = view;
        graph.userMovedViewport = false;
        mirror.updateProjection();
        reheat(1, true);
      },
      setGravity: function (gravity) {
        graph.gravity = core.clamp(Number(gravity) || 0, 0, 100);
        graph.userMovedViewport = false;
        reheat(.62, true);
      },
      reheat: reheat,
      tick: function () {
        applyLatest();
        if (graph.alpha <= 0 || stepPending) return;
        stepPending = true;
        send("step", {
          count: state.nodes.length > 120 ? 3 : 1,
          controls: controlsFor(state),
        });
      },
      visibleEdges: mirror.visibleEdges,
      neighbors: mirror.neighbors,
      computePortSlots: mirror.computePortSlots,
      edgePath: mirror.edgePath,
      edgeStyle: mirror.edgeStyle,
      layoutSpread: mirror.layoutSpread,
      clusterCenters: mirror.clusterCenters,
      congestion: mirror.congestion,
      dispose: function () {
        if (rendererInstance) rendererInstance.destroy();
        worker.terminate();
      },
    };

    rendererInstance = renderer.attach(runtime, root);
    runtime.renderer = rendererInstance;
    return runtime;
  }

  var api = {};
  Object.keys(core).forEach(function (key) { api[key] = core[key]; });
  api.create = create;
  return api;
}));
