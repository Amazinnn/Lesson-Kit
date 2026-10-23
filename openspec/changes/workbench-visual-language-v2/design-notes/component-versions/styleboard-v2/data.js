/* 组件样式一览 v2 —— 目录数据 + 候选形态 CSS
 *
 * ⚠️ 本文件是**评审件**（tmp/ 被 gitignore，不入库）。
 * ⚠️ 候选形态一律**只用产品已有 token**（var(--…)），**不硬编码 hex**。
 * ⚠️ 候选 CSS 会被 app.js 注入到每一侧的 <style> 块里。
 * ⚠️ 「现状」那一列用的是**产品真实类名**（primary / outline / paper-dot …），
 *    样式完全由 workbench.css / agent-ui.css 决定 —— 不在本文件里重写。
 */
window.LK_SB = (function () {
  "use strict";

  /* 产品真实 CSS（相对 styleboard-v2/ 的正确层级：../../.. 到仓库根） */
  var CSS_WORKBENCH = "../../../../../../workbench/server/static/workbench.css";
  var CSS_AGENT = "../../../../../../workbench/server/static/agent-ui.css";

  /* ---- 产品里真实存在的空态静物插画（inline 自 workbench/server/static/assets/empty/empty-canvas.svg） */
  var ART = '<svg viewBox="0 0 240 200" class="asset asset-empty" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    + '<g stroke-linecap="round" stroke-linejoin="round">'
    + '<g class="asset-empty__shadow">'
    + '<path d="M 40 168 L 200 168" fill="none" stroke="color-mix(in oklab, var(--asset-ink, #2a2620) 8%, var(--asset-paper, #fffdf7))" stroke-width="3"/>'
    + '<ellipse cx="120" cy="165" rx="40" ry="2.5" fill="color-mix(in oklab, var(--asset-ink, #2a2620) 8%, var(--asset-paper, #fffdf7))"/>'
    + '</g>'
    + '<g class="asset-empty__wash">'
    + '<path fill-rule="evenodd" d="M 76 48 L 164 48 Q 170 48 170 54 L 170 144 Q 170 150 164 150 L 76 150 Q 70 150 70 144 L 70 54 Q 70 48 76 48 Z M 83 58 L 157 58 Q 160 58 160 61 L 160 137 Q 160 140 157 140 L 83 140 Q 80 140 80 137 L 80 61 Q 80 58 83 58 Z" fill="color-mix(in oklab, var(--asset-ground-yellow, #f5c518) 12%, var(--asset-paper, #fffdf7))"/>'
    + '<path d="M 83 58 L 157 58 Q 160 58 160 61 L 160 137 Q 160 140 157 140 L 83 140 Q 80 140 80 137 L 80 61 Q 80 58 83 58 Z" fill="var(--asset-paper, #fffdf7)"/>'
    + '<path d="M 104 140 L 160 140 L 160 104 Q 146 126 104 140 Z" fill="color-mix(in oklab, var(--asset-ink, #2a2620) 8%, var(--asset-paper, #fffdf7))"/>'
    + '</g>'
    + '<g class="asset-empty__line" fill="none" stroke="var(--asset-ink, #2a2620)">'
    + '<path d="M 92 126 L 126 96" stroke="color-mix(in oklab, var(--asset-ground-blue, #2b62e8) 8%, var(--asset-paper, #fffdf7))" stroke-width="3"/>'
    + '<path d="M 80 150 L 70 166" stroke-width="2"/>'
    + '<path d="M 160 150 L 170 166" stroke-width="2"/>'
    + '<path d="M 120 150 L 120 166" stroke-width="2"/>'
    + '<path d="M 76 48 L 164 48 Q 170 48 170 54 L 170 144 Q 170 150 164 150 L 76 150 Q 70 150 70 144 L 70 54 Q 70 48 76 48 Z" stroke-width="3"/>'
    + '<path d="M 83 58 L 157 58 Q 160 58 160 61 L 160 137 Q 160 140 157 140 L 83 140 Q 80 140 80 137 L 80 61 Q 80 58 83 58 Z" stroke-width="2"/>'
    + '</g>'
    + '<g class="asset-empty__highlight" fill="none" stroke="var(--asset-highlight, rgb(255 255 255 / 55%))">'
    + '<path d="M 72.5 62 L 72.5 56 Q 72.5 50.5 78 50.5 L 88 50.5" stroke-width="1.5"/>'
    + '</g></g></svg>';

  var ICON_X = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
  var ICON_CHEV = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>';
  var ICON_PLUS = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';

  /* ======================================================================
     候选形态 CSS —— 只用现有 token
     ====================================================================== */
  var candidateCss = [
    /* ---------- 通用小工具（不是候选，是样品尺寸/面层级的取值） ---------- */
    '.sb-w160{width:160px}.sb-w200{width:200px}.sb-w240{width:240px}.sb-w280{width:280px}.sb-w320{width:320px}',
    '.sb-h120{height:120px}.sb-h160{height:160px}.sb-h200{height:200px}.sb-h240{height:240px}',
    '.sb-rel{position:relative;display:block;width:100%}',

    /* ---------- §4.1 主按钮 ---------- */
    '[data-variant="btn-primary-soft"]{height:auto;min-height:44px;padding:0 var(--sp-5);border:0;border-radius:var(--r-md);background:var(--role-blue);color:var(--ink-on-role);box-shadow:var(--elev-2);font-weight:600}',
    '[data-variant="btn-primary-flat"]{height:auto;min-height:40px;padding:0 var(--sp-4);border:0;border-radius:var(--r-md);background:var(--role-blue);color:var(--ink-on-role);box-shadow:none;font-weight:600}',
    '[data-variant="btn-primary-tall"]{height:auto;min-height:48px;padding:0 var(--sp-6);border:0;border-radius:var(--r-md);background:var(--role-blue);color:var(--ink-on-role);box-shadow:var(--elev-3);font-weight:700;gap:var(--sp-2)}',
    '[data-variant="btn-primary-tall"] svg{width:18px;height:18px;flex:none;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}',

    /* ---------- §4.2 次按钮 ---------- */
    '[data-variant="btn-secondary-paper"]{height:auto;min-height:44px;padding:0 16px;border:1px solid var(--rule-control);border-radius:var(--r-md);background:var(--surface-card);color:var(--ink-strong);box-shadow:var(--elev-1);font-weight:600}',
    '[data-variant="btn-secondary-quiet"]{height:auto;min-height:40px;padding:0 var(--sp-3);border:0;border-radius:var(--r-md);background:transparent;color:var(--ink-muted);font-weight:500}',
    '[data-variant="btn-secondary-sunken"]{height:auto;min-height:44px;padding:0 16px;border:0;border-radius:var(--r-md);background:var(--surface-sunken);color:var(--ink-strong);box-shadow:inset 0 0 0 1px var(--rule-hair);font-weight:600}',

    /* ---------- §4.3 文字按钮 ---------- */
    '[data-variant="btn-text-muted"]{height:auto;min-height:44px;padding:0 var(--sp-3);border:0;border-radius:var(--r-md);background:transparent;color:var(--ink-muted);font-weight:500}',
    '[data-variant="btn-text-arrow"]{height:auto;min-height:44px;padding:0 var(--sp-3);border:0;border-radius:var(--r-md);background:transparent;color:var(--ink-strong);font-weight:500;gap:var(--sp-1)}',
    '[data-variant="btn-text-arrow"]::after{content:"";width:6px;height:6px;flex:none;border-top:1.5px solid currentColor;border-right:1.5px solid currentColor;transform:rotate(45deg)}',
    '[data-variant="btn-text-rule"]{height:auto;min-height:44px;padding:0 2px;border:0;border-radius:0;background:transparent;color:var(--ink-muted);font-weight:500;box-shadow:inset 0 -1px 0 var(--rule-hair)}',

    /* ---------- §4.12 标签 ---------- */
    '[data-variant="tag-soft"]{display:inline-flex;align-items:center;gap:4px;min-height:24px;padding:0 10px;border-radius:var(--r-md);background:var(--veil-hover);color:var(--ink-muted);font-size:var(--fs-label);font-weight:500;white-space:nowrap}',
    '[data-variant="tag-pill"]{display:inline-flex;align-items:center;gap:4px;min-height:22px;padding:0 10px;border-radius:var(--r-pill);background:var(--veil-hover);color:var(--ink-muted);font-size:var(--fs-label);font-weight:500;white-space:nowrap}',
    '[data-variant="tag-role"]{display:inline-flex;align-items:center;gap:6px;min-height:24px;padding:0 10px;border-radius:var(--r-md);background:var(--role-blue-wash);color:var(--role-blue);font-size:var(--fs-label);font-weight:500;white-space:nowrap}',
    '[data-variant="tag-role"]::before{content:"";width:8px;height:8px;border-radius:var(--r-pill);background:var(--role-blue);flex:none}',
    '[data-variant="tag-role-yellow"]{background:var(--role-yellow-soft);color:var(--ink-on-warm)}',
    '[data-variant="tag-role-yellow"]::before{background:var(--role-yellow)}',
    '[data-variant="tag-role-red"]{background:var(--role-red-wash);color:var(--role-red-ink)}',
    '[data-variant="tag-role-red"]::before{background:var(--role-red)}',

    /* ---------- §4.13 徽标 ---------- */
    '[data-variant="badge-neutral"]{display:inline-flex;align-items:center;justify-content:center;min-width:20px;height:20px;padding:0 6px;border-radius:var(--r-round);background:var(--surface-sunken);color:var(--ink-strong);font-size:var(--fs-label);font-weight:700;font-variant-numeric:tabular-nums;line-height:1}',
    '[data-variant="badge-pill"]{display:inline-flex;align-items:center;justify-content:center;min-width:18px;height:18px;padding:0 6px;border-radius:var(--r-pill);background:var(--surface-sunken);color:var(--ink-strong);font-size:var(--fs-label);font-weight:700;font-variant-numeric:tabular-nums;line-height:1}',
    '[data-variant="badge-alert"]{display:inline-flex;align-items:center;justify-content:center;min-width:20px;height:20px;padding:0 6px;border-radius:var(--r-round);background:var(--role-red);color:var(--ink-on-role);font-size:var(--fs-label);font-weight:700;font-variant-numeric:tabular-nums;line-height:1}',

    /* ---------- §4.14 状态圆点（spec 已定稿） ---------- */
    '[data-variant="dot-spec"]{--d:var(--ink-strong);display:inline-block;position:relative;width:10px;height:10px;border-radius:var(--r-pill);background:transparent;box-shadow:inset 0 0 0 2px var(--d);vertical-align:-1px}',
    '[data-variant="dot-spec"][data-geom="filled"]{background:var(--d);box-shadow:none}',
    '[data-variant="dot-spec"][data-geom="half"]{background:transparent;box-shadow:inset -5px 0 0 0 var(--d)}',
    '[data-variant="dot-spec"][data-geom="dash"]{background:transparent;box-shadow:none;border-radius:0;border-top:2px solid var(--d);transform:rotate(45deg) scale(.7)}',
    '[data-variant="dot-spec"][data-geom="cross"]{background:transparent;box-shadow:none;border-radius:0}',
    '[data-variant="dot-spec"][data-geom="cross"]::before,[data-variant="dot-spec"][data-geom="cross"]::after{content:"";position:absolute;inset:50% 0 auto 0;height:2px;background:var(--d);transform:translateY(-50%) rotate(45deg)}',
    '[data-variant="dot-spec"][data-geom="cross"]::after{transform:translateY(-50%) rotate(-45deg)}',
    '[data-variant="dot-spec"][data-geom="check"]{background:transparent;box-shadow:none;border-radius:0}',
    '[data-variant="dot-spec"][data-geom="check"]::before,[data-variant="dot-spec"][data-geom="check"]::after{content:"";position:absolute;left:0;top:0;height:2px;border-radius:1px;background:var(--d);transform-origin:0 50%}',
    '[data-variant="dot-spec"][data-geom="check"]::before{width:4px;left:1px;top:6px;transform:rotate(45deg)}',
    '[data-variant="dot-spec"][data-geom="check"]::after{width:8px;left:3px;top:8px;transform:rotate(-45deg)}',
    '[data-variant="dot-spec"][data-dc="blue"]{--d:var(--role-blue)}',
    '[data-variant="dot-spec"][data-dc="yellow"]{--d:var(--role-yellow)}',
    '[data-variant="dot-spec"][data-dc="red"]{--d:var(--role-red)}',
    '[data-variant="dot-spec"][data-dc="ink"]{--d:var(--ink-strong)}',
    '[data-variant="dot-spec"][data-dc="muted"]{--d:var(--ink-disabled)}',

    /* ---------- §4.15 进度条 ---------- */
    '[data-variant="progress-pill"]{display:block;width:100%;height:8px;border-radius:var(--r-pill);background:var(--veil-active);overflow:hidden}',
    '[data-variant="progress-pill"]>i{display:block;height:100%;width:62%;border-radius:inherit;background:var(--role-blue)}',
    '[data-variant="progress-thin"]{display:block;width:100%;height:4px;border-radius:var(--r-pill);background:var(--veil-active);overflow:hidden}',
    '[data-variant="progress-thin"]>i{display:block;height:100%;width:62%;border-radius:inherit;background:var(--role-blue)}',
    '[data-variant="progress-head"]{display:flex;align-items:center;gap:var(--sp-2);width:100%}',
    '[data-variant="progress-head"]>b{flex:1;height:8px;border-radius:var(--r-pill);background:var(--veil-active);position:relative}',
    '[data-variant="progress-head"]>b>i{display:block;height:100%;width:62%;border-radius:inherit;background:var(--role-blue);position:relative}',
    '[data-variant="progress-head"]>b>i::after{content:"";position:absolute;right:-4px;top:50%;width:12px;height:12px;transform:translateY(-50%);border-radius:var(--r-pill);background:var(--role-blue);box-shadow:0 0 0 2px var(--surface-base)}',
    '[data-variant="progress-head"]>em{font-style:normal;font-size:var(--fs-label);color:var(--ink-muted);font-variant-numeric:tabular-nums}',

    /* ---------- §4.17 题号格（spec 已定稿） ---------- */
    '[data-variant="qcell-spec"]{width:36px;height:36px;min-width:36px;padding:0;border:0;border-radius:var(--r-md);display:inline-flex;align-items:center;justify-content:center;background:var(--surface-card);color:var(--ink-muted);box-shadow:inset 0 0 0 2px var(--ink-disabled);font-family:var(--font-mono);font-size:var(--fs-meta);font-weight:600;font-variant-numeric:tabular-nums}',
    '[data-variant="qcell-spec"][data-q="answered"]{background:var(--role-blue);color:var(--ink-on-role);box-shadow:none}',
    '[data-variant="qcell-spec"][data-q="current"]{background:var(--role-yellow);color:var(--ink-on-warm);box-shadow:none}',
    '[data-variant="qcell-spec"][data-q="correct"]{background:var(--surface-card);color:var(--ink-strong);box-shadow:inset 0 0 0 2px var(--ink-strong);position:relative}',
    '[data-variant="qcell-spec"][data-q="correct"]::before,[data-variant="qcell-spec"][data-q="correct"]::after{content:"";position:absolute;height:2px;border-radius:1px;background:var(--ink-strong);transform-origin:0 50%}',
    '[data-variant="qcell-spec"][data-q="correct"]::before{width:6px;left:21px;top:24px;transform:rotate(45deg)}',
    '[data-variant="qcell-spec"][data-q="correct"]::after{width:12px;left:25px;top:28px;transform:rotate(-45deg)}',
    '[data-variant="qcell-spec"][data-q="wrong"]{background:var(--role-red);color:var(--ink-on-role);box-shadow:none}',
    '[data-variant="qcell-spec"][data-q="stuck"]{background:var(--surface-card);color:var(--role-red);box-shadow:inset 0 0 0 2px var(--role-red)}',

    /* ---------- §4.18 卡片 ---------- */
    '[data-variant="card-spec"]{background:var(--surface-card);border:0;border-radius:var(--r-md);box-shadow:var(--elev-1);padding:var(--sp-5);color:var(--ink-strong);width:100%;max-width:320px}',
    '[data-variant="card-tight"]{background:var(--surface-card);border:0;border-radius:var(--r-md);box-shadow:var(--elev-1);padding:var(--sp-4);color:var(--ink-strong);width:100%;max-width:320px}',
    '[data-variant="card-flat"]{background:var(--surface-card);border:0;border-radius:var(--r-md);box-shadow:inset 0 0 0 1px var(--rule-hair);padding:var(--sp-4);color:var(--ink-strong);width:100%;max-width:320px}',
    '[data-variant="card-spec"] strong,[data-variant="card-tight"] strong,[data-variant="card-flat"] strong{display:block;font-size:var(--fs-sub);font-weight:600}',
    '[data-variant="card-spec"] p,[data-variant="card-tight"] p,[data-variant="card-flat"] p{margin:6px 0 0;font-size:var(--fs-meta);color:var(--ink-muted);line-height:20px}',

    /* ---------- §4.21 空态 ---------- */
    '[data-variant="empty-flat"]{display:flex;flex-direction:column;align-items:center;gap:var(--sp-4);padding:24px;text-align:center;width:100%;max-width:340px}',
    '[data-variant="empty-flat"] .sb-art{display:block;width:120px;height:100px}',
    '[data-variant="empty-flat"] p{margin:0;font-size:var(--fs-body);line-height:22px;color:var(--ink-muted)}',
    '[data-variant="empty-flat"] .sb-act{width:100%;max-width:240px}',
    '[data-variant="empty-card"]{display:flex;flex-direction:column;align-items:center;gap:var(--sp-4);padding:var(--sp-5);text-align:center;width:100%;max-width:340px;background:var(--surface-card);border-radius:var(--r-md);box-shadow:var(--elev-1)}',
    '[data-variant="empty-card"] .sb-art{display:block;width:120px;height:100px}',
    '[data-variant="empty-card"] p{margin:0;font-size:var(--fs-body);line-height:22px;color:var(--ink-muted)}',
    '[data-variant="empty-card"] .sb-act{width:100%;max-width:240px}',
    '[data-variant="empty-rule"]{display:flex;flex-direction:column;align-items:center;gap:var(--sp-4);padding:24px;text-align:center;width:100%;max-width:340px;border-top:1px solid var(--rule-hair);border-bottom:1px solid var(--rule-hair)}',
    '[data-variant="empty-rule"] .sb-art{display:block;width:120px;height:100px}',
    '[data-variant="empty-rule"] p{margin:0;font-size:var(--fs-body);line-height:22px;color:var(--ink-muted)}',
    '[data-variant="empty-rule"] .sb-act{width:100%;max-width:240px}',

    /* ---------- §4.22 骨架屏 ---------- */
    '[data-variant="skeleton-spec"]{position:relative;display:block;overflow:hidden;width:100%;height:16px;border-radius:var(--r-xs);background:var(--skeleton-base)}',
    '[data-variant="skeleton-spec"]::after{content:"";position:absolute;inset:0 auto 0 0;width:32%;background:var(--skeleton-sheen);transform:translateX(-100%);animation:sb-sheen 1.2s var(--ease-standard) infinite}',
    '@keyframes sb-sheen{to{transform:translateX(312%)}}',
    '@media (prefers-reduced-motion: reduce){[data-variant="skeleton-spec"]::after{animation:none;transform:none}}',
    '[data-variant="skeleton-breathe"]{display:block;width:100%;height:16px;border-radius:var(--r-xs);background:var(--skeleton-base);animation:sb-breathe 1.6s var(--ease-standard) infinite}',
    '@keyframes sb-breathe{0%,100%{opacity:1}50%{opacity:.5}}',
    '@media (prefers-reduced-motion: reduce){[data-variant="skeleton-breathe"]{animation:none}}',
    '[data-variant="skeleton-soft"]{display:block;width:100%;height:12px;border-radius:var(--r-xs);background:var(--skeleton-base);opacity:.5}',

    /* ---------- §4.26 时间线 ---------- */
    '[data-variant="timeline-rail"]{list-style:none;margin:0;padding:0;display:block;width:100%;max-width:320px}',
    '[data-variant="timeline-rail"]>li{position:relative;display:grid;grid-template-columns:12px 1fr;gap:var(--sp-3);padding-bottom:var(--sp-3)}',
    '[data-variant="timeline-rail"]>li::before{content:"";position:absolute;left:5px;top:14px;bottom:-4px;width:2px;background:var(--rule-structure)}',
    '[data-variant="timeline-rail"]>li:last-child::before{display:none}',
    '[data-variant="timeline-rail"]>li>i{width:12px;height:12px;margin-top:4px;border-radius:var(--r-pill);background:var(--role-blue)}',
    '[data-variant="timeline-rail"]>li[data-t="current"]>i{width:14px;height:14px;margin-left:-1px;background:transparent;box-shadow:inset 0 0 0 3px var(--role-blue), var(--elev-1)}',
    '[data-variant="timeline-rail"]>li[data-t="failed"]>i{background:var(--role-red)}',
    '[data-variant="timeline-rail"]>li>div{background:var(--surface-card);border-radius:var(--r-md);padding:12px 16px;box-shadow:var(--elev-1);font-size:var(--fs-meta);color:var(--ink-strong);line-height:20px}',
    '[data-variant="timeline-flat"]{list-style:none;margin:0;padding:0;display:block;width:100%;max-width:320px}',
    '[data-variant="timeline-flat"]>li{display:grid;grid-template-columns:12px 1fr;gap:var(--sp-3);align-items:start;padding:var(--sp-2) 0;border-top:1px solid var(--rule-hair)}',
    '[data-variant="timeline-flat"]>li:first-child{border-top:0}',
    '[data-variant="timeline-flat"]>li>i{width:10px;height:10px;margin-top:5px;border-radius:var(--r-pill);background:var(--role-blue)}',
    '[data-variant="timeline-flat"]>li[data-t="done"]>i{background:var(--ink-strong)}',
    '[data-variant="timeline-flat"]>li>span{font-size:var(--fs-meta);color:var(--ink-strong);line-height:20px}',
    '[data-variant="timeline-flat"]>li>span em{display:block;font-style:normal;font-size:var(--fs-label);color:var(--ink-faint)}',
    '[data-variant="timeline-num"]{list-style:none;margin:0;padding:0;display:block;width:100%;max-width:320px}',
    '[data-variant="timeline-num"]>li{position:relative;display:grid;grid-template-columns:20px 1fr;gap:var(--sp-2);padding:8px 0;border-top:1px solid var(--rule-hair)}',
    '[data-variant="timeline-num"]>li:first-child{border-top:0}',
    '[data-variant="timeline-num"]>li>i{width:18px;height:18px;border-radius:var(--r-round);border:1px solid var(--ink-strong);display:inline-flex;align-items:center;justify-content:center;font-size:var(--fs-label);font-weight:700;color:var(--ink-strong);font-style:normal}',
    '[data-variant="timeline-num"]>li[data-t="running"]>i{border-color:var(--role-blue);color:var(--role-blue)}',
    '[data-variant="timeline-num"]>li[data-t="failed"]>i{border-color:var(--role-red);color:var(--role-red)}',
    '[data-variant="timeline-num"]>li>span{font-size:var(--fs-meta);color:var(--ink-strong);line-height:20px}',
    '[data-variant="timeline-num"]>li>span em{display:block;font-style:normal;font-size:var(--fs-label);color:var(--ink-faint)}',

    /* ---------- §4.28 Tab ---------- */
    '[data-variant="tab-spec"]{display:flex;gap:4px;border-bottom:0}',
    '[data-variant="tab-spec"]>a{position:relative;display:inline-flex;align-items:center;gap:var(--sp-2);min-height:48px;padding:0 16px;border-radius:var(--r-md);color:var(--ink-muted);text-decoration:none;font-size:var(--fs-body);font-weight:500}',
    '[data-variant="tab-spec"]>a[data-on="true"]{color:var(--role-blue);font-weight:600}',
    '[data-variant="tab-spec"]>a[data-on="true"]::after{content:"";position:absolute;left:12px;right:12px;bottom:0;height:3px;border-radius:3px;background:var(--role-blue)}',
    '[data-variant="tab-seg"]{display:inline-flex;gap:4px;padding:4px;border-radius:var(--r-md);background:var(--surface-base)}',
    '[data-variant="tab-seg"]>a{display:inline-flex;align-items:center;min-height:36px;padding:0 14px;border-radius:var(--r-xs);color:var(--ink-muted);text-decoration:none;font-size:var(--fs-meta);font-weight:500}',
    '[data-variant="tab-seg"]>a[data-on="true"]{background:var(--surface-raised);color:var(--ink-strong);font-weight:600;box-shadow:var(--elev-1)}',
    '[data-variant="tab-underline"]{display:flex;gap:var(--sp-4);border-bottom:1px solid var(--rule-hair)}',
    '[data-variant="tab-underline"]>a{position:relative;display:inline-flex;align-items:center;min-height:44px;padding:0 2px;color:var(--ink-muted);text-decoration:none;font-size:var(--fs-body)}',
    '[data-variant="tab-underline"]>a[data-on="true"]{color:var(--role-blue);font-weight:600}',
    '[data-variant="tab-underline"]>a[data-on="true"]::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:2px;background:var(--role-blue)}',

    /* ---------- §4.4 图标按钮 ---------- */
    '[data-variant="iconbtn-spec"]{position:relative;width:40px;height:40px;min-height:44px;padding:0;display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:var(--r-md);background:transparent;color:var(--ink-muted)}',
    '[data-variant="iconbtn-spec"]::before{content:"";position:absolute;inset:-2px;min-width:44px;min-height:44px}',
    '[data-variant="iconbtn-spec"] svg{width:20px;height:20px;display:block;fill:none;stroke:currentColor;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round}',
    '[data-variant="iconbtn-mini"]{width:32px;height:32px;padding:0;display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:var(--r-xs);background:transparent;color:var(--ink-muted)}',
    '[data-variant="iconbtn-mini"] svg{width:16px;height:16px;display:block;fill:none;stroke:currentColor;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round}',
    '[data-variant="iconbtn-round"]{width:40px;height:40px;padding:0;display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:var(--r-round);background:var(--surface-sunken);color:var(--ink-strong)}',
    '[data-variant="iconbtn-round"] svg{width:20px;height:20px;display:block;fill:none;stroke:currentColor;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round}',

    /* ---------- §4.5 输入框 ---------- */
    '[data-variant="input-spec"]{width:100%;min-height:44px;padding:0 14px;border:1px solid var(--rule-control);border-radius:var(--r-md);background:var(--surface-card);color:var(--ink-strong);font-family:var(--font-ui);font-size:var(--fs-body);line-height:1.4}',
    '[data-variant="input-sunken"]{width:100%;min-height:44px;padding:0 14px;border:0;border-radius:var(--r-md);background:var(--surface-sunken);color:var(--ink-strong);box-shadow:inset 0 0 0 1px var(--rule-hair);font-family:var(--font-ui);font-size:var(--fs-body)}',
    '[data-variant="input-rule"]{width:100%;min-height:44px;padding:0 2px;border:0;border-radius:0;background:transparent;color:var(--ink-strong);box-shadow:inset 0 -1px 0 var(--rule-control);font-family:var(--font-ui);font-size:var(--fs-body)}',

    /* ---------- §4.6 文本域 ---------- */
    '[data-variant="textarea-spec"]{width:100%;min-height:96px;padding:12px 14px;border:1px solid var(--rule-control);border-radius:var(--r-md);background:var(--surface-card);color:var(--ink-strong);resize:vertical;font-family:var(--font-ui);font-size:var(--fs-body);line-height:1.6}',
    '[data-variant="textarea-sunken"]{width:100%;min-height:96px;padding:12px 14px;border:0;border-radius:var(--r-md);background:var(--surface-sunken);color:var(--ink-strong);resize:vertical;box-shadow:inset 0 0 0 1px var(--rule-hair);font-family:var(--font-ui);font-size:var(--fs-body);line-height:1.6}',
    '[data-variant="textarea-rule"]{width:100%;min-height:96px;padding:12px 2px;border:0;border-radius:0;background:transparent;color:var(--ink-strong);resize:vertical;box-shadow:inset 0 -1px 0 var(--rule-control);font-family:var(--font-ui);font-size:var(--fs-body);line-height:1.6}',

    /* ---------- §4.7 自绘下拉 ---------- */
    '[data-variant="select-spec"]{position:relative;display:block;width:220px}',
    '[data-variant="select-spec"]>b{display:flex;align-items:center;justify-content:space-between;gap:var(--sp-2);width:100%;min-height:44px;padding:0 14px;border:1px solid var(--rule-control);border-radius:var(--r-md);background:var(--surface-card);color:var(--ink-strong);font-family:var(--font-ui);font-size:var(--fs-body);font-weight:400}',
    '[data-variant="select-spec"]>b::after{content:"";width:8px;height:8px;flex:none;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg) translate(-2px,-2px)}',
    '[data-variant="select-spec"]>u{position:absolute;z-index:2;top:calc(100% + 6px);left:0;min-width:100%;margin:0;padding:6px;list-style:none;text-decoration:none;border-radius:var(--r-md);background:var(--surface-raised);box-shadow:var(--elev-3)}',
    '[data-variant="select-spec"]>u>li{display:flex;align-items:center;justify-content:space-between;gap:var(--sp-2);min-height:40px;padding:0 12px;border-radius:var(--r-xs);color:var(--ink-strong);font-size:var(--fs-body)}',
    '[data-variant="select-spec"]>u>li[data-on="true"]{background:var(--role-blue-wash);color:var(--role-blue)}',
    '[data-variant="select-spec"]>u>li[data-on="true"]::after{content:"";width:8px;height:8px;border-radius:var(--r-pill);background:var(--role-blue);flex:none}',
    '[data-variant="select-sunken"]{display:inline-flex;align-items:center;justify-content:space-between;gap:var(--sp-2);width:220px;min-height:44px;padding:0 14px;border:0;border-radius:var(--r-md);background:var(--surface-sunken);color:var(--ink-strong);box-shadow:inset 0 0 0 1px var(--rule-hair);font-family:var(--font-ui);font-size:var(--fs-body)}',
    '[data-variant="select-rule"]{display:inline-flex;align-items:center;justify-content:space-between;gap:var(--sp-2);width:220px;min-height:44px;padding:0 2px;border:0;border-radius:0;background:transparent;color:var(--ink-strong);box-shadow:inset 0 -1px 0 var(--rule-control);font-family:var(--font-ui);font-size:var(--fs-body)}',

    /* ---------- §4.8 复选框 ---------- */
    '[data-variant="check-spec"]{display:inline-flex;align-items:center;gap:var(--sp-2);min-height:44px;cursor:pointer}',
    '[data-variant="check-spec"]>i{width:20px;height:20px;flex:none;border-radius:var(--r-xs);border:1.5px solid var(--ink-disabled);background:var(--surface-card);display:inline-flex;align-items:center;justify-content:center}',
    '[data-variant="check-spec"]>i::after{content:"";width:10px;height:5px;margin-top:-2px;border-left:2.5px solid var(--ink-on-role);border-bottom:2.5px solid var(--ink-on-role);transform:rotate(-45deg);opacity:0}',
    '[data-variant="check-spec"][data-on="true"]>i{background:var(--role-blue);border-color:var(--role-blue)}',
    '[data-variant="check-spec"][data-on="true"]>i::after{opacity:1}',
    '[data-variant="check-spec"]>span{font-size:var(--fs-body);color:var(--ink-strong)}',
    '[data-variant="check-row"]{display:inline-flex;align-items:center;gap:var(--sp-2);min-height:44px;padding:0 var(--sp-4);border-radius:var(--r-md);cursor:pointer;background:transparent;font-size:var(--fs-body);color:var(--ink-strong)}',
    '[data-variant="check-row"][data-on="true"]{background:var(--role-blue-wash);color:var(--role-blue)}',
    '[data-variant="check-row"]>i{width:18px;height:18px;flex:none;border-radius:var(--r-xs);border:1.5px solid var(--ink-disabled);background:var(--surface-card)}',
    '[data-variant="check-row"][data-on="true"]>i{background:var(--role-blue);border-color:var(--role-blue)}',
    '[data-variant="check-inline"]{display:inline-flex;align-items:center;gap:var(--sp-2);min-height:44px;cursor:pointer}',
    '[data-variant="check-inline"]>i{width:18px;height:18px;flex:none;border-radius:var(--r-xs);border:1.5px solid var(--ink-disabled);background:var(--surface-card)}',
    '[data-variant="check-inline"][data-on="true"]>i{background:var(--role-blue);border-color:var(--role-blue)}',
    '[data-variant="check-inline"]>span{font-size:var(--fs-body);color:var(--ink-strong)}',

    /* ---------- §4.9 单选 ---------- */
    '[data-variant="radio-spec"]{display:inline-flex;align-items:center;gap:var(--sp-2);min-height:44px;cursor:pointer}',
    '[data-variant="radio-spec"]>i{width:20px;height:20px;flex:none;border-radius:var(--r-round);border:1.5px solid var(--ink-disabled);background:var(--surface-card);display:inline-flex;align-items:center;justify-content:center}',
    '[data-variant="radio-spec"]>i::after{content:"";width:6px;height:6px;border-radius:var(--r-pill);background:var(--ink-on-role);opacity:0}',
    '[data-variant="radio-spec"][data-on="true"]>i{background:var(--role-blue);border-color:var(--role-blue)}',
    '[data-variant="radio-spec"][data-on="true"]>i::after{opacity:1}',
    '[data-variant="radio-spec"]>span{font-size:var(--fs-body);color:var(--ink-strong)}',
    '[data-variant="radio-row"]{display:flex;align-items:center;gap:var(--sp-3);width:100%;max-width:260px;min-height:44px;padding:var(--sp-2) var(--sp-3);border-radius:var(--r-md);cursor:pointer;font-size:var(--fs-body);color:var(--ink-strong)}',
    '[data-variant="radio-row"][data-on="true"]{background:var(--role-blue-wash);color:var(--role-blue)}',
    '[data-variant="radio-row"]>i{width:18px;height:18px;flex:none;border-radius:var(--r-round);border:1.5px solid var(--ink-disabled);background:var(--surface-card)}',
    '[data-variant="radio-row"][data-on="true"]>i{border-color:var(--role-blue);box-shadow:inset 0 0 0 4px var(--role-blue)}',
    '[data-variant="radio-underline"]{display:inline-flex;align-items:center;gap:var(--sp-2);min-height:44px;cursor:pointer;font-size:var(--fs-body);color:var(--ink-muted)}',
    '[data-variant="radio-underline"]>i{width:14px;height:14px;flex:none;border-radius:var(--r-round);border:1.5px solid var(--ink-disabled)}',
    '[data-variant="radio-underline"][data-on="true"]{color:var(--role-blue);box-shadow:inset 0 -2px 0 var(--role-blue)}',
    '[data-variant="radio-underline"][data-on="true"]>i{border-color:var(--role-blue);background:var(--role-blue)}',

    /* ---------- §4.10 开关 ---------- */
    '[data-variant="switch-spec"]{position:relative;display:inline-flex;align-items:center;min-height:44px;cursor:pointer}',
    '[data-variant="switch-spec"]>i{width:44px;height:26px;flex:none;border-radius:var(--r-pill);background:var(--ink-disabled);padding:3px;display:block}',
    '[data-variant="switch-spec"]>i>b{display:block;width:20px;height:20px;border-radius:var(--r-round);background:var(--surface-card);box-shadow:var(--elev-1)}',
    '[data-variant="switch-spec"][data-on="true"]>i{background:var(--role-blue)}',
    '[data-variant="switch-spec"][data-on="true"]>i>b{transform:translateX(18px)}',
    '[data-variant="switch-mini"]{display:inline-flex;align-items:center;min-height:32px;cursor:pointer}',
    '[data-variant="switch-mini"]>i{width:32px;height:18px;flex:none;border-radius:var(--r-pill);background:var(--ink-disabled);padding:2px;display:block}',
    '[data-variant="switch-mini"]>i>b{display:block;width:14px;height:14px;border-radius:var(--r-round);background:var(--surface-card)}',
    '[data-variant="switch-mini"][data-on="true"]>i{background:var(--role-blue)}',
    '[data-variant="switch-mini"][data-on="true"]>i>b{transform:translateX(14px)}',
    '[data-variant="switch-text"]{display:inline-flex;align-items:center;gap:var(--sp-2);min-height:44px;cursor:pointer;font-size:var(--fs-body);color:var(--ink-muted)}',
    '[data-variant="switch-text"]>i{font-style:normal;padding:2px 10px;border-radius:var(--r-pill);background:var(--surface-sunken);color:var(--ink-faint);font-size:var(--fs-label)}',
    '[data-variant="switch-text"][data-on="true"]>i{background:var(--role-blue-wash);color:var(--role-blue)}',

    /* ---------- §4.11 分段控件 ---------- */
    '[data-variant="seg-spec"]{display:inline-flex;gap:4px;padding:4px;border-radius:var(--r-md);background:var(--surface-base)}',
    '[data-variant="seg-spec"]>b{display:inline-flex;align-items:center;justify-content:center;min-height:36px;padding:0 14px;border-radius:var(--r-xs);background:transparent;color:var(--ink-muted);font-family:var(--font-ui);font-size:var(--fs-meta);font-weight:500}',
    '[data-variant="seg-spec"]>b[data-on="true"]{background:var(--surface-raised);color:var(--ink-strong);font-weight:600;box-shadow:var(--elev-1)}',
    '[data-variant="seg-rule"]{display:inline-flex;gap:var(--sp-4);border-bottom:1px solid var(--rule-hair)}',
    '[data-variant="seg-rule"]>b{position:relative;display:inline-flex;align-items:center;min-height:44px;padding:0 2px;color:var(--ink-muted);font-family:var(--font-ui);font-size:var(--fs-body);font-weight:400}',
    '[data-variant="seg-rule"]>b[data-on="true"]{color:var(--role-blue);font-weight:600}',
    '[data-variant="seg-rule"]>b[data-on="true"]::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:2px;background:var(--role-blue)}',
    '[data-variant="seg-pill"]{display:inline-flex;gap:2px;padding:3px;border-radius:var(--r-pill);background:var(--surface-sunken);box-shadow:inset 0 0 0 1px var(--rule-hair)}',
    '[data-variant="seg-pill"]>b{display:inline-flex;align-items:center;justify-content:center;min-height:34px;padding:0 16px;border-radius:var(--r-pill);color:var(--ink-muted);font-family:var(--font-ui);font-size:var(--fs-meta);font-weight:400}',
    '[data-variant="seg-pill"]>b[data-on="true"]{background:var(--surface-card);color:var(--ink-strong);font-weight:600;box-shadow:var(--elev-1)}',

    /* ---------- §4.19 纸面层级 ---------- */
    '[data-variant="surface-spec"] .sb-lv{padding:var(--sp-3);border-radius:var(--r-md);font-size:var(--fs-label);color:var(--ink-muted)}',
    '[data-variant="surface-spec"] .sb-lv[data-lv="0"]{background:var(--surface-base)}',
    '[data-variant="surface-spec"] .sb-lv[data-lv="1"]{background:var(--surface-card);box-shadow:var(--elev-1)}',
    '[data-variant="surface-spec"] .sb-lv[data-lv="2"]{background:var(--surface-raised);box-shadow:var(--elev-3)}',
    '[data-variant="surface-spec"] .sb-lv[data-lv="3"]{background:var(--surface-sunken);box-shadow:inset 0 0 0 1px var(--rule-hair)}',
    '[data-variant="surface-three"] .sb-lv{padding:var(--sp-3);border-radius:var(--r-md);font-size:var(--fs-label);color:var(--ink-muted)}',
    '[data-variant="surface-three"] .sb-lv[data-lv="0"]{background:var(--surface-base)}',
    '[data-variant="surface-three"] .sb-lv[data-lv="1"]{background:var(--surface-card);box-shadow:var(--elev-1)}',
    '[data-variant="surface-three"] .sb-lv[data-lv="2"]{background:var(--surface-raised);box-shadow:var(--elev-3)}',
    '[data-variant="surface-hair"] .sb-lv{padding:var(--sp-3);border-radius:var(--r-md);font-size:var(--fs-label);color:var(--ink-muted);background:var(--surface-card);box-shadow:inset 0 0 0 1px var(--rule-hair)}',
    '[data-variant="surface-hair"] .sb-lv[data-lv="0"]{background:var(--surface-base);box-shadow:none}',
    '[data-variant="surface-hair"] .sb-lv[data-lv="2"]{background:var(--surface-card);box-shadow:inset 0 0 0 1px var(--rule-control)}',

    /* ---------- §4.20 沉底块 ---------- */
    '[data-variant="sunken-spec"],[data-variant="sunken-bare"],[data-variant="sunken-rail"]{width:100%;max-width:280px;background:var(--surface-sunken);color:var(--ink-strong);border-radius:var(--r-md);padding:var(--sp-5)}',
    '[data-variant="sunken-spec"]{box-shadow:inset 0 0 0 1px var(--rule-hair)}',
    '[data-variant="sunken-rail"]{border-left:4px solid var(--role-yellow)}',
    '[data-variant="sunken-spec"]>b,[data-variant="sunken-bare"]>b,[data-variant="sunken-rail"]>b{display:block;font-family:var(--font-ui);font-size:var(--fs-hero);font-weight:700;line-height:1;font-variant-numeric:tabular-nums}',
    '[data-variant="sunken-spec"]>span,[data-variant="sunken-bare"]>span,[data-variant="sunken-rail"]>span{display:block;margin-top:var(--sp-2);font-size:var(--fs-body);color:var(--ink-body);line-height:22px}',

    /* ---------- §4.23 吐司 ---------- */
    '[data-variant="toast-spec"]{position:absolute;top:12px;right:12px;z-index:3;display:flex;align-items:flex-start;gap:var(--sp-2);min-width:200px;max-width:280px;padding:12px 16px;border-radius:var(--r-md);background:var(--surface-raised);color:var(--ink-strong);box-shadow:var(--elev-3);font-family:var(--font-ui);font-size:var(--fs-meta);line-height:20px}',
    '[data-variant="toast-spec"]::before{content:"";width:10px;height:10px;margin-top:5px;flex:none;border-radius:var(--r-pill);background:var(--role-blue)}',
    '[data-variant="toast-spec"][data-kind="err"]::before{background:var(--role-red)}',
    '[data-variant="toast-bottom"]{position:absolute;left:50%;bottom:12px;transform:translateX(-50%);z-index:3;display:flex;align-items:center;gap:var(--sp-2);padding:10px 18px;border-radius:var(--r-pill);background:var(--surface-raised);color:var(--ink-strong);box-shadow:var(--elev-3);font-family:var(--font-ui);font-size:var(--fs-meta)}',
    '[data-variant="toast-bottom"]::before{content:"";width:10px;height:10px;flex:none;border-radius:var(--r-pill);background:var(--role-blue)}',
    '[data-variant="toast-inline"]{display:flex;align-items:center;gap:var(--sp-2);width:100%;padding:10px 14px;border-radius:var(--r-md);background:var(--surface-sunken);color:var(--ink-strong);box-shadow:inset 0 0 0 1px var(--rule-hair);font-family:var(--font-ui);font-size:var(--fs-meta)}',
    '[data-variant="toast-inline"]::before{content:"";width:10px;height:10px;flex:none;border-radius:var(--r-pill);background:var(--role-blue)}',

    /* ---------- §4.27 折叠段 ---------- */
    '[data-variant="disc-spec"]{display:block;width:100%;max-width:320px}',
    '[data-variant="disc-spec"]>b{display:flex;align-items:center;gap:var(--sp-2);width:100%;min-height:44px;padding:0 16px;border:0;border-radius:var(--r-md);background:transparent;color:var(--ink-strong);font-family:var(--font-ui);font-size:var(--fs-body);font-weight:500;text-align:left}',
    '[data-variant="disc-spec"]>b::after{content:"";width:8px;height:8px;margin-left:auto;flex:none;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg) translate(-2px,-2px)}',
    '[data-variant="disc-spec"]>u{display:block;text-decoration:none;padding:0 16px 16px;color:var(--ink-muted);font-size:var(--fs-meta);line-height:20px}',
    '[data-variant="disc-rail"]{display:block;width:100%;max-width:320px;border-left:2px solid var(--rule-structure);padding-left:var(--sp-4)}',
    '[data-variant="disc-rail"]>b{display:flex;align-items:center;gap:var(--sp-2);width:100%;min-height:44px;padding:0;border:0;background:transparent;color:var(--ink-strong);font-family:var(--font-ui);font-size:var(--fs-body);font-weight:600;text-align:left}',
    '[data-variant="disc-rail"]>u{display:block;text-decoration:none;padding-bottom:var(--sp-3);color:var(--ink-muted);font-size:var(--fs-meta);line-height:20px}',
    '[data-variant="disc-accordion"]{display:block;width:100%;max-width:320px;border-radius:var(--r-md);background:var(--surface-card);box-shadow:var(--elev-1);overflow:hidden}',
    '[data-variant="disc-accordion"]>b{display:flex;align-items:center;gap:var(--sp-2);width:100%;min-height:48px;padding:0 16px;border:0;background:transparent;color:var(--ink-strong);font-family:var(--font-ui);font-size:var(--fs-body);font-weight:600;text-align:left}',
    '[data-variant="disc-accordion"]>u{display:block;text-decoration:none;padding:0 16px 16px;color:var(--ink-muted);font-size:var(--fs-meta);line-height:20px}',

    /* ---------- §4.16 分段进度条（产品里还没有） ---------- */
    '[data-variant="steps-spec"]{display:flex;gap:4px;width:100%}',
    '[data-variant="steps-spec"]>i{flex:1;min-width:12px;height:8px;border-radius:var(--r-pill);background:transparent;box-shadow:inset 0 0 0 2px var(--veil-active)}',
    '[data-variant="steps-spec"]>i[data-s="done"]{background:var(--role-yellow);box-shadow:none}',
    '[data-variant="steps-spec"]>i[data-s="cur"]{background:var(--veil-active);box-shadow:inset -50% 0 0 0 var(--role-yellow)}',
    '[data-variant="steps-spec"]>i[data-s="bad"]{background:var(--role-red);box-shadow:none}',
    '[data-variant="steps-num"]{display:flex;gap:var(--sp-2);width:100%;align-items:center}',
    '[data-variant="steps-num"]>i{width:22px;height:22px;flex:none;border-radius:var(--r-round);display:inline-flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:var(--fs-label);font-weight:700;font-style:normal;background:var(--surface-sunken);color:var(--ink-faint);box-shadow:inset 0 0 0 1px var(--rule-hair)}',
    '[data-variant="steps-num"]>i[data-s="done"]{background:var(--role-yellow);color:var(--ink-on-warm);box-shadow:none}',
    '[data-variant="steps-num"]>i[data-s="cur"]{background:var(--surface-card);color:var(--role-blue);box-shadow:inset 0 0 0 2px var(--role-blue)}',
    '[data-variant="steps-num"]>em{flex:1;height:2px;background:var(--veil-active);font-style:normal}',
    '[data-variant="steps-flag"]{display:flex;gap:var(--sp-1);width:100%;align-items:flex-end;height:28px}',
    '[data-variant="steps-flag"]>i{flex:1;height:10px;border-radius:2px 2px 0 0;background:var(--veil-active)}',
    '[data-variant="steps-flag"]>i[data-s="done"]{height:20px;background:var(--role-yellow)}',
    '[data-variant="steps-flag"]>i[data-s="cur"]{height:28px;background:var(--role-blue)}',

    /* ---------- §4.24 对话框（产品里还没有） ---------- */
    '[data-variant="dialog-spec"]{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:var(--veil-modal)}',
    '[data-variant="dialog-spec"]>div{width:min(320px,86%);background:var(--surface-raised);color:var(--ink-strong);border-radius:var(--r-md);box-shadow:var(--elev-3);padding:24px}',
    '[data-variant="dialog-spec"] h4{margin:0 0 12px;font-family:var(--font-ui);font-size:var(--fs-title);font-weight:700}',
    '[data-variant="dialog-spec"] p{margin:0;color:var(--ink-muted);font-size:var(--fs-body);line-height:22px}',
    '[data-variant="dialog-spec"]>div>div{display:flex;justify-content:flex-end;gap:var(--sp-2);margin-top:24px}',
    '[data-variant="dialog-drawer"]{position:absolute;inset:auto 0 0 0;padding:24px;background:var(--veil-modal)}',
    '[data-variant="dialog-drawer"]>div{background:var(--surface-raised);border-radius:var(--r-lg) var(--r-lg) 0 0;padding:20px 24px;box-shadow:var(--elev-3);color:var(--ink-strong)}',
    '[data-variant="dialog-drawer"] h4{margin:0 0 8px;font-family:var(--font-ui);font-size:var(--fs-title);font-weight:700}',
    '[data-variant="dialog-drawer"] p{margin:0;color:var(--ink-muted);font-size:var(--fs-body)}',
    '[data-variant="dialog-drawer"]>div>div{display:flex;justify-content:flex-end;gap:var(--sp-2);margin-top:16px}',
    '[data-variant="dialog-inline"]{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}',
    '[data-variant="dialog-inline"]>div{width:min(280px,86%);background:var(--surface-card);border-radius:var(--r-md);box-shadow:var(--elev-2);padding:var(--sp-4);color:var(--ink-strong);border-left:4px solid var(--role-yellow)}',
    '[data-variant="dialog-inline"] h4{margin:0 0 6px;font-family:var(--font-ui);font-size:var(--fs-sub);font-weight:700}',
    '[data-variant="dialog-inline"] p{margin:0;color:var(--ink-muted);font-size:var(--fs-meta);line-height:20px}',

    /* ---------- §4.25 工具调用卡（产品里还没有） ---------- */
    '[data-variant="tool-spec"]{display:block;width:100%;max-width:320px;background:var(--surface-card);border-radius:var(--r-md);box-shadow:var(--elev-1);overflow:hidden}',
    '[data-variant="tool-spec"]>b{display:flex;align-items:center;gap:var(--sp-2);width:100%;min-height:44px;padding:12px 14px;border:0;background:transparent;color:var(--ink-strong);font-family:var(--font-ui);font-size:var(--fs-meta);text-align:left}',
    '[data-variant="tool-spec"]>b::before{content:"";width:10px;height:10px;flex:none;border-radius:var(--r-pill);background:var(--role-blue)}',
    '[data-variant="tool-spec"]>b code{font-family:var(--font-mono);font-weight:600}',
    '[data-variant="tool-spec"]>b em{margin-left:auto;font-style:normal;font-family:var(--font-mono);font-size:var(--fs-label);color:var(--ink-faint)}',
    '[data-variant="tool-spec"]>u{display:block;text-decoration:none;padding:0 14px 14px;color:var(--ink-muted);font-size:var(--fs-meta);line-height:20px}',
    '[data-variant="tool-line"]{display:flex;align-items:center;gap:var(--sp-2);width:100%;max-width:320px;padding:8px 10px;border-radius:var(--r-md);background:var(--surface-base);font-family:var(--font-ui);font-size:var(--fs-meta);color:var(--ink-strong)}',
    '[data-variant="tool-line"]::before{content:"";width:8px;height:8px;flex:none;border-radius:var(--r-pill);background:var(--role-blue)}',
    '[data-variant="tool-line"] code{font-family:var(--font-mono)}',
    '[data-variant="tool-line"] em{margin-left:auto;font-style:normal;color:var(--ink-faint);font-size:var(--fs-label)}',
    '[data-variant="tool-rail"]{display:block;width:100%;max-width:320px;padding:var(--sp-3) var(--sp-4);border-left:2px solid var(--rule-structure);border-radius:0 var(--r-md) var(--r-md) 0;font-size:var(--fs-meta);color:var(--ink-strong)}',
    '[data-variant="tool-rail"] code{font-family:var(--font-mono);font-weight:600}',
    '[data-variant="tool-rail"] em{display:block;font-style:normal;color:var(--ink-faint);font-size:var(--fs-label);margin-top:2px}'
  ].join("\n");

  /* ======================================================================
     目录
     ====================================================================== */
  var components = [
    /* ---------------- A 段：产品里已有独立形态 ---------------- */
    {
      key: "btn-primary", sec: "§4.1", name: "按钮 · 主按钮", status: "ok",
      spec: ".lk-btn / .lk-btn--primary",
      product: "button.primary", productWhere: "workbench.css:939-945",
      inventory: "产品里用语义单词 <code>primary</code>，spec 命名零命中。现状是蓝底 + 1px 近黑描边 + 2px 2px 0 硬阴影 + 18px 胶囊圆角 + 高 36px —— 与 spec §4.1（无描边 / 柔影 / 12px / 44px）四种都不同。",
      current: {
        where: "workbench.css:939",
        html: '<button class="primary" type="button">开始练习</button>',
        note: "现状：蓝底 + <b>近黑描边</b> + <b>硬阴影</b> + 18px 胶囊圆角 + 高 36px。视觉上偏「贴纸」，与 spec 的柔影语言不符。"
      },
      variants: [
        { id: "btn-primary-soft", name: "A · 柔影实心",
          html: '<button data-variant="btn-primary-soft" type="button">开始练习</button>',
          note: "去掉黑描边与硬阴影，换 12px 圆角 + <code>--elev-2</code> 柔影、高 44px —— 直接落到 spec §4.1 的形态，存在感靠柔影而不是靠黑边。" },
        { id: "btn-primary-flat", name: "B · 无影平底",
          html: '<button data-variant="btn-primary-flat" type="button">开始练习</button>',
          note: "同样去掉描边，但**不要阴影**、高度收到 40px —— 更安静，适合主按钮旁边已经有其它视觉重物时。" },
        { id: "btn-primary-tall", name: "C · 高身带图标",
          html: '<button data-variant="btn-primary-tall" type="button">' + ICON_PLUS + '开始练习</button>',
          note: "48px 高 + 图标 + 更重的柔影 —— 唯一主角，适合空态 CTA、试卷开始这类「就它一个动作」的场景。" }
      ]
    },
    {
      key: "btn-secondary", sec: "§4.2", name: "按钮 · 次按钮", status: "ok",
      spec: ".lk-btn--secondary",
      product: "button.outline", productWhere: "workbench.css:947-948",
      inventory: "spec 命名零命中。现状是透明底 + 1px <code>--rule-control</code> 边 + 18px 胶囊圆角 + 无阴影；spec §4.2 要的是卡面底 + <code>--elev-1</code> 柔影 + 12px 圆角。",
      current: {
        where: "workbench.css:947",
        html: '<button class="outline" type="button">取消</button>',
        note: "现状：<b>透明底</b> + 1px 控件边 + 胶囊圆角 + 无阴影 —— 在卡面上几乎看不见自己是个按钮。"
      },
      variants: [
        { id: "btn-secondary-paper", name: "A · 纸面次按钮",
          html: '<button data-variant="btn-secondary-paper" type="button">取消</button>',
          note: "卡面底 + 1px 控件边 + 柔影 + 12px —— spec §4.2 的形态，和主按钮并排时次按钮明显「退半步」但不消失。" },
        { id: "btn-secondary-quiet", name: "B · 裸文字次按钮",
          html: '<button data-variant="btn-secondary-quiet" type="button">取消</button>',
          note: "完全去掉边框与底，只留中等墨色文字 —— 比现状更轻，但和 §4.3 文字按钮的区分度会变小。" },
        { id: "btn-secondary-sunken", name: "C · 沉底次按钮",
          html: '<button data-variant="btn-secondary-sunken" type="button">取消</button>',
          note: "沉底面 + 内发丝线 —— 读成「压下去」而不是「浮起来」，适合「撤销 / 回退」这类往回走的动作。" }
      ]
    },
    {
      key: "btn-text", sec: "§4.3", name: "按钮 · 文字按钮", status: "ok",
      spec: ".lk-btn--text",
      product: "button.ghost", productWhere: "workbench.css:946（仅 :hover 一条）",
      inventory: "spec 命名零命中。现状 <code>ghost</code> 只有一条 hover 规则，其余全靠 <code>button</code> 基类 —— 字体色、圆角、内距都不是它自己的。",
      current: {
        where: "workbench.css:946",
        html: '<button class="ghost" type="button">更多</button>',
        note: "现状：透明底 + hover 洗底，其余靠基类；墨色与圆角都不是它自己定的。"
      },
      variants: [
        { id: "btn-text-muted", name: "A · 中性文字",
          html: '<button data-variant="btn-text-muted" type="button">更多</button>',
          note: "透明底 + <code>--ink-muted</code> + 12px 圆角 + 500 字重 —— spec §4.3 的形态，最低强调。" },
        { id: "btn-text-arrow", name: "B · 带箭头",
          html: '<button data-variant="btn-text-arrow" type="button">更多</button>',
          note: "文字 + 一个 CSS 画的右箭头 —— 更像「通往别处」，可点性更强，适合「查看全部 / 展开」。" },
        { id: "btn-text-rule", name: "C · 带底线",
          html: '<button data-variant="btn-text-rule" type="button">更多</button>',
          note: "底部一根发丝线 —— 像书里的链接，安静但仍看得出可点，适合放在正文末尾。" }
      ]
    },
    {
      key: "tag", sec: "§4.12", name: "标签（Tag / Chip）", status: "ok",
      spec: ".lk-tag",
      product: ".agent-context-chip / .chip（仅图谱） / .record-verdict", productWhere: "agent-ui.css:35-44 · workbench.css:3514 · workbench.css:2448",
      inventory: "spec 命名零命中。产品里同一个角色有<b>三套</b>实现，圆角（胶囊 / 3px / 胶囊）、字号（11 / 9 / 12）、边界（描边 / 内发丝线）全不一致。现状列取 <code>.agent-context-chip</code>（唯一在正式界面里的）。",
      current: {
        where: "agent-ui.css:35",
        html: '<span class="agent-context-chip">高等数学</span>',
        note: "现状：999px 胶囊 + <b>1px 描边</b> + 11px 字 —— 描边让它读起来像一个可点的东西，而 spec 规定标签是静态的。"
      },
      variants: [
        { id: "tag-soft", name: "A · 柔底标签",
          html: '<span data-variant="tag-soft">高等数学</span>',
          note: "柔底 + 12px 圆角 + 12px 字、<b>没有描边</b> —— spec §4.12 的形态，明确读成「不可点的分类标记」。" },
        { id: "tag-pill", name: "B · 药丸标签",
          html: '<span data-variant="tag-pill">高等数学</span>',
          note: "保留胶囊轮廓但去掉描边、比 A 再小一号 —— 介于标签和徽标之间，适合密集列表里的属性标记。" },
        { id: "tag-role", name: "C · 角色色标签",
          html: '<span data-variant="tag-role">待复习</span><span data-variant="tag-role tag-role-yellow">连对 5</span><span data-variant="tag-role tag-role-red">卡住</span>',
          note: "角色色洗底 + 左侧状态点 —— 承载语义（spec §4.12 的蓝 / 黄 / 红三变体），一眼能分状态，代价是要守「同卡不超过 2 个」的配额。" }
      ]
    },
    {
      key: "badge", sec: "§4.13", name: "徽标（Badge）", status: "ok",
      spec: ".lk-badge / .lk-badge--alert",
      product: ".count-badge", productWhere: "workbench.css:831-841",
      inventory: "spec 命名零命中。现状 <code>.count-badge</code> = 18px 最小宽 + 胶囊 + 卡面底 + 淡墨 + 11px 字；spec §4.13 要 20px / 圆 / 沉底底 / 浓墨 / 12px·700 / tabular-nums。产品里<b>没有「红底阻塞计数」这一档</b>。",
      current: {
        where: "workbench.css:831",
        html: '<span class="count-badge">3</span><span class="count-badge">12</span>',
        note: "现状：卡面底 + 淡墨 + 11px —— 在卡面上几乎看不见，是个「小数字」而不是「徽标」。"
      },
      variants: [
        { id: "badge-neutral", name: "A · 沉底计数",
          html: '<span data-variant="badge-neutral">3</span><span data-variant="badge-neutral">12</span>',
          note: "沉底底 + 浓墨 + 12px·700 + 等宽数字 —— spec §4.13 的中性档，在任何底色上都读得出。" },
        { id: "badge-pill", name: "B · 胶囊计数",
          html: '<span data-variant="badge-pill">3</span><span data-variant="badge-pill">12</span>',
          note: "胶囊轮廓但用沉底实心 —— 比现状强，又不像实心圆那么「闹钟」；适合侧栏标题上的待办数。" },
        { id: "badge-alert", name: "C · 红底阻塞计数",
          html: '<span data-variant="badge-alert">3</span>',
          note: "红底 + 反白墨 —— spec §4.13 的阻塞档，<b>产品里目前完全没有</b>；用之前要先确认「阻塞数」这个概念真的存在。" }
      ]
    },
    {
      key: "dot", sec: "§4.14", name: "状态圆点（Status dot）", status: "ok",
      spec: ".lk-dot + 14 个变体",
      product: ".lk-dot（只实现 6 个变体）", productWhere: "workbench.css:1112-1165",
      inventory: "spec 命名<b>唯一真正落地</b>的一条，但只落地了 6 个变体（<code>--red/--yellow/--ink</code> + <code>--cross/--dash/--check</code>），缺的 8 个里包括 <code>--filled</code>（<code>pages.py:102</code> 已经用了但没规则）。",
      current: {
        where: "workbench.css:1112",
        html: '<span class="lk-dot lk-dot--red lk-dot--cross" aria-hidden="true"></span><span class="lk-dot lk-dot--yellow lk-dot--dash" aria-hidden="true"></span><span class="lk-dot lk-dot--ink lk-dot--check" aria-hidden="true"></span>',
        note: "现状：12px 实心圆 + 挖空几何（叉 / 杠 / 勾）—— 三态在灰度下也能分辨；缺的是<b>未开始 / 进行中 / 空心环</b>这几档。"
      },
      variants: [
        { id: "dot-spec", name: "A · spec 全几何集（已定稿，仅供确认）",
          html: '<span data-variant="dot-spec" data-dc="muted" data-geom="ring" title="未开始"></span>'
            + '<span data-variant="dot-spec" data-dc="blue" data-geom="half" title="进行中"></span>'
            + '<span data-variant="dot-spec" data-dc="blue" data-geom="filled" title="已完成"></span>'
            + '<span data-variant="dot-spec" data-dc="yellow" data-geom="dash" title="到期"></span>'
            + '<span data-variant="dot-spec" data-dc="red" data-geom="cross" title="阻塞"></span>'
            + '<span data-variant="dot-spec" data-dc="ink" data-geom="check" title="判定正确"></span>',
          note: "spec 已定稿（§3.6 的几何集 + §4.14 的映射），这里只补齐现状缺的 <b>ring / half / filled</b> 三档并把尺寸收到 10px —— <b>形态不再给替代方案</b>。" }
      ]
    },
    {
      key: "progress", sec: "§4.15", name: "进度条（Progress bar）", status: "ok",
      spec: ".lk-progress / .lk-progress__fill",
      product: ".record-run-progress（另有 .record-rating-track / .record-verdict-dist-track）", productWhere: "workbench.css:2424-2428 · 2390-2394 · 2407-2411",
      inventory: "spec 的 <code>.lk-progress</code> <b>轨道没有 CSS</b>（只有 <code>__fill</code> 子规则），完成页那条进度带渲染不出来；真正在跑的是 <code>.record-run-progress</code> 一族：8px 直角条、沉底轨道、纯色填充。",
      current: {
        where: "workbench.css:2424",
        html: '<div class="sb-w280"><div class="record-run-progress"><span style="width:62%"></span></div></div>',
        note: "现状：8px <b>直角</b>条 + 沉底轨道 + 纯色填充 —— 与 spec §4.15 的胶囊轨道差一个圆角，轨道底色也不同。"
      },
      variants: [
        { id: "progress-pill", name: "A · 胶囊进度",
          html: '<div data-variant="progress-pill"><i></i></div>',
          note: "8px 胶囊 + <code>--veil-active</code> 轨道 + 蓝填充 —— spec §4.15 的形态，与题号格、状态点的圆角语言一致。" },
        { id: "progress-thin", name: "B · 细进度",
          html: '<div data-variant="progress-thin"><i></i></div>',
          note: "收到 4px —— 更省纵向空间，适合放在卡片标题行下面当副信息。" },
        { id: "progress-head", name: "C · 带端点与数字",
          html: '<div data-variant="progress-head"><b><i></i></b><em>62%</em></div>',
          note: "轨道末端加一个实心圆点 + 右侧百分比 —— 进度「有落点」，存在感最强；代价是不能再纯图形地扫读。" }
      ]
    },
    {
      key: "qcell", sec: "§4.17", name: "题号格（Question cell）", status: "ok",
      spec: ".lk-qcell / .lk-qgrid",
      product: ".paper-dot + .state-* / .is-current", productWhere: "workbench.css:3652-3674",
      inventory: "spec §4.17 自己就写了「现状 <code>.paper-dot</code>」，两边对得上；但形态差得远：现状 34px <b>圆</b> + 1px 描边，当前题用 <code>outline: 3px</code>；spec 要 36px <b>方</b> + 12px 圆角 + 黄实心 + scale(1.06)。",
      current: {
        where: "workbench.css:3652",
        html: '<button class="paper-dot" type="button">1</button><button class="paper-dot state-filled" type="button">2</button><button class="paper-dot state-correct" type="button">3</button><button class="paper-dot state-wrong" type="button">4</button><button class="paper-dot is-current" type="button">5</button>',
        note: "现状：34px 圆 + 1px 墨边；已答=黄、锁定=蓝洗底、正确=墨环+勾、错误=红洗底、当前=蓝 outline。<b>当前题用 outline 而不是底色</b>，与 spec 的黄实心不同。"
      },
      variants: [
        { id: "qcell-spec", name: "A · spec 形态（已定稿，仅供确认）",
          html: '<button data-variant="qcell-spec" type="button">1</button>'
            + '<button data-variant="qcell-spec" data-q="answered" type="button">2</button>'
            + '<button data-variant="qcell-spec" data-q="correct" type="button">3</button>'
            + '<button data-variant="qcell-spec" data-q="wrong" type="button">4</button>'
            + '<button data-variant="qcell-spec" data-q="stuck" type="button">5</button>'
            + '<button data-variant="qcell-spec" data-q="current" type="button">6</button>',
          note: "spec §4.17 的规则（36px 方 + 12px 圆角 + 未答/已答/当前/正确/错误/卡住六态）已唯一确定，<b>形态不再给替代方案</b>；这里只把它画出来供确认。" }
      ]
    },
    {
      key: "card", sec: "§4.18", name: "卡片（Card）", status: "ok",
      spec: ".lk-card",
      product: ".card + .lk-card（两份同规格规则）", productWhere: "workbench.css:1019-1026 与 1034-1040",
      inventory: "spec 类名真的落地了，但 CSS 注释自己写着「与 <code>.card</code> 基类同规格」—— 两个类名一份规则。更麻烦的是覆写散落：<code>.practice-set-card</code> 加黄顶条、<code>.practice-question-card</code> 与 <code>.agent-artifact-card</code> 各加蓝左边条，卡片语言已经分叉。",
      current: {
        where: "workbench.css:1019",
        html: '<div class="card lk-card"><strong>知识点分组</strong><p>导数与微分 · 12 个知识点 · 3 个待复习</p></div>',
        note: "现状：12px 圆角 + <code>--elev-1</code> 柔影 + 18px 留白、无描边 —— 与 spec §4.18 只差<b>留白（18 vs 24）</b>和 hover 反馈。"
      },
      variants: [
        { id: "card-spec", name: "A · spec 留白",
          html: '<div data-variant="card-spec"><strong>知识点分组</strong><p>导数与微分 · 12 个知识点 · 3 个待复习</p></div>',
          note: "留白升到 24px（<code>--sp-5</code>）—— spec §4.18 的形态；卡片更「松」，长文本的卡片最吃这一档。" },
        { id: "card-tight", name: "B · 紧凑卡",
          html: '<div data-variant="card-tight"><strong>知识点分组</strong><p>导数与微分 · 12 个知识点 · 3 个待复习</p></div>',
          note: "留白收到 16px —— 同一屏能多放一张；记录中心那种一列长流最需要这一档。" },
        { id: "card-flat", name: "C · 无影卡",
          html: '<div data-variant="card-flat"><strong>知识点分组</strong><p>导数与微分 · 12 个知识点 · 3 个待复习</p></div>',
          note: "柔影换成 1px 内发丝线 —— 纸面感更强（和沉底块同语言），但离群卡片不再「浮起来」。" }
      ]
    },
    {
      key: "empty", sec: "§4.21", name: "空态（Empty state）", status: "ok",
      spec: ".lk-empty / .lk-empty__art / __text / __action",
      product: ".empty-state + .lk-empty", productWhere: "workbench.css:1222 · 1234-1255",
      inventory: "spec 类名真的落地（三个子元素也落地）。现状与 spec 有两处差：插画 <b>180px</b>（spec 要 144px）；<b>面是沉底块</b>—— spec §4.21 原文没规定空态用什么面，这是实现先行的选择，需主会话裁决。",
      current: {
        where: "workbench.css:1234",
        html: '<div class="empty-state lk-empty"><span class="lk-empty__art" aria-hidden="true">' + ART + '</span><p class="lk-empty__text">这里还没有内容</p><span class="lk-empty__action"><button class="primary" type="button">开始练习</button></span></div>',
        note: "现状：<b>沉底面</b> + 内发丝线 + 180px 插画 + 一句 + 满宽主按钮 —— 形态已经很接近 spec §4.21，差别在面与插画尺寸。"
      },
      variants: [
        { id: "empty-flat", name: "A · 无面空态",
          html: '<div data-variant="empty-flat"><span class="sb-art" aria-hidden="true">' + ART + '</span><p>这里还没有内容</p><span class="sb-act"><button class="primary" type="button">开始练习</button></span></div>',
          note: "去掉沉底面，只留插画 + 一句 + 满宽按钮 —— 最轻；插画缩小到 120px，版面更紧凑。" },
        { id: "empty-card", name: "B · 卡面空态",
          html: '<div data-variant="empty-card"><span class="sb-art" aria-hidden="true">' + ART + '</span><p>这里还没有内容</p><span class="sb-act"><button class="primary" type="button">开始练习</button></span></div>',
          note: "改用卡面 + 柔影 —— 空态与其它内容<b>同级</b>，读成「这是一张还没填内容的卡」，而不是「这里是块空地」。" },
        { id: "empty-rule", name: "C · 上下分线空态",
          html: '<div data-variant="empty-rule"><span class="sb-art" aria-hidden="true">' + ART + '</span><p>这里还没有内容</p><span class="sb-act"><button class="primary" type="button">开始练习</button></span></div>',
          note: "上下各一根发丝线、不给面 —— 用「分隔」代替「容器」，适合夹在两段内容之间的空位。" }
      ]
    },
    {
      key: "skeleton", sec: "§4.22", name: "骨架屏（Skeleton）", status: "ok",
      spec: ".lk-skeleton / --text / --block / --avatar",
      product: ".lk-skeleton（只有基类）", productWhere: "workbench.css:2773-2787",
      inventory: "spec 类名落地了，但<b>只有基类</b>：<code>--text / --block / --avatar</code> 三个尺寸变体都没写，<code>pages.py:345</code> 那个 <code>lk-skeleton--text</code> <b>没有高度，渲染不出来</b>。另外现状微光用 <code>linear-gradient</code>，与 spec 明文「不用渐变」冲突。",
      current: {
        where: "workbench.css:2773",
        html: '<span class="lk-skeleton lk-skeleton--text" aria-hidden="true"></span><span class="lk-skeleton lk-skeleton--text" aria-hidden="true"></span>',
        note: "现状：<b>渲染为空</b> —— <code>.lk-skeleton</code> 只给了底色，没给高度；即使给了高度，微光也是一条 <code>linear-gradient</code>（spec 全局禁渐变）。"
      },
      variants: [
        { id: "skeleton-spec", name: "A · spec 实色微光",
          html: '<span data-variant="skeleton-spec" aria-hidden="true"></span><span data-variant="skeleton-spec" aria-hidden="true"></span>',
          note: "32% 宽的<b>实色块</b>横向平移（无渐变）+ 高度锁定 16px —— spec §4.22 的形态，加载完成时不跳版。" },
        { id: "skeleton-breathe", name: "B · 呼吸式",
          html: '<span data-variant="skeleton-breathe" aria-hidden="true"></span><span data-variant="skeleton-breathe" aria-hidden="true"></span>',
          note: "不做横扫、只让底色整体明暗呼吸 —— 动效更安静，窄栏里不会晃眼；同样支持 reduced-motion 直切。" },
        { id: "skeleton-soft", name: "C · 低对比静块",
          html: '<span data-variant="skeleton-soft" aria-hidden="true"></span><span data-variant="skeleton-soft" aria-hidden="true"></span>',
          note: "不做任何动效，只用更低的对比度表示「这里会有内容」—— 最克制，适合刷新不频繁的页面。" }
      ]
    },
    {
      key: "timeline", sec: "§4.26", name: "时间线节点（Timeline node）", status: "ok",
      spec: ".lk-timeline / .lk-timeline__item / .lk-timeline__dot",
      product: ".agent-milestone（agent-ui.css） + .ai-plan-step（workbench.css）", productWhere: "agent-ui.css:292-336 · workbench.css:1394-1426",
      inventory: "spec 命名零命中，而且<b>产品里同一角色有两套几何</b>：Agent 里程碑是 18px <b>圆环带数字</b>，计划步骤是 9px <b>方块</b>（蓝空心 / 蓝脉冲 / 黄 / 红）—— 视觉上像两个产品。",
      current: {
        where: "agent-ui.css:292",
        html: '<div class="agent-milestone"><span class="agent-milestone-marker">1</span><div class="agent-milestone-body"><strong>读取题面</strong><span class="agent-milestone-state">已完成</span></div></div>'
          + '<div class="agent-milestone is-running"><span class="agent-milestone-marker">2</span><div class="agent-milestone-body"><strong>检索知识点</strong><span class="agent-milestone-state">进行中</span></div></div>',
        note: "现状（<code>.agent-milestone</code>）：20px 列 + <b>18px 圆环</b> + 发丝线分隔 —— 编号感强。另有一套 <code>.ai-plan-step</code> 是 9px 方块，<b>两套同时出现在产品里</b>。"
      },
      variants: [
        { id: "timeline-rail", name: "A · 竖轨时间线",
          html: '<ul data-variant="timeline-rail"><li><i></i><div>读取题面</div></li><li data-t="current"><i></i><div>检索知识点（当前）</div></li><li data-t="failed"><i></i><div>写入卡片 · 失败</div></li></ul>',
          note: "2px 竖线串起 12px 点 + 内容卡 —— spec §4.26 的形态；「步骤之间的先后」读得最清楚。" },
        { id: "timeline-flat", name: "B · 分隔线时间线",
          html: '<ul data-variant="timeline-flat"><li><i></i><span>读取题面<em>已完成</em></span></li><li data-t="done"><i></i><span>检索知识点<em>已完成</em></span></li><li><i></i><span>写入卡片<em>进行中</em></span></li></ul>',
          note: "不画竖线、只用发丝线分隔 + 小圆点 —— 更安静、更省横向空间，代价是「先后」要靠上下顺序读。" },
        { id: "timeline-num", name: "C · 编号时间线",
          html: '<ul data-variant="timeline-num"><li><i>1</i><span>读取题面<em>已完成</em></span></li><li data-t="running"><i>2</i><span>检索知识点<em>进行中</em></span></li><li data-t="failed"><i>3</i><span>写入卡片<em>失败</em></span></li></ul>',
          note: "现状 <code>.agent-milestone</code> 的加强版：编号圆环 + 发丝线，去掉双列网格 —— <b>两套现状收敛到这一套</b>的最省事方案。" }
      ]
    },
    {
      key: "tab", sec: "§4.28", name: "Tab（标签页）", status: "ok",
      spec: ".lk-tablist / .lk-tab",
      product: ".record-tabs + .record-tab（另图谱页 .seg）", productWhere: "workbench.css:2217-2229",
      inventory: "spec 命名零命中。现状是 <code>&lt;a&gt;</code> 标签页 + 8px 11px 内距 + 底部 3px 蓝指示条 + 容器底部 1px 分隔线；spec §4.28 要 48px 高 + 16px 内距 + 12px 圆角 hover 底。<b>换实现要留意：现状是链接（可右键新开），spec 示例是按钮。</b>",
      current: {
        where: "workbench.css:2217",
        html: '<nav class="record-tabs"><a class="record-tab active" href="#">概览</a><a class="record-tab" href="#">作答明细</a><a class="record-tab" href="#">错题</a><a class="record-tab" href="#">复习负荷</a></nav>',
        note: "现状：<code>&lt;a&gt;</code> + 3px 蓝下边框 + 容器底部发丝线 —— 能用，但点击区只有一行文字那么高。"
      },
      variants: [
        { id: "tab-spec", name: "A · spec 标签页",
          html: '<nav data-variant="tab-spec"><a href="#" data-on="true">概览</a><a href="#">作答明细</a><a href="#">错题</a><a href="#">复习负荷</a></nav>',
          note: "48px 高 + 16px 内距 + 12px 圆角（hover 才见底）+ 3px 蓝指示条 —— spec §4.28 的形态，命中区达标。" },
        { id: "tab-seg", name: "B · 分段式标签页",
          html: '<nav data-variant="tab-seg"><a href="#" data-on="true">概览</a><a href="#">作答明细</a><a href="#">错题</a><a href="#">复习负荷</a></nav>',
          note: "用分段控件的形态 —— 和 §4.11 共用一套语言，切换的「互斥」感最强；代价是它就不像链接了。" },
        { id: "tab-underline", name: "C · 细线标签页",
          html: '<nav data-variant="tab-underline"><a href="#" data-on="true">概览</a><a href="#">作答明细</a><a href="#">错题</a><a href="#">复习负荷</a></nav>',
          note: "44px 高 + 2px 细指示条 —— 比现状更轻，但比现状多了一点纵向余量；适合放在窄栏顶部。" }
      ]
    },

    /* ---------------- B 段：产品里还没有的形态 ---------------- */
    {
      key: "iconbtn", sec: "§4.4", name: "按钮 · 图标按钮", status: "gap",
      spec: ".lk-iconbtn",
      product: "button.icon-only（CSS 零命中） · button.icon-btn（仅图谱，冻结）", productWhere: "pages.py:213,215,254,267,1035",
      inventory: "5 处产品用法<b>完全借用 <code>button</code> 基类</b> —— 图标按钮和文字按钮现在长得一模一样。spec 命名零命中。",
      current: {
        where: "pages.py:267（真实 markup：图标按钮里放的是字符 ☰ ◌ − × ‹，不是 SVG）",
        html: '<button class="ghost sm icon-only" type="button" aria-label="关闭工件预览">×</button>',
        note: "现状：借用了文字按钮的底子（28px 高 + 胶囊圆角 + 文字内距），图标是<b>字符</b>不是 SVG —— <b>图标被拉变形了</b>，且没有 40×40 的视觉尺寸与 44px 命中区。"
      },
      variants: [
        { id: "iconbtn-spec", name: "A · spec 图标按钮",
          html: '<button data-variant="iconbtn-spec" type="button" aria-label="关闭">' + ICON_X + '</button>',
          note: "40×40 + 12px 圆角 + hover 洗底 + 伪元素把命中区补到 44px —— spec §4.4 的形态。" },
        { id: "iconbtn-mini", name: "B · 迷你图标按钮",
          html: '<button data-variant="iconbtn-mini" type="button" aria-label="关闭">' + ICON_X + '</button>',
          note: "32×32 + 6px 圆角、无底 —— 适合工具条里成排出现的小图标；命中区要另想办法补。" },
        { id: "iconbtn-round", name: "C · 圆形图标按钮",
          html: '<button data-variant="iconbtn-round" type="button" aria-label="关闭">' + ICON_X + '</button>',
          note: "40×40 圆形 + 沉底面 —— 存在感最强，适合「悬浮动作」这种要抓眼球的单点动作。" }
      ]
    },
    {
      key: "input", sec: "§4.5", name: "输入框（Input）", status: "gap",
      spec: ".lk-input",
      product: "元素选择器 textarea, input[type=text]…（无类名）", productWhere: "workbench.css:962-975",
      inventory: "产品里<b>没有类名</b>，靠标签选择器统一定型：现状高 32px、圆角 10px、内距 6px 10px；spec §4.5 要 44px / <code>--r-md</code> / <code>0 14px</code> / 聚焦蓝环。另外 <code>input:focus { outline: none }</code> 与 spec A-1 冲突。",
      current: {
        where: "workbench.css:962",
        html: '<input type="text" placeholder="请输入…" aria-label="输入框现状">',
        note: "现状：32px 高、10px 圆角、6px 10px 内距 —— 在 44px 命中区的规则下明显偏矮；聚焦只换边框色、<b>没有焦点环</b>。"
      },
      variants: [
        { id: "input-spec", name: "A · spec 输入框",
          html: '<input data-variant="input-spec" type="text" placeholder="请输入…" aria-label="输入框候选 A">',
          note: "44px 高 + 12px 圆角 + <code>0 14px</code> 内距 + 聚焦蓝边与 3px 蓝洗底光晕 —— spec §4.5 的形态。" },
        { id: "input-sunken", name: "B · 沉底输入框",
          html: '<input data-variant="input-sunken" type="text" placeholder="请输入…" aria-label="输入框候选 B">',
          note: "沉底面 + 内发丝线、无描边 —— 与沉底块同一语言，表单区更安静；但聚焦时「我在被编辑」要靠底色变化来表达。" },
        { id: "input-rule", name: "C · 底线输入框",
          html: '<input data-variant="input-rule" type="text" placeholder="请输入…" aria-label="输入框候选 C">',
          note: "只有一根底线 —— 最轻，适合筛选条里的行内输入；可点性最弱，不适合当主输入。" }
      ]
    },
    {
      key: "textarea", sec: "§4.6", name: "文本域（Textarea）", status: "gap",
      spec: ".lk-textarea / .lk-textarea--composer",
      product: "元素选择器（与输入框同一条规则）", productWhere: "workbench.css:962",
      inventory: "文本域与输入框<b>共用一条规则</b>，两者没有分开定型；spec §4.6 的「最小高 96px / 行高 1.6 / <code>resize: vertical</code>」都没落地。",
      current: {
        where: "workbench.css:962",
        html: '<textarea rows="3" placeholder="写下你的思路…" aria-label="文本域现状"></textarea>',
        note: "现状：与输入框同一套（10px 圆角、6px 10px 内距、14px/1.4）—— <b>多行文本没有自己的行高与最小高度</b>。"
      },
      variants: [
        { id: "textarea-spec", name: "A · spec 文本域",
          html: '<textarea data-variant="textarea-spec" rows="3" placeholder="写下你的思路…" aria-label="文本域候选 A"></textarea>',
          note: "最小高 96px + 行高 1.6 + 12px 圆角 + 竖向可拉 —— spec §4.6 的形态，长文本读起来最舒服。" },
        { id: "textarea-sunken", name: "B · 沉底文本域",
          html: '<textarea data-variant="textarea-sunken" rows="3" placeholder="写下你的思路…" aria-label="文本域候选 B"></textarea>',
          note: "沉底面 + 内发丝线 —— 和输入框 B 配成一套，表单区整体更安静。" },
        { id: "textarea-rule", name: "C · 底线文本域",
          html: '<textarea data-variant="textarea-rule" rows="3" placeholder="写下你的思路…" aria-label="文本域候选 C"></textarea>',
          note: "只有底线、无框 —— 最像「纸上手写」，但多行文本没有边界，滚动时容易失去位置感。" }
      ]
    },
    {
      key: "select", sec: "§4.7", name: "自绘下拉（Select / Combobox）", status: "gap",
      spec: ".lk-select / __trigger / __panel / __option",
      product: "原生 <select>（8 处）", productWhere: "workbench.css:874-885",
      inventory: "<b>自绘 combobox 在产品里完全不存在</b>，8 处全是原生 <code>&lt;select&gt;</code>（spec §5.2 计划的替换尚未开始）。原生控件的圆角、内距、命中区、键盘行为全由浏览器决定。",
      current: {
        where: "workbench.css:874",
        html: '<select aria-label="下拉现状"><option>第三章 函数与导数</option><option>第四章 积分</option></select>',
        note: "现状：原生控件，34px 高、<code>--r-xs</code> 圆角、聚焦换边框色但 <b>outline: none</b>；在两套主题下都是浏览器原生外观。"
      },
      variants: [
        { id: "select-spec", name: "A · spec 自绘下拉",
          html: '<div data-variant="select-spec"><b>第三章 函数与导数</b><ul><li>第三章 函数与导数</li><li data-on="true">第四章 积分</li><li>第五章 级数</li></ul></div>',
          note: "触发器 + 浮起面板 + 选中项蓝洗底 + 行尾蓝点 —— spec §4.7 的形态；自绘后要另配键盘与 ARIA，并保留 hidden input 承载载荷。" },
        { id: "select-sunken", name: "B · 沉底下拉",
          html: '<div data-variant="select-sunken">第三章 函数与导数</div>',
          note: "触发器用沉底面（只画触发器，面板省略）—— 与沉底输入框配成一套，表单区语言统一。" },
        { id: "select-rule", name: "C · 底下拉",
          html: '<div data-variant="select-rule">第三章 函数与导数</div>',
          note: "只有底线 —— 最轻，但下拉是「要展开的面板」的控件，存在感太弱会让人以为不能点。" }
      ]
    },
    {
      key: "checkbox", sec: "§4.8", name: "复选框（Checkbox）", status: "gap",
      spec: ".lk-check / .lk-check__box / .lk-check__row",
      product: "原生 <input type=checkbox>", productWhere: "practice-flow.js:968,1652 · paper-practice.js:797",
      inventory: "<b>完全用原生控件</b>，浏览器默认外观（系统蓝方框），没有任何专属 CSS；唯一一处调色是 <code>.chapter-lens-toggle input { accent-color }</code>。spec §4.8 要求的 20px 方框 / 6px 圆角 / 蓝底白勾 / 44px 命中区<b>一条都没有</b>。",
      current: {
        where: "practice-flow.js:968",
        html: '<label><input type="checkbox" checked> 关联题目</label><label><input type="checkbox"> 附加提示</label>',
        note: "现状：<b>浏览器默认外观</b>（Windows 上是系统蓝方框）—— 与产品的暖纸语言完全不在一个世界里，尺寸也不受控。"
      },
      variants: [
        { id: "check-spec", name: "A · spec 复选框",
          html: '<span data-variant="check-spec" data-on="true"><i></i><span>关联题目</span></span><span data-variant="check-spec"><i></i><span>附加提示</span></span>',
          note: "20px 方框 + 6px 圆角 + 蓝底白勾 + 整行 44px 命中区 —— spec §4.8 的形态，勾是几何不是颜色。" },
        { id: "check-row", name: "B · 整行选中",
          html: '<span data-variant="check-row" data-on="true"><i></i>关联题目</span><span data-variant="check-row"><i></i>附加提示</span>',
          note: "选中时整行铺一层蓝洗底 —— 批量筛选这类「一次选多个」的场景里，一眼能看出选中了哪几行。" },
        { id: "check-inline", name: "C · 行内复选框",
          html: '<span data-variant="check-inline" data-on="true"><i></i>关联题目</span><span data-variant="check-inline"><i></i>附加提示</span>',
          note: "18px 小方框 + 文字，结构与现状一致 —— <b>迁移成本最低</b>的一档：只换方框外观，不动 DOM 结构。" }
      ]
    },
    {
      key: "radio", sec: "§4.9", name: "单选（Radio）", status: "gap",
      spec: ".lk-radio / .lk-radio__dot / .lk-choicegroup",
      product: "原生 <input type=radio>", productWhere: "practice-flow.js:968 · paper-practice.js:797",
      inventory: "纯原生、零专属样式。另外 spec §4.9 要求的 <code>fieldset</code> + <code>legend</code> 分组结构<b>产品里也没有</b> —— 现在是裸 input 平铺。",
      current: {
        where: "practice-flow.js:968",
        html: '<label><input type="radio" name="sb-cur-radio" checked> 选项 A</label><label><input type="radio" name="sb-cur-radio"> 选项 B</label>',
        note: "现状：<b>浏览器默认外观</b>（系统圆点）—— 与复选框一样完全不在暖纸语言里。"
      },
      variants: [
        { id: "radio-spec", name: "A · spec 单选",
          html: '<span data-variant="radio-spec" data-on="true"><i></i><span>选项 A</span></span><span data-variant="radio-spec"><i></i><span>选项 B</span></span>',
          note: "20px 圆 + 蓝底白内核点 + 整行 44px —— spec §4.9 的形态；几何上和复选框明确区分开。" },
        { id: "radio-row", name: "B · 整行卡选中",
          html: '<span data-variant="radio-row" data-on="true"><i></i>选项 A</span><span data-variant="radio-row"><i></i>选项 B</span>',
          note: "选中时整行蓝洗底 + 圆环内填 —— 选项是「卡片」而不是「控件」，适合选项本身带说明文字的场景。" },
        { id: "radio-underline", name: "C · 文字下划单选",
          html: '<span data-variant="radio-underline" data-on="true"><i></i>选项 A</span><span data-variant="radio-underline"><i></i>选项 B</span>',
          note: "选中项本身带蓝色下划线 —— 最轻，适合放在设置页的一两行之间。" }
      ]
    },
    {
      key: "switch", sec: "§4.10", name: "开关（Switch）", status: "gap",
      spec: ".lk-switch / .lk-switch__track / .lk-switch__thumb",
      product: ".lk-switch（markup 在，CSS 零命中）", productWhere: "pages.py:862-865, 880-891",
      inventory: "典型「markup 在、样式没接上」：<code>.lk-switch</code> 在 <code>pages.py</code> 有 9 处命中，<b>在 workbench.css 里 grep 命中数为 0</b> ⇒ 设置页那三个开关<b>渲染出来是空的</b>。产品里真正生效的开关是 <code>.chapter-lens-toggle</code>（原生 checkbox 染色）。",
      current: {
        where: "pages.py:862",
        html: '<label class="lk-switch"><input type="checkbox" class="visually-hidden" checked><span class="lk-switch__track" aria-hidden="true"><span class="lk-switch__thumb"></span></span></label>',
        note: "现状：<b>渲染不出来</b> —— 轨道与滑块都没有任何 CSS，页面上只剩一个（视觉隐藏的）原生勾选框。"
      },
      variants: [
        { id: "switch-spec", name: "A · spec 开关",
          html: '<span data-variant="switch-spec" data-on="true"><i><b></b></i></span><span data-variant="switch-spec"><i><b></b></i></span>',
          note: "44×26 胶囊轨道 + 20px 滑块 + 开态蓝 —— spec §4.10 的形态；轨道本体 26px，命中区由整行 44px 承担。" },
        { id: "switch-mini", name: "B · 迷你开关",
          html: '<span data-variant="switch-mini" data-on="true"><i><b></b></i></span><span data-variant="switch-mini"><i><b></b></i></span>',
          note: "32×18 —— 适合放在表格行里的一列；命中区要另补。" },
        { id: "switch-text", name: "C · 文字开关",
          html: '<span data-variant="switch-text" data-on="true"><i>开</i></span><span data-variant="switch-text"><i>关</i></span>',
          note: "用「开 / 关」两枚药丸代替滑块 —— 状态<b>零歧义</b>，不依赖位置与颜色的解读；代价是占横向空间。" }
      ]
    },
    {
      key: "seg", sec: "§4.11", name: "分段控件（Segmented control）", status: "gap",
      spec: ".lk-seg / .lk-seg__item / --semantic / --scroll",
      product: ".lk-seg（markup 在，CSS 零命中） · .seg（仅图谱，冻结） · button.rate", productWhere: "pages.py:870-876 · workbench.css:3340-3350 · 949-959",
      inventory: "<code>.lk-seg</code> / <code>.lk-seg__item</code> 在 <code>pages.py</code> 有 3 处，<b>CSS 零命中</b> ⇒ 设置页那组「衬线 / 无衬线」渲染成两个没有样式的 label。产品里另有两套分段：图谱页 <code>.seg</code>（冻结项）与 <code>button.rate</code>（1–5 自评胶囊组）。",
      current: {
        where: "pages.py:870",
        html: '<span class="lk-seg" role="radiogroup"><label class="lk-seg__item"><input type="radio" name="sb-cur-face" checked>衬线</label><label class="lk-seg__item"><input type="radio" name="sb-cur-face">无衬线</label></span>',
        note: "现状：<b>渲染不出来</b> —— 没有胶囊槽、没有选中态，两个选项就是两段裸文字 + 浏览器默认圆点。"
      },
      variants: [
        { id: "seg-spec", name: "A · spec 分段控件",
          html: '<span data-variant="seg-spec"><b data-on="true">衬线</b><b>无衬线</b></span>',
          note: "沉底槽 + 4px 间隙 + 选中项抬成卡面并带柔影 —— spec §4.11 的形态；选中靠「浮起来」而不是颜色。" },
        { id: "seg-rule", name: "B · 下划线分段",
          html: '<span data-variant="seg-rule"><b data-on="true">衬线</b><b>无衬线</b></span>',
          note: "只有一条底线和一条蓝指示 —— 最轻，适合放在工具条或卡片头部。" },
        { id: "seg-pill", name: "C · 药丸分段",
          html: '<span data-variant="seg-pill"><b data-on="true">衬线</b><b>无衬线</b></span>',
          note: "整组胶囊、选中项是白色药丸 —— 比 spec 的方槽更「软」，和胶囊按钮容易混。" }
      ]
    },
    {
      key: "surface", sec: "§4.19", name: "纸面层级（Paper level）", status: "gap",
      spec: ".lk-surface-0 / -1 / -2 / -3",
      product: "无类名 —— 直接用 --surface-* token", productWhere: "workbench.css:133-138（暖纸）· 281-286（夜纸）",
      inventory: "spec 的四个类名<b>零命中</b>。产品的做法是直接用 token，<b>没有层级类</b> ⇒ 「哪一层」没有单一出口：同一个 L1 在不同文件里被写成 <code>--surface-card</code> / <code>.card</code> / <code>--surface-raised</code>，全凭各处自觉。",
      current: {
        where: "workbench.css:133-138",
        html: '<div class="sb-s0 sb-w160">L0 底</div><div class="sb-s1 sb-w160">L1 卡</div><div class="sb-s2 sb-w160">L2 浮起</div><div class="sb-s3 sb-w160">L3 沉底</div>',
        note: "现状：<b>没有类名</b>，四个面各自被硬写进各处。本列用 token 直接画出来，是「现状的取值」而不是「现状的接口」。"
      },
      variants: [
        { id: "surface-spec", name: "A · spec 四层",
          html: '<div data-variant="surface-spec"><div class="sb-lv" data-lv="0">L0 底</div><div class="sb-lv" data-lv="1">L1 卡</div><div class="sb-lv" data-lv="2">L2 浮起</div><div class="sb-lv" data-lv="3">L3 沉底</div></div>',
          note: "四层齐活：底 / 卡 / 浮起 / 沉底，靠圆角 + 柔影 + 内发丝线分层 —— spec §4.19 的形态。" },
        { id: "surface-three", name: "B · 只留三层",
          html: '<div data-variant="surface-three"><div class="sb-lv" data-lv="0">L0 底</div><div class="sb-lv" data-lv="1">L1 卡</div><div class="sb-lv" data-lv="2">L2 浮起</div></div>',
          note: "<b>砍掉 L3 沉底</b> —— 少一层就少一处「底色差只有 1.035:1」的误读风险（夜纸里 L1/L3 差 ΔL\\* 1.49），但会丢掉沉底块这个最强的强调手段。" },
        { id: "surface-hair", name: "C · 发丝线分层",
          html: '<div data-variant="surface-hair"><div class="sb-lv" data-lv="0">L0 底</div><div class="sb-lv" data-lv="1">L1 卡</div><div class="sb-lv" data-lv="2">L2 浮起</div></div>',
          note: "不用柔影、全部改用 1px 内发丝线 —— 纸面感更强、更平；代价是夜纸下柔影本来就几乎看不见，这一档等于放弃「浮起」的读法。" }
      ]
    },
    {
      key: "sunken", sec: "§4.20", name: "沉底块（Sunken block）", status: "gap",
      spec: ".lk-sunkenblock",
      product: "无同名类 —— 4 处各写一遍 --surface-sunken + 内发丝线", productWhere: "workbench.css:1003(.msg.user) · 1234(.lk-empty) · 2230(.record-filter-note) · 2870(.lk-streak)",
      inventory: "规则已经存在，但<b>被复制了 4 遍</b> ⇒ 改一次圆角要改 4 个地方。这正是 spec §4.20 想要抽出来的东西。",
      current: {
        where: "workbench.css:1003",
        html: '<div class="msg user">这道题的思路我不太确定，先记下来。</div>',
        note: "现状（<code>.msg.user</code>）：沉底面 + 12px 圆角 + 内发丝线、无柔影 —— <b>规则是对的，只是没有共同的名字</b>。"
      },
      variants: [
        { id: "sunken-spec", name: "A · spec 沉底块",
          html: '<div data-variant="sunken-spec"><b>36</b><span>连对 36 题</span></div>',
          note: "沉底 + 内发丝线 + 36px 英雄数字 —— spec §4.20 的形态；强调力来自「尺度 + 挖坑感」，不再来自近黑反差。" },
        { id: "sunken-bare", name: "B · 裸沉底",
          html: '<div data-variant="sunken-bare"><b>36</b><span>连对 36 题</span></div>',
          note: "只留底色、去掉内发丝线 —— 更干净，但夜纸下 L1/L3 底色差只有 ΔL\\* 1.49，<b>边界会糊</b>。" },
        { id: "sunken-rail", name: "C · 竖线沉底",
          html: '<div data-variant="sunken-rail"><b>36</b><span>连对 36 题</span></div>',
          note: "沉底 + 左侧 4px 黄竖线 —— 借用「单侧结构线」语言，注意力被拉到左边；黄只承载面积不承载文字。" }
      ]
    },
    {
      key: "toast", sec: "§4.23", name: "吐司（Toast）", status: "gap",
      spec: ".lk-toast / .lk-toast__action",
      product: ".toast（仅图谱页，仿古硬编码）", productWhere: "workbench.css:3570-3576 · pages.py:696",
      inventory: "<b>工作台主体里没有吐司</b>。唯一那一个是图谱页仿古件（近黑底 + 3px 圆角 + 10px 字 + 底部居中，硬编码 hex），而图谱是冻结项 —— 对吐司来说，现状<b>基本等于「没有」</b>。",
      current: {
        where: "workbench.css:3570",
        html: '<div class="sb-rel sb-h120"><div class="toast show">已保存</div></div>',
        note: "现状（<b>仅图谱页</b>）：近黑底 + 3px 圆角 + 10px 字 + <b>底部居中</b> —— 是「仿古方向」的产物，与新语言相反。"
      },
      variants: [
        { id: "toast-spec", name: "A · spec 吐司",
          html: '<div class="sb-rel sb-h120"><div data-variant="toast-spec">已保存到草稿</div></div>',
          note: "右上角浮起面 + 12px 圆角 + 13px 字 + 左侧状态点 —— spec §4.23 的形态；A-23 之后吐司改浅底深字，不再是墨块。" },
        { id: "toast-bottom", name: "B · 底部胶囊吐司",
          html: '<div class="sb-rel sb-h120"><div data-variant="toast-bottom">已保存到草稿</div></div>',
          note: "底部居中胶囊 —— 不挡右上角的内容区，接近手机端的习惯；但和「活动浮层」会抢同一个区域。" },
        { id: "toast-inline", name: "C · 内联提示条",
          html: '<div data-variant="toast-inline">已保存到草稿</div>',
          note: "不浮起、直接内联在内容流里 —— 完全不抢注意力，但也不再是「瞬时反馈」的载体。" }
      ]
    },
    {
      key: "disclosure", sec: "§4.27", name: "折叠段（Disclosure）", status: "gap",
      spec: ".lk-disclosure__head / .lk-disclosure__body",
      product: "原生 <details>/<summary>，四处各写各的", productWhere: "workbench.css:1437 · 1733-1740 · 2524 · 1208",
      inventory: "<b>没有共享组件</b>：四处 <code>&lt;summary&gt;</code> 的箭头、字号、间距各不相同（有一处甚至没写 <code>cursor: pointer</code>）。spec §4.27 说「现状用 <code>&lt;details&gt;</code>」是对的，但产品里是 <b>4 种</b>不同的 details。",
      current: {
        where: "workbench.css:1733",
        html: '<details class="practice-set-item-body"><summary><span class="practice-set-item-index">1</span><span class="practice-set-item-title">第三章 函数与导数</span></summary><p>展开后是这一组的题目列表。</p></details>',
        note: "现状（<code>.practice-set-item-body</code>）：<code>▸/▾</code> 字符箭头 + 三列 grid + 11px 小字 —— 另外三处各有各的写法。"
      },
      variants: [
        { id: "disc-spec", name: "A · spec 折叠段",
          html: '<div data-variant="disc-spec"><b>计划详情</b><u>展开后的正文在这里。</u></div>',
          note: "44px 头行 + 16px 箭头（展开旋转 180°）+ 12px 圆角 —— spec §4.27 的形态；头行本身是按钮，命中区达标。" },
        { id: "disc-rail", name: "B · 竖线折叠段",
          html: '<div data-variant="disc-rail"><b>计划详情</b><u>展开后的正文在这里。</u></div>',
          note: "左侧 2px 结构线 + 无箭头 —— 最安静，和正文里的「结构块」同语言；但「这里能展开」需要额外提示。" },
        { id: "disc-accordion", name: "C · 手风琴折叠段",
          html: '<div data-variant="disc-accordion"><b>计划详情</b><u>展开后的正文在这里。</u></div>',
          note: "卡面 + 48px 头 + 内容在同一张卡里 —— 存在感最强，适合「这一段是主角」的场合；同组多个时容易变成庞然大物。" }
      ]
    },
    {
      key: "steps", sec: "§4.16", name: "分段进度条（Segmented progress）", status: "gap",
      spec: ".lk-steps / .lk-steps__seg",
      product: "无 —— 全仓零命中", productWhere: "（最接近的是 .lk-flames 连对火苗，workbench.css:2823-2842）",
      inventory: "<b>全新能力</b>。产品里最接近的是 <code>.lk-flames</code>（12×16px 火苗剪影，<code>--role-yellow</code> 点亮）—— 那是火苗图标串，不是分段条。spec §4.16 的规则可以直接当设计用。",
      current: {
        where: "—",
        html: "",
        note: "现状：<b>产品里没有这个界面</b>。下面三个候选全是新设计。"
      },
      variants: [
        { id: "steps-spec", name: "A · spec 分段进度",
          html: '<div data-variant="steps-spec"><i data-s="done"></i><i data-s="done"></i><i data-s="cur"></i><i></i><i></i><i></i></div>',
          note: "8px 胶囊段 + 4px 间隙，用「实心 / 半填 / 空心环」三种几何表达三态 —— spec §4.16 的形态；灰度下也能读出进度。" },
        { id: "steps-num", name: "B · 编号点串",
          html: '<div data-variant="steps-num"><i data-s="done">1</i><em></em><i data-s="done">2</i><em></em><i data-s="cur">3</i><em></em><i>4</i></div>',
          note: "编号圆点 + 连接线 —— 「第几轮」一眼可数，适合复习轮次这种需要数数的场景；点数多了就挤。" },
        { id: "steps-flag", name: "C · 里程碑柱",
          html: '<div data-variant="steps-flag"><i data-s="done"></i><i data-s="done"></i><i data-s="cur"></i><i></i><i></i><i></i></div>',
          note: "像柱状图一样逐格长高 —— 进度有「爬升」的感觉；但高度编码不如「实心/空心」直接。" }
      ]
    },
    {
      key: "dialog", sec: "§4.24", name: "对话框（Dialog）", status: "gap",
      spec: ".lk-dialog / .lk-dialog-backdrop / __title / __body / __actions",
      product: "无 —— 只有原生 window.confirm() 与 Agent 内联确认卡", productWhere: "workbench.js:2979,3019,3099,4843,5360 · agent-ui.css:341-347",
      inventory: "<b>全新能力</b>。产品里的「打断式确认」有两种，<b>都不是模态</b>：原生 <code>window.confirm()</code>（浏览器弹窗）与 Agent 的内联「需要确认」卡（替换输入区，不弹层）。spec §4.24 的遮罩 / 焦点陷阱 / 焦点归还<b>全部要新建</b>。",
      current: {
        where: "agent-ui.css:341",
        html: '<div class="agent-approval-card"><p class="agent-surface-kicker">需要确认</p><strong class="agent-approval-title">确认操作</strong><p class="agent-approval-reason">此操作需要你的明确确认。</p><div class="agent-approval-actions"><button class="outline sm" type="button">取消</button><button class="primary sm" type="button">确认</button></div></div>',
        note: "现状（最接近的件）：<b>内联确认卡</b>，黄色左边条 + 黄底 —— 它是「替换输入区」而不是弹层，所以<b>不打断视线</b>；真正的模态对话框产品里没有。"
      },
      variants: [
        { id: "dialog-spec", name: "A · spec 对话框",
          html: '<div class="sb-rel sb-h240"><div data-variant="dialog-spec"><div><h4>确认删除这张试卷？</h4><p>做题记录不会被删除。</p><div><button class="outline" type="button">取消</button><button class="primary" type="button">确认</button></div></div></div></div>',
          note: "暖墨面纱遮罩 + 浮起面板 + 右对齐动作区 —— spec §4.24 的形态；需要一并实现 Esc 关闭、焦点陷阱与焦点归还。" },
        { id: "dialog-drawer", name: "B · 底部抽屉",
          html: '<div class="sb-rel sb-h240"><div data-variant="dialog-drawer"><div><h4>确认删除这张试卷？</h4><p>做题记录不会被删除。</p><div><button class="outline" type="button">取消</button><button class="primary" type="button">确认</button></div></div></div></div>',
          note: "底部抽屉式 —— 更像手机习惯、与内容区不重叠；桌面宽屏下会觉得「太重」。" },
        { id: "dialog-inline", name: "C · 紧凑确认卡",
          html: '<div class="sb-rel sb-h240"><div data-variant="dialog-inline"><div><h4>确认删除这张试卷？</h4><p>做题记录不会被删除。</p></div></div></div>',
          note: "无遮罩的居中小卡 + 黄左边线 —— 直接升级现在的内联确认卡，<b>不引入模态</b>；打断感弱，但也不会被误关。" }
      ]
    },
    {
      key: "toolcard", sec: "§4.25", name: "工具调用卡（Tool-call card）", status: "gap",
      spec: ".lk-tool / .lk-tool__head / __name / __cost / __body / __payload",
      product: "无 —— grep tool_name / toolName / tool-call 全仓零命中", productWhere: "（最接近：.ai-activity + .ai-plan-step + .ai-plan-output）",
      inventory: "<b>全新能力</b>：产品<b>不渲染工具调用</b>。可以复用的现成结构是 <code>.ai-activity</code>（4px 左边条状态块）、<code>.ai-plan-step</code>（一步）与 <code>.ai-plan-output</code>（步骤里的 details 折叠）。",
      current: {
        where: "workbench.css:1453",
        html: '<div class="ai-activity"><div class="ai-plan-step"><span class="ai-plan-marker"></span><div class="ai-plan-body"><div class="ai-plan-heading"><span class="ai-plan-label">读取题面</span><span class="ai-plan-state">已完成</span></div><details class="ai-plan-output"><summary>查看输出</summary><pre>…</pre></details></div></div></div>',
        note: "现状（最接近的件）：<b>计划步骤 + 折叠输出</b>拼在一起，左边条承载状态 —— 结构已在，但<b>没有「工具名 + 耗时」这一层</b>，所以还不是 spec §4.25 的工具调用卡。"
      },
      variants: [
        { id: "tool-spec", name: "A · spec 工具调用卡",
          html: '<div data-variant="tool-spec"><b><code>read_file</code><em>0.2s</em></b><u>读取 src/a.py —— 42 行</u></div>',
          note: "状态点 + 等宽工具名 + 耗时 + 可展开载荷 —— spec §4.25 的形态；摘要 ≤ 240 字，失败时末尾省略号、红只由点承担。" },
        { id: "tool-line", name: "B · 单行流水",
          html: '<div data-variant="tool-line"><code>read_file</code><em>0.2s</em></div>',
          note: "一行摘要 —— 最省纵向空间，适合把一串工具调用压成日志；细节要靠 hover/点击再看。" },
        { id: "tool-rail", name: "C · 左竖线流水",
          html: '<div data-variant="tool-rail"><code>read_file</code><em>读取 src/a.py —— 42 行</em></div>',
          note: "左侧 2px 结构线 + 工具名 + 说明 —— 复用正文的结构块语言，不引入卡片，列表感更强。" }
      ]
    }
  ];

  return {
    CSS_WORKBENCH: CSS_WORKBENCH,
    CSS_AGENT: CSS_AGENT,
    candidateCss: candidateCss,
    components: components
  };
})();
