// Replay with Playwright browser_run_code_unsafe filename, while a read-only
// python -m http.server 38971 --bind 127.0.0.1 runs at this checkout root.
async (page) => {
  let generation = 1, loads = 0;
  await page.route('**/api/runtime', r => r.fulfill({json:{generation,assets_generation:1}}));
  await page.route('**/runtime-fixture', r => {
    loads++;
    return r.fulfill({contentType:'text/html; charset=utf-8',body:`<meta charset='utf-8'><script src='/workbench/server/static/runtime.js'></script><textarea id='ai-input'></textarea><textarea id='submitted' readonly>submitted</textarea><article data-turn-id='turn-002' id='qcard'></article><script>window.sent=0;document.addEventListener('submit',()=>window.sent++);window.LessonKitMarkdown={richText:s=>s,renderMath:()=>{}};
// Mirror workbench.js aiEditPendingMessage: model owns the text; the editor
// resyncs the model on input; a queue re-render rebuilds from the model.
window.queueModel={text:'server text'};
window.renderQueue=function(edit){
  var card=document.getElementById('qcard');card.innerHTML='';
  if(!edit)return;
  var t=document.createElement('textarea');t.className='ai-pending-editor';
  t.value=window.queueModel.text;
  t.addEventListener('input',function(){window.queueModel.text=t.value;});
  card.appendChild(t);
};</script><script src='/workbench/server/static/live-editor.js'></script>`});
  await page.goto('http://127.0.0.1:38971/runtime-fixture');
  await page.waitForTimeout(1200);
  await page.evaluate(() => { const el=document.querySelector('#ai-input');el.value='unsent 中文';el.setSelectionRange(2,5); });
  // User edits a queued message: editor opens, keystrokes sync the model.
  await page.evaluate(() => {
    window.renderQueue(true);
    const t=document.querySelector('.ai-pending-editor');
    t.value='排队编辑草稿';
    t.dispatchEvent(new Event('input',{bubbles:true}));
  });
  generation++;
  await page.waitForTimeout(1500);
  // After reload the bootstrap renders the queue read-only; the user opens
  // the editor again, then the queue re-renders from the model.
  await page.evaluate(() => window.renderQueue(true));
  await page.waitForTimeout(100);
  await page.evaluate(() => window.renderQueue(true));
  const result=await page.evaluate(()=>({value:document.querySelector('#ai-input').value,selection:[document.querySelector('#ai-input').selectionStart,document.querySelector('#ai-input').selectionEnd],submitted:document.querySelector('#submitted').value,sent:window.sent,queue:document.querySelector('.ai-pending-editor').value,queueModel:window.queueModel.text}));
  if(loads!==2 || result.value!=='unsent 中文' || String(result.selection)!=='2,5' || result.submitted!=='submitted' || result.sent!==0) throw new Error(JSON.stringify({loads,result}));
  if(result.queue!=='排队编辑草稿' || result.queueModel!=='排队编辑草稿') throw new Error('queue edit draft lost after re-render: '+JSON.stringify(result));
  await page.evaluate(()=>document.querySelector('#ai-input').dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true})));
  generation++;
  await page.waitForTimeout(1200);
  if(loads!==2) throw new Error('IME composition was interrupted');
  await page.evaluate(()=>document.querySelector('#ai-input').dispatchEvent(new CompositionEvent('compositionend',{bubbles:true})));
  await page.waitForTimeout(1200);
  if(loads!==3) throw new Error('IME completion did not resume refresh');
  return {loads,result};
}
