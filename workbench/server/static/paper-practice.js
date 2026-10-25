/* PaperPractice — browser controller for freely navigable saved-Paper runs. */
(function (root, factory) {
  root.PaperPractice = factory();
}(typeof globalThis === "object" ? globalThis : this, function () {
  var EMPTY = {
    currentProblem: function () { return null; },
    session: function () { return []; },
    visiblePracticeImages: function () { return []; },
    draftAnswer: function () { return ""; },
    draftNote: function () { return ""; },
    selectionContext: function () { return {}; },
    dispose: function () {},
  };

  function start(deps, legacyStart) {
    var root = document.getElementById("paper-practice");
    if (!root) return EMPTY;

    var layout = document.getElementById("layout");
    var workspace = layout && layout.dataset ? layout.dataset.workspace : "";
    var api = deps.api;
    var post = deps.post;
    var showRatingEnabled = deps.showRatingEnabled || function () { return true; };
    var renderMath = deps.renderMath || function () {};
    var richText = deps.richText || function (value) { return deps.escapeHtml(String(value || "")); };
    var escapeHtml = deps.escapeHtml || function (value) { return String(value || ""); };
    var navigate = deps.navigate || function (target) { window.location.href = target; };
    var ids = {
      setup: document.getElementById("paper-setup"),
      title: document.getElementById("paper-title"),
      count: document.getElementById("paper-count"),
      timing: document.getElementById("paper-reveal-timing"),
      start: document.getElementById("paper-start"),
      error: document.getElementById("paper-error"),
      work: document.getElementById("paper-work"),
      stemIndex: document.getElementById("paper-stem-index"),
      question: document.getElementById("paper-question"),
      answer: document.getElementById("paper-answer"),
      options: document.getElementById("paper-options"),
      itemSubmit: document.getElementById("paper-item-submit"),
      reference: document.getElementById("paper-reference"),
      rating: document.getElementById("paper-rating"),
      toolbar: document.getElementById("paper-toolbar"),
      previous: document.getElementById("paper-prev"),
      next: document.getElementById("paper-next"),
      stuck: document.getElementById("paper-stuck"),
      finalSubmit: document.getElementById("paper-final-submit"),
      dots: document.getElementById("paper-dots"),
      pause: document.getElementById("paper-pause"),
      completion: document.getElementById("paper-completion"),
      completionStats: document.getElementById("paper-completion-stats"),
      completionFigures: document.getElementById("paper-completion-figures"),
      review: document.getElementById("paper-review"),
      return: document.getElementById("paper-return"),
      again: document.getElementById("paper-again"),
      links: document.getElementById("paper-links"),
    };
    var address = new URL(window.location.href);
    var requestedPaperId = address.searchParams.get("paper") || "";
    var requestedRunId = address.searchParams.get("run") || "";
    var savedPaper = null;
    var run = null;
    var archived = null;
    var archivedRecord = null;
    var local = null;
    var localKey = "";
    var legacy = null;
    var position = 0;
    var renderingArchived = false;
    var reviewing = false;
    var disposed = false;
    var navigationBusy = false;
    var modeAdopting = false;
    var finalBusy = false;
    var answerBusy = {};
    var draftTimers = {};
    var draftWrites = {};
    var renderGeneration = 0;
    var requestCounter = 0;
    var ratingInput = null;
    var ratingNote = null;
    var celebrationAnchorEl = null;
    /* ---------- 连对反馈（tasks.md 17.1 / 17.3 / 17.8） ----------
       与快速练习流（practice-flow.js）同一套：状态机在公共 API window.lkStreak
       里（decisions.md A-58），这里只持有本轮的一个实例 —— 计数 / 三级档 /
       递增 / 断裂 / 复位 / 横幅 / 火苗只有一份实现。
       判定来源仍在本流（提交载荷里的 verdict）——公共 API 只管「拿到判定之后
       怎么反馈」，判定语义不动。
       ⚠️ 该共用件与 window.lkTicker 一样是「可有可无」的：不带 workbench.js
       单独跑本文件时（测试夹具）没有连对反馈 —— 挂一个恒为 0 的数字是没有
       信息量的假事实（A-59 同一原则）。 */
    var streak = window.lkStreak && typeof window.lkStreak.create === "function"
      ? window.lkStreak.create({ root: ids.question })
      : null;

    function emptyLocal() {
      return {
        position: 0,
        drafts: {},
        sequences: {},
        pendingDrafts: {},
        pendingAttempts: {},
        pendingStuck: {},
        pendingRatings: {},
        ratingDrafts: {},
        pendingPosition: null,
        pendingFinalize: null,
      };
    }

    function jsonCopy(value) {
      return JSON.parse(JSON.stringify(value));
    }

    function requestId() {
      if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID();
      requestCounter += 1;
      return Date.now().toString(36) + "-" + requestCounter.toString(36);
    }

    function setVisible(element, visible) {
      if (!element) return;
      element.hidden = !visible;
      if (element.classList) element.classList.toggle("hidden", !visible);
    }

    function clearError() {
      if (!ids.error) return;
      ids.error.textContent = "";
      if (ids.error.replaceChildren) ids.error.replaceChildren();
      setVisible(ids.error, false);
    }

    function showError(message) {
      if (!ids.error) return;
      ids.error.textContent = String(message || "操作未完成");
      setVisible(ids.error, true);
    }

    function showRetryError(message, label, retry) {
      if (!ids.error) return;
      if (ids.error.replaceChildren) ids.error.replaceChildren();
      var text = document.createElement("span");
      text.textContent = String(message || "操作未完成");
      var button = document.createElement("button");
      button.type = "button";
      button.className = "outline sm";
      button.textContent = label;
      button.addEventListener("click", function () {
        clearError();
        retry();
      });
      ids.error.appendChild(text);
      ids.error.appendChild(button);
      setVisible(ids.error, true);
    }

    function workspaceName() {
      if (workspace) return workspace;
      return address.pathname.split("/")[2] || "default";
    }

    function itemPosition(item, index) {
      return typeof item.position === "number" ? item.position : index;
    }

    function rowAt(index) {
      return run && run.items ? run.items[index] || null : null;
    }

    function activeItem() {
      return rowAt(position);
    }

    function rowKey(item, index) {
      return String(item ? itemPosition(item, index === undefined ? position : index) : "");
    }

    function hasBusyAnswerWrites() {
      return Object.keys(answerBusy).some(function (key) { return !!answerBusy[key]; });
    }

    function isVisibleItem(item, index) {
      var current = activeItem();
      return position === index && current && current.item_id === item.item_id;
    }

    function isPaperRun(record) {
      return !!record && record.execution_id !== undefined && record.execution_id !== null
        && String(record.execution_id) !== ""
        && Array.isArray(record.items)
        && record.items.length > 0
        && record.items.every(function (item) { return item.item_type === "problem"; });
    }

    function isSavedPaperRun(record) {
      return !!record && typeof record.source_ref === "string"
        && record.source_ref.indexOf("ps-") === 0;
    }

    function currentMode() {
      return (run && run.reveal_timing) || "per_item";
    }

    function contextFor(record, item, index) {
      return {
        execution_id: record.execution_id,
        paper_id: record.source_ref || record.paper_id || null,
        paper_generation: record.paper_generation || record.generation || 1,
        item_id: item.item_id,
        content_revision: item.content_revision,
        position: itemPosition(item, index),
      };
    }

    function localStorageKey(executionId) {
      return "wb_paper_practice_" + workspaceName() + "_" + String(executionId);
    }

    function loadLocal(record) {
      localKey = localStorageKey(record.execution_id);
      var raw = window.localStorage.getItem(localKey);
      local = emptyLocal();
      if (!raw) return;
      try {
        var stored = JSON.parse(raw);
        Object.keys(local).forEach(function (key) {
          if (stored[key] !== undefined) local[key] = stored[key];
        });
      } catch (error) {
        window.localStorage.removeItem(localKey);
      }
    }

    function localHasPending() {
      return !!(local && (Object.keys(local.pendingDrafts).length
        || Object.keys(local.pendingAttempts).length
        || Object.keys(local.pendingStuck).length
        || Object.keys(local.pendingRatings).length
        || local.pendingPosition || local.pendingFinalize));
    }

    function persistLocal() {
      if (!local || !localKey) return;
      local.position = position;
      if (!localHasPending() && !Object.keys(local.drafts).length
          && !Object.keys(local.ratingDrafts).length) {
        window.localStorage.removeItem(localKey);
        return;
      }
      window.localStorage.setItem(localKey, JSON.stringify(local));
    }

    function draftValue(item) {
      if (!item.draft || typeof item.draft !== "object") item.draft = {};
      return {
        answer: String(item.draft.answer || ""),
        choices: Array.isArray(item.draft.choices) ? item.draft.choices.slice() : [],
        stuck: !!item.draft.stuck,
        reference_viewed: !!item.draft.reference_viewed,
      };
    }

    function mergeLocalDrafts(record) {
      if (!local || !record || !record.items) return;
      record.items.forEach(function (item, index) {
        var key = rowKey(item, index);
        var pending = local.pendingDrafts[key];
        var sequence = Number(local.sequences[key] || 0);
        if (pending || (local.drafts[key] && sequence > Number(item.draft_sequence || 0))) {
          item.draft = jsonCopy(pending ? pending.draft : local.drafts[key]);
          item.draft_sequence = Math.max(sequence, Number(item.draft_sequence || 0));
        }
      });
      if (local.position !== undefined && (local.pendingPosition || local.pendingFinalize)) {
        position = Math.max(0, Math.min(Number(local.position) || 0, record.items.length - 1));
      }
    }

    function extractPractice(response) {
      if (!response) return null;
      if (response.practice && response.practice.practice) return response.practice.practice;
      if (response.practice && Array.isArray(response.practice.items)) return response.practice;
      if (Array.isArray(response.items)) return response;
      return null;
    }

    function adoptRun(record, renderIfCurrent) {
      if (!record || record.execution_id !== run.execution_id) return false;
      var activePosition = position;
      run = record;
      position = Math.max(0, Math.min(activePosition, (run.items || []).length - 1));
      mergeLocalDrafts(run);
      if (renderIfCurrent) renderCurrent();
      return true;
    }

    function delegateLegacy() {
      setVisible(root, false);
      setVisible(document.getElementById("legacy-practice"), true);
      if (legacy) return legacy;
      if (typeof legacyStart === "function") legacy = legacyStart(deps) || EMPTY;
      else legacy = EMPTY;
      return legacy;
    }

    function prepareRun(record, isArchived) {
      var shouldAdoptMode = !isArchived && !record.reveal_timing && isPaperRun(record);
      run = record;
      if (streak) streak.reset();   /* 新的一轮从零开始 */
      renderingArchived = !!isArchived;
      reviewing = false;
      modeAdopting = shouldAdoptMode;
      position = Math.max(0, Math.min(Number(record.cursor) || 0, (record.items || []).length - 1));
      loadLocal(record);
      mergeLocalDrafts(record);
      setVisible(ids.setup, false);
      setVisible(ids.work, !isArchived);
      /* The milestone facts must be on the surface before it turns visible:
         the shared celebration reads them the moment the completion shows. */
      if (isArchived) writeCompletionFacts(record);
      setVisible(ids.completion, !!isArchived);
      setVisible(ids.return, false);
      if (isArchived) {
        archived = record;
        renderCompletion();
      } else {
        archived = null;
        archivedRecord = null;
        setVisible(ids.toolbar, true);
        renderCurrent();
        if (shouldAdoptMode) adoptLegacyMode();
        else retryPendingWrites();
      }
    }

    function adoptLegacyMode() {
      if (!run || !modeAdopting || disposed) return Promise.resolve();
      var item = activeItem();
      var index = position;
      var body = {
        execution_id: run.execution_id,
        position: itemPosition(item, index),
        practice_context: contextFor(run, item, index),
      };
      renderCurrent();
      return post("/practice/current/navigate", body).then(function (response) {
        var updated = extractPractice(response);
        if (!updated || updated.execution_id !== run.execution_id || !updated.reveal_timing) {
          throw new Error("服务端未确认练习模式更新，请重试。");
        }
        adoptRun(updated, false);
        modeAdopting = false;
        persistLocal();
        clearError();
        renderCurrent();
        retryPendingWrites();
      }).catch(function (error) {
        modeAdopting = true;
        renderCurrent();
        showRetryError(error.message || "无法恢复此试卷练习，请重试。", "重试恢复", adoptLegacyMode);
      });
    }

    function showSetup(record) {
      savedPaper = record;
      var count = record.count || (record.plan && record.plan.items ? record.plan.items.length : 0);
      if (ids.title) ids.title.textContent = record.title || "练习试卷";
      if (ids.count) ids.count.textContent = String(count);
      var continuation = record.continuation || null;
      var canContinue = !!(continuation && continuation.available);
      var canStart = record.can_start !== false || canContinue;
      var execution = continuation && continuation.execution || {};
      if (continuation) {
        if (ids.timing) {
          ids.timing.value = execution.reveal_timing || "per_item";
          ids.timing.disabled = true;
        }
        if (ids.start) ids.start.textContent = canContinue ? "继续练习" : "暂不能继续";
        if (!canContinue) showError(continuation.reason || record.start_block_reason || "当前试卷无法继续。");
      } else {
        if (ids.timing) {
          ids.timing.disabled = false;
          if (ids.timing.value !== "on_submit" && ids.timing.value !== "per_item") {
            ids.timing.value = "per_item";
          }
        }
        if (ids.start) ids.start.textContent = "开始练习";
        if (!canStart) showError(record.start_block_reason || "当前试卷暂时无法开始。");
      }
      if (ids.start) ids.start.disabled = !canStart;
      setVisible(ids.setup, true);
      setVisible(ids.work, false);
      setVisible(ids.completion, false);
      setVisible(ids.toolbar, false);
    }

    function initializePaper(paperId) {
      Promise.all([
        api("/practice-sets/" + encodeURIComponent(paperId)),
        api("/practice/current"),
      ]).then(function (results) {
        if (disposed) return;
        var record = results[0];
        var current = results[1] && results[1].practice;
        if (current && (current.items || []).some(function (item) { return item.item_type === "card"; })) {
          delegateLegacy();
          return;
        }
        showSetup(record);
      }).catch(function (error) {
        if (!disposed) showError(error.message || "无法读取试卷。");
      });
    }

    function initializeCurrent() {
      api("/practice/current").then(function (response) {
        if (disposed) return;
        var current = response && response.practice;
        if (isPaperRun(current)) {
          prepareRun(current, false);
          return;
        }
        if (current && (current.items || []).some(function (item) { return item.item_type === "card"; })) {
          delegateLegacy();
          return;
        }
        if (current) {
          delegateLegacy();
          return;
        }
        showEmptySetup();
      }).catch(function (error) {
        if (!disposed) showError(error.message || "无法恢复当前练习。");
      });
    }

    function showEmptySetup() {
      savedPaper = null;
      clearError();
      if (ids.title) ids.title.textContent = "选择一份试卷";
      if (ids.count) ids.count.textContent = "先从试卷列表打开一份已保存的试卷。";
      if (ids.timing) ids.timing.disabled = true;
      if (ids.start) {
        ids.start.disabled = true;
        ids.start.textContent = "选择试卷";
      }
      setVisible(ids.setup, true);
      setVisible(ids.work, false);
      setVisible(ids.toolbar, false);
      setVisible(ids.completion, false);
    }

    function initializeArchived(runId) {
      api("/practice/runs/" + encodeURIComponent(runId)).then(function (record) {
        if (disposed) return;
        prepareRun(record, true);
      }).catch(function (error) {
        if (!disposed) showError(error.message || "无法读取本次答卷。");
      });
    }

    function savedStart() {
      if (!savedPaper || !ids.start || ids.start.disabled) return Promise.resolve();
      ids.start.disabled = true;
      clearError();
      var continuation = savedPaper.continuation;
      var body;
      var startRequest;
      if (archivedRecord) {
        var replay = archivedRecord;
        body = {
          source_kind: "paper",
          source_ref: null,
          source_label: replay.source_label || savedPaper.title || "练习试卷",
          kp_ids: Array.isArray(replay.kp_ids) ? replay.kp_ids.slice() : [],
          practice_mode: replay.practice_mode || "exam",
          rating_mode: showRatingEnabled() ? "immediate" : "off",
          reveal_timing: ids.timing && ids.timing.value === "on_submit" ? "on_submit" : "per_item",
          items: (replay.items || []).map(function (item) {
            return {
              item_type: item.item_type,
              item_id: item.item_id,
              direction: item.direction || "",
            };
          }),
        };
        startRequest = post("/practice/current", body);
      } else {
        body = {
          practice_mode: "exam",
          rating_mode: showRatingEnabled() ? "immediate" : "off",
        };
        if (!continuation) body.reveal_timing = ids.timing && ids.timing.value === "on_submit"
          ? "on_submit" : "per_item";
        startRequest = post("/practice-sets/" + encodeURIComponent(savedPaper.practice_set_id) + "/start", body);
      }
      return startRequest
        .then(function (response) {
          var started = extractPractice(response);
          if (!started) throw new Error("服务端未返回已开始的练习。");
          prepareRun(started, false);
        }).catch(function (error) {
          ids.start.disabled = false;
          showError(error.message || "无法开始练习。");
        });
    }

    function problemFor(item) {
      return item && item.payload && typeof item.payload === "object" ? item.payload : {};
    }

    function quizFor(problem) {
      return problem && problem.micro_quiz && typeof problem.micro_quiz === "object"
        ? problem.micro_quiz : null;
    }

    function quizHasKey(quiz) {
      if (!quiz) return false;
      var answer = quiz.answer_key;
      return typeof answer === "string" ? !!answer.trim()
        : Array.isArray(answer) && answer.length > 0;
    }

    function optionsFor(problem) {
      var quiz = quizFor(problem);
      if (quiz) {
        if (quiz.quiz_type === "yes_no") return (quiz.options || ["是", "否"]).map(function (text) {
          return { id: String(text), text: String(text) };
        });
        if (quiz.quiz_type === "single_choice" || quiz.quiz_type === "multiple_choice") {
          return (quiz.options || []).map(function (text) {
            return { id: String(text), text: String(text) };
          });
        }
      }
      var raw = problem && problem.options_json;
      if (typeof raw === "string") {
        try { raw = JSON.parse(raw); } catch (error) { return []; }
      }
      if (!Array.isArray(raw)) return [];
      return raw.map(function (option) {
        if (typeof option === "string") return { id: option, text: option };
        if (!option || typeof option !== "object") return null;
        var value = option.id || option.key || option.value || option.text || "";
        var text = option.text || option.label || option.value || option.id || "";
        return value ? { id: String(value), text: String(text) } : null;
      }).filter(function (option) { return !!option; });
    }

    function isMultiple(item) {
      var quiz = quizFor(problemFor(item));
      return !!quiz && quiz.quiz_type === "multiple_choice";
    }

    function isTextItem(item) {
      return optionsFor(problemFor(item)).length === 0;
    }

    function grade(item, choices) {
      var quiz = quizFor(problemFor(item));
      if (!quizHasKey(quiz)) return null;
      if (quiz.quiz_type === "multiple_choice") {
        if (!Array.isArray(quiz.answer_key)) return null;
        return choices.slice().sort().join("|") === quiz.answer_key.slice().sort().join("|");
      }
      return choices[0] === quiz.answer_key;
    }

    function itemDraftIsFilled(item) {
      var draft = draftValue(item);
      return !!(draft.answer.trim() || draft.choices.length);
    }

    function itemStatus(item, index) {
      var draft = draftValue(item);
      var attempt = item.attempt || {};
      if (renderingArchived) {
        if (item.state === "stuck") return "stuck";
        if (attempt.verdict === true || attempt.verdict === 1) return "correct";
        if (attempt.verdict === false || attempt.verdict === 0) return "wrong";
        return item.state === "answered" ? "locked" : "unanswered";
      }
      if (currentMode() === "on_submit") {
        if (draft.stuck) return "stuck";
        return itemDraftIsFilled(item) ? "filled" : "unanswered";
      }
      if (item.state === "stuck") return "stuck";
      if (item.state === "answered") {
        if (attempt.verdict === true || attempt.verdict === 1) return "correct";
        if (attempt.verdict === false || attempt.verdict === 0) return "wrong";
        return "locked";
      }
      return itemDraftIsFilled(item) ? "filled" : "unanswered";
    }

    function statusLabel(status) {
      return {
        unanswered: "未作答", filled: "已填写，未提交", stuck: "不会",
        correct: "正确", wrong: "错误", locked: "已提交，暂无判定",
      }[status] || "状态未知";
    }

    function renderDots() {
      if (!ids.dots || !run) return;
      ids.dots.replaceChildren();
      run.items.forEach(function (item, index) {
        var status = itemStatus(item, index);
        var button = document.createElement("button");
        button.type = "button";
        button.className = "paper-dot state-" + status + (position === index ? " is-current" : "");
        button.dataset.paperPosition = String(index);
        button.textContent = String(itemPosition(item, index));
        button.disabled = navigationBusy || modeAdopting;
        button.setAttribute("aria-label", "第" + itemPosition(item, index) + "题，" + statusLabel(status)
          + (position === index ? "，当前题" : ""));
        if (position === index) button.setAttribute("aria-current", "step");
        button.addEventListener("click", function () { moveTo(index); });
        ids.dots.appendChild(button);
      });
    }

    function answerChoices(item) {
      if (renderingArchived) {
        if (Array.isArray(item.attempt && item.attempt.choices) && item.attempt.choices.length) {
          return item.attempt.choices.slice();
        }
        return item.attempt && item.attempt.answer_text ? [String(item.attempt.answer_text)] : [];
      }
      if (currentMode() === "per_item" && item.state === "answered") {
        if (Array.isArray(item.attempt && item.attempt.choices) && item.attempt.choices.length) {
          return item.attempt.choices.slice();
        }
        return item.attempt && item.attempt.answer_text ? [String(item.attempt.answer_text)] : [];
      }
      return draftValue(item).choices;
    }

    function buildQuestion(problem) {
      var title = problem.display_title || problem.title || "未命名题目";
      var prompt = problem.problem_text || "题面暂不可用。";
      var paperTitle = run.source_label || (savedPaper && savedPaper.title) || "练习试卷";
      var streakMarkup = streak ? streak.html() : "";
      /* 16.1 题号槽位：服务端只给槽位，值必须由客户端写 —— 题号随题序变，
         服务端不知道当前第几题。编号与题号点（#paper-dots）、完成页逐题链接
         同一口径：**itemPosition(item, index)** —— 单一真源，与提交载荷里的
         position / practice_position 同源（否则服务端一旦重排，页面上会出现
         两套编号）。槽位自带 aria-hidden='true'，只写值，
         不改成可读文本，也不加内联字号/颜色（样式归 workbench.css）。 */
      if (ids.stemIndex) {
        var stemItem = run && run.items ? run.items[position] : null;
        ids.stemIndex.textContent = String(itemPosition(stemItem, position));
      }
      ids.question.innerHTML = "<p class='section-kicker paper-run-title'>" + escapeHtml(paperTitle) + "</p>"
        /* 连对计数器常驻练习页；横幅绝对定位在这一行的定位上下文里。
           回看已完成的答卷时不挂 —— 那不是一轮练习。
           on_submit 模式也不挂（decisions.md A-59）：该模式没有逐题判定，
           连对计数整轮恒为 0 —— 显示一个恒为 0 的数字是没有信息量的假事实。
           判据用既有的 currentMode() === "on_submit"（与 itemStatus 等处同一口径）。
           模式未知时（老记录接管窗口：reveal_timing 尚空，currentMode() 会兜底成
           per_item）同样不挂 —— 宁可晚一点显示，也不要先闪一个恒为 0 的假数
           （所有者裁决 2026-10-22）。currentMode() 的兜底不动（它被 15 处用），
           只在这里多判一个「reveal_timing 为空」。 */
        + (renderingArchived || !run.reveal_timing || currentMode() === "on_submit"
          ? "" : "<p class='practice-streak' style='position: relative'>" + streakMarkup + "</p>")
        + "<h2>" + escapeHtml(title) + "</h2>"
        + "<div class='wb-reading wb-reading--stem problem-text'>" + richText(String(prompt)) + "</div>"
        + (problem.source_evidence
          ? "<p class='practice-source'>来源：" + escapeHtml(problem.source_evidence) + "</p>" : "");
      renderMath(ids.question);
    }

    function buildOptions(item, locked) {
      if (!ids.options) return;
      ids.options.replaceChildren();
      var options = optionsFor(problemFor(item));
      if (!options.length) return;
      var multiple = isMultiple(item);
      var choices = answerChoices(item);
      var fieldset = document.createElement("fieldset");
      fieldset.className = "problem-options";
      fieldset.disabled = !!locked;
      var legend = document.createElement("legend");
      legend.textContent = multiple ? "选择所有适用答案" : "选择答案";
      fieldset.appendChild(legend);
      options.forEach(function (option) {
        var label = document.createElement("label");
        label.className = "option-row";
        var input = document.createElement("input");
        input.type = multiple ? "checkbox" : "radio";
        input.name = "paper-choice-" + itemPosition(item, position);
        input.value = option.id;
        input.dataset.paperChoice = option.id;
        input.checked = choices.indexOf(option.id) >= 0;
        input.disabled = !!locked;
        var text = document.createElement("span");
        text.innerHTML = richText(option.text);
        label.appendChild(input);
        label.appendChild(text);
        fieldset.appendChild(label);
      });
      ids.options.appendChild(fieldset);
      renderMath(ids.options);
    }

    function referenceHtml(item, includeVerdict) {
      var problem = problemFor(item);
      var quiz = quizFor(problem);
      var attempt = item.attempt || {};
      var parts = [];
      if (includeVerdict) {
        if (item.state === "stuck") parts.push("<p class='muted'>本题已标记为“不会”。</p>");
        else if (attempt.verdict === true || attempt.verdict === 1) parts.push("<p class='micro-verdict ok'>判定：正确</p>");
        else if (attempt.verdict === false || attempt.verdict === 0) parts.push("<p class='micro-verdict bad'>判定：错误</p>");
        else if (item.state === "answered") parts.push("<p class='muted'>本次作答没有可用的客观判定。</p>");
      }
      var key = quiz && quizHasKey(quiz) ? quiz.answer_key : problem.source_answer;
      if (key !== undefined && key !== null && String(key).trim()) {
        parts.push("<p class='section-kicker'>参考答案</p><div class='wb-reading'>"
          + richText(Array.isArray(key) ? key.join("、") : String(key)) + "</div>");
      } else if (quiz) {
        parts.push("<p class='muted'>本题没有可用答案键。</p>");
      }
      if (quiz && quiz.error_reason) {
        parts.push("<p class='section-kicker'>判定依据</p><div class='wb-reading'>"
          + richText(String(quiz.error_reason)) + "</div>");
      }
      if (problem.solution && String(problem.solution).trim()) {
        parts.push("<p class='section-kicker'>解析</p><div class='wb-reading'>"
          + richText(String(problem.solution)) + "</div>");
      }
      if (!parts.length || (parts.length === 1 && !includeVerdict && parts[0].indexOf("没有可用答案键") >= 0)) {
        parts.push("<p class='muted'>本题暂无可用参考内容。</p>");
      }
      return parts.join("");
    }

    function shouldRevealReference(item) {
      if (renderingArchived) return true;
      if (currentMode() === "per_item") return item.state === "answered" || item.state === "stuck";
      return !!draftValue(item).reference_viewed;
    }

    function renderReference(item) {
      var reveal = shouldRevealReference(item);
      if (!reveal) {
        ids.reference.innerHTML = "<p class='muted'>尚未显示参考答案。交卷前不会显示判定或参考材料。</p>";
      } else {
        var full = renderingArchived || currentMode() === "per_item";
        ids.reference.innerHTML = referenceHtml(item, full);
      }
      setVisible(ids.reference, true);
      renderMath(ids.reference);
    }

    /* 答对的挤压回弹（motion-spec §3.1 / A-89）：落点是**被选中的那一项**
       ——正确选项那一行（底边为锚，读作「被顶了一下」）。
       · 判定行（`.micro-verdict.ok`）另挂 `lk-verdict-correct` 作标记（**无样式**），
         走查探针据此认出「判定正确」；
       · 落点行挂 `lk-squash`（样式表规则：
         `.lk-squash { transform-origin: 50% 100%; animation: lk-squash-bounce 517ms both; }`），
         这里同时写一份内联声明（与 workbench.js 的 `lk-error-nudge` 同一写法），
         规则补齐之前回弹也已经发生；
       · **终态铁律**：压扁只写在 `@keyframes` 里，元素的静态样式是终态
         （不压扁），降级后读得出；
       · **动效红线**：关键帧只动 `transform`（scale），不动布局；
       · 只在提交路径挂 ⇒ 判定只回弹一次，回看旧答案不重播；
       · 判定为错 / 不会 / 没有「判定正确」时整段不挂。
       本流的选项行实际类名：`<label class='option-row'>`（在
       `<fieldset class='problem-options'>` 内），「被选中」= 里面的
       `input[data-paper-choice]` 处于选中态。
       走查探针（tools/walkthrough/frames.py 的 M-7）等的是
       `document.getAnimations()` 里名为 `lk-squash-bounce` 的动画 ⇒
       落点行上必须真的有这条动画（判定行只带标记，不带动画）。 */
    function squashCorrectOption(root) {
      if (!root || typeof root.querySelectorAll !== "function") return;
      var verdicts = root.querySelectorAll(".micro-verdict.ok");
      var verdict = verdicts && verdicts.length ? verdicts[0] : null;
      if (!verdict) return;
      if (verdict.classList) verdict.classList.add("lk-verdict-correct");
      var inputs = root.querySelectorAll("input[data-paper-choice]:checked");
      Array.prototype.slice.call(inputs || []).forEach(function (input) {
        var row = input && input.closest ? input.closest("label") : null;
        if (!row || !row.classList) return;
        row.classList.add("lk-squash");
        if (row.style) {
          row.style.animation = "lk-squash-bounce 517ms both";
          row.style.transformOrigin = "50% 100%";
        }
      });
    }

    function feedbackFor(item) {
      return item.feedback || null;
    }

    function confirmedFeedback(item, body, response) {
      var feedback = Object.assign({}, feedbackFor(item) || {});
      if (response && response.feedback && typeof response.feedback === "object") {
        feedback = Object.assign(feedback, response.feedback);
      }
      feedback.attempt_id = body.attempt_id;
      feedback.rating = body.rating;
      feedback.note = body.note;
      if (response && response.feedback_event_id !== undefined) {
        feedback.id = response.feedback_event_id;
      }
      return feedback;
    }

    function canRate(item) {
      return !!(run && item.item_type === "problem"
        && item.attempt_id && (item.state === "answered" || item.state === "stuck")
        && (renderingArchived || currentMode() === "per_item"));
    }

    function renderRating(item) {
      if (!ids.rating) return;
      ids.rating.replaceChildren();
      ratingInput = null;
      ratingNote = null;
      if (!canRate(item)) {
        setVisible(ids.rating, false);
        return;
      }
      var positionKey = rowKey(item, position);
      var feedback = feedbackFor(item) || {};
      var pending = local && local.ratingDrafts[positionKey] || {};
      var heading = document.createElement("p");
      heading.className = "section-kicker";
      heading.textContent = "自评（可选）";
      var label = document.createElement("label");
      label.textContent = "自评 1–5";
      ratingInput = document.createElement("input");
      ratingInput.type = "number";
      ratingInput.min = "1";
      ratingInput.max = "5";
      ratingInput.inputMode = "numeric";
      ratingInput.value = String(pending.rating === undefined ? (feedback.rating || "") : pending.rating);
      label.appendChild(ratingInput);
      var noteLabel = document.createElement("label");
      noteLabel.textContent = "备注（可选）";
      ratingNote = document.createElement("textarea");
      ratingNote.value = pending.note === undefined ? (feedback.note || "") : pending.note;
      noteLabel.appendChild(ratingNote);
      var save = document.createElement("button");
      save.type = "button";
      save.className = "outline sm";
      save.textContent = feedback.rating ? "保存自评修改" : "保存自评";
      save.addEventListener("click", function () { saveRating(item, ratingInput, ratingNote); });
      ids.rating.appendChild(heading);
      ids.rating.appendChild(label);
      ids.rating.appendChild(noteLabel);
      ids.rating.appendChild(save);
      ratingInput.addEventListener("input", function () { saveRatingDraft(item); });
      ratingNote.addEventListener("input", function () { saveRatingDraft(item); });
      setVisible(ids.rating, true);
    }

    function saveRatingDraft(item) {
      if (!local || !ratingInput || !ratingNote) return;
      var key = rowKey(item, position);
      local.ratingDrafts[key] = { rating: ratingInput.value, note: ratingNote.value };
      persistLocal();
    }

    function saveRating(item, ratingField, noteField, retryPayload) {
      if (disposed || !canRate(item)) return Promise.resolve();
      var rating = Number(ratingField.value);
      if (!Number.isInteger(rating) || rating < 1 || rating > 5) {
        showError("请输入 1–5 的自评分数。");
        return Promise.resolve();
      }
      var key = rowKey(item, position);
      var feedback = feedbackFor(item);
      var pending = retryPayload || (local.pendingRatings[key] && local.pendingRatings[key].payload);
      var body = pending || {
        item_type: "problem",
        item_id: item.item_id,
        attempt_id: item.attempt_id,
        rating: rating,
        note: String(noteField.value || "").trim(),
        request_id: requestId(),
        practice_context: contextFor(run, item, position),
      };
      if (feedback && feedback.rating && !pending) {
        body.edit_existing = true;
        body.expected_rating = feedback.rating;
        body.expected_note = feedback.note === undefined ? null : feedback.note;
      }
      local.pendingRatings[key] = { payload: jsonCopy(body) };
      saveRatingDraft(item);
      persistLocal();
      clearError();
      return post("/feedback", body).then(function (response) {
        if (disposed) return;
        var current = rowAt(position);
        var target = run.items.find(function (candidate) { return candidate.item_id === item.item_id; });
        if (target) target.feedback = confirmedFeedback(target, body, response);
        delete local.pendingRatings[key];
        delete local.ratingDrafts[key];
        persistLocal();
        clearError();
        if (current && current.item_id === item.item_id) renderCurrent();
        if (renderingArchived) renderCompletion();
      }).catch(function (error) {
        showError(error.message || "自评尚未确认保存，编辑内容已保留。");
      });
    }

    function isLocked(item) {
      if (renderingArchived) return true;
      return currentMode() === "per_item" && item.state !== "pending";
    }

    function renderCurrent() {
      if (!run || !run.items || !run.items.length || disposed) return;
      renderGeneration += 1;
      var item = activeItem();
      if (!item) return;
      var problem = problemFor(item);
      var draft = draftValue(item);
      var attempt = item.attempt || {};
      var locked = isLocked(item);
      var finalLocked = finalBusy || !!(local && local.pendingFinalize);
      var key = rowKey(item, position);
      var pendingAttempt = local && local.pendingAttempts[key];
      var pendingStuck = local && local.pendingStuck[key];
      var inputLocked = locked || finalLocked || modeAdopting || navigationBusy
        || !!pendingAttempt || !!pendingStuck;
      var answer = renderingArchived || (currentMode() === "per_item" && item.state === "answered")
        ? String(attempt.answer_text || "") : draft.answer;
      if (ids.answer) {
        ids.answer.value = answer;
        ids.answer.disabled = inputLocked
          || currentMode() !== "per_item" && renderingArchived;
        setVisible(ids.answer, isTextItem(item));
      }
      buildQuestion(problem);
      buildOptions(item, inputLocked);
      if (ids.itemSubmit) {
        var showItemSubmit = !renderingArchived && currentMode() === "per_item"
          && (isMultiple(item) || isTextItem(item) || !!pendingAttempt || !!pendingStuck);
        setVisible(ids.itemSubmit, showItemSubmit);
        ids.itemSubmit.disabled = !!answerBusy[key] || finalLocked || locked || modeAdopting || navigationBusy;
        ids.itemSubmit.textContent = pendingAttempt || pendingStuck ? "重试提交" : "提交答案";
      }
      if (ids.stuck) {
        setVisible(ids.stuck, !renderingArchived && !locked);
        ids.stuck.disabled = !!answerBusy[key] || finalLocked || modeAdopting || navigationBusy
          || !!pendingAttempt || !!pendingStuck;
      }
      if (ids.finalSubmit) {
        setVisible(ids.finalSubmit, !renderingArchived);
        ids.finalSubmit.disabled = finalBusy || modeAdopting || hasBusyAnswerWrites();
        ids.finalSubmit.textContent = local && local.pendingFinalize ? "重试交卷" : "提交试卷";
      }
      if (ids.pause) {
        setVisible(ids.pause, !renderingArchived);
        ids.pause.disabled = navigationBusy || finalBusy || modeAdopting || hasBusyAnswerWrites();
      }
      if (ids.toolbar) setVisible(ids.toolbar, !renderingArchived || reviewing);
      if (ids.previous) ids.previous.disabled = navigationBusy || modeAdopting || position <= 0;
      if (ids.next) ids.next.disabled = navigationBusy || modeAdopting || position >= run.items.length - 1;
      if (ids.return) setVisible(ids.return, renderingArchived && reviewing);
      if (ids.completion) setVisible(ids.completion, renderingArchived && !reviewing);
      renderReference(item);
      renderRating(item);
      renderDots();
      setVisible(ids.work, !renderingArchived || reviewing);
    }

    function updateDraft(item, value) {
      var key = rowKey(item, run.items.indexOf(item));
      if (modeAdopting || navigationBusy || finalBusy || local.pendingAttempts[key] || local.pendingStuck[key]) return;
      var next = draftValue(item);
      next.answer = String(value || "");
      if (next.answer.trim()) next.stuck = false;
      item.draft = next;
      queueDraft(item);
      renderDots();
      renderReference(item);
    }

    function updateChoices(item, choice, checked) {
      var key = rowKey(item, run.items.indexOf(item));
      if (isLocked(item) || modeAdopting || navigationBusy || finalBusy || !choice
          || local.pendingAttempts[key] || local.pendingStuck[key]) return;
      var next = draftValue(item);
      if (isMultiple(item)) {
        var choices = next.choices.filter(function (value) { return value !== choice; });
        if (checked) choices.push(choice);
        next.choices = choices;
      } else {
        next.choices = checked ? [choice] : [];
      }
      next.answer = next.choices.join(", ");
      if (next.answer.trim()) next.stuck = false;
      item.draft = next;
      if (currentMode() === "per_item" && !isMultiple(item) && checked) {
        local.drafts[key] = jsonCopy(next);
        persistLocal();
      } else {
        queueDraft(item);
      }
      renderDots();
      renderReference(item);
      if (currentMode() === "per_item" && !isMultiple(item) && checked) submitAnswer(item);
    }

    function queueDraft(item) {
      if (!local || !run || disposed || renderingArchived) return;
      var index = run.items.indexOf(item);
      var key = rowKey(item, index);
      var sequence = Math.max(Number(item.draft_sequence || 0), Number(local.sequences[key] || 0)) + 1;
      item.draft_sequence = sequence;
      var draft = draftValue(item);
      local.drafts[key] = jsonCopy(draft);
      local.sequences[key] = sequence;
      var payload = {
        execution_id: run.execution_id,
        position: itemPosition(item, index),
        practice_context: contextFor(run, item, index),
        sequence: sequence,
        draft: draft,
      };
      local.pendingDrafts[key] = payload;
      persistLocal();
      if (draftTimers[key]) clearTimeout(draftTimers[key]);
      draftTimers[key] = setTimeout(function () { flushDraft(key); }, 350);
    }

    function flushDraft(key) {
      if (!local || !local.pendingDrafts[key]) return Promise.resolve();
      if (draftTimers[key]) {
        clearTimeout(draftTimers[key]);
        delete draftTimers[key];
      }
      var pending = jsonCopy(local.pendingDrafts[key]);
      var existing = draftWrites[key] || Promise.resolve();
      var write = existing.catch(function () {}).then(function () {
        return post("/practice/draft", pending);
      }).then(function (response) {
        var latest = local.pendingDrafts[key];
        var item = run && run.items.find(function (candidate, index) {
          return rowKey(candidate, index) === key;
        });
        if (item) item.draft_sequence = Math.max(Number(item.draft_sequence || 0), pending.sequence);
        if (latest && latest.sequence === pending.sequence) delete local.pendingDrafts[key];
        persistLocal();
        clearError();
        return response;
      }).catch(function (error) {
        showError(error.message || "输入尚未确认保存；编辑已保留在此浏览器中。");
        throw error;
      });
      draftWrites[key] = write;
      write.then(function () { if (draftWrites[key] === write) delete draftWrites[key]; },
        function () { if (draftWrites[key] === write) delete draftWrites[key]; });
      return write;
    }

    function makeAnswerPayload(item, pending) {
      if (pending && pending.payload) return jsonCopy(pending.payload);
      var index = run.items.indexOf(item);
      var draft = draftValue(item);
      var choices = draft.choices.slice();
      var answer = choices.length ? choices.join(", ") : draft.answer.trim();
      var verdict = choices.length ? grade(item, choices) : null;
      var body = {
        request_id: requestId(),
        problem_id: item.item_id,
        answer_text: answer,
        practice_position: itemPosition(item, index),
        practice_context: contextFor(run, item, index),
      };
      if (choices.length && isMultiple(item)) body.choices = choices;
      if (verdict !== null) body.verdict = verdict;
      return body;
    }

    function submitAnswer(item, retry) {
      if (!run || renderingArchived || currentMode() !== "per_item" || disposed) return Promise.resolve();
      var index = run.items.indexOf(item);
      var key = rowKey(item, index);
      if (item.state !== "pending" && !(local.pendingAttempts[key] || local.pendingStuck[key])) return Promise.resolve();
      if (answerBusy[key]) return answerBusy[key];
      var pending = retry || local.pendingAttempts[key] || local.pendingStuck[key];
      var payload = makeAnswerPayload(item, pending);
      if (!payload.answer_text && !pending) {
        showError("请先作答，或选择“不会”。");
        return Promise.resolve();
      }
      local.pendingAttempts[key] = { payload: jsonCopy(payload) };
      persistLocal();
      if (draftTimers[key]) {
        clearTimeout(draftTimers[key]);
        delete draftTimers[key];
      }
      var priorDraftWrite = draftWrites[key] || Promise.resolve();
      /* 连对：判定先落地，界面随后再动（数字滚动 / 火苗 / 横幅 / 断裂负反馈）。
         判定语义不动 —— 读的就是这次提交载荷里的那个 verdict。 */
      var streakLanded = null;
      answerBusy[key] = priorDraftWrite.catch(function () {}).then(function () {
        if (local.pendingDrafts[key]) return flushDraft(key).catch(function () {});
      }).then(function () {
        return post("/attempts", payload);
      }).then(function (response) {
        if (disposed) return;
        var updated = extractPractice(response && response.practice);
        delete local.pendingAttempts[key];
        delete local.pendingStuck[key];
        delete local.pendingDrafts[key];
        if (updated) adoptRun(updated, false);
        persistLocal();
        clearError();
        streakLanded = streak ? streak.judge(payload.verdict) : null;
      }).catch(function (error) {
        if (error && error.status && error.status < 500) {
          delete local.pendingAttempts[key];
          delete local.pendingStuck[key];
          if (payload.stuck && local.drafts[key]) {
            local.drafts[key].stuck = false;
            local.drafts[key].reference_viewed = false;
          }
          persistLocal();
        }
        showError(error.message || "提交未确认；答案和请求编号已保留，可重试。");
      }).then(function (value) {
        delete answerBusy[key];
        renderDots();
        if (isVisibleItem(item, index)) {
          renderCurrent();
          /* 答对的挤压回弹：判定成立的这一刻，回弹挂到**被选中的那一项**
             （正确选项行，底边为锚）——与音效同一帧落地（判定为错时那边也不响）。
             判定为错 / 不会 / 参考区里没有「判定：正确」时不动
             （负反馈是摆动，不是回弹）。 */
          squashCorrectOption(ids.work);
        }
        /* 界面已按新的连对数重画，这里再补动效（数字滚动 / 火苗 / 横幅 / 负反馈） */
        if (streak) streak.apply(streakLanded);
        return value;
      });
      if (isVisibleItem(item, index)) renderCurrent();
      return answerBusy[key];
    }

    function markStuck(item) {
      if (!run || renderingArchived || isLocked(item) || finalBusy || modeAdopting || navigationBusy || disposed) return Promise.resolve();
      var index = run.items.indexOf(item);
      var key = rowKey(item, index);
      if (answerBusy[key]) return answerBusy[key];
      if (local.pendingAttempts[key]) return Promise.resolve();
      var draft = draftValue(item);
      draft.stuck = true;
      draft.reference_viewed = true;
      item.draft = draft;
      local.drafts[key] = jsonCopy(draft);
      if (currentMode() === "per_item") {
        var pending = local.pendingStuck[key];
        var body = pending ? jsonCopy(pending.payload) : {
          request_id: requestId(),
          problem_id: item.item_id,
          answer_text: "",
          practice_position: itemPosition(item, index),
          practice_context: contextFor(run, item, index),
          stuck: true,
        };
        local.pendingStuck[key] = { payload: body };
        persistLocal();
        renderCurrent();
        var priorDraftWrite = draftWrites[key] || Promise.resolve();
        answerBusy[key] = priorDraftWrite.catch(function () {}).then(function () {
          if (local.pendingDrafts[key]) return flushDraft(key).catch(function () {});
        }).then(function () {
          return post("/attempts", body);
        }).then(function (response) {
          var updated = extractPractice(response && response.practice);
          delete local.pendingStuck[key];
          delete local.pendingDrafts[key];
          if (updated) adoptRun(updated, false);
          persistLocal();
          clearError();
        }).catch(function (error) {
          showError(error.message || "不会状态尚未确认保存；可再次提交。");
        }).then(function (value) {
          delete answerBusy[key];
          renderDots();
          if (isVisibleItem(item, index)) renderCurrent();
          return value;
        });
        if (isVisibleItem(item, index)) renderCurrent();
        return answerBusy[key];
      }
      queueDraft(item);
      var bodyStuck = local.pendingStuck[key] && local.pendingStuck[key].payload;
      if (!bodyStuck) {
        bodyStuck = {
          execution_id: run.execution_id,
          position: itemPosition(item, index),
          request_id: requestId(),
          practice_context: contextFor(run, item, index),
        };
        local.pendingStuck[key] = { payload: bodyStuck };
      }
      persistLocal();
      renderCurrent();
      answerBusy[key] = post("/practice/current/stuck", bodyStuck).then(function (response) {
        var updated = extractPractice(response);
        delete local.pendingStuck[key];
        if (updated) adoptRun(updated, false);
        persistLocal();
        clearError();
      }).catch(function (error) {
        showError(error.message || "不会状态尚未确认保存；编辑已在此浏览器保留。");
      }).then(function (value) {
        delete answerBusy[key];
        renderDots();
        if (isVisibleItem(item, index)) renderCurrent();
        return value;
      });
      if (isVisibleItem(item, index)) renderCurrent();
      return answerBusy[key];
    }

    function moveTo(target) {
      if (!run || target < 0 || target >= run.items.length || target === position || navigationBusy || disposed) {
        return Promise.resolve();
      }
      if (renderingArchived) {
        position = target;
        renderCurrent();
        return Promise.resolve();
      }
      var previousPosition = position;
      var previousItem = rowAt(previousPosition);
      var targetItem = rowAt(target);
      navigationBusy = true;
      position = target;
      local.position = target;
      var navigation = {
        execution_id: run.execution_id,
        position: itemPosition(targetItem, target),
        practice_context: contextFor(run, targetItem, target),
      };
      local.pendingPosition = navigation;
      persistLocal();
      renderCurrent();
      return flushDraft(rowKey(previousItem, previousPosition)).catch(function () {}).then(function () {
        return post("/practice/current/navigate", navigation);
      }).then(function (response) {
        local.pendingPosition = null;
        persistLocal();
        var updated = extractPractice(response);
        if (updated) adoptRun(updated, false);
        clearError();
      }).catch(function (error) {
        showError(error.message || "题目位置尚未确认保存；当前浏览位置已保留。");
      }).then(function () {
        navigationBusy = false;
        renderCurrent();
      });
    }

    function collectFinalDrafts() {
      return run.items.map(function (item, index) {
        if (item.state !== "pending") return null;
        var key = rowKey(item, index);
        var existing = local.pendingDrafts[key];
        var sequence = Number(item.draft_sequence || 0);
        if (!existing) sequence = Math.max(sequence, Number(local.sequences[key] || 0)) + 1;
        var draft = draftValue(item);
        local.drafts[key] = jsonCopy(draft);
        local.sequences[key] = sequence;
        item.draft_sequence = sequence;
        return {
          position: itemPosition(item, index),
          draft: draft,
          sequence: sequence,
          practice_context: contextFor(run, item, index),
        };
      }).filter(function (draft) { return !!draft; });
    }

    function submitPaper(retry) {
      if (!run || renderingArchived || disposed || navigationBusy || modeAdopting || hasBusyAnswerWrites()) {
        return Promise.resolve();
      }
      if (finalBusy) return Promise.resolve();
      var pending = retry || (local && local.pendingFinalize);
      var body = pending ? jsonCopy(pending) : {
        execution_id: run.execution_id,
        request_id: requestId(),
        drafts: collectFinalDrafts(),
      };
      local.pendingFinalize = jsonCopy(body);
      persistLocal();
      finalBusy = true;
      clearError();
      renderCurrent();
      return post("/practice/current/submit", body).then(function (response) {
        local.pendingFinalize = null;
        local.completedRunId = response.run_id;
        persistLocal();
        return api("/practice/runs/" + encodeURIComponent(response.run_id)).then(function (record) {
          prepareRun(record, true);
          persistLocal();
        }).catch(function () {
          renderingArchived = true;
          reviewing = false;
          archived = null;
          setVisible(ids.setup, false);
          setVisible(ids.work, false);
          setVisible(ids.toolbar, false);
          setVisible(ids.completion, true);
          if (ids.completionStats) ids.completionStats.textContent = "已交卷。答卷统计暂不可用，请稍后刷新查看。";
          showError("交卷已确认，但完成页暂时无法读取答卷。");
        });
      }).catch(function (error) {
        if (error && error.status && error.status < 500) {
          local.pendingFinalize = null;
          persistLocal();
        }
        showError(error.message || "交卷尚未确认；草稿和请求编号已保留，请重试。");
      }).then(function (value) {
        finalBusy = false;
        renderCurrent();
        return value;
      });
    }

    function retryPendingWrites() {
      if (!local || renderingArchived || disposed) return;
      if (local.pendingFinalize) {
        submitPaper(local.pendingFinalize);
        return;
      }
      Object.keys(local.pendingDrafts).forEach(function (key) { flushDraft(key).catch(function () {}); });
      if (local.pendingPosition) {
        var pendingPosition = jsonCopy(local.pendingPosition);
        post("/practice/current/navigate", pendingPosition).then(function (response) {
          if (local.pendingPosition && local.pendingPosition.position === pendingPosition.position) {
            local.pendingPosition = null;
          }
          var updated = extractPractice(response);
          if (updated) adoptRun(updated, false);
          persistLocal();
        }).catch(function (error) { showError(error.message || "浏览位置尚未确认保存。"); });
      }
      Object.keys(local.pendingAttempts).forEach(function (key) {
        var saved = local.pendingAttempts[key];
        var item = run.items.find(function (candidate, index) { return rowKey(candidate, index) === key; });
        if (item) submitAnswer(item, saved);
      });
      Object.keys(local.pendingStuck).forEach(function (key) {
        var item = run.items.find(function (candidate, index) { return rowKey(candidate, index) === key; });
        var saved = local.pendingStuck[key];
        if (item && currentMode() === "per_item") submitAnswer(item, saved);
        else if (item && saved) {
          post("/practice/current/stuck", saved.payload).then(function (response) {
            delete local.pendingStuck[key];
            var updated = extractPractice(response);
            if (updated) adoptRun(updated, false);
            persistLocal();
          }).catch(function (error) { showError(error.message || "不会状态尚未确认保存。"); });
        }
      });
      Object.keys(local.pendingRatings).forEach(function (key) {
        var item = run.items.find(function (candidate, index) { return rowKey(candidate, index) === key; });
        var saved = local.pendingRatings[key];
        if (item && saved && saved.payload) {
          post("/feedback", saved.payload).then(function (response) {
            item.feedback = confirmedFeedback(item, saved.payload, response);
            delete local.pendingRatings[key];
            delete local.ratingDrafts[key];
            persistLocal();
            if (renderingArchived) renderCompletion();
          }).catch(function (error) { showError(error.message || "自评尚未确认保存。"); });
        }
      });
    }

    function completionStats(record) {
      var items = record.items || [];
      var correct = 0;
      var wrong = 0;
      var stuck = 0;
      var pendingRatings = 0;
      items.forEach(function (item) {
        var attempt = item.attempt || {};
        if (attempt.verdict === true || attempt.verdict === 1) correct += 1;
        else if (attempt.verdict === false || attempt.verdict === 0) wrong += 1;
        if (item.state === "stuck") stuck += 1;
        if (record.rating_mode !== "off" && (item.state === "answered" || item.state === "stuck")
            && item.attempt_id && !item.feedback) {
          pendingRatings += 1;
        }
      });
      return { total: items.length, correct: correct, wrong: wrong, stuck: stuck, pendingRatings: pendingRatings };
    }

    /* The two milestone conditions (decisions.md A-29, tasks.md 17.6) are read
       by the shared celebration in workbench.js: it looks for
       `data-lk-total` / `data-lk-correct` / `data-lk-chapter-first` on the
       completion surface.  ① 本轮全对 ⇒ every item carries an objective
       verdict and all of them are correct.  ② 章节首次完成 ⇒ the client holds
       no such fact (practice_runs carries no chapter column and no
       "first completion" flag), so it stays false: the contract forbids
       approximating it with a proxy signal (same rule as CD-164). */
    function writeCompletionFacts(record) {
      if (!ids.completion || !ids.completion.dataset) return;
      var stats = completionStats(record);
      ids.completion.dataset.lkTotal = String(stats.total);
      ids.completion.dataset.lkCorrect = String(stats.correct);
      ids.completion.dataset.lkChapterFirst = "false";
    }

    /* The decoration layer the milestone burst hangs in.  The completion card
       is not positioned, so the anchor gives the burst its own coordinate
       system; it never takes clicks (the CTA stays clickable). */
    function ensureCelebrationAnchor() {
      var completion = ids.completion;
      if (!completion) return null;
      if (!celebrationAnchorEl) {
        var existing = completion.querySelectorAll
          ? completion.querySelectorAll("[data-lk-celebrate-anchor]")
          : [];
        celebrationAnchorEl = existing.length ? existing[0] : null;
      }
      if (!celebrationAnchorEl) {
        var anchor = document.createElement("div");
        anchor.setAttribute("data-lk-celebrate-anchor", "");
        anchor.className = "lk-celebrate-anchor";
        completion.appendChild(anchor);
        celebrationAnchorEl = anchor;
      }
      /* Layout, not an animation start state: the burst is absolutely
         positioned, so the anchor needs a box of its own. */
      if (completion.style) completion.style.position = "relative";
      if (celebrationAnchorEl.style) {
        celebrationAnchorEl.style.position = "absolute";
        celebrationAnchorEl.style.inset = "0";
        celebrationAnchorEl.style.pointerEvents = "none";
      }
      return celebrationAnchorEl;
    }

    /* The completion figures (tasks.md 16.7 ①): the counts this round really
       has — no invented statistics, no percentages, no new measure.  Every
       number carries `data-lk-value`, so the shared ticker rolls it; the
       label sits beside the number, never inside it, because the ticker
       rewrites the number element's text. */
    function completionFiguresHtml(stats) {
      return [
        { value: stats.total, label: "总题数" },
        { value: stats.correct, label: "判定正确" },
        { value: stats.wrong, label: "错误" },
        { value: stats.stuck, label: "不会" },
        { value: stats.pendingRatings, label: "待自评" },
      ].map(function (figure) {
        return "<p class='lk-stat'><span class='lk-stat__value' data-lk-value='"
          + figure.value + "'>" + figure.value + "</span>"
          + "<span class='lk-stat__label'>" + figure.label + "</span></p>";
      }).join("");
    }

    function renderCompletion() {
      if (!ids.completion || !archived) return;
      var stats = completionStats(archived);
      writeCompletionFacts(archived);
      ensureCelebrationAnchor();
      if (ids.title) ids.title.textContent = archived.source_label || savedPaper && savedPaper.title || "练习试卷";
      if (ids.count) ids.count.textContent = String(stats.total);
      if (ids.completionStats) {
        ids.completionStats.textContent = "共 " + stats.total + " 题；判定正确 " + stats.correct
          + " 题，错误 " + stats.wrong + " 题；不会 " + stats.stuck
          + " 题；待自评 " + stats.pendingRatings + " 题。";
      }
      if (ids.completionFigures) {
        ids.completionFigures.innerHTML = completionFiguresHtml(stats);
      }
      if (ids.links) {
        ids.links.replaceChildren();
        archived.items.forEach(function (item, index) {
          var link = document.createElement("button");
          link.type = "button";
          link.className = "outline sm";
          link.textContent = "第" + itemPosition(item, index) + "题：" + statusLabel(itemStatus(item, index));
          link.setAttribute("aria-label", "查看第" + itemPosition(item, index) + "题，" + statusLabel(itemStatus(item, index)));
          link.addEventListener("click", function () { openReview(index); });
          ids.links.appendChild(link);
        });
      }
      setVisible(ids.completion, !reviewing);
    }

    function openReview(index) {
      if (!archived) {
        if (!local || !local.completedRunId) return;
        api("/practice/runs/" + encodeURIComponent(local.completedRunId)).then(function (record) {
          prepareRun(record, true);
          openReview(index);
        }).catch(function (error) { showError(error.message || "无法读取本次答卷。"); });
        return;
      }
      reviewing = true;
      position = Math.max(0, Math.min(index || 0, archived.items.length - 1));
      renderCurrent();
    }

    function returnToCompletion() {
      reviewing = false;
      renderCurrent();
      renderCompletion();
    }

    function pauseRun() {
      if (!run || renderingArchived || navigationBusy || finalBusy || modeAdopting || disposed
          || hasBusyAnswerWrites()) return Promise.resolve();
      var item = activeItem();
      var pendingDrafts = Object.keys(local.pendingDrafts).map(function (key) {
        return flushDraft(key);
      });
      return Promise.all(pendingDrafts).then(function () {
        if (!isSavedPaperRun(run)) return null;
        var body = { execution_id: run.execution_id, practice_context: contextFor(run, item, position) };
        return api("/practice/current", {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      }).then(function () {
        local = null;
        navigate("/w/" + encodeURIComponent(workspaceName()) + "/practice-sets");
      }).catch(function (error) {
        showError(error.message || "暂停状态尚未确认保存。");
      });
    }

    function saveRatingFromCurrent() {
      var item = activeItem();
      if (item && ratingInput && ratingNote) return saveRating(item, ratingInput, ratingNote);
      return Promise.resolve();
    }

    if (ids.start) ids.start.addEventListener("click", savedStart);
    if (ids.previous) ids.previous.addEventListener("click", function () { moveTo(position - 1); });
    if (ids.next) ids.next.addEventListener("click", function () { moveTo(position + 1); });
    if (ids.stuck) ids.stuck.addEventListener("click", function () { var item = activeItem(); if (item) markStuck(item); });
    if (ids.itemSubmit) ids.itemSubmit.addEventListener("click", function () { var item = activeItem(); if (item) submitAnswer(item); });
    if (ids.finalSubmit) ids.finalSubmit.addEventListener("click", function () { submitPaper(); });
    if (ids.pause) ids.pause.addEventListener("click", pauseRun);
    if (ids.answer) ids.answer.addEventListener("input", function () {
      var item = activeItem();
      if (item && !isLocked(item) && !finalBusy && !renderingArchived) updateDraft(item, ids.answer.value);
    });
    if (ids.options) ids.options.addEventListener("change", function (event) {
      var target = event.target;
      if (!target || !target.dataset) return;
      var choice = target.dataset.paperChoice || target.dataset.choice || target.value;
      var item = activeItem();
      if (item) updateChoices(item, choice, !!target.checked);
    });
    if (ids.review) ids.review.addEventListener("click", function () { openReview(0); });
    if (ids.return) ids.return.addEventListener("click", returnToCompletion);
    function again() {
      if (archived && isPaperRun(archived) && !isSavedPaperRun(archived)) {
        var replay = archived;
        archivedRecord = replay;
        savedPaper = {
          title: replay.source_label || "练习试卷",
          count: (replay.items || []).length,
          plan: { items: (replay.items || []).map(function (item) { return { problem_id: item.item_id }; }) },
        };
        var base = "/w/" + encodeURIComponent(workspaceName()) + "/practice";
        if (window.history && typeof window.history.replaceState === "function") {
          window.history.replaceState(null, "", base);
          address = new URL(window.location.href);
          requestedPaperId = "";
          requestedRunId = "";
        }
        run = null;
        archived = null;
        local = null;
        localKey = "";
        renderingArchived = false;
        reviewing = false;
        setVisible(ids.completion, false);
        setVisible(ids.work, false);
        setVisible(ids.toolbar, false);
        clearError();
        showSetup(savedPaper);
        return;
      }
      var paperId = (archived && archived.source_ref) || requestedPaperId;
      if (!paperId) {
        navigate("/w/" + encodeURIComponent(workspaceName()) + "/practice-sets");
        return;
      }
      var target = "/w/" + encodeURIComponent(workspaceName()) + "/practice?paper=" + encodeURIComponent(paperId);
      if (window.history && typeof window.history.replaceState === "function") {
        window.history.replaceState(null, "", target);
        address = new URL(window.location.href);
        requestedPaperId = paperId;
        requestedRunId = "";
      }
      run = null;
      archived = null;
      local = null;
      localKey = "";
      renderingArchived = false;
      reviewing = false;
      setVisible(ids.completion, false);
      setVisible(ids.work, false);
      setVisible(ids.toolbar, false);
      if (ids.start) ids.start.disabled = true;
      clearError();
      api("/practice-sets/" + encodeURIComponent(paperId)).then(function (record) {
        if (!disposed) showSetup(record);
      }).catch(function (error) {
        if (!disposed) showError(error.message || "无法重新读取试卷。");
      });
    }

    if (ids.again) ids.again.addEventListener("click", again);

    function facadeCurrentProblem() {
      if (legacy) return legacy.currentProblem ? legacy.currentProblem() : null;
      var item = activeItem();
      if (!item) return null;
      return Object.assign({ id: item.item_id, kind: "problem", payload: item.payload }, item);
    }

    function facadeSession() {
      if (legacy) return legacy.session ? legacy.session() : [];
      return run && run.items ? run.items : [];
    }

    function facadeImages() {
      if (legacy) return legacy.visiblePracticeImages ? legacy.visiblePracticeImages() : [];
      if (!ids.question || !ids.question.querySelectorAll) return [];
      return Array.prototype.slice.call(ids.question.querySelectorAll("img")).map(function (image) {
        return (image.getAttribute && image.getAttribute("src")) || image.src || "";
      }).filter(function (src) { return !!src; });
    }

    function facadeAnswer() {
      if (legacy) return legacy.draftAnswer ? legacy.draftAnswer() : "";
      var item = activeItem();
      if (!item) return "";
      if (renderingArchived) return String((item.attempt && item.attempt.answer_text) || "");
      if (ids.answer && !ids.answer.hidden) return ids.answer.value;
      return draftValue(item).answer || draftValue(item).choices.join(", ");
    }

    function facadeNote() {
      if (legacy) return legacy.draftNote ? legacy.draftNote() : "";
      return ratingNote ? ratingNote.value : "";
    }

    function facadeSelectionContext() {
      if (legacy) return legacy.selectionContext ? legacy.selectionContext() : {};
      var item = activeItem();
      if (!run || !item) return {};
      return {
        kp_ids: Array.isArray(run.kp_ids) ? run.kp_ids.slice() : [],
        practice_mode: run.practice_mode || "exam",
        count: run.items.length,
        filters: { source_kinds: [], exam_years: [], docs: [] },
        practice_context: contextFor(run, item, position),
        draft_answer: facadeAnswer(),
        draft_choices: draftValue(item).choices.slice(),
        answer_state: renderingArchived ? "completed" : item.state,
      };
    }

    function dispose() {
      if (disposed) return;
      Object.keys(draftTimers).forEach(function (key) { clearTimeout(draftTimers[key]); });
      var item = activeItem();
      if (item && !renderingArchived && local) {
        var key = rowKey(item, position);
        if (ids.answer && !ids.answer.hidden && !isLocked(item)) updateDraft(item, ids.answer.value);
        if (local.pendingDrafts[key]) flushDraft(key).catch(function () {});
      }
      disposed = true;
      if (legacy && legacy.dispose) legacy.dispose();
    }

    var facade = {
      currentProblem: facadeCurrentProblem,
      session: facadeSession,
      visiblePracticeImages: facadeImages,
      draftAnswer: facadeAnswer,
      draftNote: facadeNote,
      selectionContext: facadeSelectionContext,
      dispose: dispose,
    };

    if (requestedRunId) initializeArchived(requestedRunId);
    else if (requestedPaperId) initializePaper(requestedPaperId);
    else initializeCurrent();
    return facade;
  }

  return { start: start };
}));
