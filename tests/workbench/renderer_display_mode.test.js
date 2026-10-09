"use strict";

// renderMath must ask KaTeX for display layout on a `$$` block. Without
// `displayMode`, a `$$` span is laid out inline and `\tag` fails outright
// ("\\tag works only in display equations"), so this pins the option that the
// `math display` class implies.

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const LINES = fs.readFileSync(
  path.resolve(__dirname, "../../workbench/server/static/workbench.js"), "utf8",
).split(/\r?\n/);

const start = LINES.findIndex((line) => /^ {2}function renderMath\(/.test(line));
const end = LINES.findIndex((line, i) => i > start && /^ {2}function escapeHtml\(/.test(line));
assert.ok(start >= 0 && end > start, "renderMath block not found in workbench.js");
const SOURCE = LINES.slice(start, end).join("\n");

function fakeSpan(className, textContent) {
  const classes = new Set(className ? className.split(/\s+/) : []);
  return { textContent, classList: { contains: (name) => classes.has(name) } };
}

// Returns the options katex.render was called with, per span text.
function renderWith(spans) {
  const calls = [];
  const katex = { render: (tex, span, options) => calls.push({ tex, options }) };
  // `renderMath` guards on `window.katex` and then calls the bare `katex`
  // global, exactly as the vendored <script> tag provides it in a page.
  const context = vm.createContext({
    document: { querySelectorAll: () => spans },
    window: { katex },
    katex,
  });
  vm.runInContext(SOURCE + "\nglobalThis.renderMath = renderMath;", context);
  context.renderMath();
  return calls;
}

test("a $$ block renders with displayMode on", () => {
  const calls = renderWith([fakeSpan("math display", "x=1")]);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].options.displayMode, true);
});

test("an inline $…$ renders with displayMode off", () => {
  const calls = renderWith([fakeSpan("math", "q = 2")]);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].options.displayMode, false);
});

test("the two span kinds in one document are told apart", () => {
  const calls = renderWith([fakeSpan("math", "a"), fakeSpan("math display", "b")]);
  assert.deepEqual(calls.map((call) => call.options.displayMode), [false, true]);
});

test("KaTeX receives the decoded text, not the HTML entities", () => {
  // The server escapes the fragment once; the browser decodes it once via
  // textContent, so KaTeX must see the original characters.
  const calls = renderWith([fakeSpan("math", "f'(x) < 1")]);
  assert.equal(calls[0].tex, "f'(x) < 1");
});

test("renderMath still tolerates a throwing katex", () => {
  const span = fakeSpan("math display", "x=1");
  const context = vm.createContext({
    document: { querySelectorAll: () => [span] },
    window: { katex: { render: () => { throw new Error("boom"); } } },
  });
  vm.runInContext(SOURCE + "\nglobalThis.renderMath = renderMath;", context);
  assert.doesNotThrow(() => context.renderMath());
});

test("a missing katex leaves the raw text in place", () => {
  const span = fakeSpan("math display", "x=1");
  const context = vm.createContext({
    document: { querySelectorAll: () => [span] },
    window: {},
  });
  vm.runInContext(SOURCE + "\nglobalThis.renderMath = renderMath;", context);
  assert.doesNotThrow(() => context.renderMath());
  assert.equal(span.textContent, "x=1");
});
