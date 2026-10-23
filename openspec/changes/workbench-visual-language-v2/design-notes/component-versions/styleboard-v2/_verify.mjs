// 样式板自检：CDP 直连 headless Chrome，抓控制台错误 / 异常 / token 取值 / 导出结果
// 用法: node sb-verify.mjs <file-url> <out-png>
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const url = process.argv[2];
const outPng = process.argv[3];
const PORT = 9333 + Math.floor(Math.random() * 400);

const profile = mkdtempSync(join(tmpdir(), "sb-chrome-"));
const chrome = spawn(CHROME, [
  "--headless=new",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
  "--disable-extensions",
  "--allow-file-access-from-files",
  "--window-size=1920,1200",
  "--user-data-dir=" + profile,
  "--remote-debugging-port=" + PORT,
  "about:blank",
], { stdio: ["ignore", "pipe", "pipe"] });

let chromeErr = "";
chrome.stderr.on("data", (d) => { chromeErr += d.toString(); });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitPort() {
  for (let i = 0; i < 80; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (r.ok) return await r.json();
    } catch (e) { /* not up yet */ }
    await sleep(250);
  }
  throw new Error("chrome devtools never came up:\n" + chromeErr.slice(-2000));
}

class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.handlers = []; }
  static async connect(wsUrl) {
    const ws = new WebSocket(wsUrl);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
    const c = new CDP(ws);
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && c.pending.has(msg.id)) {
        const { res, rej } = c.pending.get(msg.id);
        c.pending.delete(msg.id);
        if (msg.error) rej(new Error(JSON.stringify(msg.error))); else res(msg.result);
      } else if (msg.method) {
        c.handlers.forEach((h) => h(msg.method, msg.params));
      }
    };
    return c;
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((res, rej) => {
      this.pending.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params }));
      setTimeout(() => { if (this.pending.has(id)) { this.pending.delete(id); rej(new Error("timeout " + method)); } }, 30000);
    });
  }
  on(fn) { this.handlers.push(fn); }
}

const errors = [];
const warns = [];
const logs = [];

const version = await waitPort();
const cdp = await CDP.connect(version.webSocketDebuggerUrl);

// 新建 target
const tRes = await fetch(`http://127.0.0.1:${PORT}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
const target = await tRes.json();
const page = await CDP.connect(target.webSocketDebuggerUrl);

page.on((method, p) => {
  if (method === "Runtime.exceptionThrown") {
    const d = p.exceptionDetails || {};
    errors.push("EXCEPTION: " + (d.exception?.description || d.text || JSON.stringify(d)));
  }
  if (method === "Runtime.consoleAPICalled") {
    const text = (p.args || []).map((a) => a.value ?? a.description ?? a.type).join(" ");
    const line = `[${p.type}] ${text}`;
    if (p.type === "error") errors.push(line);
    else if (p.type === "warning") warns.push(line);
    else logs.push(line);
  }
  if (method === "Log.entryAdded") {
    const e = p.entry || {};
    const line = `[log:${e.level}] ${e.text} ${e.url ? "(" + e.url + ")" : ""}`;
    if (e.level === "error") errors.push(line);
    else if (e.level === "warning") warns.push(line);
    else logs.push(line);
  }
});

await page.send("Runtime.enable");
await page.send("Log.enable");
await page.send("Page.enable");
await page.send("Network.enable");
await page.send("Page.navigate", { url });
await sleep(4500);

const probe = await page.send("Runtime.evaluate", {
  expression: `(() => {
    const out = { href: location.href, title: document.title };
    const day = document.getElementById("sb-frame-day");
    const night = document.getElementById("sb-frame-night");
    function tokens(doc) {
      if (!doc) return null;
      const cs = doc.defaultView.getComputedStyle(doc.documentElement);
      const names = ["--surface-base","--surface-card","--surface-raised","--surface-sunken","--r-md","--ink-strong","--role-blue","--role-yellow","--role-red","--veil-active","--elev-1"];
      const o = {};
      names.forEach(n => o[n] = cs.getPropertyValue(n).trim());
      o["theme"] = doc.documentElement.getAttribute("data-theme") || "(day)";
      o["sheetCount"] = doc.styleSheets.length;
      o["sheetHrefs"] = Array.from(doc.styleSheets).map(s => (s.href||"(inline)").split("/").pop());
      o["compCount"] = doc.querySelectorAll(".sb-comp").length;
      o["variantCount"] = doc.querySelectorAll("[data-variant]").length;
      o["radioCount"] = doc.querySelectorAll('input[type="radio"][data-comp]').length;
      return o;
    }
    out.day = tokens(day && day.contentDocument);
    out.night = tokens(night && night.contentDocument);
    out.sameOrigin = !!(day && day.contentDocument);
    // 产品 CSS 是否真的加载进来：读一个只有 workbench.css 才会给的规则
    function ruleFrom(doc, sel) {
      if (!doc) return null;
      for (const s of doc.styleSheets) {
        let rules; try { rules = s.cssRules; } catch (e) { continue; }
        for (const r of rules) {
          if (r.selectorText === sel) return r.style.cssText.slice(0, 160);
        }
      }
      return null;
    }
    out.rule_day_card = ruleFrom(day && day.contentDocument, ".card");
    out.rule_night_dot = ruleFrom(night && night.contentDocument, ".lk-dot");
    out.status = (document.getElementById("sb-status")||{}).textContent;
    return JSON.stringify(out, null, 2);
  })()`,
  returnByValue: true,
  awaitPromise: false,
});

console.log("=== PROBE ===");
console.log(probe.result.value);

// 选一个候选 + 导出
const act = await page.send("Runtime.evaluate", {
  expression: `(() => {
    const r = document.querySelector('#sb-frame-day').contentDocument.querySelector('input[data-comp="btn-primary"]');
    if (!r) return "no radio";
    r.checked = true;
    r.dispatchEvent(new Event("change", {bubbles:true}));
    const r2 = document.querySelector('#sb-frame-night').contentDocument.querySelector('input[data-comp="btn-primary"][value="' + r.value + '"]');
    document.getElementById("sb-export").click();
    return JSON.stringify({
      picked: r.value,
      nightSynced: !!(r2 && r2.checked),
      exportStatus: (document.getElementById("sb-export-status")||{}).textContent,
      exportHead: (document.getElementById("sb-export-text").value||"").slice(0, 700),
      exportLen: (document.getElementById("sb-export-text").value||"").length,
      ls: (function(){ try { return window.localStorage.getItem("lk-styleboard-v2"); } catch(e) { return "LS-ERR:" + e.name; } })()
    }, null, 2);
  })()`,
  returnByValue: true,
});
console.log("=== ACTION ===");
console.log(act.result.value);
await sleep(1200);

const shot = await page.send("Page.captureScreenshot", { format: "png" });
writeFileSync(outPng, Buffer.from(shot.data, "base64"));

console.log("=== CONSOLE ===");
console.log("errors:", errors.length);
errors.forEach((e) => console.log("  E " + e));
console.log("warnings:", warns.length);
warns.forEach((e) => console.log("  W " + e));
console.log("logs:", logs.length);
logs.slice(0, 20).forEach((e) => console.log("  L " + e));
console.log("screenshot:", outPng);

try { await fetch(`http://127.0.0.1:${PORT}/json/close/${target.id}`); } catch (e) { /* ignore */ }
chrome.kill();
process.exit(0);
