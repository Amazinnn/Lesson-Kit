import { CrepeBuilder } from '@milkdown/crepe/builder';
import { codeMirror } from '@milkdown/crepe/feature/code-mirror';
import { cursor } from '@milkdown/crepe/feature/cursor';
import { latex } from '@milkdown/crepe/feature/latex';
import { listItem } from '@milkdown/crepe/feature/list-item';
import { placeholder } from '@milkdown/crepe/feature/placeholder';
import '@milkdown/crepe/theme/frame.css';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
} from 'd3-force';
import './styles.css';

const PROBLEM_STATES = ['wrong', 'stuck', 'reviewing', 'mastered', 'new'];
const STATUS_OPTIONS = ['new', 'wrong', 'stuck', 'reviewing', 'mastered'];
const SVG_NS = 'http://www.w3.org/2000/svg';
const GRAPH_MODE_FULL = 'full';
const GRAPH_MODE_FOCUS = 'focus';

const app = document.getElementById('app');

let fullGraph = null;
let graph = null;
let focusPacket = null;
let graphMode = GRAPH_MODE_FULL;
let focusSeeds = new Set();
let focusTarget = null;
let focusDepth = 2;
let focusMaxNodes = 30;
let focusDirected = false;
let focusLoading = false;
let nodes = [];
let links = [];
let nodeById = new Map();
let fullNodeById = new Map();
let neighbors = new Map();
let selectedId = null;
let hoverId = null;
let pinnedId = null;
let view = { x: 0, y: 0, scale: 1 };
let drag = null;
let editors = { body: null, fragile: null };
let svg = null;
let graphLayer = null;
let edgeLayer = null;
let nodeLayer = null;
let detailEl = null;
let searchEl = null;
let statusEl = null;
let scaleEl = null;
let toastEl = null;
let focusEl = null;
let focusPanelEl = null;
let modeFullEl = null;
let modeFocusEl = null;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));
}

function showToast(message) {
  toastEl.textContent = message;
  toastEl.classList.add('show');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toastEl.classList.remove('show'), 2200);
}

function renderLatex(source, displayMode = false) {
  try {
    return katex.renderToString(source, {
      displayMode,
      throwOnError: false,
      strict: false,
      trust: false,
      output: 'html',
    });
  } catch (error) {
    return `<code class="math-error">${escapeHtml(source)}</code>`;
  }
}

function renderInlineMarkdown(text) {
  return escapeHtml(text)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

function renderRichText(raw) {
  const text = String(raw || '');
  if (!text.trim()) return '<p class="empty">暂无内容。</p>';
  const pattern = /\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\\\(([\s\S]+?)\\\)|\$([^$\n]+?)\$/g;
  const parts = [];
  let cursor = 0;
  let match;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) {
      parts.push({ type: 'text', value: text.slice(cursor, match.index) });
    }
    const block = match[1] ?? match[2];
    const inline = match[3] ?? match[4];
    parts.push({
      type: block !== undefined ? 'math-block' : 'math-inline',
      value: block ?? inline,
    });
    cursor = pattern.lastIndex;
  }
  if (cursor < text.length) parts.push({ type: 'text', value: text.slice(cursor) });

  return parts.map((part) => {
    if (part.type === 'math-inline') {
      return `<span class="math-inline">${renderLatex(part.value, false)}</span>`;
    }
    if (part.type === 'math-block') {
      return `<div class="math-block">${renderLatex(part.value, true)}</div>`;
    }
    return part.value
      .split(/\n{2,}/)
      .map((block) => block.trim())
      .filter(Boolean)
      .map((block) => `<p>${renderInlineMarkdown(block).replace(/\n/g, '<br>')}</p>`)
      .join('');
  }).join('');
}

function splitLabel(value) {
  const label = String(value || '').replace(/\s+/g, ' ').trim();
  if (!label) return [];
  const maxChars = 14;
  const lines = [];
  let line = '';
  for (const char of Array.from(label)) {
    if (line && line.length + char.length > maxChars) {
      lines.push(line);
      line = char;
    } else {
      line += char;
    }
    if (/[ _/\\\-:：·、，,；;]/.test(char) && line.length >= 10) {
      lines.push(line);
      line = '';
    }
  }
  if (line) lines.push(line);
  return lines;
}

function uniqueValues(values) {
  return Array.from(new Set(values.filter(Boolean)));
}

function relationNeighbors(relations, nodeId) {
  const related = [];
  (relations || []).forEach((relation) => {
    if (relation.source === nodeId) related.push(relation.target);
    if (relation.target === nodeId) related.push(relation.source);
  });
  return related;
}

function relationKindLabel(relation) {
  return [
    relation.relation_type || 'related',
    relation.strength || '',
    relation.direction === 'directed' ? 'directed' : '',
  ].filter(Boolean).join(' · ');
}

function focusClass(node) {
  return [
    node.is_seed ? 'seed-node' : '',
    node.is_target ? 'target-node' : '',
    node.on_path ? 'path-node' : '',
    node.signals?.length ? 'signal-node' : '',
  ].filter(Boolean).join(' ');
}

function nodeRadius(node) {
  return Math.max(8, Math.min(23, 8 + Math.sqrt(Number(node.degree || 0)) * 4.8));
}

function collisionRadius(node) {
  const label = node.graph_label || node.label || '';
  const lineCount = splitLabel(label).length || 1;
  return Math.max(48, Math.min(150, node.radius + 24 + label.length * 3.1 + lineCount * 8));
}

function buildNeighbors() {
  neighbors = new Map(nodes.map((node) => [node.id, new Set([node.id])]));
  links.forEach((edge) => {
    const source = typeof edge.source === 'object' ? edge.source.id : edge.source;
    const target = typeof edge.target === 'object' ? edge.target.id : edge.target;
    neighbors.get(source)?.add(target);
    neighbors.get(target)?.add(source);
  });
}

function sectionCenters(width, height) {
  const sections = graph.meta.sections?.map((section) => section.name) || [];
  const unique = sections.length ? sections : Array.from(new Set(nodes.map((node) => node.section || '未分组')));
  const columns = Math.min(4, Math.max(1, Math.ceil(Math.sqrt(unique.length))));
  const rows = Math.max(1, Math.ceil(unique.length / columns));
  const centers = new Map();
  unique.forEach((section, index) => {
    const col = index % columns;
    const row = Math.floor(index / columns);
    centers.set(section, {
      x: width * ((col + 1) / (columns + 1)),
      y: height * ((row + 1) / (rows + 1)),
    });
  });
  return centers;
}

function applyTransform() {
  graphLayer.setAttribute('transform', `translate(${view.x} ${view.y}) scale(${view.scale})`);
  scaleEl.textContent = `${Math.round(view.scale * 100)}%`;
}

function setZoom(nextScale) {
  view.scale = Math.max(0.35, Math.min(3.6, nextScale));
  applyTransform();
}

function activeFocus() {
  return pinnedId || hoverId;
}

function visibleNodeIds() {
  const query = searchEl.value.trim().toLowerCase();
  const status = statusEl.value;
  return new Set(nodes
    .filter((node) => {
      const text = [node.id, node.label, node.graph_label, node.body, node.fragile, node.source_location]
        .join(' ')
        .toLowerCase();
      if (query && !text.includes(query)) return false;
      if (status === 'fragile') return Boolean(node.fragile);
      if (status !== 'all' && node.status !== status) return false;
      return true;
    })
    .map((node) => node.id));
}

function updateState() {
  const focus = activeFocus();
  const allowed = focus ? neighbors.get(focus) || new Set([focus]) : null;
  const visible = visibleNodeIds();
  nodeLayer.querySelectorAll('.node').forEach((el) => {
    const id = el.dataset.id;
    el.classList.toggle('hidden', !visible.has(id));
    el.classList.toggle('dimmed', Boolean(focus && !allowed.has(id)));
    el.classList.toggle('focused', Boolean(focus && allowed.has(id)));
    el.classList.toggle('pinned', id === pinnedId);
  });
  edgeLayer.querySelectorAll('.edge').forEach((el) => {
    const source = el.dataset.source;
    const target = el.dataset.target;
    const inFilter = visible.has(source) && visible.has(target);
    const directlyConnected = focus && (source === focus || target === focus);
    const inFocus = !focus || (allowed.has(source) && allowed.has(target));
    el.classList.toggle('hidden', !inFilter);
    el.classList.toggle('dimmed', Boolean(focus && !inFocus));
    el.classList.toggle('focused', Boolean(directlyConnected));
  });
  focusEl.textContent = pinnedId
    ? `固定：${nodeById.get(pinnedId)?.graph_label || pinnedId}`
    : hoverId
      ? `聚焦：${nodeById.get(hoverId)?.graph_label || hoverId}`
      : '未固定节点';
}

async function destroyEditors() {
  const pending = [];
  Object.values(editors).forEach((editor) => {
    if (editor) pending.push(editor.destroy().catch(() => undefined));
  });
  editors = { body: null, fragile: null };
  await Promise.all(pending);
}

async function mountEditor(root, markdown) {
  const crepe = new CrepeBuilder({
    root,
    defaultValue: markdown || '',
  })
    .addFeature(cursor)
    .addFeature(listItem)
    .addFeature(placeholder, { text: '直接输入 Markdown / LaTeX', mode: 'block' })
    .addFeature(codeMirror, { languages: [] })
    .addFeature(latex, { katexOptions: { throwOnError: false, strict: false } });
  await crepe.create();
  return crepe;
}

async function mountEditors(node) {
  await destroyEditors();
  const bodyRoot = detailEl.querySelector('[data-editor-body]');
  const fragileRoot = detailEl.querySelector('[data-editor-fragile]');
  try {
    editors.body = await mountEditor(bodyRoot, node.body || '');
    editors.fragile = await mountEditor(fragileRoot, node.fragile || '');
  } catch (error) {
    bodyRoot.innerHTML = `<textarea class="fallback-editor" data-fallback-body>${escapeHtml(node.body || '')}</textarea>`;
    fragileRoot.innerHTML = `<textarea class="fallback-editor small" data-fallback-fragile>${escapeHtml(node.fragile || '')}</textarea>`;
    showToast('富文本编辑器加载失败，已切换到源码编辑');
  }
}

function editorMarkdown(key, fallbackSelector) {
  if (editors[key]) return editors[key].getMarkdown();
  return detailEl.querySelector(fallbackSelector)?.value || '';
}

async function saveKp(node) {
  const body = editorMarkdown('body', '[data-fallback-body]');
  const fragile = editorMarkdown('fragile', '[data-fallback-fragile]');
  const response = await fetch(`/api/kp/${encodeURIComponent(node.id)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ body, fragile }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || await response.text() || 'save failed');
  }
  node.body = body;
  node.fragile = fragile;
  const fullNode = fullNodeById.get(node.id);
  if (fullNode) {
    fullNode.body = body;
    fullNode.fragile = fragile;
  }
  const activeNode = nodeById.get(node.id);
  if (activeNode) {
    activeNode.body = body;
    activeNode.fragile = fragile;
  }
  showToast('正文已保存');
}

async function recordProblem(problemId) {
  const status = detailEl.querySelector(`[data-problem-status="${CSS.escape(problemId)}"]`)?.value || 'new';
  const note = detailEl.querySelector(`[data-problem-note="${CSS.escape(problemId)}"]`)?.value || '';
  const response = await fetch(`/api/problem/${encodeURIComponent(problemId)}/record`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, note }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || await response.text() || 'record failed');
  }
  showToast('做题记录已保存');
  fullGraph = await fetchGraph();
  fullNodeById = new Map(fullGraph.nodes.map((node) => [node.id, node]));
  if (graphMode === GRAPH_MODE_FOCUS && focusSeeds.size) {
    await refreshFocusMap(false);
  } else {
    hydrateGraph(fullGraph);
    updateCounts();
    renderGraph();
  }
  await selectNode(nodeById.get(selectedId) || fullNodeById.get(selectedId) || nodes[0]);
}

function renderProblemGroups(node) {
  const groups = node.problem_groups || {};
  const html = PROBLEM_STATES.map((status) => {
    const items = groups[status] || [];
    if (!items.length) return '';
    const rows = items.map((problem) => {
      const controls = `
        <div class="record-line">
          <select data-problem-status="${escapeHtml(problem.problem_id)}">
            ${STATUS_OPTIONS.map((value) => (
              `<option value="${value}" ${value === problem.status ? 'selected' : ''}>${value}</option>`
            )).join('')}
          </select>
          <input data-problem-note="${escapeHtml(problem.problem_id)}" placeholder="备注 / 错因" />
          <button class="btn secondary" data-record-problem="${escapeHtml(problem.problem_id)}" type="button">记录</button>
        </div>`;
      return `
        <details class="problem-row">
          <summary>
            <span class="problem-id">${escapeHtml(problem.problem_id)}</span>
            <span class="problem-state ${status}">${status}</span>
          </summary>
          <div class="problem-text rich-text">${renderRichText(problem.text || '题干待补充')}</div>
          ${controls}
        </details>`;
    }).join('');
    const open = ['wrong', 'stuck', 'reviewing'].includes(status) ? ' open' : '';
    return `
      <details class="problem-group"${open}>
        <summary><span class="dot ${status}"></span><span>${status} · ${items.length}</span></summary>
        <div class="problem-list">${rows}</div>
      </details>`;
  }).join('');
  return html || '<p class="empty">暂无关联题目。</p>';
}

function bindDetail(node) {
  detailEl.querySelector('[data-toggle-seed]')?.addEventListener('click', async () => {
    if (focusSeeds.has(node.id)) {
      focusSeeds.delete(node.id);
      if (focusTarget === node.id) focusTarget = null;
    } else {
      focusSeeds.add(node.id);
    }
    renderFocusPanel();
    if (graphMode === GRAPH_MODE_FOCUS) await refreshFocusMap();
  });
  detailEl.querySelector('[data-set-target]')?.addEventListener('click', async () => {
    focusTarget = focusTarget === node.id ? null : node.id;
    renderFocusPanel();
    if (graphMode === GRAPH_MODE_FOCUS && focusSeeds.size) await refreshFocusMap();
  });
  detailEl.querySelector('[data-save-kp]')?.addEventListener('click', async () => {
    try {
      await saveKp(node);
    } catch (error) {
      showToast(error.message || String(error));
    }
  });
  detailEl.querySelectorAll('[data-record-problem]').forEach((button) => {
    button.addEventListener('click', async () => {
      try {
        await recordProblem(button.dataset.recordProblem);
      } catch (error) {
        showToast(error.message || String(error));
      }
    });
  });
  detailEl.querySelectorAll('[data-jump]').forEach((button) => {
    button.addEventListener('click', () => selectNode(nodeById.get(button.dataset.jump)));
  });
}

function focusContextHtml(node) {
  if (graphMode !== GRAPH_MODE_FOCUS) return '';
  const signals = (node.signals || [])
    .map((signal) => `<span class="chip signal-chip">${escapeHtml(signal.signal_type)} · ${escapeHtml(signal.weight)}</span>`)
    .join('');
  const findings = (focusPacket?.findings || [])
    .filter((finding) => JSON.stringify(finding).includes(node.id))
    .map((finding) => `<span class="chip">${escapeHtml(finding.type)}</span>`)
    .join('');
  return `
    <section class="detail-block compact">
      <h3>Focus Context</h3>
      <div class="chips">
        <span class="chip">distance ${node.distance ?? 'n/a'}</span>
        ${node.is_seed ? '<span class="chip seed-chip">seed</span>' : ''}
        ${node.is_target ? '<span class="chip target-chip">target</span>' : ''}
        ${node.on_path ? '<span class="chip path-chip">path</span>' : ''}
        ${signals}
        ${findings}
      </div>
    </section>
  `;
}

async function selectNode(node) {
  if (!node) return;
  selectedId = node.id;
  pinnedId = node.id;
  updateState();
  const related = (node.related || [])
    .filter((id) => nodeById.has(id))
    .map((id) => `<button class="chip" data-jump="${escapeHtml(id)}">${escapeHtml(nodeById.get(id).graph_label || nodeById.get(id).label)}</button>`)
    .join('');
  const states = Object.entries(node.problem_states || {})
    .map(([name, count]) => `<span class="chip">${escapeHtml(name)} ${count}</span>`)
    .join('');
  const isSeed = focusSeeds.has(node.id);
  const isTarget = focusTarget === node.id;
  detailEl.innerHTML = `
    <div class="detail-head">
      <div>
        <h2>${escapeHtml(node.label)}</h2>
        <p>${escapeHtml(node.id)} · degree ${node.degree || 0}</p>
      </div>
      <button class="icon-btn" data-close-detail type="button" title="收起详情">×</button>
    </div>
    <section class="detail-block compact">
      <h3>来源</h3>
      <p>${escapeHtml(node.source_location || node.section || '未分组')}</p>
    </section>
    <section class="detail-block compact">
      <h3>Focus</h3>
      <div class="button-row">
        <button class="btn secondary" data-toggle-seed type="button">${isSeed ? '移出焦点' : '加入焦点'}</button>
        <button class="btn secondary" data-set-target type="button">${isTarget ? '清除目标' : '设为目标'}</button>
      </div>
    </section>
    ${focusContextHtml(node)}
    <section class="detail-block">
      <h3>正文</h3>
      <div class="milkdown-host" data-editor-body></div>
    </section>
    <section class="detail-block">
      <h3>易错点</h3>
      <div class="milkdown-host fragile" data-editor-fragile></div>
    </section>
    <div class="button-row sticky-actions">
      <button class="btn" data-save-kp type="button">保存正文</button>
    </div>
    <section class="detail-block compact">
      <h3>状态摘要</h3>
      <div class="chips">
        <span class="chip">KP ${escapeHtml(node.kp_state || 'neutral')}</span>
        <span class="chip">${node.problem_count || 0} 题</span>
        ${states}
      </div>
    </section>
    <section class="detail-block">
      <h3>关联题目</h3>
      <div class="problem-groups">${renderProblemGroups(node)}</div>
    </section>
    <section class="detail-block">
      <h3>一步关系</h3>
      <div class="chips">${related || '<span class="empty">暂无直接关系。</span>'}</div>
    </section>
  `;
  document.body.classList.add('detail-open');
  detailEl.querySelector('[data-close-detail]')?.addEventListener('click', () => {
    document.body.classList.remove('detail-open');
    pinnedId = null;
    updateState();
  });
  bindDetail(node);
  await mountEditors(node);
}

function renderGraph() {
  const width = Number(graph.meta.layout?.width || 1600);
  const height = Number(graph.meta.layout?.height || 1000);
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  edgeLayer.innerHTML = '';
  nodeLayer.innerHTML = '';

  const edgeElements = links.map((edge) => {
    const line = document.createElementNS(SVG_NS, 'line');
    line.dataset.source = edge.source;
    line.dataset.target = edge.target;
    line.setAttribute('class', `edge ${edge.on_path ? 'path-edge' : ''} ${edge.signals?.length ? 'signal-edge' : ''}`);
    if (edge.relation_type) {
      const title = document.createElementNS(SVG_NS, 'title');
      title.textContent = relationKindLabel(edge);
      line.appendChild(title);
    }
    edgeLayer.appendChild(line);
    return line;
  });

  const nodeElements = nodes.map((node) => {
    const group = document.createElementNS(SVG_NS, 'g');
    group.dataset.id = node.id;
    group.setAttribute('class', `node ${node.status || 'neutral'} ${focusClass(node)}`);
    group.setAttribute('tabindex', '0');
    group.setAttribute('role', 'button');
    group.setAttribute('aria-label', node.label);

    const title = document.createElementNS(SVG_NS, 'title');
    title.textContent = node.label;
    group.appendChild(title);

    const halo = document.createElementNS(SVG_NS, 'circle');
    halo.setAttribute('class', 'halo');
    halo.setAttribute('r', node.radius + 8);
    group.appendChild(halo);

    const core = document.createElementNS(SVG_NS, 'circle');
    core.setAttribute('class', 'core');
    core.setAttribute('r', node.radius);
    group.appendChild(core);

    if (node.problem_count) {
      const badge = document.createElementNS(SVG_NS, 'circle');
      badge.setAttribute('class', 'marker');
      badge.setAttribute('r', 3.4);
      badge.setAttribute('cx', node.radius + 3);
      badge.setAttribute('cy', -node.radius - 1);
      group.appendChild(badge);
    }

    const label = document.createElementNS(SVG_NS, 'text');
    label.setAttribute('class', 'node-label');
    label.setAttribute('y', node.radius + 18);
    splitLabel(node.graph_label || node.label).forEach((line, index) => {
      const tspan = document.createElementNS(SVG_NS, 'tspan');
      tspan.setAttribute('x', '0');
      tspan.setAttribute('dy', index === 0 ? '0' : '1.18em');
      tspan.textContent = line;
      label.appendChild(tspan);
    });
    group.appendChild(label);

    group.addEventListener('mouseenter', () => {
      hoverId = node.id;
      updateState();
    });
    group.addEventListener('mouseleave', () => {
      hoverId = null;
      updateState();
    });
    group.addEventListener('click', (event) => {
      event.stopPropagation();
      selectNode(node);
    });
    group.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        selectNode(node);
      }
    });
    nodeLayer.appendChild(group);
    return group;
  });

  const centers = sectionCenters(width, height);
  const simulation = forceSimulation(nodes)
    .force('link', forceLink(links).id((node) => node.id).distance(graphMode === GRAPH_MODE_FOCUS ? 210 : 170).strength(0.18))
    .force('charge', forceManyBody().strength(graphMode === GRAPH_MODE_FOCUS ? -360 : -260))
    .force('center', forceCenter(width / 2, height / 2).strength(0.05))
    .force('x', forceX((node) => centers.get(node.section)?.x ?? width / 2).strength(0.035))
    .force('y', forceY((node) => centers.get(node.section)?.y ?? height / 2).strength(0.035))
    .force('collide', forceCollide((node) => node.collisionRadius).strength(0.94).iterations(3))
    .alpha(0.95)
    .alphaMin(0.018);

  simulation.on('tick', () => {
    edgeElements.forEach((line, index) => {
      const edge = links[index];
      line.setAttribute('x1', edge.source.x);
      line.setAttribute('y1', edge.source.y);
      line.setAttribute('x2', edge.target.x);
      line.setAttribute('y2', edge.target.y);
      line.dataset.source = edge.source.id;
      line.dataset.target = edge.target.id;
    });
    nodeElements.forEach((group, index) => {
      const node = nodes[index];
      node.x = Math.max(70, Math.min(width - 70, node.x));
      node.y = Math.max(70, Math.min(height - 70, node.y));
      group.setAttribute('transform', `translate(${node.x} ${node.y})`);
    });
  });

  simulation.on('end', () => {
    updateState();
  });
  updateState();
  applyTransform();
}

function hydrateGraph(nextGraph) {
  graph = nextGraph;
  const relations = graph.relations || graph.edges || [];
  nodes = graph.nodes.map((node) => {
    const fullNode = fullNodeById.get(node.id) || {};
    const mergedRelated = uniqueValues([
      ...(fullNode.related || []),
      ...(node.related || []),
      ...relationNeighbors(relations, node.id),
    ]);
    const merged = {
      ...fullNode,
      ...node,
      related: mergedRelated,
      problem_groups: fullNode.problem_groups || node.problem_groups || {},
      status: fullNode.status || node.status || 'neutral',
    };
    const radius = nodeRadius(merged);
    return {
      ...merged,
      radius,
      collisionRadius: 0,
      x: Number(node.x || 800),
      y: Number(node.y || 500),
    };
  });
  nodes.forEach((node) => {
    node.collisionRadius = collisionRadius(node);
  });
  links = relations.map((edge) => ({ ...edge }));
  nodeById = new Map(nodes.map((node) => [node.id, node]));
  buildNeighbors();
}

async function fetchGraph() {
  const response = await fetch('/api/graph');
  if (!response.ok) throw new Error(await response.text() || 'failed to load graph');
  return response.json();
}

function emptyFocusGraph() {
  return {
    meta: {
      ...(fullGraph?.meta || {}),
      view: 'focus-map',
      node_count: 0,
      edge_count: 0,
      relation_count: 0,
    },
    nodes: [],
    relations: [],
    focus: null,
  };
}

function graphFromFocusPacket(packet) {
  return {
    meta: {
      ...(fullGraph?.meta || {}),
      ...packet.meta,
      node_count: packet.meta.node_count,
      edge_count: packet.meta.relation_count,
      layout: fullGraph?.meta?.layout || packet.meta.layout || { width: 1600, height: 1000 },
    },
    nodes: packet.nodes,
    relations: packet.relations,
    focus: packet,
  };
}

async function fetchFocusMap() {
  const params = new URLSearchParams();
  focusSeeds.forEach((seed) => params.append('seed', seed));
  if (focusTarget) params.set('target', focusTarget);
  params.set('depth', String(focusDepth));
  params.set('max_nodes', String(focusMaxNodes));
  params.set('directed', focusDirected ? '1' : '0');
  const response = await fetch(`/api/focus-map?${params.toString()}`);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || await response.text() || 'failed to load focus map');
  }
  return response.json();
}

function updateCounts() {
  document.getElementById('nodeCount').textContent = graph?.meta?.node_count ?? nodes.length;
  document.getElementById('edgeCount').textContent = graph?.meta?.edge_count ?? links.length;
  document.getElementById('pageMeta').textContent = graphMode === GRAPH_MODE_FOCUS
    ? `Focus Map · ${focusSeeds.size} seed${focusSeeds.size === 1 ? '' : 's'}`
    : 'Editable Graph View';
}

function updateModeButtons() {
  modeFullEl?.classList.toggle('active', graphMode === GRAPH_MODE_FULL);
  modeFocusEl?.classList.toggle('active', graphMode === GRAPH_MODE_FOCUS);
  document.body.classList.toggle('focus-mode', graphMode === GRAPH_MODE_FOCUS);
}

async function refreshFocusMap(showEmptyToast = true) {
  if (focusLoading) return;
  focusLoading = true;
  renderFocusPanel();
  try {
    if (!focusSeeds.size) {
      focusPacket = null;
      hydrateGraph(emptyFocusGraph());
      renderGraph();
      updateCounts();
      if (showEmptyToast) showToast('先加入至少一个焦点节点');
      return;
    }
    focusPacket = await fetchFocusMap();
    hydrateGraph(graphFromFocusPacket(focusPacket));
    renderGraph();
    updateCounts();
    const nextSelected = nodeById.get(selectedId) || nodeById.get(focusTarget) || nodeById.get(Array.from(focusSeeds)[0]);
    if (nextSelected) await selectNode(nextSelected);
  } catch (error) {
    showToast(error.message || String(error));
  } finally {
    focusLoading = false;
    renderFocusPanel();
  }
}

async function setGraphMode(nextMode) {
  graphMode = nextMode;
  updateModeButtons();
  renderFocusPanel();
  if (graphMode === GRAPH_MODE_FULL) {
    hydrateGraph(fullGraph);
    renderGraph();
    updateCounts();
    await selectNode(nodeById.get(selectedId) || nodes[0]);
    return;
  }
  await refreshFocusMap();
}

function focusChip(id, kind) {
  const node = fullNodeById.get(id) || nodeById.get(id);
  const label = node?.graph_label || node?.label || id;
  const action = kind === 'seed' ? 'data-remove-seed' : 'data-clear-target';
  return `<button class="chip focus-chip ${kind}-chip" ${action}="${escapeHtml(id)}" type="button" title="${escapeHtml(id)}">${escapeHtml(label)} ×</button>`;
}

function renderFocusPanel() {
  if (!focusPanelEl) return;
  const seedHtml = Array.from(focusSeeds).map((id) => focusChip(id, 'seed')).join('');
  const targetHtml = focusTarget ? focusChip(focusTarget, 'target') : '<span class="empty">未设置目标。</span>';
  const findingHtml = (focusPacket?.findings || [])
    .map((finding) => `<span class="chip">${escapeHtml(finding.type)}</span>`)
    .join('');
  focusPanelEl.innerHTML = `
    <div class="focus-head">
      <span>Focus Map</span>
      <span>${focusLoading ? 'loading' : graphMode}</span>
    </div>
    <div class="focus-block">
      <div class="focus-label">Seeds</div>
      <div class="chips">${seedHtml || '<span class="empty">从节点详情加入焦点。</span>'}</div>
    </div>
    <div class="focus-block">
      <div class="focus-label">Target</div>
      <div class="chips">${targetHtml}</div>
    </div>
    <div class="focus-grid">
      <label class="field mini">
        <span>Depth</span>
        <input id="focusDepth" type="number" min="0" max="6" value="${focusDepth}" />
      </label>
      <label class="field mini">
        <span>Max</span>
        <input id="focusMaxNodes" type="number" min="1" max="120" value="${focusMaxNodes}" />
      </label>
    </div>
    <label class="toggle-line">
      <input id="focusDirected" type="checkbox" ${focusDirected ? 'checked' : ''} />
      <span>directed</span>
    </label>
    <div class="button-row">
      <button class="btn" id="refreshFocus" type="button">刷新 Focus</button>
      <button class="btn secondary" id="clearFocus" type="button">清空</button>
    </div>
    ${findingHtml ? `<div class="focus-block"><div class="focus-label">Findings</div><div class="chips">${findingHtml}</div></div>` : ''}
  `;
  focusPanelEl.querySelectorAll('[data-remove-seed]').forEach((button) => {
    button.addEventListener('click', async () => {
      focusSeeds.delete(button.dataset.removeSeed);
      if (focusTarget === button.dataset.removeSeed) focusTarget = null;
      renderFocusPanel();
      if (graphMode === GRAPH_MODE_FOCUS) await refreshFocusMap();
    });
  });
  focusPanelEl.querySelector('[data-clear-target]')?.addEventListener('click', async () => {
    focusTarget = null;
    renderFocusPanel();
    if (graphMode === GRAPH_MODE_FOCUS && focusSeeds.size) await refreshFocusMap();
  });
  focusPanelEl.querySelector('#focusDepth')?.addEventListener('change', async (event) => {
    focusDepth = Math.max(0, Math.min(6, Number(event.target.value || 2)));
    if (graphMode === GRAPH_MODE_FOCUS && focusSeeds.size) await refreshFocusMap();
  });
  focusPanelEl.querySelector('#focusMaxNodes')?.addEventListener('change', async (event) => {
    focusMaxNodes = Math.max(1, Math.min(120, Number(event.target.value || 30)));
    if (graphMode === GRAPH_MODE_FOCUS && focusSeeds.size) await refreshFocusMap();
  });
  focusPanelEl.querySelector('#focusDirected')?.addEventListener('change', async (event) => {
    focusDirected = event.target.checked;
    if (graphMode === GRAPH_MODE_FOCUS && focusSeeds.size) await refreshFocusMap();
  });
  focusPanelEl.querySelector('#refreshFocus')?.addEventListener('click', () => refreshFocusMap());
  focusPanelEl.querySelector('#clearFocus')?.addEventListener('click', async () => {
    focusSeeds = new Set();
    focusTarget = null;
    focusPacket = null;
    renderFocusPanel();
    if (graphMode === GRAPH_MODE_FOCUS) await refreshFocusMap(false);
  });
}

function renderShell() {
  app.innerHTML = `
    <main class="graph-app">
      <aside class="control-panel">
        <header>
          <h1 id="pageTitle">Lesson-Kit</h1>
          <p id="pageMeta">加载中</p>
        </header>
        <div class="mode-switch" role="group" aria-label="Graph view mode">
          <button id="modeFull" class="active" type="button">全图</button>
          <button id="modeFocus" type="button">Focus</button>
        </div>
        <label class="field">
          <span>搜索</span>
          <input id="search" type="search" placeholder="名称、ID、正文" autocomplete="off" />
        </label>
        <label class="field">
          <span>状态</span>
          <select id="statusFilter">
            <option value="all">全部状态</option>
            <option value="wrong">wrong</option>
            <option value="stuck">stuck</option>
            <option value="reviewing">reviewing</option>
            <option value="mastered">mastered</option>
            <option value="neutral">neutral</option>
            <option value="fragile">有 fragile note</option>
          </select>
        </label>
        <div class="metrics">
          <span><strong id="nodeCount">0</strong> 知识点</span>
          <span><strong id="edgeCount">0</strong> 关系</span>
        </div>
        <div id="focusPanel" class="focus-panel"></div>
      </aside>
      <section class="graph-stage" aria-label="知识图谱">
        <div class="graph-toolbar">
          <button id="zoomOut" class="icon-btn" type="button" title="缩小">−</button>
          <button id="zoomIn" class="icon-btn" type="button" title="放大">+</button>
          <button id="fitGraph" class="icon-btn wide" type="button" title="复位">复位</button>
          <span id="scaleBadge">100%</span>
          <span id="focusHint">未固定节点</span>
        </div>
        <svg id="graph" role="img" aria-label="Knowledge graph"></svg>
      </section>
      <aside id="detail" class="detail-panel"></aside>
    </main>
    <div id="toast" class="toast" aria-live="polite"></div>
  `;
  svg = document.getElementById('graph');
  detailEl = document.getElementById('detail');
  searchEl = document.getElementById('search');
  statusEl = document.getElementById('statusFilter');
  scaleEl = document.getElementById('scaleBadge');
  toastEl = document.getElementById('toast');
  focusEl = document.getElementById('focusHint');
  focusPanelEl = document.getElementById('focusPanel');
  modeFullEl = document.getElementById('modeFull');
  modeFocusEl = document.getElementById('modeFocus');
  graphLayer = document.createElementNS(SVG_NS, 'g');
  edgeLayer = document.createElementNS(SVG_NS, 'g');
  nodeLayer = document.createElementNS(SVG_NS, 'g');
  graphLayer.append(edgeLayer, nodeLayer);
  svg.appendChild(graphLayer);

  searchEl.addEventListener('input', updateState);
  statusEl.addEventListener('change', updateState);
  modeFullEl.addEventListener('click', () => setGraphMode(GRAPH_MODE_FULL));
  modeFocusEl.addEventListener('click', () => setGraphMode(GRAPH_MODE_FOCUS));
  document.getElementById('zoomIn').addEventListener('click', () => setZoom(view.scale * 1.16));
  document.getElementById('zoomOut').addEventListener('click', () => setZoom(view.scale / 1.16));
  document.getElementById('fitGraph').addEventListener('click', () => {
    view = { x: 0, y: 0, scale: 1 };
    applyTransform();
  });
  svg.addEventListener('click', (event) => {
    if (event.target === svg || event.target === graphLayer) {
      pinnedId = null;
      updateState();
    }
  });
  svg.addEventListener('pointerdown', (event) => {
    if (event.target.closest && event.target.closest('.node')) return;
    drag = { x: event.clientX, y: event.clientY, startX: view.x, startY: view.y };
    svg.setPointerCapture(event.pointerId);
  });
  svg.addEventListener('pointermove', (event) => {
    if (!drag) return;
    view.x = drag.startX + (event.clientX - drag.x);
    view.y = drag.startY + (event.clientY - drag.y);
    applyTransform();
  });
  svg.addEventListener('pointerup', () => {
    drag = null;
  });
  svg.addEventListener('wheel', (event) => {
    event.preventDefault();
    setZoom(view.scale * (event.deltaY > 0 ? 0.92 : 1.08));
  }, { passive: false });
  renderFocusPanel();
  updateModeButtons();
}

async function boot() {
  renderShell();
  try {
    fullGraph = await fetchGraph();
    fullNodeById = new Map(fullGraph.nodes.map((node) => [node.id, node]));
    hydrateGraph(fullGraph);
    document.getElementById('pageTitle').textContent = `${graph.meta.course_name} ${graph.meta.chapter}`;
    updateCounts();
    renderGraph();
    await selectNode(nodes[0]);
  } catch (error) {
    app.innerHTML = `<main class="error-page"><h1>图谱加载失败</h1><pre>${escapeHtml(error.message || String(error))}</pre></main>`;
  }
}

boot();
