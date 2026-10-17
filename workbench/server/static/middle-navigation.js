/* Same-workspace page navigation keeps the workbench shell mounted. */
(function (window, document) {
  "use strict";

  var layout = document.getElementById("layout");
  var middlePage = document.getElementById("middle-page");
  if (!layout || !middlePage || !window.fetch || !window.history) return;

  var workspace = layout.dataset.workspace;
  var sequence = 0;
  var graphScriptsPromise = null;

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
