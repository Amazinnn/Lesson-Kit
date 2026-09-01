"use strict";

/* practice-deck — session deck for the practice flow (vanilla JS, no build).
   Owns the session history, cursor, and per-item state so grading holds,
   card revisits, and task context read one structure instead of scattered
   DOM/session keys. Pure logic: no DOM, no network. */

(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.PracticeDeck = api;
}(typeof globalThis === "object" ? globalThis : this, function () {
  // Item states follow the historical session-entry semantics:
  // active (open on the table), unrated (played, rating deferred),
  // rated, skipped.
  function createDeck() {
    return { items: [], cursor: -1, ended: false };
  }

  function makeItem(entry) {
    return {
      id: entry.id,
      kind: entry.kind === "card" ? "card" : "problem",
      payload: entry.payload || null,
      answer_text: entry.answer_text || "",
      choices: entry.choices || [],
      verdict: entry.verdict === undefined ? null : entry.verdict,
      revealed: !!entry.revealed,
      state: entry.state || "active",
      direction: entry.kind === "card" ? (entry.direction || "forward") : "",
    };
  }

  function append(deck, entry) {
    var item = makeItem(entry);
    deck.items.push(item);
    deck.cursor = deck.items.length - 1;
    return item;
  }

  function find(deck, id, direction) {
    for (var i = 0; i < deck.items.length; i += 1) {
      if (deck.items[i].id === id
          && (direction === undefined || deck.items[i].direction === direction)) {
        return deck.items[i];
      }
    }
    return null;
  }

  function current(deck) {
    return deck.items[deck.cursor] || null;
  }

  function atEnd(deck) {
    return deck.cursor >= deck.items.length - 1;
  }

  function goTo(deck, index) {
    if (index < 0 || index >= deck.items.length) return null;
    deck.cursor = index;
    return deck.items[index];
  }

  function settle(deck, id, patch, direction) {
    var item = find(deck, id, direction);
    if (!item) return null;
    Object.keys(patch || {}).forEach(function (key) {
      item[key] = patch[key];
    });
    return item;
  }

  function ids(deck) {
    return deck.items.map(function (item) { return item.id; });
  }

  function serializeItem(item) {
    // Wire format keeps the historical session-entry field names
    // (problem_id / state / answer_text / card / front / back) so the
    // session-end view and legacy readers stay compatible.
    var data = {
      problem_id: item.id,
      state: item.state,
      answer_text: item.answer_text || "",
    };
    if (item.kind === "card") {
      data.card = true;
      data.front = (item.payload && item.payload.front) || "";
      data.back = (item.payload && item.payload.back) || "";
      data.directions = (item.payload && item.payload.directions) || ["forward"];
      data.direction = item.direction || "forward";
    } else {
      data.payload = item.payload || null;
    }
    if (item.choices && item.choices.length) data.choices = item.choices;
    if (typeof item.verdict === "boolean") data.verdict = item.verdict;
    if (item.revealed) data.revealed = true;
    return data;
  }

  function serialize(deck) {
    var data = { v: 2, cursor: deck.cursor, items: deck.items.map(serializeItem) };
    if (deck.ended) data.ended = true;
    return data;
  }

  function deserializeItem(data) {
    var card = !!data.card;
    return {
      id: data.problem_id,
      kind: card ? "card" : "problem",
      payload: card
        ? { card_id: data.problem_id, front: data.front, back: data.back,
            directions: data.directions || ["forward"] }
        : (data.payload || null),
      answer_text: data.answer_text || "",
      choices: data.choices || [],
      verdict: typeof data.verdict === "boolean" ? data.verdict : null,
      revealed: !!data.revealed,
      state: data.state || "active",
      direction: card ? (data.direction || "forward") : "",
    };
  }

  function deserialize(value) {
    var deck = createDeck();
    if (Array.isArray(value)) {
      // v1 legacy: bare entry array, cursor at the tail.
      deck.items = value.map(deserializeItem);
      deck.cursor = deck.items.length - 1;
      return deck;
    }
    if (value && value.v === 2 && Array.isArray(value.items)) {
      deck.items = value.items.map(deserializeItem);
      var tail = deck.items.length - 1;
      deck.cursor = typeof value.cursor === "number"
        ? Math.max(-1, Math.min(value.cursor, tail))
        : tail;
      deck.ended = !!value.ended;
    }
    return deck;
  }

  function directionKeys(deck) {
    return deck.items.filter(function (item) { return item.kind === "card"; })
      .map(function (item) { return item.id + ":" + item.direction; });
  }

  return {
    createDeck: createDeck,
    makeItem: makeItem,
    append: append,
    find: find,
    current: current,
    atEnd: atEnd,
    goTo: goTo,
    settle: settle,
    ids: ids,
    directionKeys: directionKeys,
    serialize: serialize,
    deserialize: deserialize,
  };
}));
