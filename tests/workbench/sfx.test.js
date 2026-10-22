"use strict";

/* Key feedback cues — the behaviour contract in code.
 *
 * Contract: openspec/changes/workbench-visual-language-v2, spec requirement
 * "Key feedback audio cues" — four events carry one cue each, every cue is
 * shorter than 200 ms, nothing else sounds, the sound preference silences
 * every cue, and no cue may play before the learner interacted with the page.
 */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const STATIC_DIR = path.join(__dirname, "../../workbench/server/static");
const SFX_SOURCE = fs.readFileSync(path.join(STATIC_DIR, "sfx.js"), "utf8");
const WORKBENCH_SOURCE = fs.readFileSync(path.join(STATIC_DIR, "workbench.js"), "utf8");

const CUE_NAMES = ["complete", "correct", "milestone", "wrong"];

function sfxFixture(options = {}) {
  const played = [];
  const created = [];
  const listeners = {};
  const store = new Map();

  class FakeAudio {
    constructor(src) {
      this.src = src;
      this.preload = "";
      this.volume = 1;
      this.currentTime = 0;
      this.playCount = 0;
      created.push(this);
    }

    play() {
      this.playCount += 1;
      played.push(this.src);
      return options.rejectPlay
        ? Promise.reject(new Error("autoplay blocked"))
        : Promise.resolve();
    }
  }

  const document = {
    documentElement: { dataset: {} },
    getElementById(id) {
      if (id === "layout") return { dataset: { workspace: "dmath" } };
      return null;
    },
    addEventListener() {},
  };

  const window = {
    Audio: FakeAudio,
    localStorage: {
      getItem(key) { return store.has(key) ? store.get(key) : null; },
      setItem(key, value) { store.set(key, String(value)); },
    },
    addEventListener(type, callback) {
      (listeners[type] = listeners[type] || []).push(callback);
    },
    removeEventListener(type, callback) {
      listeners[type] = (listeners[type] || []).filter((entry) => entry !== callback);
    },
  };

  const context = vm.createContext({ window, document });
  vm.runInContext(SFX_SOURCE, context);
  return { window, document, played, created, listeners, store };
}

function gesture(fixture, type = "pointerdown") {
  (fixture.listeners[type] || []).slice().forEach((callback) => callback({ type }));
}

test("the module exposes exactly the four contract cues", () => {
  const fixture = sfxFixture();
  assert.deepEqual(Object.keys(fixture.window.lkSfx.cues).sort(), CUE_NAMES.slice().sort());
});

test("every cue is shorter than 200 ms", () => {
  const fixture = sfxFixture();
  for (const cue of Object.values(fixture.window.lkSfx.cues)) {
    assert.ok(cue.seconds > 0, "cue has a length");
    assert.ok(cue.seconds < 0.2, `cue ${cue.file} is ${cue.seconds}s, under 200 ms`);
  }
});

test("nothing is created or played while the page loads", () => {
  const fixture = sfxFixture();
  assert.equal(fixture.created.length, 0, "no audio element exists before a gesture");
  assert.equal(fixture.played.length, 0, "nothing played before a gesture");
});

test("a cue asked for before the first gesture stays silent", () => {
  const fixture = sfxFixture();
  assert.equal(fixture.window.lkSfx.playCue("correct"), false);
  assert.equal(fixture.played.length, 0);
  assert.equal(fixture.created.length, 0);
});

test("after a gesture the cue plays once", () => {
  const fixture = sfxFixture();
  gesture(fixture);
  assert.equal(fixture.window.lkSfx.playCue("correct"), true);
  assert.equal(fixture.played.length, 1);
  assert.match(fixture.played[0], /sfx-right\.wav$/);
});

test("every cue plays its own asset", () => {
  const fixture = sfxFixture();
  gesture(fixture);
  const expected = {
    correct: "sfx-right.wav",
    wrong: "sfx-wrong.wav",
    complete: "sfx-complete.wav",
    milestone: "sfx-milestone.wav",
  };
  for (const [name, file] of Object.entries(expected)) {
    fixture.played.length = 0;
    fixture.window.lkSfx.playCue(name);
    assert.equal(fixture.played.length, 1, `${name} plays once`);
    assert.match(fixture.played[0], new RegExp(`${file}$`));
  }
});

test("an unknown event is not a cue", () => {
  const fixture = sfxFixture();
  gesture(fixture);
  assert.equal(fixture.window.lkSfx.playCue("hover"), false);
  assert.equal(fixture.window.lkSfx.playCue("scroll"), false);
  assert.equal(fixture.played.length, 0);
});

test("the sound preference silences every cue", () => {
  const fixture = sfxFixture();
  gesture(fixture);
  fixture.window.lkSfx.setEnabled(false);
  for (const name of CUE_NAMES) {
    assert.equal(fixture.window.lkSfx.playCue(name), false, `${name} is silent`);
  }
  assert.equal(fixture.played.length, 0, "no cue played while muted");
});

test("turning the preference off takes effect without a reload", () => {
  const fixture = sfxFixture();
  gesture(fixture);
  fixture.window.lkSfx.playCue("correct");
  assert.equal(fixture.played.length, 1);
  fixture.window.lkSfx.setEnabled(false);
  fixture.window.lkSfx.playCue("correct");
  assert.equal(fixture.played.length, 1, "the second cue is silent");
  fixture.window.lkSfx.setEnabled(true);
  fixture.window.lkSfx.playCue("correct");
  assert.equal(fixture.played.length, 2, "the cue is back after switching on");
});

test("the preference lives in the workspace settings object", () => {
  const fixture = sfxFixture();
  fixture.window.lkSfx.setEnabled(false);
  const raw = fixture.store.get("wb_settings_dmath");
  assert.ok(raw, "the workspace settings key is written");
  assert.deepEqual(JSON.parse(raw), { sound: false });
  assert.equal(fixture.document.documentElement.dataset.sound, "off");
  fixture.window.lkSfx.setEnabled(true);
  assert.equal(fixture.document.documentElement.dataset.sound, "on");
});

test("the preference defaults to on when nothing is stored", () => {
  const fixture = sfxFixture();
  assert.equal(fixture.window.lkSfx.isEnabled(), true);
});

test("a blocked playback is swallowed instead of reported", () => {
  const fixture = sfxFixture({ rejectPlay: true });
  gesture(fixture);
  assert.doesNotThrow(() => fixture.window.lkSfx.playCue("correct"));
});

test("the shell calls the four cues and nothing else", () => {
  const calls = WORKBENCH_SOURCE.match(/playCue\("[^"]+"\)/g) || [];
  assert.equal(calls.length, 4, `four call points, got ${calls.join(", ")}`);
  const names = calls.map((call) => call.replace(/playCue\("([^"]+)"\)/, "$1")).sort();
  assert.deepEqual(names, CUE_NAMES.slice().sort());
});

test("the shell never builds an audio element of its own", () => {
  assert.equal(/new Audio\(/.test(WORKBENCH_SOURCE), false);
  assert.equal(/Audio\(/.test(WORKBENCH_SOURCE), false);
});
