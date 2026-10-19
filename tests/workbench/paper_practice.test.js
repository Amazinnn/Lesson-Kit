"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const SOURCE = fs.readFileSync(
  path.join(__dirname, "../../workbench/server/static/paper-practice.js"),
  "utf8",
);

function element(id) {
  const listeners = {};
  const classes = new Set();
  return {
    id,
    value: "",
    checked: false,
    disabled: false,
    hidden: false,
    textContent: "",
    innerHTML: "",
    dataset: {},
    children: [],
    style: {},
    handlers: listeners,
    classList: {
      add(name) { classes.add(name); },
      remove(name) { classes.delete(name); },
      contains(name) { return classes.has(name); },
      toggle(name, force) {
        const enabled = force === undefined ? !classes.has(name) : !!force;
        if (enabled) classes.add(name); else classes.delete(name);
        return enabled;
      },
    },
    addEventListener(type, callback) { (listeners[type] ||= []).push(callback); },
    dispatch(type, event = {}) {
      event.target ||= this;
      return (listeners[type] || []).map((callback) => callback(event)).at(-1);
    },
    appendChild(child) { this.children.push(child); return child; },
    replaceChildren(...children) { this.children = children; },
    setAttribute(name, value) { this[name] = String(value); },
    removeAttribute(name) { delete this[name]; },
    getAttribute(name) { return this[name] || null; },
    querySelectorAll() { return []; },
    closest() { return null; },
  };
}

const PAPER_IDS = [
  "paper-practice", "paper-setup", "paper-title", "paper-count", "paper-reveal-timing",
  "paper-start", "paper-error", "paper-work", "paper-question", "paper-answer",
  "paper-options", "paper-item-submit", "paper-reference", "paper-rating", "paper-toolbar",
  "paper-prev", "paper-next", "paper-stuck", "paper-final-submit", "paper-dots",
  "paper-pause", "paper-completion", "paper-completion-stats", "paper-review",
  "paper-return", "paper-again", "paper-links",
  "legacy-practice",
];

function problem(id, quizType, answerKey, options) {
  return {
    problem_id: id,
    display_title: "题目 " + id,
    problem_text: "题面 " + id,
    micro_quiz: quizType ? {
      quiz_type: quizType,
      options: options || [],
      answer_key: answerKey,
      error_reason: "因为答案键如此",
    } : null,
    solution: "解析 " + id,
  };
}

function practice(options = {}) {
  return {
    execution_id: 91,
    source_ref: "ps-017",
    source_label: "期中练习卷",
    paper_generation: 3,
    reveal_timing: options.revealTiming === undefined ? "per_item" : options.revealTiming,
    rating_mode: "immediate",
    cursor: options.cursor || 0,
    items: options.items || [{
      position: 0,
      item_type: "problem",
      item_id: "p-1",
      content_revision: 7,
      state: "pending",
      draft_sequence: 0,
      draft: { answer: "", choices: [], stuck: false, reference_viewed: false },
      payload: problem("p-1", "single_choice", "A", ["A", "B"]),
    }],
  };
}

function fixture(options = {}) {
  const events = {};
  const calls = [];
  const ids = Object.fromEntries(PAPER_IDS.map((id) => [id, element(id)]));
  ids["legacy-practice"].hidden = true;
  ids["legacy-practice"].classList.add("hidden");
  ids["paper-reveal-timing"].value = "per_item";
  const document = {
    getElementById(id) { return ids[id] || null; },
    createElement(tag) { return element(tag); },
    querySelectorAll() { return []; },
  };
  const local = options.localStorage || new Map();
  const window = {
    location: { href: options.href || "http://lesson-kit.test/w/alpha/practice" },
    history: {
      replaceState(_state, _title, target) {
        window.location.href = new URL(target, window.location.href).href;
      },
    },
    localStorage: {
      getItem(key) { return local.has(key) ? local.get(key) : null; },
      setItem(key, value) { local.set(key, String(value)); },
      removeItem(key) { local.delete(key); },
    },
    crypto: { randomUUID: (() => { let id = 0; return () => "request-" + (++id); })() },
  };
  const api = async (path, request) => {
    if (request && request.method === "DELETE") {
      calls.push({ method: "DELETE", path, body: JSON.parse(request.body || "{}") });
      return {};
    }
    calls.push({ method: "GET", path });
    if (path === "/practice/current") return { practice: options.active || null };
    if (path.startsWith("/practice-sets/")) {
      return options.savedPaper || {
        practice_set_id: "ps-017", title: "期中练习卷", count: 1,
        plan: { items: [{ problem_id: "p-1" }] },
      };
    }
    if (path.startsWith("/practice/runs/")) return options.archived || practice();
    return {};
  };
  const write = async (method, path, body) => {
    calls.push({ method, path, body });
    const key = method + " " + path;
    if (options.writeHandlers && options.writeHandlers[key]) {
      return options.writeHandlers[key](body);
    }
    if (path === "/practice-sets/ps-017/start") return { practice: options.started || practice({ revealTiming: body.reveal_timing }) };
  if (path === "/attempts") return { attempt_id: 501, problem_id: "p-1", recorded: true,
    practice: { practice: options.afterAttempt || practice() } };
    if (path === "/practice/current/submit") return { completed: true, run_id: 112, execution_id: 91 };
    if (path === "/practice/current/navigate") return { practice: options.active || practice({ cursor: body.position }) };
    if (path === "/practice/current/stuck") return { practice: options.active || practice({ revealTiming: "on_submit" }) };
    if (path === "/practice/draft") return { saved: true };
    if (path === "/feedback") return { saved: true };
    return {};
  };
  const deps = {
    api,
    post: (path, body) => write("POST", path, body),
    patch: (path, body) => write("PATCH", path, body),
    store() {},
    load(_key, fallback) { return fallback; },
    showRatingEnabled() { return true; },
    renderMath() {},
    escapeHtml(value) { return String(value).replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#x27;",
    }[ch])); },
    richText(value) { return "<span>" + String(value) + "</span>"; },
    navigate(target) { events.navigated = target; },
  };
  const context = { document, window, URL, Promise, Array, Object, JSON, Number, String, Math, Date, setTimeout, clearTimeout };
  vm.runInNewContext(SOURCE, context);
  const legacyCalls = [];
  const runtime = context.PaperPractice.start(deps, (...args) => {
    legacyCalls.push(args);
    return { currentProblem() { return null; }, session() { return []; }, selectionContext() { return {}; }, dispose() {} };
  });
  return { calls, deps, document, events, ids, legacyCalls, local, runtime, window };
}

async function flush() {
  for (let i = 0; i < 5; i += 1) await new Promise((resolve) => setImmediate(resolve));
}

test("saved Paper setup fixes the selected reveal timing when starting", async () => {
  const app = fixture({ href: "http://lesson-kit.test/w/alpha/practice?paper=ps-017" });
  await flush();

  assert.equal(app.ids["paper-title"].textContent, "期中练习卷");
  assert.equal(app.ids["paper-count"].textContent, "1");
  app.ids["paper-reveal-timing"].value = "on_submit";
  await app.ids["paper-start"].dispatch("click");
  await flush();

  const start = app.calls.find((call) => call.path === "/practice-sets/ps-017/start");
  assert.deepEqual(JSON.parse(JSON.stringify(start.body)), {
    practice_mode: "exam", rating_mode: "immediate", reveal_timing: "on_submit",
  });
  assert.match(app.ids["paper-question"].innerHTML, /题面 p-1/);
  assert.ok(app.ids["paper-question"].innerHTML.includes(app.ids["paper-title"].textContent));
  assert.equal(app.ids["paper-item-submit"].hidden, true);
});

test("opening a saved Paper shows its setup even when another Paper is active", async () => {
  const other = { ...practice(), source_ref: "ps-099", source_label: "Other Paper" };
  const app = fixture({
    href: "http://lesson-kit.test/w/alpha/practice?paper=ps-017",
    active: other,
  });
  await flush();

  assert.equal(app.ids["paper-setup"].hidden, false);
  assert.equal(app.ids["paper-title"].textContent, "期中练习卷");
  assert.equal(app.ids["paper-start"].disabled, false);
  assert.equal(app.legacyCalls.length, 0);
});

test("the plain practice route shows the saved-Paper entry state when nothing is active", async () => {
  const app = fixture();
  await flush();

  assert.equal(app.ids["paper-setup"].hidden, false);
  assert.equal(app.ids["paper-start"].disabled, true);
  assert.equal(app.legacyCalls.length, 0);
});

test("a legacy ordinary saved-Paper run adopts per-item mode before interaction", async () => {
  const legacy = practice({ revealTiming: null });
  const adopted = practice({ revealTiming: "per_item" });
  const app = fixture({
    active: legacy,
    writeHandlers: {
      "POST /practice/current/navigate": (body) => {
        assert.equal(body.execution_id, legacy.execution_id);
        assert.equal(body.position, legacy.cursor);
        return { practice: adopted };
      },
    },
  });
  await flush();

  const adoption = app.calls.find((call) => call.path === "/practice/current/navigate");
  assert.ok(adoption);
  assert.equal(adoption.body.position, 0);
  assert.equal(app.ids["paper-answer"].disabled, false);
  assert.equal(app.runtime.session()[0].state, "pending");
});

test("a fixed temporary ordinary execution adopts free navigation without a saved-Paper ID", async () => {
  const legacy = { ...practice({ revealTiming: null }), source_ref: null, source_label: "CLI practice" };
  const adopted = { ...legacy, reveal_timing: "per_item" };
  const app = fixture({
    active: legacy,
    writeHandlers: {
      "POST /practice/current/navigate": () => ({ practice: adopted }),
    },
  });
  await flush();

  assert.equal(app.legacyCalls.length, 0);
  assert.equal(app.ids["paper-work"].hidden, false);
  assert.ok(app.calls.some((call) => call.path === "/practice/current/navigate"));
  assert.match(app.ids["paper-question"].innerHTML, /CLI practice/);
});

test("card executions reveal the legacy practice surface when delegated", async () => {
  const active = { ...practice(), items: [{ position: 0, item_type: "card", item_id: "card-1" }] };
  const app = fixture({ active });
  await flush();

  assert.equal(app.legacyCalls.length, 1);
  assert.equal(app.ids["paper-practice"].hidden, true);
  assert.equal(app.ids["legacy-practice"].hidden, false);
  assert.equal(app.ids["legacy-practice"].classList.contains("hidden"), false);
});

test("single-choice selection submits once and shows the returned locked result", async () => {
  const answered = practice({ items: [{
    position: 0, item_type: "problem", item_id: "p-1", content_revision: 7,
    state: "answered", attempt_id: 501, draft_sequence: 0,
    draft: { answer: "", choices: [], stuck: false, reference_viewed: false },
    attempt: { attempt_id: 501, answer_text: "A", choices: [], verdict: true },
    payload: problem("p-1", "single_choice", "A", ["A", "B"]),
  }] });
  const app = fixture({ active: practice(), afterAttempt: answered });
  await flush();
  const radio = { dataset: { choice: "A" }, value: "A", checked: true };
  await app.ids["paper-options"].dispatch("change", { target: radio });
  await flush();

  const attempt = app.calls.find((call) => call.path === "/attempts");
  assert.equal(attempt.body.problem_id, "p-1");
  assert.equal(attempt.body.answer_text, "A");
  assert.equal(attempt.body.verdict, true);
  assert.equal(app.ids["paper-reference"].hidden, false);
  assert.equal(app.runtime.session()[0].attempt_id, 501);
  assert.equal(app.ids["paper-options"].children[0].children[1].children[0].checked, true);
});

test("single-choice controls lock while the first answer request is unresolved", async () => {
  const answered = practice({ items: [{
    position: 0, item_type: "problem", item_id: "p-1", content_revision: 7,
    state: "answered", attempt_id: 501, draft_sequence: 0,
    draft: { answer: "", choices: [], stuck: false, reference_viewed: false },
    attempt: { attempt_id: 501, answer_text: "A", choices: [], verdict: true },
    payload: problem("p-1", "single_choice", "A", ["A", "B"]),
  }] });
  let resolveAttempt;
  const pendingResponse = new Promise((resolve) => { resolveAttempt = resolve; });
  const app = fixture({
    active: practice(),
    afterAttempt: answered,
    writeHandlers: { "POST /attempts": () => pendingResponse },
  });
  await flush();

  await app.ids["paper-options"].dispatch("change", {
    target: { dataset: { paperChoice: "A" }, value: "A", checked: true },
  });
  const firstRadio = app.ids["paper-options"].children[0].children[1].children[0];
  assert.equal(firstRadio.disabled, true);
  app.ids["paper-options"].dispatch("change", {
    target: { dataset: { paperChoice: "B" }, value: "B", checked: true },
  });
  await flush();
  assert.equal(app.calls.filter((call) => call.path === "/attempts").length, 1);
  assert.equal(app.calls.find((call) => call.path === "/attempts").body.answer_text, "A");

  resolveAttempt({ practice: { practice: answered } });
  await flush();
  assert.equal(app.ids["paper-options"].children[0].children[1].children[0].checked, true);
});

test("whole-Paper navigation keeps drafts editable and sends them only with final submit", async () => {
  const items = [0, 1].map((index) => ({
    position: index, item_type: "problem", item_id: "p-" + (index + 1),
    content_revision: 7, state: "pending", draft_sequence: 0,
    draft: { answer: "", choices: [], stuck: false, reference_viewed: false },
    payload: problem("p-" + (index + 1), "text", null),
  }));
  const app = fixture({ active: practice({ revealTiming: "on_submit", items }) });
  await flush();
  assert.match(app.ids["paper-reference"].innerHTML, /尚未显示/);

  app.ids["paper-answer"].value = "第一题答案";
  app.ids["paper-answer"].dispatch("input");
  await app.ids["paper-next"].dispatch("click");
  await flush();
  app.ids["paper-answer"].value = "第二题答案";
  app.ids["paper-answer"].dispatch("input");
  await app.ids["paper-final-submit"].dispatch("click");
  await flush();

  const finalize = app.calls.find((call) => call.path === "/practice/current/submit");
  assert.ok(finalize);
  assert.equal(finalize.body.drafts.length, 2);
  assert.equal(finalize.body.drafts[0].draft.answer, "第一题答案");
  assert.equal(finalize.body.drafts[1].draft.answer, "第二题答案");
  assert.equal(app.ids["paper-completion"].hidden, false);
  assert.equal(app.calls.some((call) => call.path === "/attempts"), false);
});

test("per-item finalization submits only still-pending draft rows", async () => {
  const items = [
    {
      position: 0, item_type: "problem", item_id: "p-1", content_revision: 7,
      state: "answered", attempt_id: 501,
      draft: { answer: "", choices: [], stuck: false, reference_viewed: true },
      attempt: { attempt_id: 501, answer_text: "A", verdict: true },
      payload: problem("p-1", "single_choice", "A", ["A", "B"]),
    },
    {
      position: 1, item_type: "problem", item_id: "p-2", content_revision: 4,
      state: "pending", draft_sequence: 0,
      draft: { answer: "still thinking", choices: [], stuck: false, reference_viewed: false },
      payload: problem("p-2", "text", null),
    },
  ];
  const app = fixture({ active: practice({ items }) });
  await flush();

  assert.equal(app.ids["paper-final-submit"].hidden, false);
  await app.ids["paper-final-submit"].dispatch("click");
  await flush();

  const final = app.calls.find((call) => call.path === "/practice/current/submit");
  assert.deepEqual(final.body.drafts.map((draft) => draft.position), [1]);
  assert.equal(final.body.drafts[0].draft.answer, "still thinking");
});

test("first feedback list response becomes editable and edits use the real object response", async () => {
  const stuck = practice({ items: [{
    position: 0, item_type: "problem", item_id: "p-1", content_revision: 7,
    state: "stuck", attempt_id: 502,
    draft: { answer: "", choices: [], stuck: true, reference_viewed: true },
    attempt: { attempt_id: 502, answer_text: "", stuck: true },
    feedback: null,
    payload: problem("p-1", "text", null),
  }] });
  const app = fixture({
    active: stuck,
    writeHandlers: {
      "POST /feedback": (body) => body.edit_existing
        ? { edited: true, attempt_id: body.attempt_id, feedback_event_id: 818 }
        : ["event logged", "progress updated"],
    },
  });
  await flush();
  assert.equal(app.ids["paper-rating"].hidden, false);

  let fields = app.ids["paper-rating"].children;
  fields[1].children[0].value = "5";
  fields[2].children[0].value = "needs another pass";
  fields[3].dispatch("click");
  await flush();
  assert.equal(app.ids["paper-rating"].children[1].children[0].value, "5");
  assert.equal(app.ids["paper-rating"].children[2].children[0].value, "needs another pass");
  fields = app.ids["paper-rating"].children;
  fields[1].children[0].value = "4";
  fields[2].children[0].value = "reviewed once";
  fields[3].dispatch("click");
  await flush();

  const feedback = app.calls.filter((call) => call.path === "/feedback");
  assert.equal(feedback.length, 2);
  assert.equal(feedback[0].body.edit_existing, undefined);
  assert.equal(feedback[0].body.attempt_id, 502);
  assert.equal(feedback[0].body.practice_context.execution_id, 91);
  assert.equal(feedback[1].body.edit_existing, true);
  assert.equal(feedback[1].body.expected_rating, 5);
  assert.equal(feedback[1].body.expected_note, "needs another pass");
  assert.equal(app.runtime.session()[0].feedback.rating, 4);
  assert.equal(app.runtime.session()[0].feedback.note, "reviewed once");
});

test("editing a historical feedback event preserves its null note token", async () => {
  const stuck = practice({ items: [{
    position: 0, item_type: "problem", item_id: "p-1", content_revision: 7,
    state: "stuck", attempt_id: 502,
    draft: { answer: "", choices: [], stuck: true, reference_viewed: true },
    attempt: { attempt_id: 502, answer_text: "", stuck: true },
    feedback: { id: 818, attempt_id: 502, rating: 3, note: null },
    payload: problem("p-1", "text", null),
  }] });
  const app = fixture({ active: stuck });
  await flush();

  const fields = app.ids["paper-rating"].children;
  fields[1].children[0].value = "4";
  fields[2].children[0].value = "updated";
  fields[3].dispatch("click");
  await flush();

  const feedback = app.calls.find((call) => call.path === "/feedback");
  assert.equal(feedback.body.expected_rating, 3);
  assert.equal(feedback.body.expected_note, null);
});

test("archived answer-sheet review returns to completion without resubmitting", async () => {
  const archived = {
    ...practice(), id: 112, run_id: 112, reveal_timing: "per_item",
    items: [{
      position: 0, item_type: "problem", item_id: "p-1", state: "answered",
      attempt_id: 501, attempt: { attempt_id: 501, answer_text: "A", verdict: true },
      feedback: null, payload: problem("p-1", "single_choice", "A", ["A", "B"]),
    }],
  };
  const app = fixture({ href: "http://lesson-kit.test/w/alpha/practice?run=112", archived });
  await flush();
  assert.equal(app.ids["paper-completion"].hidden, false);
  await app.ids["paper-review"].dispatch("click");
  assert.equal(app.ids["paper-work"].hidden, false);
  assert.equal(app.ids["paper-answer"].disabled, true);
  assert.equal(app.ids["paper-options"].children[0].children[1].children[0].checked, true);
  await app.ids["paper-return"].dispatch("click");
  assert.equal(app.ids["paper-completion"].hidden, false);
  assert.equal(app.calls.some((call) => call.path === "/practice/current/submit"), false);
  await app.ids["paper-again"].dispatch("click");
  await flush();
  assert.equal(app.ids["paper-setup"].hidden, false);
  assert.equal(app.ids["paper-start"].disabled, false);
  assert.match(app.window.location.href, /paper=ps-017/);
});

test("Again starts a fresh temporary Paper run from the archived item order", async () => {
  const archived = {
    ...practice(), id: 113, run_id: 113, source_ref: null, source_label: "CLI practice",
    kp_ids: ["kp-2", "kp-1"], practice_mode: "exam", rating_mode: "off",
    items: [
      { position: 0, item_type: "problem", item_id: "p-2", direction: "", payload: problem("p-2", "text", null) },
      { position: 1, item_type: "problem", item_id: "p-1", direction: "", payload: problem("p-1", "text", null) },
    ],
  };
  const app = fixture({
    href: "http://lesson-kit.test/w/alpha/practice?run=113",
    archived,
    writeHandlers: {
      "POST /practice/current": (body) => ({ practice: {
        ...practice({ revealTiming: body.reveal_timing }),
        source_ref: null,
        source_label: body.source_label,
        items: body.items.map((item, index) => ({
          ...item, position: index, state: "pending", draft: { answer: "", choices: [] },
          payload: problem(item.item_id, "text", null),
        })),
      } }),
    },
  });
  await flush();

  await app.ids["paper-again"].dispatch("click");
  await flush();
  assert.equal(app.ids["paper-setup"].hidden, false);
  assert.equal(app.ids["paper-title"].textContent, "CLI practice");
  assert.equal(app.ids["paper-count"].textContent, "2");
  assert.equal(app.ids["paper-reveal-timing"].disabled, false);
  assert.equal(new URL(app.window.location.href).pathname, "/w/alpha/practice");
  assert.equal(new URL(app.window.location.href).searchParams.has("run"), false);

  app.ids["paper-reveal-timing"].value = "on_submit";
  await app.ids["paper-start"].dispatch("click");
  await flush();
  const start = app.calls.find((call) => call.method === "POST" && call.path === "/practice/current");
  assert.deepEqual(JSON.parse(JSON.stringify(start.body)), {
    source_kind: "paper", source_ref: null, source_label: "CLI practice",
    kp_ids: ["kp-2", "kp-1"], practice_mode: "exam", rating_mode: "immediate",
    reveal_timing: "on_submit",
    items: [
      { item_type: "problem", item_id: "p-2", direction: "" },
      { item_type: "problem", item_id: "p-1", direction: "" },
    ],
  });
  assert.equal(app.ids["paper-work"].hidden, false);
});

test("pause parks the current run with context and returns to the saved-Paper list", async () => {
  const app = fixture({ active: practice() });
  await flush();

  await app.ids["paper-pause"].dispatch("click");
  await flush();

  const pause = app.calls.find((call) => call.method === "DELETE" && call.path === "/practice/current");
  assert.ok(pause);
  assert.equal(pause.body.execution_id, 91);
  assert.equal(pause.body.practice_context.position, 0);
  assert.equal(app.events.navigated, "/w/alpha/practice-sets");
});

test("pausing a temporary ordinary execution flushes drafts without parking its active singleton", async () => {
  const temporary = { ...practice(), source_ref: null, source_label: "CLI practice" };
  const app = fixture({ active: temporary });
  await flush();

  app.ids["paper-answer"].value = "temporary answer";
  app.ids["paper-answer"].dispatch("input");
  await app.ids["paper-pause"].dispatch("click");
  await flush();

  const draft = app.calls.find((call) => call.path === "/practice/draft");
  assert.ok(draft);
  assert.equal(draft.body.draft.answer, "temporary answer");
  assert.equal(app.calls.some((call) => call.method === "DELETE" && call.path === "/practice/current"), false);
  assert.equal(app.events.navigated, "/w/alpha/practice-sets");
});
