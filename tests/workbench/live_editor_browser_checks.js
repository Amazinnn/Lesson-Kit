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
