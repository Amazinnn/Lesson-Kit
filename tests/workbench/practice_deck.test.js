"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const deck = require("../../workbench/server/static/practice-deck.js");

function problemItem(id, payload) {
  return { id, kind: "problem", payload: payload || { problem_id: id, problem_text: "题面 " + id } };
}

function cardItem(id, front, back) {
  return { id, kind: "card", payload: { card_id: id, front: front || "正面 " + id, back: back || "背面 " + id } };
}

test("append moves the cursor to the tail", () => {
  const d = deck.createDeck();
  assert.equal(deck.current(d), null);
  assert.equal(deck.atEnd(d), true);
  deck.append(d, problemItem("p-1"));
  deck.append(d, problemItem("p-2"));
  assert.equal(deck.current(d).id, "p-2");
  assert.equal(deck.atEnd(d), true);
  assert.deepEqual(deck.ids(d), ["p-1", "p-2"]);
});

test("goTo navigates history and rejects out-of-range indexes", () => {
  const d = deck.createDeck();
  deck.append(d, problemItem("p-1"));
  deck.append(d, problemItem("p-2"));
  deck.append(d, problemItem("p-3"));
  assert.equal(deck.goTo(d, 0).id, "p-1");
  assert.equal(deck.atEnd(d), false);
  assert.equal(deck.goTo(d, 1).id, "p-2");
  assert.equal(deck.goTo(d, -1), null);
  assert.equal(deck.goTo(d, 99), null);
  assert.equal(deck.current(d).id, "p-2");
});

test("settle merges a patch into the item with the given id", () => {
  const d = deck.createDeck();
  deck.append(d, problemItem("p-1"));
  deck.append(d, problemItem("p-2"));
  const settled = deck.settle(d, "p-1", { choices: ["是"], verdict: true, state: "unrated" });
  assert.equal(settled.state, "unrated");
  assert.equal(settled.verdict, true);
  assert.deepEqual(settled.choices, ["是"]);
  assert.equal(deck.settle(d, "missing"), null);
  // other items untouched
  assert.equal(deck.current(d).verdict, null);
});

test("serialize / deserialize round-trips cursor, cards, and view state", () => {
  const d = deck.createDeck();
  deck.append(d, cardItem("kp-1-fc-001", "鸽巢原理", "n+1 个物品放进 n 个抽屉"));
  deck.append(d, problemItem("mq-001", { problem_id: "mq-001", problem_text: "1+1=?" }));
  deck.settle(d, "kp-1-fc-001", { revealed: true, state: "unrated" });
  deck.settle(d, "mq-001", { choices: ["2"], verdict: false, answer_text: "2", state: "unrated" });
  deck.goTo(d, 0);
  const restored = deck.deserialize(deck.serialize(d));
  assert.equal(restored.cursor, 0);
  assert.equal(restored.items.length, 2);
  const card = restored.items[0];
  assert.equal(card.kind, "card");
  assert.equal(card.payload.front, "鸽巢原理");
  assert.equal(card.payload.back, "n+1 个物品放进 n 个抽屉");
  assert.equal(card.revealed, true);
  assert.equal(card.state, "unrated");
  const problem = restored.items[1];
  assert.equal(problem.kind, "problem");
  assert.equal(problem.payload.problem_text, "1+1=?");
  assert.deepEqual(problem.choices, ["2"]);
  assert.equal(problem.verdict, false);
  assert.equal(problem.answer_text, "2");
});

test("wire format keeps the historical session-entry field names", () => {
  const d = deck.createDeck();
  deck.append(d, cardItem("kp-1-fc-002"));
  const data = deck.serialize(d);
  const entry = data.items[0];
  assert.equal(data.v, 2);
  assert.equal(entry.problem_id, "kp-1-fc-002");
  assert.equal(entry.card, true);
  assert.equal(entry.front, "正面 kp-1-fc-002");
  assert.equal(entry.back, "背面 kp-1-fc-002");
  assert.equal(entry.state, "active");
});

test("deserialize accepts the v1 legacy bare-array format at the tail", () => {
  const legacy = [
    { problem_id: "mq-003", answer_text: "是", state: "rated" },
    { problem_id: "kp-1-fc-003", card: true, front: "F", back: "B", answer_text: "", state: "unrated" },
  ];
  const d = deck.deserialize(legacy);
  assert.equal(d.cursor, 1);
  assert.equal(d.items[0].kind, "problem");
  assert.equal(d.items[0].answer_text, "是");
  assert.equal(d.items[0].verdict, null);
  assert.equal(d.items[1].kind, "card");
  assert.equal(d.items[1].payload.back, "B");
  assert.equal(deck.atEnd(d), true);
});

test("deserialize clamps a stale cursor to the tail", () => {
  const d = deck.deserialize({ v: 2, cursor: 99, items: [
    { problem_id: "a", state: "active" },
    { problem_id: "b", state: "active" },
  ] });
  assert.equal(d.cursor, 1);
});

test("deserialize of unknown input yields an empty deck", () => {
  const d = deck.deserialize(null);
  assert.equal(d.items.length, 0);
  assert.equal(d.cursor, -1);
  assert.equal(deck.current(deck.deserialize("junk")), null);
});

test("the exhausted flag survives a round trip", () => {
  const d = deck.deserialize({ v: 2, cursor: 0, ended: true, items: [
    { problem_id: "p-1", state: "unrated" },
  ] });
  assert.equal(d.ended, true);
  const out = deck.serialize(d);
  assert.equal(out.ended, true);
  assert.equal(deck.deserialize(deck.serialize(deck.createDeck())).ended, false);
  assert.equal("ended" in deck.serialize(deck.createDeck()), false);
});
