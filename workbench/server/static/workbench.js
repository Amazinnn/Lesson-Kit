/* workbench — DSH-styled client logic (vanilla JS, no build) */

(function () {
  "use strict";

  var layout = document.getElementById("layout");
  if (!layout) return;
  var WS = layout.dataset.workspace;

  var SESSION_KEY = "wb_session_" + WS;
  var KPS_KEY = "wb_kps_" + WS;
  var CURRENT_KEY = "wb_current_" + WS;
  var AI_KEY = "wb_ai_" + WS;

  /* ---------- helpers ---------- */

  function api(path, options) {
    return fetch("/api/w/" + WS + path, options).then(function (resp) {
      if (!resp.ok) throw new Error(resp.status);
      return resp.json();
    });
  }

  function post(path, body) {
    return api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  }

  function store(key, value) {
    sessionStorage.setItem(key, JSON.stringify(value));
  }

  function load(key, fallback) {
    var raw = sessionStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  }

  function renderMath(root) {
    var spans = (root || document).querySelectorAll(".math");
    if (!spans.length || !window.katex) return;
    spans.forEach(function (span) {
      try {
        katex.render(span.textContent, span, { throwOnError: false });
      } catch (e) { /* keep raw text */ }
    });
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function richText(text) {
    return escapeHtml(text)
      .replace(/\$\$([\s\S]+?)\$\$/g, function (_, m) {
        return "<span class='math'>" + m + "</span>";
      })
      .replace(/\$([^$\n]+)\$/g, function (_, m) {
        return "<span class='math'>" + m + "</span>";
      })
      .replace(/\n/g, "<br>");
  }

  /* ---------- workspace switch ---------- */

  var selector = document.getElementById("workspace-select");
  if (selector) {
    selector.addEventListener("change", function () {
      window.location = "/w/" + selector.value + "/practice";
    });
  }

  /* ---------- practice message stream ---------- */

  var stream = document.getElementById("stream");
  var composer = document.getElementById("composer");
  var answerBox = document.getElementById("answer-box");
  var submitAnswer = document.getElementById("answer-submit");
  var showAnswer = document.getElementById("show-answer");
  var noTime = document.getElementById("no-time");
  var startPractice = document.getElementById("start-practice");
  var gotoSessionEnd = document.getElementById("goto-session-end");

  var currentProblem = null;
  var stuckStep = "";

  function session() {
    return load(SESSION_KEY, []);
  }

  function currentKps() {
    return load(KPS_KEY, []);
  }

  function setCurrent(problem) {
    currentProblem = problem || null;
    store(CURRENT_KEY, currentProblem);
    updateAiContext();
  }

  function updateAiContext() {
    var el = document.getElementById("ai-context");
    if (!el) return;
    if (!currentProblem) {
      el.textContent = "上下文：无";
      return;
    }
    var list = session();
    var recent = list.slice(-3, -1).map(function (p) { return p.problem_id; });
    var suffix = recent.length
      ? "  · 最近：" + recent.join(", ")
      : "";
    el.textContent = "当前题：" + currentProblem.problem_id + suffix;
  }

  function addMessage(html, cls) {
    var div = document.createElement("div");
    div.className = "msg " + (cls || "teacher");
    div.innerHTML = html;
    stream.appendChild(div);
    stream.scrollTop = stream.scrollHeight;
    renderMath(div);
  }

  function showComposer(show) {
    composer.classList.toggle("hidden", !show);
  }

  function startSession() {
    api("/weak?limit=5").then(function (items) {
      var kps = items.map(function (i) { return i.kp_id; });
      store(KPS_KEY, kps);
      loadNext(kps);
    });
  }

  function loadNext(kps) {
    var exclude = session().map(function (p) { return p.problem_id; });
    api("/pull", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kp_ids: kps, n: 5, mode: "weak" }),
    }).then(function (result) {
      if (!result.problems.length) {
        addMessage("<p>本组题目已练完。</p>");
        showComposer(false);
        gotoSessionEnd.classList.remove("hidden");
        return;
      }
      var problem = result.problems[0];
      var seen = session();
      seen.push({ problem_id: problem.problem_id, answer_text: "" });
      store(SESSION_KEY, seen);
      setCurrent({ problem_id: problem.problem_id, answer_text: "" });
      addMessage(
        "<div class='meta'>题目 · " + escapeHtml(problem.problem_id) + "</div>"
        + "<div class='problem-text'>" + richText(problem.problem_text) + "</div>"
      );
      stuckStep = "";
      answerBox.value = "";
      showComposer(true);
      var actions = document.getElementById("composer-actions");
      actions.classList.add("hidden");
      submitAnswer.classList.remove("hidden");
      answerBox.focus();
    });
  }

  submitAnswer.addEventListener("click", function () {
    var text = answerBox.value.trim();
    addMessage("<div class='meta'>我的作答</div><p>" + richText(text || "（未作答）") + "</p>", "user");
    var cur = load(CURRENT_KEY, {});
    cur.answer_text = text;
    setCurrent(cur);
    var list = session();
    for (var i = list.length - 1; i >= 0; i--) {
      if (list[i].problem_id === cur.problem_id) {
        list[i].answer_text = text;
        break;
      }
    }
    store(SESSION_KEY, list);
    submitAnswer.classList.add("hidden");
    var actions = document.getElementById("composer-actions");
    actions.classList.remove("hidden");
    showAnswer.classList.remove("hidden");
    noTime.classList.remove("hidden");
    answerBox.disabled = true;
  });

  showAnswer.addEventListener("click", function () {
    api("/problem/" + currentProblem.problem_id).then(function (detail) {
      var solution = detail.problem.solution || "";
      var blocks = solution.split(/\n\s*\n/).map(function (b) { return b.trim(); })
        .filter(Boolean);
      var html = "<div class='meta'>解答</div>";
      if (!blocks.length) {
        html += "<p>（本题无解答文本）</p>";
      } else {
        html += blocks.map(function (block, i) {
          return "<div class='solution-block' data-idx='" + (i + 1) + "'>"
            + "<b>第 " + (i + 1) + " 步</b> " + richText(block) + "</div>";
        }).join("");
      }
      html += feedbackHtml();
      addMessage(html, "teacher");
      bindFeedback();
    });
  });

  noTime.addEventListener("click", function () {
    finishProblem("skip", "");
  });

  function feedbackHtml() {
    return "<div class='feedback'>"
      + "<p class='meta'>反馈（可选）</p>"
      + "<div class='rating'>"
      + [1, 2, 3, 4, 5].map(function (r) {
        return "<button class='rate sm' data-r='" + r + "'>" + r + "</button>";
      }).join(" ")
      + "</div>"
      + "<textarea id='feedback-note' rows='2' placeholder='自然语言反馈（薄弱点）'></textarea>"
      + "<div style='margin-top:6px'>"
      + "<button id='mark-stuck' class='outline sm'>标记卡点（先点上面某一步）</button>"
      + "</div></div>";
  }

  function bindFeedback() {
    var feedback = stream.querySelector(".feedback:last-of-type");
    if (!feedback) return;
    feedback.querySelectorAll(".solution-block").forEach(function (block) {
      block.addEventListener("click", function () {
        feedback.querySelectorAll(".solution-block").forEach(function (b) {
          b.classList.remove("stuck");
        });
        block.classList.add("stuck");
        stuckStep = block.dataset.idx;
      });
    });
    feedback.querySelectorAll(".rate").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var rating = parseInt(btn.dataset.r, 10);
        var note = feedback.querySelector("#feedback-note").value.trim();
        post("/feedback", {
          item_type: "problem", item_id: currentProblem.problem_id,
          rating: rating, note: note,
        }).then(function () {
          finishProblem("skip", note);
        });
      });
    });
    var mark = feedback.querySelector("#mark-stuck");
    if (mark) {
      mark.addEventListener("click", function () {
        var note = feedback.querySelector("#feedback-note").value.trim();
        var stuckNote = (stuckStep ? "卡在第" + stuckStep + "步" : "卡住") + " " + note;
        finishProblem("stuck", stuckNote);
      });
    }
  }

  function finishProblem(result, note) {
    var body = {
      problem_id: currentProblem.problem_id,
      result: result,
      note: note,
    };
    if (currentProblem.answer_text) body.answer_text = currentProblem.answer_text;
    post("/practice", body).catch(function () { /* record-only */ }).then(function () {
      addMessage("<div class='meta'>已记录：" + result + "</div>", "user");
      setCurrent(null);
      var kps = currentKps();
      loadNext(kps);
    });
  }

  if (startPractice) {
    startPractice.addEventListener("click", startSession);
  }

  /* ---------- session-end ---------- */

  var pending = document.getElementById("pending-ratings");
  if (pending) {
    var list = session();
    if (!list.length) {
      pending.innerHTML = "<p>本会话暂无记录。</p>";
    } else {
      var html = "";
      list.forEach(function (item) {
        html += "<div class='card' data-pid='" + item.problem_id + "'>"
          + "<h3>" + escapeHtml(item.problem_id) + "</h3>"
          + "<div class='rating'>"
          + [1, 2, 3, 4, 5].map(function (r) {
            return "<button class='rate sm' data-r='" + r + "'>" + r + "</button>";
          }).join(" ")
          + "</div>"
          + "<textarea class='end-note' rows='2' placeholder='可选反馈'></textarea>"
          + "</div>";
      });
      pending.innerHTML = html;
      pending.querySelectorAll(".rate").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var card = btn.closest(".card");
          var pid = card.dataset.pid;
          var rating = parseInt(btn.dataset.r, 10);
          var note = card.querySelector(".end-note").value.trim();
          post("/feedback", {
            item_type: "problem", item_id: pid, rating: rating, note: note,
          }).then(function () {
            card.remove();
            if (!pending.querySelector(".card")) {
              pending.innerHTML = "<p>全部评完 ✓</p>";
            }
          });
        });
      });
    }
    var skipAll = document.getElementById("skip-all");
    if (skipAll) {
      skipAll.addEventListener("click", function () {
        sessionStorage.removeItem(SESSION_KEY);
        pending.innerHTML = "<p>已跳过，记录保留在池中。</p>";
      });
    }
    var similar = document.getElementById("practice-similar");
    if (similar) {
      similar.addEventListener("click", function () {
        window.location = "practice";
      });
    }
  }

  /* ---------- AI column ---------- */

  var messages = document.getElementById("ai-messages");
  var aiInput = document.getElementById("ai-input");

  function aiAdd(html, cls) {
    var div = document.createElement("div");
    div.className = "msg " + (cls || "ai");
    div.innerHTML = html;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    renderMath(div);
  }

  function aiTask(operation) {
    var current = load(CURRENT_KEY, null);
    if (!current) {
      aiAdd("<p>先打开一道题再发起讲解/诊断。</p>", "user");
      return;
    }
    var note = aiInput ? aiInput.value.trim() : "";
    var body = { problem_id: current.problem_id, note: note };
    if (current.answer_text) {
      body.user_answer = current.answer_text;
    }
    if (stuckStep) {
      body.stuck_step = stuckStep;
    }
    aiAdd("<p>已发起：" + operation + " " + current.problem_id + "</p>", "user");
    if (aiInput) aiInput.value = "";
    post("/ai/" + operation, body).then(function (data) {
      pollJob(data.job_id, operation, current.problem_id);
    }).catch(function () {
      aiAdd("<p>桥接不可用：请先配置 provider（wb bridge add）。记录不受影响。</p>");
    });
  }

  function pollJob(jobId, operation, problemId) {
    var tries = 0;
    var timer = setInterval(function () {
      tries += 1;
      api("/ai/jobs/" + jobId).then(function (status) {
        if (status.state === "done") {
          clearInterval(timer);
          api("/explain/" + problemId).then(function (data) {
            aiAdd(renderResult(data.markdown, operation), "ai");
          });
        } else if (status.state === "failed") {
          clearInterval(timer);
          aiAdd("<p>任务失败：" + escapeHtml(status.error || "未知原因") + "</p>");
        } else if (tries > 60) {
          clearInterval(timer);
          aiAdd("<p>任务超时未完成。</p>");
        }
      }).catch(function () {
        clearInterval(timer);
        aiAdd("<p>状态查询失败。</p>");
      });
    }, 2000);
  }

  function renderResult(markdown, operation) {
    var html = "<p><b>" + operation + " 结果</b></p>";
    markdown.split(/\n## /).forEach(function (section) {
      var lines = section.trim().split("\n");
      var title = lines.shift().replace(/^#+\s*/, "");
      html += "<div class='section'><h4>" + escapeHtml(title) + "</h4><p>"
        + richText(lines.join("\n")) + "</p></div>";
    });
    return html;
  }

  var explain = document.getElementById("ai-explain");
  var diagnose = document.getElementById("ai-diagnose");
  var fresh = document.getElementById("ai-new");
  var send = document.getElementById("ai-send");
  if (explain) explain.addEventListener("click", function () { aiTask("explain"); });
  if (diagnose) diagnose.addEventListener("click", function () { aiTask("diagnose"); });
  if (send) send.addEventListener("click", function () { aiTask("explain"); });
  if (fresh) fresh.addEventListener("click", function () {
    messages.innerHTML = "";
    store(AI_KEY, []);
    aiAdd("<p>新会话已开始（记录仍在池中）。</p>");
  });

  updateAiContext();
})();
