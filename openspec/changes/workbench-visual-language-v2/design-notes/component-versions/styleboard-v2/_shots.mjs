// 样式板第二遍：滚动到 B 段（产品里还没有的形态）截图 + 逐组件体检
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const url = process.argv[2];
const outDir = process.argv[3];
const PORT = 9700 + Math.floor(Math.random() * 200);

const profile = mkdtempSync(join(tmpdir(), "sb-chrome2-"));
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
  "--disable-extensions", "--allow-file-access-from-files",
  "--window-size=1920,1200", "--user-data-dir=" + profile,
  "--remote-debugging-port=" + PORT, "about:blank",
], { stdio: ["ignore", "pipe", "pipe"] });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitPort() {
  for (let i = 0; i < 80; i++) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/json/version`); if (r.ok) return await r.json(); } catch (e) {}
    await sleep(250);
  }
  throw new Error("no devtools");
}
class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.handlers = []; }
  static async connect(u) {
    const ws = new WebSocket(u);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
    const c = new CDP(ws);
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id && c.pending.has(m.id)) { const p = c.pending.get(m.id); c.pending.delete(m.id); m.error ? p.rej(new Error(JSON.stringify(m.error))) : p.res(m.result); }
      else if (m.method) c.handlers.forEach((h) => h(m.method, m.params));
    };
    return c;
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((res, rej) => { this.pending.set(id, { res, rej }); this.ws.send(JSON.stringify({ id, method, params })); setTimeout(() => { if (this.pending.has(id)) { this.pending.delete(id); rej(new Error("timeout " + method)); } }, 30000); });
  }
  on(fn) { this.handlers.push(fn); }
}
const errors = [], warns = [];
await waitPort();
const v = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
const root = await CDP.connect(v.webSocketDebuggerUrl);
const t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?${encodeURIComponent(url)}`, { method: "PUT" })).json();
const page = await CDP.connect(t.webSocketDebuggerUrl);
page.on((m, p) => {
  if (m === "Runtime.exceptionThrown") errors.push("EXC " + (p.exceptionDetails?.exception?.description || p.exceptionDetails?.text));
  if (m === "Runtime.consoleAPICalled" && (p.type === "error" || p.type === "warning")) (p.type === "error" ? errors : warns).push(p.type + " " + (p.args || []).map((a) => a.value ?? a.description).join(" "));
  if (m === "Log.entryAdded" && (p.entry.level === "error" || p.entry.level === "warning")) (p.entry.level === "error" ? errors : warns).push("log " + p.entry.text + " " + (p.entry.url || ""));
});
await page.send("Runtime.enable"); await page.send("Log.enable"); await page.send("Page.enable");
await page.send("Page.navigate", { url });
await sleep(4500);

// 逐组件体检：每个组件的现状/候选样品是否真的有渲染尺寸
const health = await page.send("Runtime.evaluate", {
  expression: `(() => {
    const d = document.getElementById("sb-frame-day").contentDocument;
    const out = [];
    d.querySelectorAll(".sb-comp").forEach(c => {
      const key = c.id.replace("sb-","");
      const stages = Array.from(c.querySelectorAll(".sb-stage"));
      const zeroStages = stages.filter(s => s.getBoundingClientRect().height < 12).length;
      const emptyStages = stages.filter(s => {
        const kids = Array.from(s.children).filter(k => k.tagName !== "SPAN" || !k.className.includes("sb-none"));
        return kids.length === 0 && s.textContent.trim() === "";
      }).length;
      out.push({
        key,
        title: c.querySelector("h3") ? c.querySelector("h3").textContent : "?",
        stages: stages.length,
        zeroStages,
        emptyStages,
        hasCurrent: !!c.querySelector(".sb-sample--cur"),
        radios: c.querySelectorAll('input[type="radio"]').length,
        note: (c.querySelector(".sb-inv")||{textContent:""}).textContent.slice(0,0)
      });
    });
    return JSON.stringify(out, null, 1);
  })()`,
  returnByValue: true,
});
const arr = JSON.parse(health.result.value);
console.log("=== 组件体检（stage 数为「现状 + 候选数」）===");
arr.forEach((r) => console.log(
  (r.zeroStages ? "!" : " ") + (r.emptyStages ? "E" : " ") +
  r.key.padEnd(12) + " stages=" + r.stages + " zeroH=" + r.zeroStages + " empty=" + r.emptyStages +
  " radios=" + r.radios + "  " + r.title));
const bad = arr.filter((r) => r.emptyStages > 0);
console.log("空样品组件数:", bad.length, bad.map((b) => b.key).join(","));

// 滚到 B 段截图
const scrollTo = async (sel) => {
  await page.send("Runtime.evaluate", { expression: `(() => { const d=document.getElementById("sb-frame-day").contentDocument; const e=d.querySelector("${sel}"); if(e){e.scrollIntoView({block:"start"}); const y=d.documentElement.scrollTop||d.body.scrollTop; document.getElementById("sb-frame-night").contentWindow.scrollTo(0,y); return y;} return -1; })()`, returnByValue: true });
  await sleep(700);
};
for (const [name, sel] of [["gap", ".sb-section--gap"], ["dialog", "#sb-dialog"], ["tool", "#sb-toolcard"], ["switch", "#sb-switch"]]) {
  const r = await page.send("Runtime.evaluate", { expression: `(() => { const d=document.getElementById("sb-frame-day").contentDocument; const e=d.querySelector("${sel}"); if(e){e.scrollIntoView({block:"start"}); const y=d.documentElement.scrollTop||d.body.scrollTop; document.getElementById("sb-frame-night").contentWindow.scrollTo(0,y); return y;} return -1; })()`, returnByValue: true });
  await sleep(800);
  const shot = await page.send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(outDir, "_shot-" + name + ".png"), Buffer.from(shot.data, "base64"));
  console.log("shot", name, "scrollY=", r.result.value);
}

console.log("=== CONSOLE ===");
console.log("errors:", errors.length); errors.forEach((e) => console.log("  E " + e));
console.log("warnings:", warns.length); warns.forEach((e) => console.log("  W " + e));
try { await fetch(`http://127.0.0.1:${PORT}/json/close/${t.id}`); } catch (e) {}
chrome.kill();
process.exit(0);
