/* 组件样式一览 v2 —— 渲染 / 选择 / 导出
 *
 * ⚠️ 评审件（tmp/ 被 gitignore）。不引外部资源，无 fetch（file:// 下会被 CORS 拦）。
 * ⚠️ 夜纸靠 <html data-theme="night">（与设置视图同口径）—— 所以夜纸那一侧
 *    是一个独立的文档（about:blank iframe，与父页同源、同 base URL）。
 * ⚠️ 「现状」那一列完全由产品真实 CSS 决定（workbench.css / agent-ui.css），
 *    本文件只负责搭结构，不改任何产品样式。
 */
(function () {
  "use strict";

  var SB = window.LK_SB;
  var KEY = "lk-styleboard-v2";
  var chromeCss = (document.getElementById("sb-chrome") || {}).textContent || "";
  var picks = {};
  var views = [];
  var syncLock = 0;

  function byId(id) { return document.getElementById(id); }

  /* 类名 / 定位是**纯文本**（可能含 <select> 这类标签名）⇒ 必须转义后再进 innerHTML，
     否则 HTML 解析器会把它当成真标签（会报 <select> 嵌套的解析警告）。 */
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  /* ------------------------------------------------------------------ 存储 */
  function loadPicks() {
    try {
      var raw = window.localStorage.getItem(KEY);
      if (raw) {
        var obj = JSON.parse(raw);
        if (obj && typeof obj === "object") { return obj; }
      }
    } catch (e) { /* file:// 下 localStorage 可能不可用 —— 静默降级为内存态 */ }
    return {};
  }
  function savePicks() {
    try { window.localStorage.setItem(KEY, JSON.stringify(picks)); return true; }
    catch (e) { return false; }
  }

  /* ------------------------------------------------------------------ 渲染 */
  function statusLabel(c) {
    if (c.status === "ok") { return '<span class="sb-flag sb-flag--ok">✅ 有独立形态</span>'; }
    if (c.sec === "§4.16" || c.sec === "§4.24" || c.sec === "§4.25") {
      return '<span class="sb-flag sb-flag--none">❌ 产品里根本没有这个界面</span>';
    }
    return '<span class="sb-flag sb-flag--gap">⚠️ 存在但没有专属样式</span>';
  }

  function currentHtml(c) {
    var body;
    if (c.current.html) {
      body = '<div class="sb-stage">' + c.current.html + '</div>';
    } else {
      body = '<div class="sb-stage sb-stage--none"><span class="sb-none">产品里没有这个界面</span></div>';
    }
    return '' +
      '<div class="sb-sample sb-sample--cur">' +
        '<div class="sb-sample-top"><span class="sb-tag-cur">现状</span><span class="sb-src">' + (c.current.where || "—") + '</span></div>' +
        body +
        '<p class="sb-delta">' + c.current.note + '</p>' +
      '</div>';
  }

  function variantHtml(c, v, idx) {
    return '' +
      '<div class="sb-sample sb-sample--var">' +
        '<div class="sb-sample-top"><span class="sb-tag-var">' + v.name + '</span><span class="sb-src">data-variant="' + v.id + '"</span></div>' +
        '<div class="sb-stage">' + v.html + '</div>' +
        '<p class="sb-delta">' + v.note + '</p>' +
        '<label class="sb-pick"><input type="radio" name="sb-' + c.key + '" value="' + v.id + '" data-comp="' + c.key + '"><span>★ 选它</span></label>' +
      '</div>';
  }

  function compHtml(c) {
    var h = [];
    h.push('<article class="sb-comp" id="sb-' + c.key + '">');
    h.push('<header class="sb-comp-head">');
    h.push('<div class="sb-comp-title"><span class="sb-sec">' + c.sec + '</span><h3>' + c.name + '</h3></div>');
    h.push(statusLabel(c));
    h.push('<dl class="sb-meta">');
    h.push('<div><dt>spec 类名</dt><dd><code>' + esc(c.spec) + '</code></dd></div>');
    h.push('<div><dt>产品真实类名</dt><dd><code>' + esc(c.product) + '</code>' + (c.productWhere ? '<span class="sb-where">' + esc(c.productWhere) + '</span>' : '') + '</dd></div>');
    h.push('</dl>');
    h.push('<p class="sb-inv">' + c.inventory + '</p>');
    if (c.status !== "ok") {
      h.push('<p class="sb-gap">⚠️ <b>产品里还没有这个形态</b> —— 下面三个候选是<b>新设计</b>，不是现状的改版。</p>');
    }
    h.push('</header>');
    h.push('<div class="sb-samples">');
    h.push(currentHtml(c));
    for (var i = 0; i < c.variants.length; i++) { h.push(variantHtml(c, c.variants[i], i)); }
    h.push('</div>');
    h.push('</article>');
    return h.join("");
  }

  function tocHtml() {
    var ok = [], gap = [];
    SB.components.forEach(function (c) { (c.status === "ok" ? ok : gap).push(c); });
    function items(list) {
      return list.map(function (c) {
        return '<li><a href="#sb-' + c.key + '" data-goto="sb-' + c.key + '"><span class="sb-sec">' + c.sec + '</span>' + c.name + '</a></li>';
      }).join("");
    }
    return '' +
      '<details class="sb-toc"><summary>组件目录（28 个 · 点条目可跳到两侧）</summary>' +
        '<div class="sb-toc-cols"><ul>' + items(ok) + '</ul><ul>' + items(gap) + '</ul></div>' +
      '</details>';
  }

  function probeCells(doc) {
    var names = ["--surface-base", "--surface-card", "--surface-raised", "--surface-sunken",
      "--r-md", "--ink-strong", "--role-blue", "--role-yellow", "--role-red"];
    var cs = doc.defaultView.getComputedStyle(doc.documentElement);
    return names.map(function (n) {
      var v = cs.getPropertyValue(n);
      return '<span class="sb-token"><b>' + n + '</b><code>' + (v ? esc(v.trim()) : "—") + '</code></span>';
    }).join("");
  }

  function probeHtml(doc, theme) {
    return '' +
      '<div class="sb-frame-head">' +
        '<div class="sb-frame-title"><strong>' + (theme === "night" ? "夜纸 night" : "暖纸 day") + '</strong>' +
          '<span class="sb-frame-sub">' + (theme === "night" ? '<code>html[data-theme="night"]</code>' : '默认（暖纸）') + '</span></div>' +
        '<div class="sb-tokens" data-probe>' + probeCells(doc) + '</div>' +
      '</div>';
  }

  /* 链接的样式表是异步加载的 ⇒ 首帧读 token 可能是空的。
     样式表到位后重刷一次探测条（这也是「token 真的命中了吗」的自证）。 */
  function refreshProbe(view) {
    try {
      var box = view.doc.querySelector("[data-probe]");
      if (box) { box.innerHTML = probeCells(view.doc); }
    } catch (e) { /* ignore */ }
  }

  function catalogHtml(doc, theme) {
    var ok = [], gap = [];
    SB.components.forEach(function (c) { (c.status === "ok" ? ok : gap).push(c); });
    var h = [];
    h.push(probeHtml(doc, theme));
    h.push(tocHtml());
    h.push('<section class="sb-section"><h2 class="sb-section-title">A · 产品里已有独立形态<span>' + ok.length + ' 个</span></h2>');
    ok.forEach(function (c) { h.push(compHtml(c)); });
    h.push('</section>');
    h.push('<section class="sb-section sb-section--gap"><h2 class="sb-section-title">B · 产品里还没有的形态<span>' + gap.length + ' 个</span></h2>');
    h.push('<p class="sb-section-lead">这一节的组件：要么<b>只有原生控件</b>、要么<b>markup 已落地但样式零命中</b>、要么<b>产品里压根没有</b>。' +
      '下面的候选都是<b>新设计</b>，供你挑形态；落地时需要连带补齐 aria / 键盘 / 载荷契约。</p>');
    gap.forEach(function (c) { h.push(compHtml(c)); });
    h.push('</section>');
    return h.join("");
  }

  /* ------------------------------------------------------------ 挂载与同步 */
  function mountFrame(iframe, theme) {
    var doc = iframe.contentWindow.document;
    doc.open();
    doc.write('<!doctype html><html lang="zh-CN"' + (theme === "night" ? ' data-theme="night"' : '') + '>' +
      '<head><meta charset="utf-8">' +
      '<link rel="stylesheet" href="' + SB.CSS_WORKBENCH + '">' +
      '<link rel="stylesheet" href="' + SB.CSS_AGENT + '">' +
      '<style>' + chromeCss + '</style>' +
      '<style>' + SB.candidateCss + '</style>' +
      '</head><body class="sb-frame"><div id="sb-catalog"></div></body></html>');
    doc.close();
    doc.getElementById("sb-catalog").innerHTML = catalogHtml(doc, theme);
    return doc;
  }

  function applyPicks() {
    views.forEach(function (v) {
      var radios = v.doc.querySelectorAll('input[type="radio"][data-comp]');
      for (var i = 0; i < radios.length; i++) {
        var comp = radios[i].getAttribute("data-comp");
        radios[i].checked = (picks[comp] === radios[i].value);
      }
    });
  }

  function onPickChange(comp, value) {
    picks[comp] = value;
    savePicks();
    applyPicks();
    updateStatus();
  }

  function updateStatus() {
    var n = Object.keys(picks).length;
    var s = byId("sb-status");
    if (s) {
      s.textContent = "已选 " + n + " / " + SB.components.length + " 个组件" +
        (savePicks() ? "（已存入 localStorage: " + KEY + "）" : "（localStorage 不可用，本次会话有效）");
    }
  }

  function attachScrollSync(a, b) {
    function link(src, dst) {
      src.contentWindow.addEventListener("scroll", function () {
        var now = Date.now();
        if (now < syncLock) { return; }
        syncLock = now + 140;
        try { dst.contentWindow.scrollTo(0, src.contentWindow.scrollY); } catch (e) { /* ignore */ }
      });
    }
    link(a, b);
    link(b, a);
  }

  function attachDoc(doc) {
    doc.addEventListener("change", function (ev) {
      var t = ev.target;
      if (!t || t.type !== "radio" || !t.getAttribute) { return; }
      var comp = t.getAttribute("data-comp");
      if (!comp) { return; }
      onPickChange(comp, t.value);
    });
    doc.addEventListener("click", function (ev) {
      var a = ev.target && ev.target.closest ? ev.target.closest("a[data-goto]") : null;
      if (!a) { return; }
      ev.preventDefault();
      var id = a.getAttribute("data-goto");
      views.forEach(function (v) {
        try {
          var t = v.doc.getElementById(id);
          if (t && t.scrollIntoView) { t.scrollIntoView({ block: "start" }); }
        } catch (e) { /* ignore */ }
      });
    });
  }

  /* ------------------------------------------------------------------ 导出 */
  function buildExport() {
    var L = [];
    L.push("# 组件样式一览 v2 · 我的选择");
    L.push("");
    L.push("- 生成时间：" + new Date().toISOString());
    L.push("- 存储键：`" + KEY + "`");
    L.push("- 清单来源：`openspec/changes/workbench-visual-language-v2/component-inventory.md`（spec 类名 ↔ 产品真实类名）");
    L.push("- 形态来源：`openspec/changes/workbench-visual-language-v2/design-notes/component-spec.md` §4");
    L.push("");
    var unchosen = [];
    SB.components.forEach(function (c) {
      L.push("## " + c.sec + " " + c.name);
      L.push("");
      L.push("- **spec 类名**：`" + c.spec + "`");
      L.push("- **产品真实类名**：`" + c.product + "`" + (c.productWhere ? "　（" + c.productWhere + "）" : ""));
      L.push("- **状态**：" + (c.status === "ok" ? "✅ 有独立形态"
        : (c.sec === "§4.16" || c.sec === "§4.24" || c.sec === "§4.25")
          ? "❌ 产品里根本没有这个界面"
          : "⚠️ 存在但没有专属样式"));
      L.push("- **现状**：" + c.current.note.replace(/<[^>]+>/g, ""));
      var pick = picks[c.key];
      if (pick) {
        var v = null;
        for (var i = 0; i < c.variants.length; i++) { if (c.variants[i].id === pick) { v = c.variants[i]; } }
        if (v) {
          L.push("- **★ 选择**：" + v.name + "　`data-variant=\"" + v.id + "\"`");
          L.push("- **改变了什么**：" + v.note.replace(/<[^>]+>/g, ""));
        }
      } else {
        L.push("- **★ 选择**：（未选）");
        unchosen.push(c.sec + " " + c.name);
      }
      L.push("");
    });
    if (unchosen.length) {
      L.push("---");
      L.push("");
      L.push("## 未选择的组件（" + unchosen.length + "）");
      L.push("");
      unchosen.forEach(function (n) { L.push("- " + n); });
      L.push("");
    }
    return L.join("\n");
  }

  function legacyCopy(text) {
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "readonly");
      ta.style.position = "fixed";
      ta.style.top = "0";
      ta.style.left = "0";
      ta.style.width = "2px";
      ta.style.height = "2px";
      ta.style.padding = "0";
      ta.style.border = "0";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      if (ta.setSelectionRange) { ta.setSelectionRange(0, ta.value.length); }
      var ok = document.execCommand("copy");
      document.body.removeChild(ta);
      if (ok) { return "exec"; }
    } catch (e) { /* ignore */ }
    return "manual";
  }

  function copyText(text) {
    return new Promise(function (resolve) {
      var canUse = false;
      try {
        canUse = !!(navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext);
      } catch (e) { canUse = false; }
      if (!canUse) { resolve(legacyCopy(text)); return; }
      try {
        navigator.clipboard.writeText(text).then(function () {
          resolve("clipboard");
        }, function () {
          resolve(legacyCopy(text));
        });
      } catch (e) {
        resolve(legacyCopy(text));
      }
    });
  }

  function doExport() {
    var text = buildExport();
    var box = byId("sb-export-text");
    if (box) { box.value = text; }
    var panel = byId("sb-export-panel");
    if (panel) { panel.open = true; }
    var st = byId("sb-export-status");
    copyText(text).then(function (how) {
      if (!st) { return; }
      if (how === "clipboard") { st.textContent = "✅ 已复制到剪贴板"; st.className = "sb-export-status sb-ok"; }
      else if (how === "exec") { st.textContent = "✅ 已复制到剪贴板（execCommand 降级通道）"; st.className = "sb-export-status sb-ok"; }
      else { st.textContent = "⚠️ 浏览器拒绝了剪贴板访问 —— 结果已渲染在下方文本框里，请手动复制（Ctrl/Cmd + A, C）"; st.className = "sb-export-status sb-warn"; }
    });
  }

  function doClear() {
    picks = {};
    savePicks();
    applyPicks();
    updateStatus();
    var st = byId("sb-export-status");
    if (st) { st.textContent = "已清空选择"; st.className = "sb-export-status"; }
  }

  /* ------------------------------------------------------------------ 启动 */
  function init() {
    picks = loadPicks();

    var warm = byId("sb-frame-day");
    var night = byId("sb-frame-night");
    if (!warm || !night) { return; }

    var dDay = mountFrame(warm, "day");
    var dNight = mountFrame(night, "night");
    views = [
      { doc: dDay, theme: "day", frame: warm },
      { doc: dNight, theme: "night", frame: night }
    ];
    views.forEach(function (v) {
      v.frame.addEventListener("load", function () { refreshProbe(v); });
      window.setTimeout(function () { refreshProbe(v); }, 120);
      window.setTimeout(function () { refreshProbe(v); }, 900);
    });
    attachDoc(dDay);
    attachDoc(dNight);
    attachScrollSync(warm, night);
    applyPicks();
    updateStatus();

    var ex = byId("sb-export");
    if (ex) { ex.addEventListener("click", doExport); }
    var cl = byId("sb-clear");
    if (cl) { cl.addEventListener("click", doClear); }
    var cp = byId("sb-copy-again");
    if (cp) {
      cp.addEventListener("click", function () {
        var box = byId("sb-export-text");
        if (!box) { return; }
        box.focus();
        box.select();
        copyText(box.value).then(function (how) {
          var st = byId("sb-export-status");
          if (!st) { return; }
          if (how === "manual") {
            st.textContent = "⚠️ 剪贴板不可用 —— 文本已全选，请按 Ctrl/Cmd + C 复制";
            st.className = "sb-export-status sb-warn";
          } else {
            st.textContent = "✅ 已复制到剪贴板";
            st.className = "sb-export-status sb-ok";
          }
        });
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
