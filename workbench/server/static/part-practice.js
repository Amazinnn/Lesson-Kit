/* Per-part controls consume the server's disclosure-safe learner projection. */
(function (root) {
  var labels = {correct:'正确',wrong:'错误',partially_correct:'部分正确',needs_confirmation:'待确认',unprovided:'未作答',pending:'待批改',running:'批改中',completed:'已批改',failed:'批改失败',not_requested:'未请求',hidden:'等待揭晓',submitted:'已提交',withdrawn:'已撤回'};
  function status(p) {
    var g = p.grading && (p.grading.payload || p.grading) || {};
    return (p.locked ? '已提交' : (p.answer || (p.choices || []).length ? '草稿' : '未作答'))
      + (p.stuck ? ' · 不会' : '') + (p.grading_status ? ' · ' + (labels[p.grading_status] || p.grading_status) : '')
      + (g.answer_conclusion ? ' · 答案：' + labels[g.answer_conclusion] : '')
      + (g.process_conclusion ? ' · 过程：' + (g.process_conclusion === 'unprovided' ? '未提供过程' : labels[g.process_conclusion]) : '')
      + (p.objective_verdict === true || p.objective_verdict === 1 ? ' · 正确' : p.objective_verdict === false || p.objective_verdict === 0 ? ' · 错误' : '');
  }
  function mount(o) {
    var node = document.createElement('section'), current, signature, pending = {}, queue = Promise.resolve(), dead = false, requests={}, boundParts=[];
    node.className = 'part-practice'; o.anchor.after(node);
    function granularity() { try { return JSON.parse(localStorage.getItem('wb_settings_' + o.workspace) || '{}').submissionGranularity || 'per_part'; } catch (_) { return 'per_part'; } }
    function body(p) { return {execution_id:o.run().execution_id,position:current.position,part_id:p.id,practice_context:o.context(current)}; }
    function flush() {
      var batch = pending; pending = {};
      Object.keys(batch).forEach(function (id) { var data = batch[id]; queue = queue.catch(function(){}).then(function () { return o.post('/practice/part-draft', data); }).then(function(r){var p=boundParts.find(function(p){return p.id===data.part_id;});if(p && p.sequence===data.sequence)p._dirty=false;if(r.practice)o.accept(r.practice);}); });
      queue = queue.catch(function (e) { Object.keys(batch).forEach(function (id) { if (!pending[id]) pending[id] = batch[id]; }); o.error(e.message); throw e; });
      return queue;
    }
    function save(p) { p._dirty=true;p.sequence=Number(p.sequence || 0)+1; pending[current.position+':'+p.id] = Object.assign(body(p), {answer:p.answer || '',choices:p.choices || [],stuck:!!p.stuck,sequence:p.sequence}); flush().catch(function () {}); }
    function submit(p) { var data = body(p || {}); if (!p) delete data.part_id; var key=data.execution_id+':'+data.position+':'+(data.part_id || '*'); data.request_id=requests[key] || (requests[key]=root.crypto.randomUUID()); return flush().then(function () { return o.post('/practice/part-submit',data); }).then(function (r) { delete requests[key];o.accept(r.practice || r); }).catch(function (e) { o.error(e.message); }); }
    function result(card,p) {
      card.querySelector('.part-state').textContent = status(p);
      var target = card.querySelector('.part-result'), g = p.grading && (p.grading.payload || p.grading) || {};
      var version=JSON.stringify([p.grading,p.reference_answer,p.reference_reasoning,p.grading_status]);
      var changed=target.dataset.version!==version;
      if(changed)target.replaceChildren();
      function line(label,value) { if (value == null || value === '') return; var block = document.createElement('div'); block.className = 'wb-reading'; var title = document.createElement('strong'); title.textContent=label; var text=document.createElement('div'); text.innerHTML=o.richText(String(value)); block.append(title,text); target.append(block); }
      if(changed){
        if (p.type !== 'proof') { line('你的答案',g.extracted_answer); line('参考答案',g.reference_answer || p.reference_answer); }
        line('参考过程',g.reference_reasoning || p.reference_reasoning); line('点评',g.feedback);
        if(p.grading_status==='failed'){var retry=document.createElement('button');retry.type='button';retry.textContent='重试批改';retry.addEventListener('click',function(){o.post('/grading',{action:'retry',attempt_id:p.attempt_id}).then(refresh).catch(function(e){o.error(e.message);});});target.append(retry);}
        target.dataset.version=version;
      }
      card.querySelectorAll('textarea,input,.part-submit,.part-stuck').forEach(function (el) { el.disabled=!!p.locked || o.archived(); });
      if(changed)o.math(target);
    }
    function update(item) {
      current=item;
      if (!item || !item.part_items || !item.part_items.length) { node.hidden=true; signature=null; return false; }
      node.hidden=false;
      var next=String(o.run().execution_id || o.run().run_id) + ':' + item.position + ':' + item.part_items.map(function(p){return p.id;}).join(',');
      if (signature !== next) {
        signature=next; node.replaceChildren();boundParts=item.part_items;
        var summary=document.createElement('p');summary.className='part-summary';summary.setAttribute('aria-live','polite');node.append(summary);
        item.part_items.forEach(function(p,index) {
          var card=document.createElement('section'); card.className='part-card'; card.dataset.partId=p.id;
          var prompt=document.createElement('div'); prompt.className='wb-reading part-prompt'; prompt.innerHTML=o.richText(p.prompt || '作答');
          var heading=document.createElement('h3'); heading.textContent='小问 '+(index+1);
          var state=document.createElement('p'); state.className='part-state'; state.setAttribute('aria-live','polite'); card.append(heading,prompt,state);
          if (['yes_no','single_choice','multiple_choice'].includes(p.type)) {
            (p.options || (p.type==='yes_no' ? ['是','否']:[])).forEach(function(value) { var label=document.createElement('label'), input=document.createElement('input'); input.type=p.type==='multiple_choice'?'checkbox':'radio'; input.name='part-'+p.id; input.checked=(p.choices || []).includes(value); input.addEventListener('change',function(){ p.choices=Array.from(card.querySelectorAll('input:checked')).map(function(i){return i.value;}); save(p); }); input.value=value; label.append(input,document.createTextNode(value)); label.className='part-option'; card.append(label); });
          } else { var input=document.createElement('textarea'); input.rows=6; input.value=p.answer || ''; input.setAttribute('aria-label','小问 '+(index+1)+' 作答与过程'); input.placeholder='在此自由填写答案与过程'; input.addEventListener('input',function(){p.answer=input.value; if(p.answer.trim())p.stuck=false;save(p);}); card.append(input); }
          var actions=document.createElement('div'); actions.className='part-actions';
          var send=document.createElement('button'); send.type='button'; send.className='part-submit'; send.textContent='提交小问'; send.addEventListener('click',function(){submit(p);});
          var stuck=document.createElement('button'); stuck.type='button'; stuck.className='part-stuck outline'; stuck.textContent='不会'; stuck.addEventListener('click',function(){p.stuck=true;save(p); if(granularity()==='per_part')submit(p);}); actions.append(send,stuck);card.append(actions);
          var output=document.createElement('div'); output.className='part-result'; card.append(output);node.append(card);
        });
        var all=document.createElement('button'); all.type='button'; all.className='part-submit-all'; all.textContent='提交本题剩余小问'; all.addEventListener('click',function(){submit();}); node.append(all);
        o.math(node);
      }
      item.part_items=item.part_items.map(function(p){var stable=boundParts.find(function(old){return old.id===p.id;});if(stable && stable!==p){var draft=stable._dirty ? {answer:stable.answer,choices:stable.choices,stuck:stable.stuck,sequence:stable.sequence,_dirty:true}:null;Object.assign(stable,p,draft || {});return stable;}return p;});
      item.part_items.forEach(function(p){ var card=Array.from(node.querySelectorAll('.part-card')).find(function(c){return c.dataset.partId===p.id;}); result(card,p); });
      var s=item.part_summary || {}, text='已提交 '+(s.submitted == null ? item.part_items.filter(function(p){return p.locked;}).length : s.submitted)+' / '+item.part_items.length;
      ['grading','answer','process'].forEach(function(d){Object.keys(s[d] || {}).forEach(function(k){text+=' · '+({grading:'批改',answer:'答案',process:'过程'}[d])+' '+(labels[k] || k)+' '+s[d][k];});});
      node.querySelector('.part-summary').textContent=text;
      preference(); return true;
    }
    function preference() { node.querySelectorAll('.part-submit').forEach(function(b){b.hidden=granularity()==='whole_problem';}); var all=node.querySelector('.part-submit-all');if(all)all.hidden=o.archived() || !!(current && current.part_items.every(function(p){return p.locked;})); }
    function refresh() { if(dead || !current || !current.part_items || !current.part_items.length)return; o.refresh().then(function(item){if(item)update(item);}).catch(function(){}); }
    var timer=setInterval(refresh,1800); root.addEventListener('storage',preference);root.addEventListener('lk-submission-granularity',preference);
    return {update:update,flush:flush,dispose:function(){dead=true;clearInterval(timer);root.removeEventListener('storage',preference);root.removeEventListener('lk-submission-granularity',preference);node.remove();}};
  }
  function preview(button,item) {
    if (!item.part_items || !item.part_items.length)return;
    var card=document.createElement('div'); card.className='part-preview';card.hidden=true;card.tabIndex=0;card.setAttribute('role','region');card.setAttribute('aria-label','各小问做题情况');
    item.part_items.forEach(function(p,index){var line=document.createElement('p');line.textContent='小问 '+(index+1)+'：'+status(p);card.append(line);});
    var wrap=document.createElement('span');wrap.className='part-preview-wrap';button.replaceWith(wrap);wrap.append(button,card);
    var pinned=false;function render(){card.replaceChildren();item.part_items.forEach(function(p,index){var line=document.createElement('p');line.textContent='小问 '+(index+1)+'：'+status(p);card.append(line);});}function show(){render();card.hidden=false;}function hide(){if(!pinned)card.hidden=true;}
    wrap.addEventListener('mouseenter',show);wrap.addEventListener('mouseleave',hide);wrap.addEventListener('focusin',show);wrap.addEventListener('focusout',function(e){if(!wrap.contains(e.relatedTarget))hide();});card.addEventListener('click',function(){pinned=!pinned;});wrap.addEventListener('keydown',function(e){if(e.key==='Escape'){pinned=false;card.hidden=true;}});
  }
  root.PartPractice={mount:mount,preview:preview,status:status};
  if(root.document)root.document.addEventListener('keydown',function(e){if(e.key==='Escape')root.document.querySelectorAll('.part-preview').forEach(function(card){card.hidden=true;});});
}(typeof globalThis==='object'?globalThis:this));
