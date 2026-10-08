/* Knowledge-point practice experience editor. */
(function () {
  "use strict";

  var panel = document.getElementById("practice-experience");
  var layout = document.getElementById("layout");
  if (!panel || !layout) return;

  var workspace = layout.dataset.workspace;
  var kpId = panel.dataset.kpId;
  var editor = document.getElementById("experience-editor");
  var edit = document.getElementById("experience-edit");
  var cancel = document.getElementById("experience-cancel");
  var save = document.getElementById("experience-save");
  var remove = document.getElementById("experience-delete");
  var content = document.getElementById("experience-content");
  var choices = document.getElementById("experience-problem-choices");
  var error = document.getElementById("experience-error");
  var choicesLoaded = false;

  function endpoint() {
    return "/api/w/" + encodeURIComponent(workspace)
      + "/kp/" + encodeURIComponent(kpId) + "/experience";
  }

  function kpEndpoint() {
    return "/api/w/" + encodeURIComponent(workspace)
      + "/kp/" + encodeURIComponent(kpId);
  }

  function escapeHtml(text) {
    return String(text == null ? "" : text).replace(/[&<>\"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[ch];
    });
  }

  function showError(message) {
    if (!error) return;
    error.textContent = message || "保存失败";
    error.classList.remove("hidden");
  }

  function setEditing(open) {
    if (!editor) return;
    editor.classList.toggle("hidden", !open);
    if (edit) edit.classList.toggle("hidden", open);
    if (remove) remove.classList.toggle("hidden", open);
    if (error) {
      error.textContent = "";
      error.classList.add("hidden");
    }
    if (open && content) content.focus();
  }

  function selectedProblems() {
    return Array.from(panel.querySelectorAll(
      "#experience-problem-choices input[type=checkbox]:checked"
    )).map(function (input) { return input.value; });
  }

  function request(method, url, body) {
    var options = { method: method, headers: {} };
    if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    return fetch(url, options).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (data) {
        if (!response.ok) {
          var err = new Error(data.error || String(response.status));
          err.status = response.status;
          throw err;
        }
        return data;
      });
    });
  }

  function loadChoices() {
    if (choicesLoaded || !choices) return Promise.resolve();
    if (save) save.disabled = true;
    choices.innerHTML = "<p class='muted'>正在载入关联题目…</p>";
    return Promise.all([
      request("GET", kpEndpoint()),
      request("GET", endpoint()),
    ]).then(function (results) {
      var kp = results[0] || {};
      var record = (results[1] || {}).experience || null;
      var selected = new Set(record && Array.isArray(record.problem_ids)
        ? record.problem_ids : []);
      var problems = Array.isArray(kp.problems) ? kp.problems : [];
      if (!problems.length) {
        choices.innerHTML = "<p class='muted'>这个知识点暂时没有关联题目。</p>";
      } else {
        choices.innerHTML = problems.map(function (problem) {
          var id = problem.problem_id || "";
          var title = problem.display_title || (problem.problem_text || "").slice(0, 80) || id;
          return "<label class='experience-problem-choice'>"
            + "<input type='checkbox' value='" + escapeHtml(id) + "'"
            + (selected.has(id) ? " checked" : "") + ">"
            + "<span>" + escapeHtml(title) + "</span></label>";
        }).join("");
      }
      choicesLoaded = true;
      if (record && typeof record.revision === "number") {
        panel.dataset.revision = String(record.revision);
      }
    }).finally(function () {
      if (save) save.disabled = false;
    });
  }

  if (edit) edit.addEventListener("click", function () {
    setEditing(true);
    loadChoices().catch(function (err) { showError(err.message); });
  });
  if (cancel) cancel.addEventListener("click", function () { setEditing(false); });

  if (save) save.addEventListener("click", function () {
    var text = content ? content.value.trim() : "";
    if (!text) {
      showError("经验总结不能为空；暂时没有经验时请保持未创建状态。");
      return;
    }
    if (!choicesLoaded) {
      showError("关联题目仍在载入，请稍后再保存。");
      return;
    }
    var revision = Number(panel.dataset.revision || 0);
    var body = { content: text, problem_ids: selectedProblems() };
    var method = revision ? "PATCH" : "POST";
    if (revision) body.expected_revision = revision;
    save.disabled = true;
    request(method, endpoint(), body).then(function () {
      window.location.reload();
    }).catch(function (err) {
      save.disabled = false;
      if (err.status === 409) {
        showError("这份经验刚刚被其他编辑更新，请刷新后合并你的修改。");
      } else {
        showError(err.message);
      }
    });
  });

  if (remove) remove.addEventListener("click", function () {
    var revision = Number(panel.dataset.revision || 0);
    if (!revision) return;
    if (!window.confirm("删除这份做题经验？知识点、题目和学习记录不会受影响。")) return;
    remove.disabled = true;
    request("DELETE", endpoint() + "?expected_revision=" + encodeURIComponent(revision))
      .then(function () { window.location.reload(); })
      .catch(function (err) {
        remove.disabled = false;
        if (err.status === 409) {
          showError("这份经验刚刚被其他编辑更新，请刷新后再删除。");
        } else {
          showError(err.message);
        }
      });
  });
})();
