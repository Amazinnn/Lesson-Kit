/* practice-flow — DOM and request lifecycle for a practice session. */
(function (root, factory) {
  root.PracticeFlow = factory();
}(typeof globalThis === "object" ? globalThis : this, function () {
  function start(deps) {
    var layout = document.getElementById("layout");
    if (!layout) return {
      currentProblem: function () { return null; },
      session: function () { return []; },
      visiblePracticeImages: function () { return []; },
      draftAnswer: function () { return ""; },
      draftNote: function () { return ""; },
    };
    var WS = layout.dataset.workspace;
    var api = deps.api;
    var post = deps.post;
    var patch = deps.patch;
    var store = deps.store;
    var load = deps.load;
    var renderMath = deps.renderMath;
    var escapeHtml = deps.escapeHtml;
    var richText = deps.richText;
    var selectedKpIds = deps.selectedKpIds;
    var saveSelectedKpIds = deps.saveSelectedKpIds;
    var recordRecent = deps.recordRecent;
    var SESSION_KEY = "wb_session_" + WS;
    var KPS_KEY = "wb_kps_" + WS;
    var CURRENT_KEY = "wb_current_" + WS;
    var SIMILAR_KEY = "wb_similar_round_" + WS;
    var MODE_KEY = "wb_practice_mode_" + WS;
    var INCLUDE_KEY = "wb_practice_include_" + WS;
    var RATING_MODE_KEY = "wb_practice_rating_mode_" + WS;
    var FLASH_DIRECTION_KEY = "wb_flash_direction_" + WS;
  /* ---------- practice session ---------- */

  var stream = document.getElementById("stream");
  var composer = document.getElementById("composer");
  var answerBox = document.getElementById("answer-box");
  var submitAnswer = document.getElementById("answer-submit");
  var showAnswer = document.getElementById("show-answer");
  var noTime = document.getElementById("no-time");
  var startPractice = document.getElementById("start-practice");
  var similarRound = sessionStorage.getItem(SIMILAR_KEY) === "1";
  var scopedMatch = String(window.location.search || "").match(/[?&]kp=([^&]+)/);
  var scopedKpId = layout.dataset.practiceKpId || (scopedMatch && decodeURIComponent(scopedMatch[1])) || "";
  if (scopedKpId) saveSelectedKpIds([scopedKpId]);
  var storedKps = load(KPS_KEY, []);
  var practiceDeck = PracticeDeck.deserialize(load(SESSION_KEY, null));
  var activePractice = null;
  // Legacy tabs stored the rendered payload of the current item separately;
  // adopt it into the deck so a refresh restores without pulling again.
  var legacyCurrent = load(CURRENT_KEY, null);
  if (legacyCurrent && practiceDeck.items.length) {
    var legacyTail = practiceDeck.items[practiceDeck.items.length - 1];
    if (legacyTail.id === legacyCurrent.problem_id && !legacyTail.payload) {
      legacyTail.payload = legacyCurrent;
    }
  }
  if (stream && scopedKpId && (storedKps.length !== 1 || storedKps[0] !== scopedKpId)) {
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(CURRENT_KEY);
    sessionStorage.removeItem(MODE_KEY);
    sessionStorage.removeItem(RATING_MODE_KEY);
    store(KPS_KEY, [scopedKpId]);
    practiceDeck = PracticeDeck.deserialize(null);
  }

  function persistDeck() {
    store(SESSION_KEY, PracticeDeck.serialize(practiceDeck));
  }


  function currentProblem() {
    return PracticeDeck.current(practiceDeck);
  }

  function session() {
    return practiceDeck.items;
  }

  function currentKps() {
    return load(KPS_KEY, selectedKpIds());
  }

  function visiblePracticeImages() {
    // Whatever the current question card shows right now — the answer the
    // learner is asking about, not an archive of the page.
    if (!stream || !stream.querySelectorAll) return [];
    var nodes = stream.querySelectorAll(".practice-question-card img");
    return Array.prototype.slice.call(nodes).map(function (img) {
      return (img && img.getAttribute && img.getAttribute("src")) || "";
    }).filter(function (src) { return !!src; });
  }

  function updateSession(problemId, values, direction) {
    var active = currentProblem();
    var concreteDirection = direction === undefined && active && active.kind === "card"
      ? active.direction : direction;
    PracticeDeck.settle(practiceDeck, problemId, values, concreteDirection);
    persistDeck();
  }

  function newPracticeRequestId() {
    return window.crypto && window.crypto.randomUUID
      ? window.crypto.randomUUID()
      : Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);
  }

  var pendingAttemptRequests = {};
  function ensureAttempt(item) {
    if (item.attempt_id) return Promise.resolve(item.attempt_id);
    if (!item.attempt_request) return Promise.resolve(null);
    var saved = item.attempt_request;
    if (pendingAttemptRequests[saved.request_id]) {
      return pendingAttemptRequests[saved.request_id];
    }
    updateSession(item.id, { attempt_status: "saving" }, item.direction);
    var request = post("/attempts", saved.payload).then(function (recorded) {
      updateSession(item.id, { attempt_id: recorded.attempt_id, attempt_status: "saved" },
        item.direction);
      if (recorded.practice) {
        activePractice = recorded.practice.completed ? null : recorded.practice.practice;
        renderResumeCard(activePractice);
      }
      return recorded.attempt_id;
    }).catch(function (error) {
      updateSession(item.id, { attempt_status: "failed" }, item.direction);
      throw error;
    });
    pendingAttemptRequests[saved.request_id] = request;
    request.then(function () { delete pendingAttemptRequests[saved.request_id]; },
      function () { delete pendingAttemptRequests[saved.request_id]; });
    return request;
  }

  function saveItemFeedback(item, payload) {
    var saved = item.feedback_request;
    if (!saved) {
      payload.request_id = newPracticeRequestId();
      saved = { request_id: payload.request_id, payload: payload };
      updateSession(item.id, { feedback_request: saved }, item.direction);
    }
    updateSession(item.id, { feedback_status: "saving" }, item.direction);
    return post("/feedback", saved.payload).then(function (result) {
      updateSession(item.id, { state: "rated", feedback_status: "saved" }, item.direction);
      return result;
    }).catch(function (error) {
      updateSession(item.id, { feedback_status: "failed" }, item.direction);
      throw error;
    });
  }

  // A refresh can happen after the server wrote an answer but before its reply.
  // The saved request is sent unchanged until the original attempt id returns.
  session().forEach(function (item) {
    if (item.attempt_request && !item.attempt_id) {
      ensureAttempt(item).catch(function () { /* retry on the next rating or refresh */ });
    }
  });

  function cardSides(item) {
    var payload = item.payload || {};
    return item.direction === "reverse"
      ? { prompt: payload.back || "", answer: payload.front || "" }
      : { prompt: payload.front || "", answer: payload.back || "" };
  }

  if (stream) {
    var modeExam = document.getElementById("practice-mode-exam");
    var modeMicro = document.getElementById("practice-mode-micro");
    var modeFlashCard = document.getElementById("practice-mode-flash_card");
    var modeYesNo = document.getElementById("practice-mode-yes_no");
    var modeImmediate = document.getElementById("practice-mode-immediate");
    var modeBatch = document.getElementById("practice-mode-batch");
    var ratingImmediate = document.getElementById("practice-rating-immediate");
    var ratingBatch = document.getElementById("practice-rating-batch");
    var flashDirectionChoice = document.getElementById("flash-direction-choice");
    var flashDirectionForward = document.getElementById("flash-direction-forward");
    var flashDirectionReverse = document.getElementById("flash-direction-reverse");
    var legacyModeControls = !!(modeImmediate || modeBatch);
    var actions = document.getElementById("composer-actions");
    var feedbackArea = document.getElementById("feedback-area");
    var ratingInput = document.getElementById("rating-input");
    var feedbackNote = document.getElementById("feedback-note");
    var saveRating = document.getElementById("save-rating");
    var sessionEntry = document.getElementById("session-end-entry");
    var startArea = document.getElementById("start-area");
    var practiceCount = document.getElementById("practice-count");
    var savePracticeSet = document.getElementById("save-practice-set");
    var resumeCard = document.getElementById("active-practice-resume");
    var resumeTitle = document.getElementById("active-practice-title");
    var resumeMeta = document.getElementById("active-practice-meta");
    var resumeFill = document.getElementById("active-practice-progress-fill");
    var resumeButton = document.getElementById("resume-practice");
    var practiceError = document.getElementById("practice-error");
    var retryPractice = document.getElementById("retry-practice");
    var cardNav = document.getElementById("card-nav");
    var cardPrev = document.getElementById("card-prev");
    var cardNext = document.getElementById("card-next");
    var pulling = false;
    var VERDICT_HOLD_MS = 2000;
    var advanceToken = 0;

    function showPracticeError(error, retryable) {
      if (!practiceError) return;
      practiceError.textContent = "请求未完成：" + (error.message || error || "未知错误");
      practiceError.classList.remove("hidden");
      if (retryPractice) retryPractice.classList.toggle("hidden", !retryable);
    }

    function clearPracticeError() {
      if (!practiceError) return;
      practiceError.textContent = "";
      practiceError.classList.add("hidden");
      if (retryPractice) retryPractice.classList.add("hidden");
    }

    function activeToDeck(practice) {
      var deck = PracticeDeck.createDeck();
      (practice.items || []).forEach(function (row) {
        var attempt = row.attempt || {};
        var item = PracticeDeck.append(deck, {
          id: row.item_id,
          kind: row.item_type === "card" ? "card" : "problem",
          direction: row.direction || "forward",
          payload: row.payload || null,
          answer_text: attempt.answer_text || "",
          choices: Array.isArray(attempt.choices) ? attempt.choices : [],
          verdict: attempt.verdict === null || attempt.verdict === undefined
            ? null : !!attempt.verdict,
          state: row.state === "pending" ? "active"
            : row.state === "stuck" ? "skipped"
              : (row.feedback ? "rated" : "unrated"),
        });
        if (row.attempt_id) item.attempt_id = row.attempt_id;
      });
      deck.cursor = Math.max(0, Math.min(
        typeof practice.cursor === "number" ? practice.cursor : 0,
        Math.max(0, deck.items.length - 1)
      ));
      return deck;
    }

    function renderResumeCard(practice) {
      if (!resumeCard) return;
      if (!practice) {
        resumeCard.classList.add("hidden");
        return;
      }
      var progress = practice.progress || {};
      var total = progress.total || 0;
      var completed = progress.completed || 0;
      var percent = total ? Math.round(completed * 100 / total) : 0;
      if (resumeTitle) resumeTitle.textContent = "未完成练习";
      if (resumeMeta) {
        resumeMeta.textContent = completed + " / " + total
          + " · " + (progress.answered || 0) + " 已作答 · "
          + (progress.stuck || 0) + " 不会 · "
          + (progress.remaining || 0) + " 待完成";
      }
      if (resumeFill && resumeFill.style) resumeFill.style.width = percent + "%";
      resumeCard.classList.remove("hidden");
    }

    function resumeActivePractice() {
      if (!activePractice) return;
      practiceDeck = activeToDeck(activePractice);
      persistDeck();
      sessionStorage.setItem(MODE_KEY, activePractice.practice_mode || "exam");
      sessionStorage.setItem(RATING_MODE_KEY, activePractice.rating_mode || "immediate");
      store(KPS_KEY, activePractice.kp_ids || []);
      if (startArea) startArea.classList.add("hidden");
      renderResumeCard(null);
      setPracticeFocus(true);
      var item = currentProblem();
      if (item) {
        renderDeckItem(item);
        showComposer(true);
      }
    }

    function loadActivePractice() {
      return api("/practice/current").then(function (result) {
        if (!result || !Object.prototype.hasOwnProperty.call(result, "practice")) return null;
        activePractice = result.practice || null;
        if (!activePractice) {
          sessionStorage.removeItem(SESSION_KEY);
          sessionStorage.removeItem(CURRENT_KEY);
          practiceDeck = PracticeDeck.createDeck();
          renderResumeCard(null);
          showComposer(false);
          setPracticeFocus(false);
          if (startArea) startArea.classList.remove("hidden");
          return null;
        }
        renderResumeCard(activePractice);
        showComposer(false);
        setPracticeFocus(false);
        if (startArea) startArea.classList.remove("hidden");
        return activePractice;
      }).catch(function () {
        // A pre-migration pool keeps the old client cache usable; the API error
        // remains non-destructive until the workspace is migrated.
        return null;
      });
    }

    function selectedCount() {
      var value = practiceCount ? parseInt(practiceCount.value, 10) : 10;
      return value === 5 || value === 20 ? value : 10;
    }

    function selectedContentMode() {
      if (modeExam && modeExam.checked) return "exam";
      if (modeMicro && modeMicro.checked) return "micro";
      if (modeYesNo && modeYesNo.checked) return "yes_no";
      if (modeFlashCard && modeFlashCard.checked) return "flash_card";
      return "";
    }

    function selectedRatingMode() {
      if (ratingImmediate && ratingImmediate.checked) return "immediate";
      if (ratingBatch && ratingBatch.checked) return "batch";
      if (modeImmediate && modeImmediate.checked) return "immediate";
      if (modeBatch && modeBatch.checked) return "batch";
      return "";
    }

    function selectedFlashDirection() {
      if (flashDirectionReverse && flashDirectionReverse.checked) return "reverse";
      return "forward";
    }

    function showFlashDirectionChoice() {
      if (flashDirectionChoice) {
        flashDirectionChoice.classList.toggle("hidden", selectedContentMode() !== "flash_card");
      }
    }

    function readyToStart() {
      var content = selectedContentMode() || (legacyModeControls ? "exam" : "");
      return !!content && !!selectedRatingMode()
        && (legacyModeControls || selectedKpIds().length > 0);
    }

    function microQuiz(problem) {
      var payload = problem && problem.micro_quiz;
      if (!payload || typeof payload !== "object") return null;
      return payload;
    }

    function problemOptions(problem) {
      var quiz = microQuiz(problem);
      if (quiz) {
        var type = quiz.quiz_type;
        if (type === "yes_no") return (quiz.options || ["是", "否"]).map(function (text) { return { id: text, text: text }; });
        if (type === "single_choice" || type === "multiple_choice") {
          return (quiz.options || []).map(function (text) { return { id: text, text: text }; });
        }
        return [];
      }
      var raw = problem && problem.options_json;
      if (!raw) return [];
      if (typeof raw === "string") {
        try { raw = JSON.parse(raw); } catch (_) { return []; }
      }
      if (!Array.isArray(raw)) return [];
      return raw.map(function (option, index) {
        if (typeof option === "string") return { id: String(index + 1), text: option };
        return {
          id: String(option.id || option.option_id || index + 1),
          text: String(option.text || option.label || option.value || ""),
        };
      }).filter(function (option) { return option.text; });
    }

    function showComposer(show) {
      if (composer) composer.classList.toggle("hidden", !show);
      if (sessionEntry) sessionEntry.classList.toggle("hidden", !show);
    }

    function setPracticeFocus(active) {
      var columns = document.getElementById("practice-columns");
      if (columns) columns.classList.toggle("hidden", active);
      var flow = document.querySelector(".practice-flow");
      if (active && flow && flow.scrollIntoView) flow.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function setComposerLayout(mode) {
      // "card": no answer row (reveal instead); "choice": options only;
      // "text": textarea + submit (ordinary exam answers).
      var row = document.getElementById("composer-row");
      if (row) row.classList.toggle("hidden", mode === "card");
      if (answerBox) answerBox.classList.toggle("hidden", mode !== "text");
      if (showAnswer) showAnswer.textContent = mode === "card" ? "揭示另一面" : "查看解析";
    }

    function ratingNow() {
      return sessionStorage.getItem(RATING_MODE_KEY) === "immediate"
        || (legacyModeControls && sessionStorage.getItem(MODE_KEY) === "immediate");
    }

    function batchNow() {
      return sessionStorage.getItem(RATING_MODE_KEY) === "batch"
        || (legacyModeControls && sessionStorage.getItem(MODE_KEY) === "batch");
    }

    function deckItemAnswered(item) {
      if (item.kind === "card") return false;
      return !!(item.choices && item.choices.length)
        || !!(item.answer_text || "").trim()
        || item.state === "unrated" || item.state === "rated";
    }

    function verdictLine(item) {
      if (typeof item.verdict !== "boolean") return "";
      var quiz = microQuiz(item.payload) || {};
      // error_reason goes through richText: it renders its $…$ and, unlike the
      // old string concat, cannot inject markup.
      return "<p id='micro-quiz-verdict' class='micro-verdict "
        + (item.verdict ? "ok" : "bad") + "'>"
        + (item.verdict
          ? "回答正确。"
          : "回答错误。 " + richText(quiz.error_reason || "")) + "</p>";
    }

    function keylessLine(item) {
      var quiz = microQuiz(item.payload);
      if (!quiz || quizHasKey(quiz)) return "";
      return "<p id='micro-quiz-keyless' class='muted'>"
        + "本题未录入答案键，请对照课本或解析自评。</p>";
    }

    function attemptHistoryHtml(attempts) {
      // Every past answer of this problem, oldest last; the record the current
      // session just wrote may not be in the payload yet, which is fine — the
      // records page holds the full ledger.
      if (!attempts || !attempts.length) return "";
      var rows = attempts.slice(-5).map(function (attempt) {
        var verdict = attempt.verdict;
        var badge = verdict === null || verdict === undefined
          ? "未判定" : (verdict ? "对" : "错");
        var stars = "";
        if (typeof attempt.rating === "number" && attempt.rating >= 1) {
          stars = " · " + "★".repeat(attempt.rating) + "☆".repeat(5 - attempt.rating);
        }
        return "<div class='attempt-row'>"
          + "<span class='record-verdict "
          + (verdict === false ? "record-verdict-bad" : "record-verdict-open")
          + "'>" + badge + "</span>"
          + "<time>" + escapeHtml(String(attempt.created_at || "")) + "</time>"
          + stars
          + (attempt.answer_text
            ? "<div class='rich-text'>" + richText(attempt.answer_text) + "</div>"
            : "")
          + "</div>";
      });
      return "<details class='attempt-history'><summary>历史作答 "
        + attempts.length + " 条</summary>" + rows.join("") + "</details>";
    }

    function optionHtmlFor(item) {
      var problem = item.payload || {};
      var quiz = microQuiz(problem);
      var options = problemOptions(problem);
      if (!options.length) return "";
      var multiple = !!quiz && quiz.quiz_type === "multiple_choice";
      var answered = deckItemAnswered(item);
      var keyList = multiple ? (quiz.answer_key || []) : [quiz.answer_key];
      return "<fieldset class='problem-options'" + (answered ? " disabled" : "") + "><legend>选择答案</legend>"
        + options.map(function (option) {
          var selected = answered && (item.choices || []).indexOf(option.id) >= 0;
          var correct = keyList.indexOf(option.id) >= 0;
          var classes = [];
          if (selected) classes.push("option-selected");
          if (answered && item.verdict === false && correct) classes.push("option-correct");
          return "<label" + (classes.length ? " class='" + classes.join(" ") + "'" : "") + ">"
            + "<input data-choice-option type='" + (multiple ? "checkbox" : "radio")
            + "' name='problem-option' value='" + escapeHtml(option.id) + "'"
            + (selected ? " checked disabled" : "") + "> "
            + "<span class='rich-text'>" + richText(option.text) + "</span></label>";
        }).join("") + "</fieldset>";
    }

    function updateCardNav(item) {
      var isCard = item.kind === "card";
      if (cardNav) cardNav.classList.toggle("hidden", !isCard);
      if (!isCard) return;
      if (cardPrev) cardPrev.disabled = practiceDeck.cursor <= 0;
      if (cardNext) cardNext.disabled = pulling;
    }

    function renderDeckItem(item) {
      updateCardNav(item);
      if (item.kind === "card") {
        var sides = cardSides(item);
        var directionLabel = item.direction === "reverse" ? "反向" : "正向";
        var cardBody = "<div class='flash-card-stage"
          + (item.revealed ? " is-revealed" : "") + "'>"
          + "<section class='flash-card-face flash-card-answer' aria-label='另一面'"
          + (item.revealed ? "" : " aria-hidden='true'") + ">"
          + "<p class='section-kicker'>另一面</p><div class='rich-text'>"
          + richText(sides.answer) + "</div></section>"
          + "<section class='flash-card-face flash-card-prompt' aria-label='提示面'>"
          + "<p class='section-kicker'>提示面</p><div class='rich-text'>"
          + richText(sides.prompt) + "</div></section></div>";
        stream.innerHTML = "<article class='practice-question-card card flash-card-shell'>"
          + "<p class='context-line'>闪卡</p>"
          + "<p class='muted flash-direction-label'>" + directionLabel
          + " · 先在心里回忆，再揭示对照。</p>" + cardBody
          + (item.state === "rated" ? "<p class='muted'>已评分。</p>" : "")
          + "</article>";
        renderMath(stream);
        setComposerLayout("card");
        if (showAnswer) showAnswer.classList.toggle("hidden", item.revealed);
        if (feedbackArea) {
          feedbackArea.classList.toggle("hidden",
            !(ratingNow() && item.revealed && item.state !== "rated"));
        }
        if (item.feedback_request) {
          if (ratingInput) ratingInput.value = item.feedback_request.payload.rating;
          if (feedbackNote) feedbackNote.value = item.feedback_request.payload.note || "";
        }
        if (actions) actions.classList.remove("hidden");
        return;
      }
      var problem = item.payload || {};
      var answered = deckItemAnswered(item);
      stream.innerHTML = "<article class='practice-question-card card'>"
        + "<p class='context-line'>练习题</p><h2>"
        + escapeHtml(problem.display_title || "未命名题目") + "</h2>"
        + practiceSourceHtml(problem)
        + "<div class='problem-text rich-text'>" + richText(problem.problem_text || "") + "</div>"
        + optionHtmlFor(item) + keylessLine(item) + verdictLine(item) + "</article>";
      renderMath(stream);
      setComposerLayout(
        microQuiz(problem) && problemOptions(problem).length ? "choice" : "text");
      answerBox.value = (answered && !(item.choices && item.choices.length))
        ? (item.answer_text || "") : "";
      if (answered) {
        answerBox.disabled = true;
        submitAnswer.classList.add("hidden");
        actions.classList.remove("hidden");
        feedbackArea.classList.add("hidden");
      } else {
        answerBox.disabled = false;
        submitAnswer.classList.remove("hidden");
        actions.classList.add("hidden");
        feedbackArea.classList.add("hidden");
        answerBox.focus();
      }
    }

    function quizHasKey(quiz) {
      if (!quiz) return false;
      var answer = quiz.answer_key;
      if (typeof answer === "string") return answer.trim().length > 0;
      if (Object.prototype.toString.call(answer) === "[object Array]") {
        return answer.length > 0;
      }
      return false;
    }

    function gradeMicroQuiz(problem, submittedTexts) {
      var quiz = microQuiz(problem);
      if (!quiz) return null;
      // An item whose source lost its answer key is practised ungraded: guessing
      // a verdict from a missing key would mark every answer wrong.
      if (!quizHasKey(quiz)) return null;
      var type = quiz.quiz_type;
      var answer = quiz.answer_key;
      if (type === "multiple_choice") {
        if (!Array.isArray(submittedTexts) || !Array.isArray(answer)) return false;
        return submittedTexts.slice().sort().join("|") === answer.slice().sort().join("|");
      }
      return submittedTexts[0] === answer;
    }

    function finishExhausted() {
      var mode = sessionStorage.getItem(MODE_KEY);
      var ratingMode = sessionStorage.getItem(RATING_MODE_KEY);
      var emptyMessage = similarRound
        ? "暂无更多同类题。"
        : (mode === "flash_card" ? "当前范围暂无可用的闪卡，请选择其他模式。"
          : mode === "micro" ? "当前范围暂无可用的小测题目，请选择其他模式。"
          : mode === "yes_no" ? "当前范围暂无可用的 Yes / No 题目，请选择其他模式。"
            : "本轮相关题目已练完。");
      advanceToken += 1;
      practiceDeck.ended = true;
      persistDeck();
      stream.innerHTML = "<p class='muted'>" + emptyMessage + "</p>";
      similarRound = false;
      sessionStorage.removeItem(SIMILAR_KEY);
      showComposer(false);
      setPracticeFocus(false);
      if (ratingMode === "batch") window.location = "session-end";
      else {
        sessionStorage.removeItem(MODE_KEY);
        sessionStorage.removeItem(RATING_MODE_KEY);
        [modeExam, modeMicro, modeFlashCard, modeYesNo, modeImmediate, modeBatch].forEach(function (input) {
          if (input) input.checked = false;
        });
        startPractice.disabled = true;
        if (startArea) startArea.classList.remove("hidden");
      }
    }

    function cancelScheduledAdvance() {
      advanceToken += 1;
    }

    function scheduleAdvance() {
      var token = advanceToken;
      setTimeout(function () {
        if (token !== advanceToken) return;
        advance();
      }, VERDICT_HOLD_MS);
    }

    // Advance replays the presented history first; only past its end does a
    // new pull happen. This is what makes flash-card paging and the batch
    // verdict hold one rule instead of two.
    function advance() {
      cancelScheduledAdvance();
      if (!PracticeDeck.atEnd(practiceDeck)) {
        renderDeckItem(PracticeDeck.goTo(practiceDeck, practiceDeck.cursor + 1));
        persistDeck();
        return;
      }
      if (resumeCard) finishExhausted();
      else loadNext();
    }

    function loadNext() {
      var kps = currentKps();
      var mode = sessionStorage.getItem(MODE_KEY);
      if (!kps.length || !mode || pulling) return;
      var exclude = PracticeDeck.ids(practiceDeck);
      var includeIds = load(INCLUDE_KEY, null);
      clearPracticeError();
      pulling = true;
      if (mode === "flash_card") {
        api("/pull-cards", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            kp_ids: kps,
            direction_mode: sessionStorage.getItem(FLASH_DIRECTION_KEY) || "forward",
            exclude_directions: PracticeDeck.directionKeys(practiceDeck),
          }),
        }).then(function (result) {
          pulling = false;
          var card = (result.cards || [])[0];
          if (!card) {
            finishExhausted();
            return;
          }
          PracticeDeck.append(practiceDeck, {
            id: card.card_id, kind: "card",
            direction: card.direction || "forward",
            payload: {
              card_id: card.card_id,
              front: card.front,
              back: card.back,
              directions: card.directions || ["forward"],
            },
          });
          persistDeck();
          renderDeckItem(PracticeDeck.current(practiceDeck));
          ratingInput.value = "";
          feedbackNote.value = "";
          showComposer(true);
        }).catch(function (error) { pulling = false; showPracticeError(error, true); });
        return;
      }
      var pullBody = {
        kp_ids: kps, n: 1,
        mode: mode,
        exclude_ids: exclude,
      };
      applyFiltersToPullBody(pullBody);
      if (includeIds && includeIds.length) {
        pullBody.include_ids = (pullBody.include_ids || []).concat(
          includeIds.filter(function (id) {
            return (pullBody.include_ids || []).indexOf(id) < 0;
          }));
      }
      api("/pull", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pullBody),
      }).then(function (result) {
        pulling = false;
        sessionStorage.removeItem(INCLUDE_KEY);
        if (!result.problems.length) {
          finishExhausted();
          return;
        }
        var problem = result.problems[0];
        PracticeDeck.append(practiceDeck, {
          id: problem.problem_id, kind: "problem", payload: problem,
        });
        persistDeck();
        recordRecent("problem", problem.problem_id);
        renderDeckItem(PracticeDeck.current(practiceDeck));
        showComposer(true);
      }).catch(function (error) { pulling = false; showPracticeError(error, true); });
    }

    function selectFixedItems(kps, contentMode) {
      var count = selectedCount();
      if (contentMode === "flash_card") {
        return api("/pull-cards", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            kp_ids: kps,
            direction_mode: selectedFlashDirection(),
            exclude_directions: [],
          }),
        }).then(function (result) {
          return {
            request: {
              kp_ids: kps.slice(), n: count, mode: contentMode,
              direction_mode: selectedFlashDirection(),
            },
            items: (result.cards || []).slice(0, count).map(function (card) {
              return {
                item_type: "card", item_id: card.card_id,
                direction: card.direction || "forward",
              };
            }),
          };
        });
      }

      var pullBody = { kp_ids: kps, n: count, mode: contentMode };
      applyFiltersToPullBody(pullBody);
      var includeIds = load(INCLUDE_KEY, null);
      if (includeIds && includeIds.length) pullBody.include_ids = includeIds.slice();
      var request = JSON.parse(JSON.stringify(pullBody));
      return api("/pull", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pullBody),
      }).then(function (result) {
        return {
          request: request,
          items: (result.problems || []).map(function (problem) {
            return { item_type: "problem", item_id: problem.problem_id };
          }),
        };
      });
    }

    function beginFixedPractice(kps, contentMode, ratingMode) {
      if (!kps.length || pulling) return;
      var replace = false;
      if (activePractice) {
        var oldKps = (activePractice.kp_ids || []).slice().sort().join("|");
        var newKps = kps.slice().sort().join("|");
        var prompt = oldKps === newKps
          ? "当前知识点还有一轮未完成练习。确定重新开始吗？"
          : "当前还有一轮练习没有完成。确定开始新的练习吗？";
        if (window.confirm && !window.confirm(prompt)) {
          resumeActivePractice();
          return;
        }
        replace = true;
      }

      clearPracticeError();
      pulling = true;
      selectFixedItems(kps, contentMode).then(function (selection) {
        if (!selection.items.length) throw new Error("当前范围没有可用题目。");
        return post("/practice/current", {
          source_kind: "quick",
          kp_ids: kps,
          practice_mode: contentMode,
          rating_mode: ratingMode,
          items: selection.items,
          replace: replace,
        });
      }).then(function (practice) {
        pulling = false;
        activePractice = practice;
        sessionStorage.removeItem(INCLUDE_KEY);
        sessionStorage.setItem(MODE_KEY, contentMode);
        sessionStorage.setItem(RATING_MODE_KEY, ratingMode);
        if (contentMode === "flash_card") {
          sessionStorage.setItem(FLASH_DIRECTION_KEY, selectedFlashDirection());
        }
        store(KPS_KEY, kps);
        resumeActivePractice();
      }).catch(function (error) {
        pulling = false;
        showPracticeError(error, true);
      });
    }

    function saveCurrentSelectionAsPaper() {
      var contentMode = selectedContentMode() || (legacyModeControls ? "exam" : "");
      var kps = legacyModeControls && scopedKpId ? [scopedKpId] : selectedKpIds();
      if (!contentMode || !kps.length) return;
      if (contentMode === "flash_card") {
        showPracticeError("试卷只保存题目；闪卡请直接开始练习。", false);
        return;
      }
      var title = window.prompt ? window.prompt("试卷名称", "新的试卷") : "新的试卷";
      if (!title || !title.trim()) return;
      clearPracticeError();
      pulling = true;
      if (savePracticeSet) savePracticeSet.disabled = true;
      selectFixedItems(kps, contentMode).then(function (selection) {
        if (!selection.items.length) throw new Error("当前范围没有可保存的题目。");
        return post("/practice-sets", {
          title: title.trim(),
          problem_ids: selection.items.map(function (item) { return item.item_id; }),
          request: selection.request,
        });
      }).then(function () {
        pulling = false;
        sessionStorage.removeItem(INCLUDE_KEY);
        window.location = "/w/" + encodeURIComponent(WS) + "/practice-sets";
      }).catch(function (error) {
        pulling = false;
        if (savePracticeSet) savePracticeSet.disabled = !readyToStart();
        showPracticeError(error, true);
      });
    }

    function startLegacySession(contentMode, ratingMode) {
      practiceDeck = PracticeDeck.deserialize(null);
      sessionStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(CURRENT_KEY);
      sessionStorage.setItem(MODE_KEY, contentMode);
      sessionStorage.setItem(RATING_MODE_KEY, ratingMode);
      if (contentMode === "flash_card") {
        sessionStorage.setItem(FLASH_DIRECTION_KEY, selectedFlashDirection());
      } else {
        sessionStorage.removeItem(FLASH_DIRECTION_KEY);
      }
      if (legacyModeControls && scopedKpId) {
        store(KPS_KEY, [scopedKpId]);
        if (startArea) startArea.classList.add("hidden");
        setPracticeFocus(true);
        loadNext();
        return;
      }
      if (legacyModeControls) {
        api("/weak?limit=200").then(function (items) {
          store(KPS_KEY, items.map(function (item) { return item.kp_id; }));
          if (startArea) startArea.classList.add("hidden");
          setPracticeFocus(true);
          loadNext();
        }).catch(showPracticeError);
        return;
      }
      var ids = selectedKpIds();
      if (!ids.length) {
        if (practiceError) showPracticeError("请先在知识点视图选择范围", false);
        return;
      }
      store(KPS_KEY, ids);
      if (startArea) startArea.classList.add("hidden");
      setPracticeFocus(true);
      loadNext();
    }

    function startSession() {
      var contentMode = selectedContentMode();
      var ratingMode = selectedRatingMode();
      if (legacyModeControls && !ratingMode) ratingMode = selectedRatingMode();
      if (!contentMode && legacyModeControls) contentMode = "exam";
      if (!contentMode || !ratingMode) return;
      advanceToken += 1;
      if (!resumeCard) {
        startLegacySession(contentMode, ratingMode);
        return;
      }

      if (legacyModeControls && scopedKpId) {
        beginFixedPractice([scopedKpId], contentMode, ratingMode);
        return;
      }
      if (legacyModeControls) {
        api("/weak?limit=200").then(function (items) {
          beginFixedPractice(items.map(function (item) { return item.kp_id; }),
            contentMode, ratingMode);
        }).catch(showPracticeError);
        return;
      }
      var ids = selectedKpIds();
      if (!ids.length) {
        if (practiceError) showPracticeError("请先在知识点视图选择范围", false);
        return;
      }
      beginFixedPractice(ids, contentMode, ratingMode);
    }

    function syncSelectionActions() {
      var ready = readyToStart();
      if (startPractice) startPractice.disabled = !ready;
      if (savePracticeSet) {
        savePracticeSet.disabled = !ready || selectedContentMode() === "flash_card";
      }
    }

    function bindMode(mode) {
      if (mode) mode.addEventListener("change", function () {
        showFlashDirectionChoice();
        syncSelectionActions();
      });
    }

    bindMode(modeExam);
    bindMode(modeMicro);
    bindMode(modeFlashCard);
    bindMode(modeYesNo);
    bindMode(modeImmediate);
    bindMode(modeBatch);
    bindMode(ratingImmediate);
    bindMode(ratingBatch);
    var restoredMode = sessionStorage.getItem(MODE_KEY);
    var restoredFlashDirection = sessionStorage.getItem(FLASH_DIRECTION_KEY) || "forward";
    if (flashDirectionForward) flashDirectionForward.checked = restoredFlashDirection === "forward";
    if (flashDirectionReverse) flashDirectionReverse.checked = restoredFlashDirection === "reverse";
    var restoredRatingMode = sessionStorage.getItem(RATING_MODE_KEY)
      || (restoredMode === "batch" ? "batch" : "");
    var restoredItem = currentProblem();
    var hasPendingRatings = restoredRatingMode === "batch" && session().some(function (item) {
      return item.state === "unrated";
    });
    if (hasPendingRatings && restoredItem && practiceDeck.ended) {
      window.location = "session-end";
    } else if (restoredMode && restoredItem) {
      if (modeExam) modeExam.checked = restoredMode === "exam";
      if (modeMicro) modeMicro.checked = restoredMode === "micro";
      if (modeFlashCard) modeFlashCard.checked = restoredMode === "flash_card";
      if (modeYesNo) modeYesNo.checked = restoredMode === "yes_no";
      if (modeImmediate) modeImmediate.checked = restoredMode === "immediate";
      if (modeBatch) modeBatch.checked = restoredMode === "batch";
      if (ratingImmediate) ratingImmediate.checked = restoredRatingMode === "immediate";
      if (ratingBatch) ratingBatch.checked = restoredRatingMode === "batch";
      if (startArea) startArea.classList.add("hidden");
      setPracticeFocus(true);
      renderDeckItem(restoredItem);
      showComposer(true);
    }
    showFlashDirectionChoice();
    if (startPractice) startPractice.addEventListener("click", startSession);
    if (savePracticeSet) {
      savePracticeSet.addEventListener("click", saveCurrentSelectionAsPaper);
    }
    syncSelectionActions();
    if (resumeButton) resumeButton.addEventListener("click", resumeActivePractice);
    if (retryPractice) retryPractice.addEventListener("click", resumeCard ? startSession : loadNext);
    if (resumeCard) loadActivePractice();

    /* ---------- 来源筛选浮窗 ---------- */

    var FILTER_KEY = "wb_practice_filters_" + WS;
    var filterLaunch = document.getElementById("filter-launch");
    var filterCount = document.getElementById("filter-count");
    var filterPopup = document.getElementById("filter-popup");
    var filterFacets = null;
    var filterState = load(FILTER_KEY, null)
      || { source_kinds: [], exam_years: [], docs: [], picked: {} };
    if (!filterState.picked) filterState.picked = {};

    function filterActiveCount() {
      return filterState.source_kinds.length + filterState.exam_years.length
        + filterState.docs.length + Object.keys(filterState.picked).length;
    }

    function updateFilterBadge() {
      if (!filterCount) return;
      var count = filterActiveCount();
      filterCount.textContent = count ? String(count) : "";
      filterCount.classList.toggle("hidden", !count);
    }

    function saveFilters() {
      store(FILTER_KEY, filterState);
      updateFilterBadge();
    }

    function applyFiltersToPullBody(pullBody) {
      var dimensions = {};
      ["source_kinds", "exam_years", "docs"].forEach(function (key) {
        if (filterState[key] && filterState[key].length) {
          dimensions[key] = filterState[key].slice();
        }
      });
      if (Object.keys(dimensions).length) pullBody.filters = dimensions;
      var pickedIds = Object.keys(filterState.picked || {});
      if (pickedIds.length) pullBody.include_ids = pickedIds;
    }

    function filterDimension(name, label, entries) {
      var state = filterState[name] || [];
      var options = entries.map(function (facet) {
        var checked = state.indexOf(facet.value) >= 0;
        return "<label class='filter-option'><input type='checkbox' data-filter-dimension='"
          + escapeHtml(name) + "' value='" + escapeHtml(facet.value) + "'"
          + (checked ? " checked" : "") + "> " + escapeHtml(facet.value)
          + " <span class='count'>" + facet.count + "</span></label>";
      }).join("");
      return "<div class='filter-dimension'><h3>" + escapeHtml(label) + "</h3>"
        + (options || "<p class='muted'>本池暂无此维度</p>") + "</div>";
    }

    function renderFilterPopup() {
      if (!filterPopup) return;
      filterPopup.innerHTML =
        filterDimension("source_kinds", "来源类型", filterFacets.source_kinds || [])
        + filterDimension("exam_years", "考查年份", filterFacets.exam_years || [])
        + filterDimension("docs", "来源文档", filterFacets.docs || [])
        + "<div class='filter-dimension'><h3>搜索选题</h3>"
        + "<div class='filter-search'><input id='filter-search-box' type='search' "
        + "placeholder='题面 / 标题 / 来源…'>"
        + "<button id='filter-search-go' class='outline sm'>搜</button></div>"
        + "<div id='filter-search-results' class='filter-search-results'></div></div>"
        + "<div class='filter-actions'>"
        + "<button id='filter-clear' class='ghost sm'>清除全部</button>"
        + "<button id='filter-close' class='outline sm'>关闭</button></div>";
      filterPopup.querySelectorAll("[data-filter-dimension]").forEach(function (box) {
        box.addEventListener("change", function () {
          var list = filterState[box.dataset.filterDimension];
          var at = list.indexOf(box.value);
          if (box.checked && at < 0) list.push(box.value);
          if (!box.checked && at >= 0) list.splice(at, 1);
          saveFilters();
        });
      });
      var searchGo = filterPopup.querySelector("#filter-search-go");
      var searchBox = filterPopup.querySelector("#filter-search-box");
      if (searchGo && searchBox) {
        var runSearch = function () {
          var term = searchBox.value.trim();
          var target = filterPopup.querySelector("#filter-search-results");
          if (!term) { target.innerHTML = ""; return; }
          api("/search/problems?q=" + encodeURIComponent(term)).then(function (found) {
            if (!found.problems.length) {
              target.innerHTML = "<p class='muted'>没有匹配的题目。</p>";
              return;
            }
            target.innerHTML = found.problems.map(function (problem) {
              var checked = problem.problem_id in filterState.picked;
              return "<label class='filter-option'><input type='checkbox' "
                + "data-picked-id='" + escapeHtml(problem.problem_id) + "'"
                + (checked ? " checked" : "") + "> "
                + escapeHtml(problem.title) + "</label>";
            }).join("");
            target.querySelectorAll("[data-picked-id]").forEach(function (box) {
              box.addEventListener("change", function () {
                if (box.checked) {
                  var hit = found.problems.filter(function (problem) {
                    return problem.problem_id === box.dataset.pickedId;
                  })[0];
                  filterState.picked[box.dataset.pickedId] = hit ? hit.title : "";
                } else {
                  delete filterState.picked[box.dataset.pickedId];
                }
                saveFilters();
              });
            });
          }).catch(function () {
            target.innerHTML = "<p class='inline-error'>搜索失败。</p>";
          });
        };
        searchGo.addEventListener("click", runSearch);
        searchBox.addEventListener("keydown", function (event) {
          if (event.key === "Enter") runSearch();
        });
      }
      var clear = filterPopup.querySelector("#filter-clear");
      if (clear) clear.addEventListener("click", function () {
        filterState = { source_kinds: [], exam_years: [], docs: [], picked: {} };
        saveFilters();
        renderFilterPopup();
      });
      var close = filterPopup.querySelector("#filter-close");
      if (close) close.addEventListener("click", function () {
        filterPopup.classList.add("hidden");
        if (filterLaunch) filterLaunch.setAttribute("aria-expanded", "false");
      });
    }

    if (filterLaunch && filterPopup) {
      filterLaunch.addEventListener("click", function () {
        var hidden = filterPopup.classList.toggle("hidden");
        filterLaunch.setAttribute("aria-expanded", hidden ? "false" : "true");
        if (!hidden && !filterFacets) {
          api("/pull-facets").then(function (facets) {
            filterFacets = facets;
            renderFilterPopup();
          }).catch(function () {
            filterPopup.innerHTML = "<p class='inline-error'>筛选维度读取失败。</p>";
          });
        }
      });
      updateFilterBadge();
    }

    if (submitAnswer) submitAnswer.addEventListener("click", function () {
      var item = currentProblem();
      if (!item || item.kind === "card") return;
      if (item.attempt_request && !item.attempt_id) {
        ensureAttempt(item).catch(showPracticeError);
        return;
      }
      var answer = answerBox.value.trim();
      var choiceInputs = (stream && stream.querySelectorAll)
        ? Array.prototype.slice.call(stream.querySelectorAll("[data-choice-option]:checked"))
        : [];
      var choiceTexts = choiceInputs.map(function (input) { return input.value; });
      if (choiceTexts.length) answer = choiceTexts.join(", ");
      var patch = { answer_text: answer };
      if (choiceTexts.length) patch.choices = choiceTexts.slice();
      var graded = gradeMicroQuiz(item.payload, choiceTexts);
      if (graded !== null) patch.verdict = graded;
      var attemptPayload = {
        request_id: newPracticeRequestId(), problem_id: item.id,
        answer_text: answer, choices: choiceTexts.length ? choiceTexts.slice() : undefined,
        verdict: graded === null ? undefined : graded,
        practice_position: activePractice ? practiceDeck.cursor : undefined,
      };
      patch.attempt_id = null;
      patch.attempt_request = { request_id: attemptPayload.request_id, payload: attemptPayload };
      patch.attempt_status = "saving";
      if (batchNow()) patch.state = "unrated";
      PracticeDeck.settle(practiceDeck, item.id, patch);
      persistDeck();
      renderDeckItem(currentProblem());
      // The attempt itself is the durable record: one POST per submission,
      // before any rating. The session's rating later links back via attempt_id.
      ensureAttempt(currentProblem()).catch(showPracticeError);
      if (batchNow()) {
        // Instant verdict, deferred rating: hold the verdict (and the
        // highlighted correct options) briefly, then advance.
        if (graded !== null) scheduleAdvance();
        else advance();
        return;
      }
    });

    if (showAnswer) showAnswer.addEventListener("click", function () {
      var item = currentProblem();
      if (!item) return;
      clearPracticeError();
      if (item.kind === "card") {
        var patch = { revealed: true };
        if (batchNow() && item.state !== "rated") patch.state = "unrated";
        PracticeDeck.settle(practiceDeck, item.id, patch, item.direction);
        persistDeck();
        renderDeckItem(currentProblem());
        return;
      }
      api("/problem/" + item.id).then(function (detail) {
        var quiz = microQuiz(detail.problem) || microQuiz(item.payload);
        var section;
        if (quiz) {
          var key = quizHasKey(quiz) ? String(quiz.answer_key) : "未录入答案键";
          var why = quiz.error_reason
            ? "<p class='section-kicker'>为什么</p>"
              + "<div class='rich-text'>" + richText(quiz.error_reason) + "</div>"
            : "";
          section = "<section class='practice-solution'><p class='section-kicker'>答案</p>"
            + "<div class='rich-text'>" + richText(key) + "</div>" + why + "</section>";
        } else {
          section = practiceSolutionHtml(detail.problem);
        }
        stream.innerHTML += section + attemptHistoryHtml(detail.attempts);
        renderMath(stream);
        showAnswer.classList.add("hidden");
        if (!batchNow()) feedbackArea.classList.remove("hidden");
      }).catch(showPracticeError);
    });

    if (saveRating) saveRating.addEventListener("click", function () {
      var rating = parseInt(ratingInput.value, 10);
      var item = currentProblem();
      if (!item) return;
      if (item.feedback_status === "saving") return;
      if (rating < 1 || rating > 5) {
        showPracticeError("请输入 1-5 的评分");
        return;
      }
      clearPracticeError();
      var feedback = {
        item_type: item.kind === "card" ? "card" : "problem",
        item_id: item.id,
        rating: rating, note: feedbackNote.value.trim(),
      };
      if (item.kind === "card") feedback.direction = item.direction;
      updateSession(item.id, { feedback_status: "saving" }, item.direction);
      ensureAttempt(item).then(function (attemptId) {
        if (item.kind !== "card" && attemptId) feedback.attempt_id = attemptId;
        return saveItemFeedback(item, feedback);
      }).then(function () {
        if (item.kind !== "card" || !activePractice) return null;
        return patch("/practice/current", {
          position: practiceDeck.cursor, state: "answered",
        }).then(function (result) {
          activePractice = result.completed ? null : result.practice;
          renderResumeCard(activePractice);
        });
      }).then(function () {
        advance();
      }).catch(function (error) {
        updateSession(item.id, { feedback_status: "failed" }, item.direction);
        showPracticeError(error);
      });
    });

    if (noTime) noTime.addEventListener("click", function () {
      var item = currentProblem();
      if (!item) return;
      clearPracticeError();
      if (!activePractice) {
        var legacyState = (item.kind === "card" && item.revealed)
          ? "unrated" : "skipped";
        updateSession(item.id, { state: legacyState }, item.direction);
        advance();
        return;
      }
      var position = practiceDeck.cursor;
      var request;
      if (item.kind === "card") {
        request = post("/feedback", {
          item_type: "card", item_id: item.id, rating: 1,
          direction: item.direction || "forward",
          request_id: newPracticeRequestId(),
        }).then(function () {
          return patch("/practice/current", {
            position: position, state: "stuck",
          });
        });
      } else {
        request = post("/attempts", {
          request_id: newPracticeRequestId(),
          problem_id: item.id,
          answer_text: "",
          stuck: true,
          practice_position: position,
        }).then(function (result) {
          return result.practice || null;
        });
      }
      request.then(function (progress) {
        if (progress) {
          activePractice = progress.completed ? null : progress.practice;
          renderResumeCard(activePractice);
        }
        updateSession(item.id, { state: "skipped" }, item.direction);
        advance();
      }).catch(showPracticeError);
    });

    var gotoBtn = document.getElementById("goto-session-end");
    if (gotoBtn) gotoBtn.addEventListener("click", function () {
      if (!resumeCard) {
        var item = currentProblem();
        if (item) {
          var endState = (item.state === "active" || item.state === "skipped")
            ? ((item.kind === "card" && item.revealed) ? "unrated" : "skipped")
            : item.state;
          updateSession(item.id, { state: endState });
        }
        cancelScheduledAdvance();
        showComposer(false);
        if (batchNow()) window.location = "session-end";
        else {
          sessionStorage.removeItem(MODE_KEY);
          sessionStorage.removeItem(RATING_MODE_KEY);
          stream.innerHTML = "<p class='muted'>本轮练习已提前结束。</p>";
          setPracticeFocus(false);
          if (startArea) startArea.classList.remove("hidden");
        }
        return;
      }
      cancelScheduledAdvance();
      showComposer(false);
      setPracticeFocus(false);
      if (stream) stream.innerHTML = "";
      if (startArea) startArea.classList.remove("hidden");
      renderResumeCard(activePractice);
    });

    if (cardPrev) cardPrev.addEventListener("click", function () {
      if (practiceDeck.cursor <= 0) return;
      cancelScheduledAdvance();
      renderDeckItem(PracticeDeck.goTo(practiceDeck, practiceDeck.cursor - 1));
      persistDeck();
    });
    if (cardNext) cardNext.addEventListener("click", function () {
      advance();
    });
  }

  /* ---------- session-end ---------- */

  var pending = document.getElementById("pending-ratings");
  if (pending) {
    var unrated = session().filter(function (item) { return item.state === "unrated"; });
    if (!unrated.length) {
      pending.innerHTML = "<p>没有待评的题。</p>";
    } else {
      var remaining = unrated.length;
      var buildRatingCard = function (contentHtml, itemType, itemId, title, direction, item) {
        var entryId = itemId + (direction ? "-" + direction : "");
        var card = document.createElement("article");
        card.className = "pending-rating-card card";
        card.dataset.pid = entryId;
        card.innerHTML = contentHtml;
        var rating = document.createElement("input");
        rating.id = "end-rating-" + entryId;
        rating.type = "number";
        rating.min = "1";
        rating.max = "5";
        rating.placeholder = "输入 1–5";
        var note = document.createElement("textarea");
        note.id = "end-note-" + entryId;
        note.placeholder = "可选备注";
        if (item.feedback_request) {
          rating.value = item.feedback_request.payload.rating;
          note.value = item.feedback_request.payload.note || "";
        }
        var save = document.createElement("button");
        save.id = "end-save-" + entryId;
        save.className = "primary sm";
        save.textContent = "保存评分";
        var ratingLabel = document.createElement("label");
        ratingLabel.id = "end-rating-label-" + entryId;
        ratingLabel.setAttribute("for", rating.id);
        ratingLabel.textContent = "为“" + title + "”评分（1-5）";
        var noteLabel = document.createElement("label");
        noteLabel.id = "end-note-label-" + entryId;
        noteLabel.setAttribute("for", note.id);
        noteLabel.textContent = "为“" + title + "”添加备注";
        var error = document.createElement("p");
        error.id = "end-error-" + entryId;
        error.className = "inline-error hidden";
        error.setAttribute("aria-live", "polite");
        function showCardError(message) {
          error.textContent = message;
          error.classList.remove("hidden");
        }
        save.addEventListener("click", function () {
          var value = parseInt(rating.value, 10);
          if (value < 1 || value > 5) {
            showCardError("请输入 1-5 的评分");
            return;
          }
          var feedback = {
            item_type: itemType, item_id: itemId,
            rating: value, note: note.value.trim(),
          };
          var origin = item;
          if (origin.feedback_status === "saving") return;
          if (itemType !== "card") {
            // Link the rating back to the attempt the submission created.
            if (origin.attempt_id) feedback.attempt_id = origin.attempt_id;
          }
          if (itemType === "card") feedback.direction = direction || "forward";
          updateSession(origin.id, { feedback_status: "saving" }, origin.direction);
          ensureAttempt(origin).then(function (attemptId) {
            if (itemType !== "card" && attemptId) feedback.attempt_id = attemptId;
            return saveItemFeedback(origin, feedback);
          }).then(function () {
            card.remove();
            remaining -= 1;
            if (!remaining) pending.innerHTML = "<p>全部评完 ✓</p>";
          }).catch(function (err) {
            updateSession(origin.id, { feedback_status: "failed" }, origin.direction);
            showCardError(err.message || "保存失败");
          });
        });
        card.appendChild(error);
        card.appendChild(ratingLabel);
        card.appendChild(rating);
        card.appendChild(noteLabel);
        card.appendChild(note);
        card.appendChild(save);
        pending.appendChild(card);
        renderMath(card);
      };
      unrated.forEach(function (item) {
        if (item.kind === "card") {
          var card = item.payload || {};
          var sides = cardSides(item);
          var directionLabel = item.direction === "reverse" ? "反向" : "正向";
          buildRatingCard(
            "<p class='context-line'>闪卡 · " + directionLabel + "</p>"
            + "<div class='problem-text rich-text'>" + richText(sides.prompt) + "</div>"
            + "<p class='section-kicker'>另一面</p><div class='rich-text'>" + richText(sides.answer) + "</div>",
            "card", item.id, String(sides.prompt || "闪卡"), item.direction, item);
          return;
        }
        api("/problem/" + item.id).then(function (detail) {
          var problem = detail.problem;
          var title = problem.display_title || "未命名题目";
          var quiz = problem.micro_quiz && typeof problem.micro_quiz === "object"
            ? problem.micro_quiz : null;
          var solutionHtml = quiz
            ? "<p class='section-kicker'>答案</p><div class='rich-text'>"
              + richText(quizHasKey(quiz) ? String(quiz.answer_key) : "未录入答案键")
              + "</div>"
              + (quiz.error_reason
                ? "<p class='section-kicker'>为什么</p><div class='rich-text'>"
                  + richText(quiz.error_reason) + "</div>"
                : "")
            : "<p class='section-kicker'>解析</p><div class='rich-text'>"
              + richText(problem.solution || "（本题无解析）") + "</div>";
          buildRatingCard(
            "<p class='context-line'>练习题</p><h2>" + escapeHtml(title) + "</h2>"
            + "<div class='problem-text rich-text'>" + richText(problem.problem_text) + "</div>"
            + "<p class='section-kicker'>我的作答</p><div class='rich-text'>" + richText(item.answer_text || "（未作答）") + "</div>"
            + solutionHtml,
            "problem", item.id, title, "", item);
        });
      });
    }
    var similar = document.getElementById("practice-similar");
    if (similar) similar.addEventListener("click", function () {
      var scope = currentKps();
      sessionStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(CURRENT_KEY);
      sessionStorage.removeItem(MODE_KEY);
      sessionStorage.removeItem(RATING_MODE_KEY);
      if (scope.length) {
        store(KPS_KEY, scope);
        saveSelectedKpIds(scope);
      }
      sessionStorage.setItem(SIMILAR_KEY, "1");
      window.location = "practice";
    });
  }

  function practiceSolutionHtml(problem) {
    // A source answer, a source solution, and an AI explanation are three
    // different things and must not read as one.
    var sections = "";
    var answer = problem.source_answer;
    if (answer && String(answer).trim()) {
      sections += "<section class='practice-solution'><p class='section-kicker'>教材答案</p>"
        + "<div class='rich-text'>" + richText(String(answer)) + "</div></section>";
    }
    var origin = problem.solution_origin;
    var label = origin === "generated" ? "AI 生成解析"
      : origin === "source" ? "教材解析" : "解析";
    var solution = problem.solution;
    if (solution && String(solution).trim()) {
      sections += "<section class='practice-solution'><p class='section-kicker'>" + label + "</p>"
        + "<div class='rich-text'>" + richText(String(solution)) + "</div></section>";
    } else if (!sections) {
      sections = "<section class='practice-solution'><p class='section-kicker'>解析</p>"
        + "<div class='rich-text'>（本题无解析，请基于自身作答自评）</div></section>";
    }
    return sections;
  }

  function practiceSourceHtml(problem) {
    var evidence = String((problem && problem.source_evidence) || "").replace(/\s+/g, " ").trim();
    if (!evidence) return "";
    return "<p class='practice-source'>来源：" + escapeHtml(evidence) + "</p>";
  }


    return {
      currentProblem: currentProblem,
      session: session,
      visiblePracticeImages: visiblePracticeImages,
      draftAnswer: function () { return answerBox ? answerBox.value : ""; },
      draftNote: function () { return feedbackNote ? feedbackNote.value : ""; },
    };
  }

  return { start: start };
}));
