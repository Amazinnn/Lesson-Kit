"use strict";

/* Public graph-physics module seam.
 *
 * The semantic solver lives in graph-physics-core.js. This file is only the
 * stable entry point used by callers, so later execution implementations can
 * replace the adapter without changing graph data or page code.
 */
(function (root) {
  if (typeof module === "object" && module.exports) {
    module.exports = require("./graph-physics-core.js");
    return;
  }
  if (!root.document || root.document.readyState !== "loading"
      || typeof root.document.write !== "function") {
    throw new Error("graph-physics.js must be parser-loaded before workbench.js");
  }
  root.document.write('<script src="/static/graph-physics-core.js"><\/script>');
  if (!root.GraphPhysics) throw new Error("graph physics core failed to load");
}(typeof globalThis === "object" ? globalThis : this));
