/* The visual source is frozen in docs/design/approved-practice-combo. */
(function (root) {
  var nextId = 0;
  var MARKUP = "<div class=\"combo-scene\" data-combo-part=\"combo-scene\" aria-hidden=\"true\"><div class=\"combo-aura\"></div><div class=\"combo-ribbon\"><div class=\"ribbon-grain\"></div><span class=\"combo-kicker\">KEEP THE SPARK</span><div class=\"combo-inside\"><span data-combo-part=\"celebration-number\" class=\"celebration-number\">5</span><svg data-combo-part=\"combo-writing\" viewBox=\"0 0 390 125\" aria-hidden=\"true\"><defs><clipPath id=\"APPROVED_CLIP\"><rect data-combo-part=\"writing-reveal\" x=\"0\" y=\"0\" width=\"0\" height=\"125\"/></clipPath></defs><g data-combo-part=\"lettering\" clip-path=\"url(#APPROVED_CLIP)\" fill=\"currentColor\"><path d=\"M54.01 103.53Q44.47 103.53 38.94 97.97Q33.41 92.41 33.41 82.16Q33.41 75.35 35.51 69.11Q37.61 62.87 41.37 58.02Q45.13 53.17 50.88 50.09Q56.63 47.01 63.66 47.01Q71.45 47.01 75.51 50.31Q79.57 53.6 79.57 58.62Q79.57 62.38 77.8 65.21Q76.03 68.05 72.49 68.05Q69.54 68.05 68.07 66.58Q66.6 65.1 66.6 63.31Q66.6 61.56 67.8 58.54Q69 55.51 69.71 53.66Q69.11 52.19 67.04 51.51Q64.96 50.83 62.73 50.83Q55.32 50.83 49.95 59.46Q44.58 68.1 44.58 80.64Q44.58 88.38 48.04 92.93Q51.5 97.48 57.39 97.48Q62.68 97.48 66.79 94.64Q70.9 91.81 74.67 86.63L77.77 88.92Q74.01 94.86 67.55 99.19Q61.1 103.53 54.01 103.53Z\"/><path d=\"M136.69 68.43Q136.69 74.86 134.51 81.29Q132.33 87.72 128.18 92.57Q123.99 97.59 118.07 100.61Q112.16 103.63 104.37 103.63Q95.32 103.63 89.68 97.8Q84.04 91.97 84.04 82.11Q84.04 74.86 86.44 68.59Q88.84 62.32 92.87 57.58Q96.96 52.84 102.98 49.93Q109 47.01 116.03 47.01Q125.73 47.01 131.21 52.92Q136.69 58.84 136.69 68.43ZM125.57 66.36Q125.57 58.62 122.82 54.75Q120.06 50.88 114.89 50.88Q110.36 50.88 106.36 53.66Q102.35 56.44 99.46 62.71Q97.23 67.45 96.19 73.25Q95.16 79.06 95.16 83.96Q95.16 91.75 97.85 95.76Q100.55 99.77 106 99.77Q110.85 99.77 114.61 96.71Q118.37 93.66 120.72 88.97Q123.06 84.4 124.31 78.48Q125.57 72.57 125.57 66.36Z\"/><path d=\"M235.33 95.84 234.51 99.33Q229.5 101.35 226.5 102.14Q223.5 102.93 221.38 102.93Q217.02 102.93 214.84 100.66Q212.66 98.4 212.66 95.08Q212.66 93.88 212.88 92.44Q213.09 90.99 213.58 89.03L218.93 68.7Q219.52 66.36 219.88 64.45Q220.23 62.54 220.23 61.4Q220.23 57.75 218.65 55.62Q217.07 53.5 213.64 53.5Q209.99 53.5 206.47 55.21Q202.96 56.93 198.54 61.62L189.06 102H178.92L187.48 65.59Q187.75 64.4 188 63.06Q188.24 61.72 188.24 61.07Q188.24 57.53 186.47 55.51Q184.7 53.5 181.27 53.5Q178.16 53.5 174.4 55.05Q170.64 56.6 165.68 62L156.47 102H146.33L154.45 66.68Q154.89 64.78 155.3 62.6Q155.71 60.42 155.71 58.89Q155.71 55.73 154.67 54.72Q153.63 53.71 150.64 53.71Q149.44 53.71 147.56 54.15Q145.68 54.59 144.64 54.86L145.46 51.37Q149.71 49.46 152.98 48.54Q156.25 47.61 158.59 47.61Q162.95 47.61 164.78 49.98Q166.61 52.35 166.71 56.44H167.04Q173.47 51.37 177.61 49.19Q181.76 47.01 187.48 47.01Q192.33 47.01 195.35 49.82Q198.38 52.62 198.76 56.87H198.98Q204.81 52.02 209.36 49.52Q213.91 47.01 219.96 47.01Q225.19 47.01 228 50.03Q230.81 53.06 230.81 57.96Q230.81 58.95 230.51 61.45Q230.21 63.96 229.55 66.41L224.97 83.91Q224.48 85.65 224.05 87.91Q223.61 90.17 223.61 91.43Q223.61 94.53 224.92 95.65Q226.23 96.77 229.33 96.77Q230.37 96.77 232.33 96.5Q234.29 96.22 235.33 95.84Z\"/><path d=\"M296.48 67.83Q296.48 75.08 293.86 81.7Q291.25 88.32 286.94 93.12Q282.53 98.02 276.97 100.83Q271.41 103.63 265.2 103.63Q260.51 103.63 256.94 102.84Q253.37 102.05 250.86 100.69Q248.3 99.28 246.61 97.5Q244.92 95.73 243.56 93.55L257.62 31.86Q257.89 30.61 258.08 29.71Q258.27 28.81 258.27 27.88Q258.27 25.92 257.62 24.86Q256.97 23.79 255.77 23.25Q254.62 22.76 252.88 22.59Q251.13 22.43 249.34 22.21L250.1 18.89L270.32 17.63L270.86 18.45L262.58 54.69H262.8Q267.7 50.33 271.44 48.67Q275.17 47.01 278.71 47.01Q286.99 47.01 291.74 52.65Q296.48 58.29 296.48 67.83ZM285.25 68.1Q285.25 65.21 284.73 62.3Q284.22 59.38 283.02 57.42Q281.76 55.35 279.58 54.15Q277.4 52.95 274.19 52.95Q272.28 52.95 270.59 53.6Q268.9 54.26 267.1 55.35Q265.52 56.33 264.02 57.72Q262.52 59.11 261.27 60.2L254.02 92.52Q254.19 93.61 255 94.92Q255.82 96.22 257.07 97.2Q258.6 98.46 260.51 99.11Q262.42 99.77 264.7 99.77Q269.01 99.77 272.8 97.23Q276.59 94.7 279.31 90.39Q282.31 85.7 283.78 79.93Q285.25 74.15 285.25 68.1Z\"/><path d=\"M356.59 68.43Q356.59 74.86 354.41 81.29Q352.23 87.72 348.09 92.57Q343.89 97.59 337.98 100.61Q332.07 103.63 324.27 103.63Q315.23 103.63 309.58 97.8Q303.94 91.97 303.94 82.11Q303.94 74.86 306.34 68.59Q308.74 62.32 312.77 57.58Q316.86 52.84 322.88 49.93Q328.9 47.01 335.94 47.01Q345.64 47.01 351.11 52.92Q356.59 58.84 356.59 68.43ZM345.47 66.36Q345.47 58.62 342.72 54.75Q339.97 50.88 334.79 50.88Q330.27 50.88 326.26 53.66Q322.26 56.44 319.37 62.71Q317.13 67.45 316.1 73.25Q315.06 79.06 315.06 83.96Q315.06 91.75 317.76 95.76Q320.46 99.77 325.91 99.77Q330.76 99.77 334.52 96.71Q338.28 93.66 340.62 88.97Q342.97 84.4 344.22 78.48Q345.47 72.57 345.47 66.36Z\"/></g><g data-combo-part=\"flying-brush\"><path d=\"M-2 -3 18 -57 Q20 -63 24 -61 Q28 -59 25 -53 L5 0Z\" fill=\"#221f1a\"/><path d=\"m-2 -3 6-13 8 4L5 4Z\" fill=\"#f5c518\"/><path d=\"M-2 0 C-12 8 -4 16 0 20 C8 14 11 7 5 1Z\" fill=\"#221f1a\"/><circle cx=\"0\" cy=\"19\" r=\"2\" fill=\"#221f1a\"/></g></svg><span class=\"ribbon-star\">✷</span></div><span data-combo-part=\"combo-message\" class=\"combo-message\">灵感正在发热。</span></div></div><div class=\"after-stroke\" data-combo-part=\"after-stroke\" aria-hidden=\"true\"></div>";
  function clamp(x,a,b) { return Math.max(a,Math.min(b,x)); }
  function paint(wrap, age, width, reduced) {
    var part = function (name) { return wrap.querySelector('[data-combo-part="'+name+'"]'); };
    var scene = part('combo-scene');
    var visible = age >= 0 && age < 2100;
    scene.style.visibility = visible ? 'visible' : 'hidden';
    if (visible) {
      var enter=clamp(age/230,0,1), exit=clamp((age-1550)/420,0,1), ease=1-Math.pow(1-enter,3);
      scene.style.opacity=String(reduced ? (age<1550?1:0) : Math.min(enter*2,1)*(1-exit));
      scene.style.transform=reduced?'none':'translateX('+((1-ease)*-width*.7+exit*width*.6)+'px) scale('+(.94+.06*ease)+')';
      var amount=reduced?1:clamp((age-150)/820,0,1);
      part('writing-reveal').setAttribute('width',amount*390);
      var brush=part('flying-brush'), x=28+amount*334;
      var y=76-Math.sin(amount*Math.PI*10)*15-(amount>.55&&amount<.8?Math.sin((amount-.55)/.25*Math.PI)*23:0);
      brush.style.opacity=!reduced&&age>120&&age<1120?'1':'0';
      brush.setAttribute('transform','translate('+x+','+(y-18)+') rotate(-12)');
    } else scene.style.opacity='0';
    part('after-stroke').style.opacity=String(!reduced&&age>=1300&&age<2800?Math.sin((age-1300)/1500*Math.PI)*.65:0);
  }
  function create(target) {
    var wrap=document.createElement('div');
    wrap.className='lk-approved-combo-wrap'; wrap.hidden=true;
    wrap.innerHTML=MARKUP.replace(/APPROVED_CLIP/g,'approved-combo-clip-'+(++nextId));
    wrap.setAttribute('role','status'); wrap.setAttribute('aria-live','polite');
    document.body.appendChild(wrap);
    var frame=0, started=0, disposed=false;
    function bounds() {
      var node=typeof target==='function'?target():target;
      var r=node.getBoundingClientRect(), top=Math.max(0,r.top), bottom=Math.min(window.innerHeight,r.bottom);
      wrap.style.left=r.left+'px'; wrap.style.top=top+'px'; wrap.style.width=r.width+'px';
      wrap.style.height=Math.max(172,bottom-top)+'px';
      return r.width;
    }
    function mode() { return window.lkMotion ? window.lkMotion.mode() : 'full'; }
    function stop() { cancelAnimationFrame(frame); frame=0; wrap.hidden=true; }
    function tick(now) {
      frame=0;
      if(disposed||document.hidden||mode()!=='full') { stop(); return; }
      var age=now-started;
      if(age>=2800) { stop(); return; }
      paint(wrap,age,bounds(),false); frame=requestAnimationFrame(tick);
    }
    function play(number) {
      if(disposed||document.hidden||mode()!=='full') return;
      stop(); bounds(); wrap.hidden=false;
      wrap.setAttribute('aria-label',number+' combo');
      wrap.querySelector('[data-combo-part="celebration-number"]').textContent=String(number);
      wrap.querySelector('[data-combo-part="combo-message"]').textContent=number>=10?'这一束光，正在加速。':'灵感正在发热。';
      started=performance.now(); paint(wrap,0,wrap.clientWidth,false); frame=requestAnimationFrame(tick);
    }
    function visibility() { if(document.hidden) stop(); }
    document.addEventListener('visibilitychange',visibility);
    return {play:play,stop:stop,dispose:function(){disposed=true;stop();document.removeEventListener('visibilitychange',visibility);wrap.remove();}};
  }
  root.ApprovedPracticeCombo={create:create,paint:paint};
}(typeof globalThis==='object'?globalThis:this));
