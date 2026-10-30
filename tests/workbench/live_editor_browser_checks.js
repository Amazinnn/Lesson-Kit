/* Run in an isolated browser page with the shipped live-editor bundle and shared renderer loaded:
   await runLiveEditorChecks(); throws on regression. Never use real course pages. */
async function runLiveEditorChecks() {
  const tick = () => new Promise(resolve => setTimeout(resolve, 30));
  function check(ok, label) { if (!ok) throw new Error(label); }
  const textarea = document.createElement('textarea');
  textarea.name = 'answer';
  const form = document.createElement('form'); form.append(textarea); document.body.append(form);
  await tick();
  const raw = '- first\n\n$$x^2$$\n\n```js\na_b\n```';
  let inputs = 0, focuses = 0;
  textarea.addEventListener('input', () => inputs++);
  textarea.addEventListener('focus', () => focuses++);
  textarea.value = raw; await tick();
  check(textarea.value === raw, 'programmatic value is exact');
  check(inputs === 0, 'programmatic/display changes do not save');
  check(new FormData(form).get('answer') === raw, 'form payload remains Markdown');
  textarea.focus(); await tick(); textarea.setSelectionRange(2, 3);
  check(textarea.selectionStart === 2 && textarea.selectionEnd === 3, 'selection bridge');
  check(focuses === 1, 'focus event forwarded');
  document.activeElement.blur(); await tick();
  check(textarea.value === raw, 'focus/blur do not serialize source');
  const second = [...textarea.nextElementSibling.querySelectorAll('.lk-live-preview')][1];
  second.dispatchEvent(new MouseEvent('mousedown', {bubbles:true,cancelable:true})); await tick();
  check(textarea.selectionStart === raw.indexOf('$$'), 'click maps to source block start');
  check(textarea.value === raw, 'click does not change source');
  textarea.setSelectionRange(0,raw.length); await tick();
  check(!textarea.nextElementSibling.querySelector('.lk-live-preview'), 'cross-block selection exposes source');
  textarea.classList.add('hidden'); await tick();
  check(textarea.nextElementSibling.hidden, 'hidden class mirrored');
  textarea.classList.remove('hidden'); textarea.disabled = true; await tick();
  check(textarea.nextElementSibling.querySelector('[contenteditable]').getAttribute('contenteditable') === 'false', 'lock mirrored');
  textarea.value = '**restored**'; await tick();
  check(textarea.value === '**restored**', 'readonly programmatic restore');
  form.remove(); await tick();
  check(!document.contains(textarea.nextElementSibling), 'removed host cleanup');
  return '12 browser behavior checks passed';
}
window.runLiveEditorChecks = runLiveEditorChecks;
async function runLiveEditorRegressions() {
  const tick = () => new Promise(resolve => setTimeout(resolve,30));
  const t=document.createElement('textarea'); document.body.append(t); await tick();
  let input=0;t.addEventListener('input',()=>input++);
  t.value='previous question answer';t.value='next question answer';t.focus();await tick();
  t.nextElementSibling.querySelector('.cm-content').dispatchEvent(new KeyboardEvent('keydown',{key:'z',code:'KeyZ',ctrlKey:true,bubbles:true,cancelable:true})); await tick();
  const changedHistory=t.value==='next question answer'&&input===0;
  t.value='same';t.focus();await tick();
  document.execCommand('insertText',false,' edit');await tick();
  const same=t.value;t.value=same;input=0;
  t.nextElementSibling.querySelector('.cm-content').dispatchEvent(new KeyboardEvent('keydown',{key:'z',code:'KeyZ',ctrlKey:true,bubbles:true,cancelable:true}));await tick();
  const sameHistory=t.value===same&&input===0;
  const math='$$\nx^2\n\n+ y^2\n$$'; t.value=math;document.activeElement.blur();await tick();
  const wholeMath=[...t.nextElementSibling.querySelectorAll('.math.display')].some(n=>n.textContent.includes('x^2')&&n.textContent.includes('+ y^2'));
  const fidelity=t.value===math;
  const fenced='```\n$$\nx^2\n```\n\n+ y^2\n$$';t.value=fenced;await tick();
  const fenceProtected=!t.nextElementSibling.querySelector('.math.display');
  t.remove();await tick();
  const result={changedHistory,sameHistory,wholeMath,fidelity,fenceProtected};
  if(Object.values(result).some(v=>!v)) throw new Error(JSON.stringify(result));
  return result;
}
window.runLiveEditorRegressions=runLiveEditorRegressions;
