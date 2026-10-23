"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const SOURCE = fs.readFileSync(
  path.join(__dirname, "../../workbench/server/static/middle-navigation.js"),
  "utf8",
);

function navigationFixture() {
  const events = {};
  const requests = [];
  const historyCalls = [];
  const middlePage = { innerHTML: "practice page" };
  const layout = { dataset: { workspace: "alpha", page: "practice" } };
  const aiColumn = { identity: "persistent-agent-rail" };
  const currentNav = { classList: classList(true) };
  const ids = {
    layout,
    "middle-page": middlePage,
    "ai-column": aiColumn,
  };
  const document = {
    head: { appendChild() {} },
    addEventListener(type, callback) { (events[type] ||= []).push(callback); },
    getElementById(id) { return ids[id] || null; },
    querySelectorAll(selector) {
      return selector === "#left-column .nav-item" ? [currentNav] : [];
    },
  };
  const window = {
    location: { href: "http://lesson-kit.test/w/alpha/practice" },
    history: {
      pushState(state, title, href) {
        historyCalls.push(["push", href]);
        window.location.href = href;
      },
      replaceState(state, title, href) {
        historyCalls.push(["replace", href]);
        window.location.href = href;
      },
    },
    addEventListener(type, callback) { (events[`window:${type}`] ||= []).push(callback); },
    fetch(href, options) {
      requests.push({ href, options });
      return Promise.resolve({
        ok: true,
        url: href,
        text: () => Promise.resolve(href),
      });
    },
    WorkbenchMiddlePage: {
      dispose() { events.disposed = (events.disposed || 0) + 1; },
      mount() { events.mounted = (events.mounted || 0) + 1; },
    },
    AgentUISurfaces: { renderContext() { events.contextRendered = (events.contextRendered || 0) + 1; } },
  };
  Object.defineProperty(window.location, "origin", {
    get() { return new URL(window.location.href).origin; },
  });

  class FakeDOMParser {
    parseFromString(href) {
      const address = new URL(href);
      const page = address.pathname.split("/").pop();
      const nextLayout = { dataset: { workspace: "alpha", page, objectType: page, objectId: page + "-1" } };
      const nextNav = { classList: classList(page === "goals") };
      return {
        getElementById(id) {
          if (id === "layout") return nextLayout;
          if (id === "middle-page") return { innerHTML: `page:${page}` };
          return null;
        },
        querySelectorAll(selector) {
          return selector === "#left-column .nav-item" ? [nextNav] : [];
        },
      };
    }
  }

  vm.runInNewContext(SOURCE, { window, document, DOMParser: FakeDOMParser, URL, Promise, Array, decodeURIComponent });
  return { aiColumn, currentNav, document, events, historyCalls, layout, middlePage, requests, window };
}

function classList(active) {
  return {
    contains(name) { return name === "active" && active; },
    toggle(name, value) { if (name === "active") active = value; return active; },
  };
}

function anchor(href, options = {}) {
  return {
    href,
    closest(selector) { return selector === "#left-column, #middle" ? {} : null; },
    hasAttribute(name) { return !!options[name]; },
    getAttribute(name) { return options[name] || null; },
  };
}

async function flush() {
  await new Promise((resolve) => setImmediate(resolve));
  await new Promise((resolve) => setImmediate(resolve));
}

test("same-workspace link and popstate replace only the middle page and refresh context", async () => {
  const app = navigationFixture();
  const link = anchor("http://lesson-kit.test/w/alpha/goals");
  let prevented = false;
  app.events.click[0]({
    target: { closest: () => link }, button: 0,
    preventDefault() { prevented = true; },
  });
  await flush();

  assert.equal(prevented, true);
  assert.equal(app.middlePage.innerHTML, "page:goals");
  assert.equal(app.layout.dataset.page, "goals");
  assert.equal(app.layout.dataset.objectId, "goals-1");
  // The scope tray is retired (the page never rendered it) and nothing in the
  // product consumes kp names, so there is no tray to refresh any more.
  assert.equal(app.events.disposed, 1);
  assert.equal(app.events.mounted, 1);
  assert.equal(app.events.contextRendered, 1);
  assert.equal(app.document.getElementById("ai-column"), app.aiColumn);
  assert.deepEqual(app.historyCalls, [["push", "http://lesson-kit.test/w/alpha/goals"]]);

  app.window.location.href = "http://lesson-kit.test/w/alpha/practice";
  app.events["window:popstate"][0]();
  await flush();
  assert.equal(app.middlePage.innerHTML, "page:practice");
  assert.equal(app.historyCalls.length, 1, "popstate does not create a new entry");
  assert.equal(app.events.disposed, 2);
  assert.equal(app.events.mounted, 2);
});

test("modified, downloaded, targeted, and cross-workspace links keep native navigation", async () => {
  const app = navigationFixture();
  const cases = [
    [anchor("http://lesson-kit.test/w/alpha/goals"), { ctrlKey: true }],
    [anchor("http://lesson-kit.test/w/alpha/goals", { download: true }), {}],
    [anchor("http://lesson-kit.test/w/alpha/goals", { target: true }), {}],
    [anchor("http://lesson-kit.test/w/alpha/goals", { rel: "noopener external" }), {}],
    [anchor("http://lesson-kit.test/w/beta/goals"), {}],
    [anchor("https://example.test/"), {}],
  ];
  for (const [link, modifiers] of cases) {
    let prevented = false;
  app.events.click[0]({
      target: { closest: () => link }, button: 0,
      preventDefault() { prevented = true; },
      ...modifiers,
    });
    assert.equal(prevented, false);
  }
  await flush();
  assert.equal(app.requests.length, 0);
  assert.equal(app.historyCalls.length, 0);
});
