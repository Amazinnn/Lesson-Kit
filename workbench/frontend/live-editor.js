import {EditorState, StateEffect, StateField, Compartment} from '@codemirror/state';
import {EditorView, Decoration, WidgetType, keymap} from '@codemirror/view';
import {history, historyKeymap, defaultKeymap} from '@codemirror/commands';
import {markdown} from '@codemirror/lang-markdown';
import {syntaxTree} from '@codemirror/language';

const refresh = StateEffect.define();
class Preview extends WidgetType {
  constructor(text, from) { super(); this.text = text; this.from = from; }
  eq(other) { return other.text === this.text && other.from === this.from; }
  toDOM(view) {
    const node = document.createElement('div');
    node.className = 'lk-live-preview';
    node.innerHTML = window.LessonKitMarkdown.richText(this.text);
    window.LessonKitMarkdown.renderMath(node);
    node.addEventListener('mousedown', event => {
      if (view.state.readOnly) { event.preventDefault(); return; }
      event.preventDefault();
      view.dispatch({selection: {anchor: this.from}, effects: refresh.of(true)});
      view.focus();
    });
    node.addEventListener('click', event => event.preventDefault());
    return node;
  }
  ignoreEvent() { return true; }
}
function decorations(state) {
  const ranges = [];
  if (!window.LessonKitMarkdown) return Decoration.none;
  const focused = state.field(focusState);
  const selected = (from, to) => focused && state.selection.ranges.some(r => r.from <= to && r.to >= from);
  const doc = state.doc;
  // Only complete top-level syntax blocks are replaced; the source document is untouched.
  for (let node = syntaxTree(state).topNode.firstChild; node; node = node.nextSibling) {
    let from = node.from, to = node.to;
    let text = doc.sliceString(from, to);
    // Display math is a paragraph in CommonMark; merge its lines through the closing delimiter.
    if (text.startsWith('$$') && !text.slice(2).includes('$$')) continue;
    if (node.name === 'FencedCode' && !/^\s*```[^\n]*\n[\s\S]*\n\s*```\s*$/.test(text)) continue;
    if (!text.trim() || selected(from, to)) continue;
    ranges.push(Decoration.replace({widget: new Preview(text, from), block: true}).range(from, to));
  }
  return Decoration.set(ranges, true);
}
const focusState = StateField.define({create: () => false, update(value, tr) {
  for (const e of tr.effects) if (e.is(refresh)) return e.value;
  return value;
}});
const previews = StateField.define({create: decorations, update(value, tr) {
  return tr.docChanged || tr.selection || tr.effects.length ? decorations(tr.state) : value;
}, provide: field => EditorView.decorations.from(field)});
const mounted = new Map();
const failed = new WeakSet();
function mount(textarea) {
  if (mounted.has(textarea) || !window.LessonKitMarkdown) return;
  const host = document.createElement('div');
  host.className = 'lk-live-editor';
  const nativeValue = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');
  const nativeStart = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'selectionStart');
  const nativeEnd = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'selectionEnd');
  const mode = new Compartment();
  let syncing = false;
  const view = new EditorView({parent: host, state: EditorState.create({
    doc: nativeValue.get.call(textarea),
    extensions: [focusState, markdown(), previews, history(), keymap.of([...historyKeymap, ...defaultKeymap]),
      mode.of([EditorState.readOnly.of(textarea.disabled || textarea.readOnly), EditorView.editable.of(!textarea.disabled && !textarea.readOnly)]),
      EditorView.lineWrapping,
      EditorView.contentAttributes.of({'aria-label': textarea.getAttribute('aria-label') || textarea.placeholder || 'Markdown', role: 'textbox', 'aria-multiline': 'true'}),
      EditorView.domEventHandlers({focus() { view.dispatch({effects: refresh.of(true)}); textarea.dispatchEvent(new Event('focus')); }, blur() {
        view.dispatch({effects: refresh.of(false)}); textarea.dispatchEvent(new Event('blur')); textarea.dispatchEvent(new Event('change', {bubbles:true}));
      }, keydown(event) {
        if (event.isComposing || view.composing || event.keyCode === 229) return false;
        const forwarded = new KeyboardEvent('keydown', {key:event.key, code:event.code, shiftKey:event.shiftKey, ctrlKey:event.ctrlKey, altKey:event.altKey, metaKey:event.metaKey, bubbles:true, cancelable:true});
        textarea.dispatchEvent(forwarded);
        if (forwarded.defaultPrevented) { event.preventDefault(); return true; }
        return false;
      }}),
      EditorView.updateListener.of(update => {
        if (update.docChanged && !syncing) {
          nativeValue.set.call(textarea, view.state.doc.toString());
          textarea.dispatchEvent(new Event('input', {bubbles:true}));
        }
      })]
  })});
  Object.defineProperty(textarea, 'value', {configurable:true, get() {return nativeValue.get.call(this);}, set(value) {
    nativeValue.set.call(this, value);
    const text = nativeValue.get.call(this);
    if (view.state.doc.toString() !== text) {
      syncing = true; view.dispatch({changes:{from:0,to:view.state.doc.length,insert:text}}); syncing = false;
    }
  }});
  for (const [key, native] of [['selectionStart',nativeStart],['selectionEnd',nativeEnd]]) Object.defineProperty(textarea,key,{configurable:true,get() {return key === 'selectionStart' ? view.state.selection.main.from : view.state.selection.main.to;},set(value) {
    native.set.call(this,value); view.dispatch({selection:{anchor:nativeStart.get.call(this),head:nativeEnd.get.call(this)}});
  }});
  const originalFocus = textarea.focus, originalSelection = textarea.setSelectionRange;
  textarea.focus = () => view.focus();
  textarea.setSelectionRange = (start,end) => view.dispatch({selection:{anchor:Math.min(start,view.state.doc.length),head:Math.min(end,view.state.doc.length)}});
  const sync = () => {
    host.hidden = textarea.hidden || textarea.classList.contains('hidden');
    host.className = 'lk-live-editor ' + [...textarea.classList].filter(c => c !== 'lk-live-source').join(' ');
    host.style.display = textarea.style.display === 'none' ? 'none' : '';
    view.dispatch({effects:mode.reconfigure([EditorState.readOnly.of(textarea.disabled || textarea.readOnly),EditorView.editable.of(!textarea.disabled && !textarea.readOnly)])});
  };
  textarea.after(host);
  textarea.classList.add('lk-live-source');
  const observer = new MutationObserver(sync);
  observer.observe(textarea,{attributes:true,attributeFilter:['disabled','readonly','class','hidden','style']});
  sync();
  mounted.set(textarea, () => {
    observer.disconnect(); view.destroy(); host.remove(); textarea.classList.remove('lk-live-source');
    for (const key of ['value','selectionStart','selectionEnd']) delete textarea[key];
    textarea.focus = originalFocus; textarea.setSelectionRange = originalSelection;
  });
}
function scan() {
  if (window.LessonKitMarkdown) document.querySelectorAll('[data-live-markdown]').forEach(node => {
    node.removeAttribute('data-live-markdown');
    node.innerHTML = window.LessonKitMarkdown.richText(node.textContent);
    window.LessonKitMarkdown.renderMath(node);
  });
  for (const [textarea,destroy] of mounted) if (!textarea.isConnected) {destroy();mounted.delete(textarea);}
  document.querySelectorAll('textarea:not([data-plain-text])').forEach(textarea => {
    if (mounted.has(textarea) || failed.has(textarea)) return;
    try {mount(textarea);} catch (error) {
      failed.add(textarea); textarea.classList.remove('lk-live-source');
      const warning=document.createElement('small'); warning.textContent='实时编辑器不可用，保留源码输入。'; textarea.after(warning);
      console.error(error);
    }
  });
}
const style=document.createElement('style');
style.textContent='.lk-live-source{display:none!important}.lk-live-editor{border:1px solid var(--border,#ccc);border-radius:8px;min-height:4em;background:var(--surface,#fff);color:inherit}.lk-live-editor.hidden,.lk-live-editor[hidden]{display:none}.lk-live-editor .cm-editor{background:transparent}.lk-live-editor .cm-content{font:inherit;padding:8px;min-height:4em}.lk-live-preview{white-space:normal;overflow-wrap:anywhere;padding:2px 0;cursor:text}.lk-live-preview p{margin:0 0 .5em}.lk-live-preview img{max-width:100%}.lk-live-preview .math.display{display:block;overflow:auto}.lk-live-preview pre{white-space:pre-wrap}';
document.head.append(style);
new MutationObserver(scan).observe(document.body,{childList:true,subtree:true});
scan();
window.LessonKitLiveEditor = {scan};
