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
    // Steps allowed to be in flight at once.
    //
    // This used to be a single boolean, so a step could only be sent after the previous
    // snapshot came back: one physics tick per round trip, and since positions only change
    // when a snapshot is applied, the picture advanced at the round-trip rate rather than the
    // frame rate. Measured during a solve, rAF was delivering 39-56 frames a second while node
    // positions changed 10-21 times a second, which is what "the refresh rate feels low" was.
    //
    // Pipelining hides the latency instead of waiting on it. The worker processes messages in
    // order, so the newest snapshot is always the furthest along, and applyLatest() — which
    // runs once per frame — now finds something new on essentially every frame. The physics
    // still advances by the same number of ticks; only the waiting is gone.
    var stepsInFlight = 0;
    var MAX_STEPS_IN_FLIGHT = 4;
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
      stepsInFlight = 0;
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
      // The slot is released in the worker message handler, on arrival — not here. Doing
      // it in both places would decrement twice for one step and let the pipeline run
      // unbounded, which would queue steps faster than the worker can retire them.
      latest = null;
    }

    // `settle` is the restored-layout path: adopt the coordinates that come in with
    // the controls and stop, instead of re-solving them. ADR 0028 used to restore
    // the seed as anchors, reheat at .34, release the anchors and reheat again —
    // three rounds of visible motion to arrive back where the learner already was.
    function reheat(alpha, autoFit, settle) {
      if (failed) return;
      mirror.reheat(alpha, autoFit);
      savedThisSettle = false;
      controlRevision = send("reheat", {
        alpha: alpha,
        autoFit: autoFit,
        settle: settle === true,
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
        if (graph.alpha <= 0 || stepsInFlight >= MAX_STEPS_IN_FLIGHT) return;
        stepsInFlight += 1;
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
        // Decremented before the revision gate below: a discarded snapshot still means the
        // worker finished a step, and leaving the slot occupied would stall the pipeline.
        if (message.kind === "step") stepsInFlight = Math.max(0, stepsInFlight - 1);
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
        if (seeded.length === state.nodes.length) {
          // Every point has a seat, so this is the layout the learner left. Adopt it
          // and stop: no anchors to release later, no re-solve to watch.
          seeded.forEach(function (node) {
            node.anchorX = node.x;
            node.anchorY = node.y;
          });
          runtime.reheat(0, true, true);
          seeded.forEach(function (node) {
            node.anchorX = null;
            node.anchorY = null;
          });
        } else if (seeded.length) {
          // A partial seat is not the layout the learner left, so it still has to
          // be solved — from where those points already are. Keep the cached seats
          // for the first paint, then release them before the solve resumes.
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
