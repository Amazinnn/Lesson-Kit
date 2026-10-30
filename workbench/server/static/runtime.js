/* Runtime updates preserve fields only on matching page surfaces. */
(() => {
  const storageKey = 'lessonkit-runtime:' + location.pathname + location.search;
  let initial, activeWrites = 0, uncertain = false, composing = false;
  addEventListener('compositionstart', () => { composing = true; }, true);
  addEventListener('compositionend', () => { composing = false; }, true);
  const originalFetch = window.fetch;
  window.fetch = async function(input, options = {}) {
    const method = (options.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
    const write = !['GET', 'HEAD'].includes(method);
    if (write) activeWrites++;
    try { return await originalFetch.apply(this, arguments); }
    catch (error) { if (write) uncertain = true; throw error; }
    finally { if (write) activeWrites--; }
  };
  function notice(message) {
    let node = document.getElementById('runtime-update-notice');
    if (!node) {
      node = document.createElement('div');
      node.id = 'runtime-update-notice'; node.setAttribute('role', 'status');
      node.style.cssText = 'position:fixed;bottom:12px;left:12px;z-index:9999;background:var(--paper,#fff);color:var(--ink,#222);padding:8px 12px;border:1px solid #aaa;border-radius:8px';
      document.body.append(node);
    }
    node.textContent = message; node.hidden = !message;
  }
  const dirty = new WeakSet();
  addEventListener('input', event => { dirty.add(event.target); }, true);
  const fields = () => [...document.querySelectorAll('input,textarea,select')].filter(
    el => !el.disabled && !el.readOnly && !el.closest('[hidden],.hidden') && !['password','file','submit','button','hidden'].includes(el.type));
  function identity(el) {
    if (el.id && !/^(paper-answer|goal-|experience|kp-experience)/.test(el.id)) return 'id:' + el.id;
    const turn = el.closest('[data-turn-id]');
    if (!turn) return null;
    const siblings = [...turn.querySelectorAll('input,textarea,select')];
    return 'turn:' + turn.dataset.turnId + ':' + (el.name || siblings.indexOf(el));
  }
  let saved = JSON.parse(sessionStorage.getItem(storageKey) || '[]');
  function restore() {
    saved = saved.filter(record => {
      const el = fields().find(el => identity(el) === record.key);
      if (!el) return true;
      el.value = record.value;
      if ('checked' in record) el.checked = record.checked;
      if (record.selection && typeof el.setSelectionRange === 'function') {
        try { el.setSelectionRange(...record.selection); } catch (_) { /* non-text input */ }
      }
      // The value adapter follows the property write into CodeMirror; the
      // input/change replay lets page models (queue edit drafts, paper
      // drafts) resync so a re-render rebuilds from the restored text.
      // Neither event submits or sends.
      el.dispatchEvent(new Event('input', {bubbles: true}));
      if (['checkbox', 'radio'].includes(el.type) || el.tagName === 'SELECT') {
        el.dispatchEvent(new Event('change', {bubbles: true}));
      }
      return false;
    });
    if (saved.length) sessionStorage.setItem(storageKey, JSON.stringify(saved));
    else sessionStorage.removeItem(storageKey);
  }
  async function poll() {
    try {
      const response = await originalFetch('/api/runtime', {cache: 'no-store'});
      if (!response.ok) return;
      const runtime = await response.json();
      const generation = runtime.generation + ':' + runtime.assets_generation;
      if (!initial) initial = generation;
      if (runtime.error) { notice('更新失败：' + runtime.error); return; }
      if (runtime.pending) { notice('更新等待中：正在等待当前任务完成'); return; }
      if (generation === initial) { notice(''); return; }
      if (activeWrites || uncertain || composing || (window.LessonKitRuntimeBusy && window.LessonKitRuntimeBusy())) { notice('更新等待中：请先确认发送或保存结果'); return; }
      const records = [];
      for (const el of fields()) {
        const key = identity(el);
        if (!key && dirty.has(el) && (el.value || el.checked)) { notice('更新等待中：请先保存当前编辑内容'); return; }
        if (!key) continue;
        const record = {key, value: el.value};
        if (['checkbox', 'radio'].includes(el.type)) record.checked = el.checked;
        if (typeof el.selectionStart === 'number') record.selection = [el.selectionStart, el.selectionEnd, el.selectionDirection];
        records.push(record);
      }
      sessionStorage.setItem(storageKey, JSON.stringify(records));
      location.reload();
    } catch (_) { /* replacement worker may briefly be unavailable */ }
  }
  addEventListener('DOMContentLoaded', () => {
    restore(); new MutationObserver(restore).observe(document.body, {childList:true, subtree:true});
    setInterval(poll, 1000); poll();
  });
})();
