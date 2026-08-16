/* workbench — minimal client logic (vanilla JS, no build) */

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

  function problemTextToHtml(text) {
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

  /* ---------- practice flow ---------- */

  var problemCard = document.getElementById("problem-card");
  var startButton = document.getElementById("start-practice");

  function session() {
    return load(SESSION_KEY, []);
  }

  function currentKps() {
    var stored = load(KPS_KEY, null);
    if (stored) return stored;
    return [];
  }

  function setCurrent(problem) {
    store(CURRENT_KEY, problem || null);
    updateAiContext();
  }

  function updateAiContext() {
    var el = document.getElementById("ai-context");
    if (!el) return;
    var current = load(CURRENT_KEY, null);
    el.textContent = current ? "当前题：" + current.problem_id : "上下文：无";
  }

  if (startButton) {
    startButton.addEventListener("click", function () {
      api("/weak?limit=5").then(function (items) {
        var kps = items.map(function (i) { return i.kp_id; });
        if (!kps.length) kps = [];
        store(KPS_KEY, kps);
        loadNext(kps);
      });
    });
  }

  function loadNext(kps, mode) {
    var exclude = session().map(function (p) { return p.problem_id; });
    api("/pull", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kp_ids: kps, n: 5, mode: mode || "weak" }),
    }).then(function (result) {
      if (!result.problems.length) {
        problemCard.innerHTML =
          "<p>本组题目已练完。</p>" +
          "<a href='session-end'>去会话末统一自评</a>";
        problemCard.classList.remove("hidden");
        return;
      }
      renderProblem(result.problems[0]);
    });
  }

  function renderProblem(problem) {
    problemCard.classList.remove("hidden");
    var seen = session();
    seen.push({ problem_id: problem.problem_id, answer_text: "" });
    store(SESSION_KEY, seen);
    setCurrent({ problem_id: problem.problem_id, answer_text: "" });

    var options = "";
    if (problem.options_json) {
      try {
        var opts = JSON.parse(problem.options_json);
        options = opts.map(function (o, i) {
          return "<button class='option' data-idx='" + i + "'>"
            + escapeHtml(o) + "</button>";
        }).join(" ");
      } catch (e) { /* no options */ }
    }

    problemCard.innerHTML =
      "<h2>" + escapeHtml(problem.problem_id) + "</h2>"
      + "<div class='problem-text'>" + problemTextToHtml(problem.problem_text) + "</div>"
      + (options ? "<div class='options'>" + options + "</div>" : "")
      + "<textarea id='answer-box' rows='3' placeholder='作答（开放题）'></textarea>"
      + "<div><button id='show-answer' class='primary'>看答案</button></div>"
      + "<div id='solution-area' class='hidden'></div>";
    renderMath(problemCard);

    var answerBox = document.getElementById("answer-box");
    var current = load(CURRENT_KEY, null);
    if (current && current.answer_text) answerBox.value = current.answer_text;
    answerBox.addEventListener("input", function () {
      var cur = load(CURRENT_KEY, {});
      cur.answer_text = answerBox.value;
      setCurrent(cur);
      var list = session();
      for (var i = list.length - 1; i >= 0; i--) {
        if (list[i].problem_id === problem.problem_id) {
          list[i].answer_text = answerBox.value;
          break;
        }
      }
      store(SESSION_KEY, list);
    });

    if (problem.options_json) {
      problemCard.querySelectorAll(".option").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var idx = parseInt(btn.dataset.idx, 10);
          var correct = String(idx) === String(problem.correct_option_id);
          finishProblem(problem, correct ? "correct" : "wrong",
            "选了选项 " + idx, answerBox.value);
        });
      });
    } else {
      document.getElementById("show-answer").addEventListener("click", function () {
        api("/problem/" + problem.problem_id).then(function (detail) {
          showSolution(detail.problem.solution || "", problem);
        });
      });
    }
  }

  function showSolution(solution, problem) {
    var area = document.getElementById("solution-area");
    area.classList.remove("hidden");
    var blocks = solution.split(/\n\s*\n/).map(function (b) { return b.trim(); })
      .filter(Boolean);
    var html = blocks.map(function (block, i) {
      return "<div class='solution-block' data-idx='" + (i + 1) + "'>"
        + "<b>第 " + (i + 1) + " 步</b> " + problemTextToHtml(block)
        + "</div>";
    }).join("");
    html +=
      "<div class='feedback'>"
      + "<p>反馈（可选）</p>"
      + "<div class='rating'>"
      + [1, 2, 3, 4, 5].map(function (r) {
        return "<button class='rate' data-r='" + r + "'>" + r + "</button>";
      }).join(" ")
      + "</div>"
      + "<textarea id='feedback-note' rows='2' placeholder='自然语言反馈（薄弱点）'></textarea>"
      + "<div><button id='mark-stuck'>标记卡点（点上面某一步）</button>"
      + "<button id='no-time'>没时间批改</button></div>"
      + "</div>";
    area.innerHTML = html;
    renderMath(area);

    area.querySelectorAll(".solution-block").forEach(function (block) {
      block.addEventListener("click", function () {
        area.querySelectorAll(".solution-block").forEach(function (b) {
          b.classList.remove("stuck");
        });
        block.classList.add("stuck");
        area.dataset.stuck = block.dataset.idx;
      });
    });
    document.getElementById("mark-stuck").addEventListener("click", function () {
      var stuck = area.dataset.stuck || "";
      finishProblem(problem, "stuck",
        (stuck ? "卡在第" + stuck + "步" : "卡住")
        + " " + document.getElementById("feedback-note").value.trim(),
        load(CURRENT_KEY, {}).answer_text || "");
    });
    document.getElementById("no-time").addEventListener("click", function () {
      finishProblem(problem, "skip", "", load(CURRENT_KEY, {}).answer_text || "");
    });
    area.querySelectorAll(".rate").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var rating = parseInt(btn.dataset.r, 10);
        var note = document.getElementById("feedback-note").value.trim();
        post("/feedback", {
          item_type: "problem", item_id: problem.problem_id,
          rating: rating, note: note,
        }).then(function () {
          finishProblem(problem, "skip", note,
            load(CURRENT_KEY, {}).answer_text || "");
        });
      });
    });
  }

  function finishProblem(problem, result, note, answerText) {
    var body = { problem_id: problem.problem_id, result: result, note: note };
    if (answerText) body.answer_text = answerText;
    post("/practice", body).catch(function () { /* record-only fallback */ })
      .then(function () {
        setCurrent(null);
        var kps = currentKps();
        if (!kps.length) kps = [];
        loadNext(kps);
      });
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
            return "<button class='rate' data-r='" + r + "'>" + r + "</button>";
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
    if (operation === "diagnose" && current.answer_text) {
      body.user_answer = current.answer_text;
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
    var sections = markdown.split(/\n## /);
    sections.forEach(function (section) {
      var lines = section.trim().split("\n");
      var title = lines.shift().replace(/^#+\s*/, "");
      html += "<div class='section'><h4>" + escapeHtml(title) + "</h4><p>"
        + problemTextToHtml(lines.join("\n")) + "</p></div>";
    });
    return html;
  }

  function bindAiButtons() {
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
  }

  bindAiButtons();
  updateAiContext();
})();
