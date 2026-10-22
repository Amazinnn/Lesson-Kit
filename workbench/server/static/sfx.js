/* Key feedback cues — the only four sounds the workbench may make.
 *
 * Contract: openspec/changes/workbench-visual-language-v2
 *   spec requirement "Key feedback audio cues" — a correct answer, a wrong
 *   answer, a finished round and a milestone each carry one cue shorter than
 *   200 ms; no other surface, event or state change may produce sound.
 *   decisions.md A-3 — crisp xylophone / glass, short, never loud.
 *
 * The four assets are synthesised from scratch (tests/workbench/sfx_assets.py);
 * no sample, recording or third-party file is involved.
 *
 * Browser rules honoured here:
 *   - nothing is created or played while the page loads;
 *   - the first cue can only follow a user gesture, so the audio elements are
 *     unlocked by that gesture (the browser autoplay policy);
 *   - the sound preference is read on every cue, so flipping it takes effect
 *     without a reload and never removes a visual feedback.
 */
(function (window, document) {
  "use strict";

  var CUES = {
    correct: { file: "sfx-right.wav", seconds: 0.140, volume: 0.5 },
    wrong: { file: "sfx-wrong.wav", seconds: 0.140, volume: 0.5 },
    complete: { file: "sfx-complete.wav", seconds: 0.185, volume: 0.5 },
    milestone: { file: "sfx-milestone.wav", seconds: 0.190, volume: 0.5 },
  };

  var SETTINGS_PREFIX = "wb_settings_";
  var PREFERENCE_KEY = "sound";
  var DEFAULT_BASE = "/static/assets/audio/";

  var players = {};
  var listeners = [];
  var unlocked = false;

  function audioBase() {
    /* The base is a seam for the file:// self-check page; the server path is
       the default and the only one the product uses. */
    return window.LK_SFX_AUDIO_BASE || DEFAULT_BASE;
  }

  function workspace() {
    var layout = document.getElementById("layout");
    if (layout && layout.dataset) return layout.dataset.workspace || "";
    return "";
  }

  function settingsKey() {
    return SETTINGS_PREFIX + workspace();
  }

  function storedSettings() {
    var raw = null;
    try { raw = window.localStorage.getItem(settingsKey()); }
    catch (error) { return {}; }
    if (!raw) return {};
    try {
      var data = JSON.parse(raw);
      return data && typeof data === "object" ? data : {};
    } catch (error) { return {}; }
  }

  function readEnabled() {
    var data = storedSettings();
    if (data[PREFERENCE_KEY] === undefined) return true;
    return data[PREFERENCE_KEY] !== false;
  }

  function writeEnabled(on) {
    var data = storedSettings();
    data[PREFERENCE_KEY] = !!on;
    try { window.localStorage.setItem(settingsKey(), JSON.stringify(data)); }
    catch (error) { /* a locked store must not break the page */ }
  }

  function reflectEnabled() {
    var on = readEnabled();
    var root = document.documentElement;
    if (root && root.dataset) root.dataset.sound = on ? "on" : "off";
    return on;
  }

  function player(name) {
    if (players[name]) return players[name];
    var cue = CUES[name];
    var audio = new window.Audio(audioBase() + cue.file);
    audio.preload = "auto";
    audio.volume = cue.volume;
    players[name] = audio;
    return audio;
  }

  function preload() {
    Object.keys(CUES).forEach(function (name) { player(name); });
  }

  function playCue(name) {
    var cue = CUES[name];
    if (!cue) return false;
    if (!unlocked) return false;       /* no sound before the learner acted */
    if (!readEnabled()) return false;  /* the sound preference silences cues */
    var audio = player(name);
    try {
      audio.currentTime = 0;
      var started = audio.play();
      if (started && typeof started.catch === "function") started.catch(function () {});
    } catch (error) {
      /* a blocked or missing asset must never break the page */
    }
    return true;
  }

  function unlock() {
    if (unlocked) return;
    unlocked = true;
    window.removeEventListener("pointerdown", unlock, true);
    window.removeEventListener("keydown", unlock, true);
    window.removeEventListener("touchstart", unlock, true);
    preload();
  }

  window.addEventListener("pointerdown", unlock, true);
  window.addEventListener("keydown", unlock, true);
  window.addEventListener("touchstart", unlock, true);

  window.lkSfx = {
    playCue: playCue,
    isEnabled: readEnabled,
    setEnabled: function (on) {
      writeEnabled(!!on);
      reflectEnabled();
      listeners.forEach(function (listener) {
        try { listener(!!on); } catch (error) { /* one bad listener, no sound */ }
      });
    },
    onPreferenceChange: function (listener) {
      if (typeof listener === "function") listeners.push(listener);
    },
    cues: CUES,
  };

  reflectEnabled();
})(window, document);
