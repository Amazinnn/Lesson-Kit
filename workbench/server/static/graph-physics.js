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

  if (root.GraphPhysics && root.GraphPhysics.workerBacked) return;
  var core = root.GraphPhysics;
  delete root.GraphPhysics;
  if (!root.document) throw new Error("graph physics requires a document");
  if (!core) throw new Error("graph physics core failed to load");
  var renderer = root.GraphRenderer;
  if (!renderer) throw new Error("graph renderer failed to load");
  if (typeof root.Worker !== "function") {
    throw new Error("Lesson Kit knowledge graph requires Web Worker support");
  }

  root.GraphPhysics = factory(root, core, renderer);
}(typeof globalThis === "object" ? globalThis : this, function (root, core, renderer) {
  var LAYOUT_CACHE_VERSION = 1;

  function graphIdentity(nodes, edges) {
    var nodeIds = (nodes || []).map(function (node) { return String(node.id); }).sort();
    var relations = (edges || []).map(function (edge) {
      return [
        String(edge.s === undefined ? edge.source : edge.s),
        String(edge.t === undefined ? edge.target : edge.t),
        String(edge.type === undefined ? edge.relation_type || "" : edge.type || ""),
        String(edge.direction || ""),
      ].join("|");
    }).sort();
    return JSON.stringify({ nodes: nodeIds, edges: relations });
  }

  function layoutStorageKey() {
    var layout = root.document && root.document.getElementById
      ? root.document.getElementById("layout") : null;
    var workspace = layout && layout.dataset ? layout.dataset.workspace : "default";
    return "lk_graph_layout_v" + LAYOUT_CACHE_VERSION + "_" + String(workspace || "default");
  }

  function storage() {
    try { return root.localStorage || null; }
    catch (_) { return null; }
  }

  function readLayoutSeed(identity) {
    var store = storage();
    if (!store) return null;
    try {
      var value = JSON.parse(store.getItem(layoutStorageKey()) || "null");
      if (!value || value.version !== LAYOUT_CACHE_VERSION || value.identity !== identity || !value.positions) {
        return null;
      }
      return value.positions;
    } catch (_) {
      return null;
    }
  }

  function writeLayoutSeed(identity, state) {
    var store = storage();
    if (!store) return false;
    var positions = {};
    state.nodes.forEach(function (node) {
      if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) return;
      positions[node.id] = [Math.round(node.x * 10) / 10, Math.round(node.y * 10) / 10];
    });
    try {
      store.setItem(layoutStorageKey(), JSON.stringify({
        version: LAYOUT_CACHE_VERSION,
        identity: identity,
        positions: positions,
      }));
      return true;
    } catch (_) {
      return false;
    }
  }

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
    var identity = graphIdentity(inputNodes, inputEdges);
    var savedThisSettle = false;
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
      if (graph.settled && !savedThisSettle) {
        writeLayoutSeed(identity, state);
        savedThisSettle = true;
      } else if (!graph.settled) {
        savedThisSettle = false;
      }
      if (latest.kind === "step") stepPending = false;
      latest = null;
    }

    function reheat(alpha, autoFit) {
      if (failed) return;
      mirror.reheat(alpha, autoFit);
      savedThisSettle = false;
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
    if (!failed) {
      var seed = readLayoutSeed(identity);
      if (seed) {
        var seeded = [];
        state.nodes.forEach(function (node) {
          var point = seed[node.id];
          if (!point || !Number.isFinite(point[0]) || !Number.isFinite(point[1])) return;
          node.x = point[0];
          node.y = point[1];
          node.vx = 0;
          node.vy = 0;
          node.anchorX = point[0];
          node.anchorY = point[1];
          seeded.push(node);
        });
        if (seeded.length) {
          runtime.reheat(.34, false);
          var schedule = typeof root.requestAnimationFrame === "function"
            ? root.requestAnimationFrame.bind(root)
            : root.setTimeout.bind(root);
          schedule(function () {
            schedule(function () {
              seeded.forEach(function (node) {
                node.anchorX = null;
                node.anchorY = null;
              });
              runtime.reheat(.28, true);
            });
          });
        }
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
