"use strict";

// Runs the REAL browser renderer out of workbench.js and prints one JSON line
// per case. The Python parity test drives this and compares byte-for-byte
// against pages._rich / pages._render_markdown.
//
// Usage: node renderer_parity_cases.js <cases.json>

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../../workbench/server/static/workbench.js"), "utf8");
const LINES = SOURCE.split(/\r?\n/);

function block(fromRe, toRe) {
  const start = LINES.findIndex((line) => fromRe.test(line));
  const end = LINES.findIndex((line, i) => i > start && toRe.test(line));
  if (start < 0 || end < 0) {
    throw new Error("workbench.js block not found: " + fromRe + " .. " + toRe);
  }
  return LINES.slice(start, end).join("\n");
}

// The renderer helpers are private to the IIFE, so lift the exact source of
// escapeHtml + richInline + richText into a context that supplies the one
// binding they close over: WS, the workspace name read from #layout.
const context = vm.createContext({ WS: "dmath", console });
vm.runInContext(
  block(/^ {2}function escapeHtml\(/, /^ {2}\/\* Placeholder delimiters/)
  + "\n"
  + block(/^ {2}\/\* Placeholder delimiters/, /^ {2}function recordRecent\(/)
  + "\nglobalThis.richInline = richInline;\nglobalThis.richText = richText;",
  context, { filename: "workbench-renderer.js" });

const parsed = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const cases = Array.isArray(parsed) ? parsed : parsed.cases;
for (const item of cases) {
  const src = item.markdown ?? item.in ?? "";
  const mode = item.mode ?? "block";
  const out = mode === "inline"
    ? context.richInline(src)
    : context.richText(src);
  process.stdout.write(JSON.stringify({ mode, in: src, out }) + "\n");
}
