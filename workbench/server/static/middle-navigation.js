/* Same-workspace page navigation keeps the workbench shell mounted. */
(function (window, document) {
  "use strict";

  var layout = document.getElementById("layout");
  var middlePage = document.getElementById("middle-page");
  if (!layout || !middlePage || !window.fetch || !window.history) return;

  var middle = document.getElementById("middle");
  var workspace = layout.dataset.workspace;
  var sequence = 0;
  var graphScriptsPromise = null;
  var middleScrollTop = 0;

  function sameWorkspace(url) {
    if (url.origin !== window.location.origin) return false;
    var parts = url.pathname.split("/");
    if (parts.length < 4 || parts[1] !== "w") return false;
    try { return decodeURIComponent(parts[2]) === workspace; }
    catch (_) { return false; }
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement("script");
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  function ensureGraphScripts() {
    if (window.GraphPhysics && window.GraphPhysics.workerBacked) return Promise.resolve();
    if (!graphScriptsPromise) {
      graphScriptsPromise = loadScript("/static/graph-physics-core.js")
        .then(function () { return loadScript("/static/graph-renderer.js"); })
        .then(function () { return loadScript("/static/graph-physics.js"); })
        .catch(function (error) {
          graphScriptsPromise = null;
          throw error;
        });
    }
    return graphScriptsPromise;
  }

  /* ---- 加载态：骨架屏（tasks.md 21.1 / 21.5）--------------------------------
     切页时 `#middle-page` 的 innerHTML 会被整体替换 ⇒ 进场动效只能由 CSS 的
     容器动画接管（`#layout:not([data-page="graph"]) #middle-page > *` 挂
     `lk-rise-in-12`），JS 不给子元素加一次性动效类名 —— 那类名会随 innerHTML
     一起被冲掉。JS 在这里只做「切页前把容器切成骨架态」这一件事：
     切页前呈骨架，内容到位后由容器动画接管。
     图谱页的转场作用域由 CSS 的 `#layout:not([data-page="graph"])` 排除，
     JS 侧不重复实现、也不给图谱页加任何特判。 */

  /* 骨架块：一条标题 + 一张卡 + 三行正文，与阅读列同宽。
     每个中栏页面各画一套占位形状的成本不低（design.md D-7「代价」），
     先取一个通用形状。 */
  var SKELETON_BLOCKS = [
    { height: 26, width: "46%", gap: 0 },
    { height: 128, width: "100%", gap: 22 },
    { height: 15, width: "92%", gap: 20 },
    { height: 15, width: "76%", gap: 10 },
    { height: 15, width: "86%", gap: 10 }
  ];

  function skeletonBlock(block) {
    var style = "height:" + block.height + "px;width:" + block.width
      + (block.gap ? ";margin-top:" + block.gap + "px" : "");
    /* 灰块 + 微光扫过：灰块与扫光都来自 CSS 的 `.lk-skeleton`
       （`lk-skeleton-sweep` 只动覆盖层的 transform），JS 不写动效。 */
    return '<div class="lk-skeleton" style="' + style + '"></div>';
  }

  function skeletonMarkup() {
    var blocks = [];
    for (var i = 0; i < SKELETON_BLOCKS.length; i += 1) {
      blocks.push(skeletonBlock(SKELETON_BLOCKS[i]));
    }
    /* 装饰层：`aria-hidden` + `pointer-events:none` —— 可交互元素一律不在
       装饰层内，浮层出现时也不抢焦点（tasks.md 21.3）。 */
    return '<div data-lk-skeleton="1" aria-hidden="true"'
      + ' style="pointer-events:none;max-width:800px;margin:0 auto">'
      + blocks.join("") + "</div>";
  }

  /* 切页前：容器先呈骨架 + `aria-busy` 置位；内容到位后由
     `installPageContent` 复位（骨架随 innerHTML 一起被内容替换）。 */
  function showLoadingState() {
    if (middle) middleScrollTop = middle.scrollTop;
    middlePage.setAttribute("aria-busy", "true");
    middlePage.innerHTML = skeletonMarkup();
  }

  function updateLayout(nextLayout) {
    ["page", "objectType", "objectId", "practiceKpId"].forEach(function (key) {
      if (nextLayout.dataset[key] === undefined) delete layout.dataset[key];
      else layout.dataset[key] = nextLayout.dataset[key];
    });
    delete layout.dataset.practiceSetId;
  }

  function updateActiveNavigation(nextDocument) {
    var currentItems = document.querySelectorAll("#left-column .nav-item");
    var nextItems = nextDocument.querySelectorAll("#left-column .nav-item");
    Array.prototype.forEach.call(currentItems, function (item, index) {
      var next = nextItems[index];
      if (item.classList && next) item.classList.toggle("active", next.classList.contains("active"));
    });
  }

  function updateScopeNames(nextDocument) {
    var currentTray = document.getElementById("scope-tray");
    var nextTray = nextDocument.getElementById("scope-tray");
    if (currentTray && nextTray) currentTray.dataset.kpNames = nextTray.dataset.kpNames || "{}";
  }

  function installPage(nextDocument, requestSequence) {
    var nextLayout = nextDocument.getElementById("layout");
    var nextPage = nextDocument.getElementById("middle-page");
    if (!nextLayout || !nextPage || nextLayout.dataset.workspace !== workspace) return false;

    if (nextLayout.dataset.page === "graph") {
      return ensureGraphScripts().then(function () {
        if (requestSequence !== sequence) return false;
        return installPageContent(nextDocument, nextLayout, nextPage);
      });
    }
    return installPageContent(nextDocument, nextLayout, nextPage);
  }

  function installPageContent(nextDocument, nextLayout, nextPage) {
    if (window.WorkbenchMiddlePage) window.WorkbenchMiddlePage.dispose();
    updateLayout(nextLayout);
    updateActiveNavigation(nextDocument);
    updateScopeNames(nextDocument);
    middlePage.innerHTML = nextPage.innerHTML;
    /* 骨架被内容替换 —— 容器动画此刻接管；加载态复位。 */
    middlePage.setAttribute("aria-busy", "false");
    if (middle && middleScrollTop) {
      middle.scrollTop = middleScrollTop;
      middleScrollTop = 0;
    }
    if (window.WorkbenchMiddlePage) window.WorkbenchMiddlePage.mount();
    if (window.AgentUISurfaces && window.AgentUISurfaces.renderContext) {
      window.AgentUISurfaces.renderContext();
    }
    return true;
  }

  function navigate(target, options) {
    options = options || {};
    var url = new URL(target, window.location.href);
    if (!sameWorkspace(url)) {
      window.location.href = url.href;
      return Promise.resolve(false);
    }
    if (!options.refresh && !options.popstate && url.href === window.location.href) return Promise.resolve(true);
    var requestSequence = ++sequence;
    if (!options.popstate) {
      if (options.replace) window.history.replaceState({ middle: true }, "", url.href);
      else window.history.pushState({ middle: true }, "", url.href);
    }
    showLoadingState();
    return window.fetch(url.href, { headers: { Accept: "text/html" } })
      .then(function (response) {
        if (!response.ok) throw new Error("page request failed");
        if (response.url) {
          var finalAddress = new URL(response.url, url.href);
          if (!sameWorkspace(finalAddress)) {
            window.location.href = url.href;
            return null;
          }
        }
        return response.text();
      })
      .then(function (source) {
        if (requestSequence !== sequence || source === null) return false;
        var nextDocument = new DOMParser().parseFromString(source, "text/html");
        var nextLayout = nextDocument.getElementById("layout");
        if (!nextLayout || nextLayout.dataset.workspace !== workspace) {
          throw new Error("destination is outside this workbench");
        }
        return installPage(nextDocument, requestSequence);
      })
      .catch(function () {
        if (requestSequence === sequence) window.location.href = url.href;
        return false;
      });
  }

  function handleClick(event) {
    if (event.defaultPrevented || event.button !== 0
        || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    var anchor = event.target && event.target.closest ? event.target.closest("a[href]") : null;
    if (!anchor || !anchor.closest("#left-column, #middle")) return;
    var rel = (anchor.getAttribute("rel") || "").toLowerCase().split(/\s+/);
    if (anchor.hasAttribute("download") || anchor.hasAttribute("target")
        || rel.indexOf("external") >= 0) return;
    var url = new URL(anchor.href, window.location.href);
    if (!sameWorkspace(url)) return;
    var current = new URL(window.location.href);
    if (url.pathname === current.pathname && url.search === current.search
        && url.hash !== current.hash) return;
    event.preventDefault();
    navigate(url.href);
  }

  document.addEventListener("click", handleClick);
  window.addEventListener("popstate", function () {
    navigate(window.location.href, { popstate: true });
  });
  window.WorkbenchNavigation = {
    navigate: navigate,
    refresh: function () { return navigate(window.location.href, { replace: true, refresh: true }); },
  };
}(window, document));
