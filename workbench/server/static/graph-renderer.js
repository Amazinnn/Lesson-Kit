"use strict";

/* Current Lesson Kit graph renderer implementation.
 *
 * Relations are painted with WebGL2. DOM nodes remain the canonical visual,
 * interaction and accessibility layer. This module is the one renderer used by
 * the current release; unsupported WebGL is an explicit failure, not a switch
 * to the retired SVG renderer.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GraphRenderer = api;
}(typeof globalThis === "object" ? globalThis : this, function () {
  var EDGE_COLORS = {
    prereq: [69 / 255, 111 / 255, 201 / 255],
    apply: [195 / 255, 161 / 255, 40 / 255],
    contrast: [199 / 255, 90 / 255, 82 / 255],
    related: [117 / 255, 112 / 255, 104 / 255],
    legacy: [187 / 255, 180 / 255, 169 / 255],
  };

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function stageScale(stage) {
    if (!stage || !stage.style) return 1;
    var match = String(stage.style.transform || "").match(/scale\(([^)]+)\)/);
    var value = match ? Number(match[1]) : 1;
    return Number.isFinite(value) && value > 0 ? value : 1;
  }

  function parseCurve(path) {
    var values = String(path || "").match(/-?\d+(?:\.\d+)?/g);
    if (!values || values.length !== 8) return null;
    values = values.map(Number);
    if (!values.every(Number.isFinite)) return null;
    return {
      p0: [values[0], values[1]],
      p1: [values[2], values[3]],
      p2: [values[4], values[5]],
      p3: [values[6], values[7]],
    };
  }

  function cubic(curve, t) {
    var u = 1 - t, uu = u * u, tt = t * t;
    return [
      uu * u * curve.p0[0] + 3 * uu * t * curve.p1[0] + 3 * u * tt * curve.p2[0] + tt * t * curve.p3[0],
      uu * u * curve.p0[1] + 3 * uu * t * curve.p1[1] + 3 * u * tt * curve.p2[1] + tt * t * curve.p3[1],
    ];
  }

  function compile(gl, type, source) {
    var shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      var error = gl.getShaderInfoLog(shader) || "shader compile failed";
      gl.deleteShader(shader);
      throw new Error(error);
    }
    return shader;
  }

  function program(gl, vertex, fragment) {
    var out = gl.createProgram();
    var vertexShader = null;
    var fragmentShader = null;
    try {
      vertexShader = compile(gl, gl.VERTEX_SHADER, vertex);
      fragmentShader = compile(gl, gl.FRAGMENT_SHADER, fragment);
      gl.attachShader(out, vertexShader);
      gl.attachShader(out, fragmentShader);
      gl.linkProgram(out);
      if (!gl.getProgramParameter(out, gl.LINK_STATUS)) {
        throw new Error(gl.getProgramInfoLog(out) || "program link failed");
      }
      return out;
    } catch (error) {
      if (vertexShader) gl.deleteShader(vertexShader);
      if (fragmentShader) gl.deleteShader(fragmentShader);
      gl.deleteProgram(out);
      throw error;
    }
  }

  function pushVertex(out, point, color, alpha) {
    out.push(point[0], point[1], color[0], color[1], color[2], alpha);
  }

  function pushSegment(out, a, b, width, color, alpha) {
    var dx = b[0] - a[0], dy = b[1] - a[1];
    var length = Math.max(.001, Math.sqrt(dx * dx + dy * dy));
    var ox = -dy / length * width / 2, oy = dx / length * width / 2;
    var p0 = [a[0] + ox, a[1] + oy], p1 = [a[0] - ox, a[1] - oy];
    var p2 = [b[0] + ox, b[1] + oy], p3 = [b[0] - ox, b[1] - oy];
    pushVertex(out, p0, color, alpha); pushVertex(out, p1, color, alpha); pushVertex(out, p2, color, alpha);
    pushVertex(out, p2, color, alpha); pushVertex(out, p1, color, alpha); pushVertex(out, p3, color, alpha);
  }

  function pushArrow(out, tip, previous, size, color, alpha) {
    var dx = tip[0] - previous[0], dy = tip[1] - previous[1];
    var length = Math.max(.001, Math.sqrt(dx * dx + dy * dy));
    var ux = dx / length, uy = dy / length, px = -uy, py = ux;
    var base = [tip[0] - ux * size, tip[1] - uy * size];
    pushVertex(out, tip, color, alpha);
    pushVertex(out, [base[0] + px * size * .48, base[1] + py * size * .48], color, alpha);
    pushVertex(out, [base[0] - px * size * .48, base[1] - py * size * .48], color, alpha);
  }

  function addStyle(document) {
    if (document.getElementById("graph-renderer-style")) return null;
    var style = document.createElement("style");
    style.id = "graph-renderer-style";
    style.textContent = [
      ".graph-renderer-layer{position:absolute;left:0;top:0;z-index:1;pointer-events:none}",
      "#graph-canvas.graph-renderer-active .graph-edges{display:none}",
    ].join("\n");
    (document.head || document.documentElement).appendChild(style);
    return style;
  }

  function attach(runtime, root) {
    root = root || (typeof globalThis === "object" ? globalThis : null);
    var document = root && root.document;
    if (!document || !runtime || !runtime.state) {
      throw new Error("GraphRenderer requires a browser graph runtime");
    }
    var stage = document.getElementById("graph-stage");
    var canvasHost = document.getElementById("graph-canvas");
    if (!stage || !canvasHost || typeof document.createElement !== "function") {
      throw new Error("GraphRenderer requires the Workbench graph surface");
    }

    var canvas = document.createElement("canvas");
    var gl = canvas.getContext && canvas.getContext("webgl2", {
      alpha: true,
      antialias: true,
      premultipliedAlpha: true,
      powerPreference: "high-performance",
    });
    if (!gl) throw new Error("Lesson Kit knowledge graph requires WebGL2");

    var state = runtime.state;
    var routePorts = runtime.computePortSlots;
    var routePath = runtime.edgePath;
    var edgeProgram = null;
    var edgeBuffer = null;
    var styleElement = null;
    var frame = null;
    var destroyed = false;
    var runtimePatched = false;

    function resize() {
      var dpr = clamp(Number(root.devicePixelRatio) || 1, 1, 2);
      var cssWidth = Math.max(1, state.stageWidth), cssHeight = Math.max(1, state.stageHeight);
      var width = Math.round(cssWidth * dpr), height = Math.round(cssHeight * dpr);
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width; canvas.height = height;
        canvas.style.width = cssWidth + "px"; canvas.style.height = cssHeight + "px";
      }
      gl.viewport(0, 0, width, height);
    }

    function bindEdges(vertices) {
      if (!vertices.length) return;
      gl.useProgram(edgeProgram);
      gl.bindBuffer(gl.ARRAY_BUFFER, edgeBuffer);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.DYNAMIC_DRAW);
      var stride = 6 * 4;
      var pos = gl.getAttribLocation(edgeProgram, "a_pos");
      var color = gl.getAttribLocation(edgeProgram, "a_color");
      gl.enableVertexAttribArray(pos);
      gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, stride, 0);
      gl.enableVertexAttribArray(color);
      gl.vertexAttribPointer(color, 4, gl.FLOAT, false, stride, 2 * 4);
      gl.uniform2f(gl.getUniformLocation(edgeProgram, "u_size"), state.stageWidth, state.stageHeight);
      gl.drawArrays(gl.TRIANGLES, 0, vertices.length / 6);
    }

    function draw() {
      frame = null;
      if (destroyed) return;
      resize();
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

      var vertices = [];
      var activeEdges = runtime.visibleEdges();
      routePorts(activeEdges);
      var selected = state.graph.selected;
      var scale = stageScale(stage);

      activeEdges.forEach(function (edge) {
        var curve = parseCurve(routePath(edge));
        if (!curve) return;
        var a = state.byId.get(edge.s), b = state.byId.get(edge.t);
        if (!a || !b || a.opacity < .015 || b.opacity < .015) return;
        var color = EDGE_COLORS[edge.type] || EDGE_COLORS.related;
        var style = runtime.edgeStyle(edge);
        var edgeFocus = 1;
        if (selected) {
          edgeFocus = edge.s === selected || edge.t === selected ? 1
            : a.focusWeight >= .48 && b.focusWeight >= .48 ? .38 : .07;
        }
        var alpha = Math.min(a.opacity, b.opacity) * edgeFocus * style.baseOpacity;
        var width = style.width / Math.max(.25, scale);
        var previous = cubic(curve, 0);
        for (var i = 1; i <= 16; i += 1) {
          var point = cubic(curve, i / 16);
          var paint = edge.type === "contrast" ? i % 2 === 0
            : edge.type === "legacy" ? i % 3 === 1 : true;
          if (paint) pushSegment(vertices, previous, point, width, color, alpha);
          previous = point;
        }
        if ((edge.type === "prereq" || edge.type === "apply") && edge.direction !== "symmetric") {
          pushArrow(vertices, curve.p3, cubic(curve, .93), 7 / Math.max(.35, scale), color, alpha);
        }
      });
      bindEdges(vertices);
      frame = root.requestAnimationFrame(draw);
    }

    function cleanup() {
      if (destroyed) return;
      destroyed = true;
      if (frame !== null) {
        root.cancelAnimationFrame(frame);
        frame = null;
      }
      if (runtimePatched) {
        runtime.computePortSlots = routePorts;
        runtime.edgePath = routePath;
        runtimePatched = false;
      }
      canvasHost.classList.remove("graph-renderer-active");
      if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
      if (styleElement && styleElement.parentNode) styleElement.parentNode.removeChild(styleElement);
      if (edgeBuffer) gl.deleteBuffer(edgeBuffer);
      if (edgeProgram) gl.deleteProgram(edgeProgram);
    }

    try {
      edgeProgram = program(gl,
        "#version 300 es\nin vec2 a_pos;in vec4 a_color;uniform vec2 u_size;out vec4 v_color;void main(){vec2 p=(a_pos/u_size)*2.0-1.0;gl_Position=vec4(p.x,-p.y,0,1);v_color=a_color;}",
        "#version 300 es\nprecision mediump float;in vec4 v_color;out vec4 outColor;void main(){outColor=v_color;}"
      );
      edgeBuffer = gl.createBuffer();
      canvas.className = "graph-renderer-layer";
      stage.insertBefore(canvas, stage.firstChild || null);
      styleElement = addStyle(document);
      canvasHost.classList.add("graph-renderer-active");

      // Keep routing in the physics contract while the renderer owns paint.
      runtime.computePortSlots = function () { return state.portSlots; };
      runtime.edgePath = function () { return "M 0 0"; };
      runtimePatched = true;
      frame = root.requestAnimationFrame(draw);
    } catch (error) {
      cleanup();
      throw error;
    }

    return {
      render: draw,
      resize: resize,
      destroy: cleanup,
    };
  }

  return {
    attach: attach,
    cubic: cubic,
    parseCurve: parseCurve,
    stageScale: stageScale,
  };
}));
