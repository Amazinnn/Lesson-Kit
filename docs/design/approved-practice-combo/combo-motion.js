function renderApprovedCombo(wrap,elapsed,width,reduced=false){
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const $=id=>wrap.querySelector("#"+id), state={reduced},clock=elapsed,comboAt=0,sw=width;
const writingReveal=$("writing-reveal");
  function drawWriting(age) {
    const amount = state.reduced ? 1 : clamp((age-150)/820,0,1);
    writingReveal.setAttribute('width', amount*390);
    const brush = $('flying-brush');
    brush.style.opacity = !state.reduced && age>120 && age<1120 ? '1' : '0';
    const x = 28 + amount*334;
    const y = 76 - Math.sin(amount*Math.PI*10)*15 - (amount>.55 && amount<.8 ? Math.sin((amount-.55)/.25*Math.PI)*23 : 0);
    brush.setAttribute('transform', `translate(${x},${y-18}) rotate(-12)`);
  }
    const age = clock - comboAt, visible = age >= 0 && age < 2100;
    const banner = $('combo-scene');
    banner.style.visibility = visible ? 'visible' : 'hidden';
    if (visible) {
      const enter = clamp(age / 230, 0, 1), exit = clamp((age - 1550) / 420, 0, 1);
      const ease = 1 - Math.pow(1 - enter, 3);
      banner.style.opacity = String(state.reduced ? (age < 1550 ? 1 : 0) : Math.min(enter * 2, 1) * (1 - exit));
      banner.style.transform = state.reduced ? 'none' : `translateX(${(1 - ease) * -sw * .7 + exit * sw * .6}px) scale(${.94 + .06 * ease})`;
      drawWriting(age);
    } else { banner.style.opacity = '0'; }
    $('after-stroke').style.opacity = String(!state.reduced && age >= 1300 && age < 2800 ? Math.sin((age - 1300) / 1500 * Math.PI) * .65 : 0);

}
