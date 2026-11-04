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


function previewFixture() {
  const elements = [];
  const handlers = {};
  const document = {
    activeElement: null,
    body: null,
    documentElement: null,
    createElement(tag) {
      const node = {
        tag, children: [], handlers: {}, attributes: {}, hidden: false, parentElement: null,
        setAttribute(key, value) { this.attributes[key] = String(value); },
        addEventListener(key, callback) { (this.handlers[key] ||= []).push(callback); },
        fire(key, event = {}) {
          event.target ||= this;
          for (const callback of this.handlers[key] || []) callback(event);
        },
        append(...children) {
          for (const child of children) { child.parentElement = this; this.children.push(child); }
        },
        replaceChildren(...children) { this.children = []; this.append(...children); },
        replaceWith(replacement) {
          const siblings = this.parentElement.children;
          siblings[siblings.indexOf(this)] = replacement;
          replacement.parentElement = this.parentElement;
        },
        contains(other) {
          while (other) { if (other === this) return true; other = other.parentElement; }
          return false;
        },
        focus() { document.activeElement = this; },
        style: {},
        getBoundingClientRect() { return { top: 0, bottom: 0, left: 0, right: 0, width: 0, height: 0 }; },
        remove() {
          const parent = this.parentElement;
          if (parent) { const index = parent.children.indexOf(this); if (index >= 0) parent.children.splice(index, 1); }
          this.parentElement = null;
        },
      };
      elements.push(node);
      return node;
    },
    addEventListener(key, callback) { (handlers[key] ||= []).push(callback); },
    fire(key, event = {}) { for (const callback of handlers[key] || []) callback(event); },
    querySelectorAll(selector) {
      return selector === '.part-preview'
        ? elements.filter((node) => node.className === 'part-preview') : [];
    },
  };
  const context = { document };
  vm.runInNewContext(
    fs.readFileSync(path.join(__dirname, '../../workbench/server/static/part-practice.js'), 'utf8'),
    context,
  );
  const container = document.createElement('div');
  const button = document.createElement('button');
  container.append(button);
  document.body = document.createElement('body');
  context.PartPractice.preview(button, { part_items: [{ id: 'p-1', answer: '草稿' }] });
  const wrap = container.children[0];
  const card = document.body.children[0];
  return { document, container, button, wrap, card };
}

test('Escape resets pinned preview, so the next mouseleave hides it', () => {
  const { document, wrap, card } = previewFixture();
  wrap.fire('mouseenter');
  assert.equal(card.hidden, false);
  card.fire('click');
  assert.equal(card.attributes['aria-pressed'], 'true');
  document.fire('keydown', { key: 'Escape' });
  assert.equal(card.hidden, true);
  assert.equal(card.attributes['aria-pressed'], 'false');
  wrap.fire('mouseenter');
  wrap.fire('mouseleave');
  assert.equal(card.hidden, true);
});

test('preview supports Enter/Space pinning and outside-pointer dismissal', () => {
  const { document, container, button, wrap, card } = previewFixture();
  assert.equal(container.children.length, 1);
  assert.equal(wrap.children.length, 1); // card is portaled to document.body
  assert.equal(wrap.children[0], button);
  wrap.fire('focusin');
  let prevented = false;
  card.fire('keydown', { key: 'Enter', preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(card.attributes['aria-pressed'], 'true');
  wrap.fire('mouseleave');
  assert.equal(card.hidden, false);
  const outside = document.createElement('div');
  document.fire('pointerdown', { target: outside });
  assert.equal(card.hidden, true);
  assert.equal(card.attributes['aria-pressed'], 'false');
  wrap.fire('focusin');
  card.fire('keydown', { key: ' ', preventDefault() {} });
  assert.equal(card.attributes['aria-pressed'], 'true');
  card.fire('keydown', { key: ' ', preventDefault() {} });
  assert.equal(card.attributes['aria-pressed'], 'false');
});

test('Escape from the focused preview restores question focus without reopening it', () => {
  const { document, button, wrap, card } = previewFixture();
  button.focus = () => {
    document.activeElement = button;
    wrap.fire('focusin', { target: button }); // real browser bubbles focusin
  };
  card.focus();
  wrap.fire('focusin', { target: card });
  card.fire('click');
  document.fire('keydown', { key: 'Escape' });
  assert.equal(document.activeElement, button);
  assert.equal(card.hidden, true);
  assert.equal(card.attributes['aria-pressed'], 'false');
});
