"use strict";

/* Public graph-physics module.
 *
 * The semantic rules live in graph-physics-core.js. Browsers execute that one
 * implementation through a Worker; Node tests export the same core directly.
 * There is no browser fallback to a second execution path.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = require("./graph-physics-core.js");
    return;
  }

  var core = root.GraphPhysics;
  delete root.GraphPhysics;
  if (!root.document || root.document.readyState !== "loading") {
    throw new Error("graph-physics.js must be parser-loaded before workbench.js");
  }
  if (!core) throw new Error("graph physics core failed to load");
  var renderer = root.GraphRenderer;
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
    var failed = false;
    var revision = 0;
    var appliedRevision = -1;
    var controlRevision = 0;
    var rendererInstance = null;
    var worker = null;
    var runtime = null;
    var failureMessage = "图谱计算失败，布局已停止。刷新页面后可重试。";
    var rendererFailureMessage = "图谱无法启动：浏览器不支持 WebGL2 或图谱渲染资源初始化失败。请刷新页面，或使用支持 WebGL2 的浏览器。";

    function destroyRenderer() {
      if (!rendererInstance) return;
      var current = rendererInstance;
      rendererInstance = null;
      current.destroy();
    }

    function terminateWorker() {
      if (!worker) return;
      var current = worker;
      worker = null;
      current.onmessage = null;
      current.onerror = null;
      current.terminate();
    }

    function stop(message, error) {
      if (failed) return;
      failed = true;
      stepPending = false;
      latest = null;
      graph.alpha = 0;
      graph.settled = true;
      if (runtime) {
        runtime.failed = true;
        runtime.error = message;
      }
      terminateWorker();
      destroyRenderer();
      if (error && typeof console !== "undefined" && console.error) {
        console.error("graph runtime failed", error.message || error);
      }
    }

    function send(type, payload) {
      if (failed || !worker) return null;
      revision += 1;
      try {
        worker.postMessage(Object.assign({ type: type, revision: revision }, payload || {}));
      } catch (error) {
        stop(failureMessage, error);
        return null;
      }
      return revision;
    }

    function applyLatest() {
      if (failed || !latest) return;
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

    function reheat(alpha, autoFit) {
      if (failed) return;
      mirror.reheat(alpha, autoFit);
      controlRevision = send("reheat", {
        alpha: alpha,
        autoFit: autoFit,
        controls: controlsFor(state),
      });
    }

    runtime = {
      state: state,
      failed: false,
      error: "",
      nodes: state.nodes,
      edges: state.edges,
      byId: state.byId,
      graph: graph,
      scoreFor: mirror.scoreFor,
      updateProjection: function () {
        if (failed) return;
        mirror.updateProjection();
      },
      setEdgeVisibility: function (next) {
        if (failed) return;
        next = next || {};
        graph.hiddenEdgeTypes = next.types || {};
        graph.hiddenEdgeIds = next.ids || new Set();
        reheat(.85, true);
      },
      setView: function (view) {
        if (failed) return;
        graph.view = view;
        graph.userMovedViewport = false;
        mirror.updateProjection();
        reheat(1, true);
      },
      setGravity: function (gravity) {
        if (failed) return;
        graph.gravity = core.clamp(Number(gravity) || 0, 0, 100);
        graph.userMovedViewport = false;
        reheat(.62, true);
      },
      reheat: reheat,
      tick: function () {
        if (failed) return;
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
        stop("", null);
      },
    };

    try {
      worker = new root.Worker("/static/graph-physics-worker.js", {
        name: "lesson-kit-graph-physics",
      });
    } catch (error) {
      stop(failureMessage, error);
    }
    if (worker) {
      worker.onmessage = function (event) {
        if (failed) return;
        var message = event.data || {};
        if (message.type !== "snapshot") return;
        if (message.kind === "step") stepPending = false;
        if (message.revision < controlRevision) return;
        latest = message;
      };
      worker.onerror = function (event) {
        stop(failureMessage, event && event.message ? event.message : event);
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
    }
    if (!failed) {
      try {
        rendererInstance = renderer.attach(runtime, root);
        runtime.renderer = rendererInstance;
      } catch (error) {
        stop(rendererFailureMessage, error);
      }
    }
    return runtime;
  }

  var api = {};
  Object.keys(core).forEach(function (key) { api[key] = core[key]; });
  api.create = create;
  Object.defineProperty(api, "workerBacked", { value: true });
  return api;
}));
