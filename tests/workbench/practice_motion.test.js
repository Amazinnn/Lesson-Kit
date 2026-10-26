const test=require('node:test');
const assert=require('node:assert/strict');
const motion=require('../../workbench/server/static/practice-motion.js');
test('comet pulse lights the center before its outer pixels and dims between arrivals',()=>{
 assert(motion.headLight(0,0)>.95);
 assert(motion.headLight(1,0)<.01);
 assert(motion.headLight(1,150)>.7);
 assert(motion.headLight(0,150)<.01);
 assert(motion.headLight(1,500)<.001);
 const ratio=.6,end=200,speed=.065+.095*ratio;
 assert(motion.headAge(end,end/speed,ratio)<1e-8);
});
test('palette, equal density widths and brighter compression preserve approved pixels',()=>{
 assert.deepEqual(motion.color(0),[226,118,44]);assert.deepEqual(motion.color(.5),[246,202,62]);assert.deepEqual(motion.color(1),[132,200,233]);
 for(let x=0;x<56;x+=2)assert(Math.abs(motion.density(x,0,.6)+motion.density(x+56,0,.6)-1)<1e-9);
 assert(motion.density(61,500,.6)>.99);
 const levels=new Set(Array.from({length:101},(_,i)=>motion.tone(.5,i/100).join(',')));assert.equal(levels.size,8);
 const luminance=c=>c[0]*.2126+c[1]*.7152+c[2]*.0722;
 assert(luminance(motion.tone(.5,1))>luminance(motion.tone(.5,0)));
});
test('completion uses item states, not cursor or correctness',()=>{
 assert.equal(motion.completed(['unanswered','correct','wrong','stuck','filled','locked'],false),4);
 assert.equal(motion.completed(['unanswered','correct','wrong','stuck','filled','locked'],true),5);
 assert.deepEqual(motion.phase(0,false),{enter:0,dock:0,summary:0});
 assert.deepEqual(motion.phase(3000,false),{enter:1,dock:1,summary:1});
 assert.deepEqual(motion.phase(0,true),{enter:1,dock:1,summary:1});
});
