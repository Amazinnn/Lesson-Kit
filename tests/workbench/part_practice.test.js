'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const context={};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../workbench/server/static/part-practice.js'),'utf8'),context);
test('subjective answer and process conclusions remain independent',()=>{
  const value=context.PartPractice.status({locked:true,grading_status:'completed',grading:{payload:{answer_conclusion:'correct',process_conclusion:'wrong'}}});
  assert.match(value,/答案：正确/);assert.match(value,/过程：错误/);
});
test('hidden grading projection cannot infer a wrong verdict',()=>{
  const value=context.PartPractice.status({locked:true,grading_status:'completed'});
  assert.doesNotMatch(value,/错误|正确|答案：|过程：/);
});
test('stuck and unprovided process coexist without a synthesized wrong result',()=>{
  const value=context.PartPractice.status({locked:true,stuck:true,grading:{payload:{process_conclusion:'unprovided'}}});
  assert.match(value,/不会/);assert.match(value,/未提供过程/);assert.doesNotMatch(value,/错误/);
});
