// Node unit smoke test of the render functions against the live API.
// This is not browser automation or a substitute for visual browser QA.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const origin=process.argv[2]||'http://127.0.0.1:8765';
const isStatic=process.argv.includes('--static');
class Element {
  constructor(){this.value='';this.innerHTML='';this.textContent='';this.dataset={};this.children=[];this.attributes={};this.listeners={};}
  append(child){this.children.push(child);}
  setAttribute(key,value){this.attributes[key]=value;}
  removeAttribute(key){delete this.attributes[key];}
  addEventListener(event,fn){this.listeners[event]=fn;}
  reportValidity(){return true;}
  showModal(){this.open=true;}
  close(){this.open=false;}
}
const elements=new Map();
const nodes=['executive','sales','delivery','experience'].map(page=>{const e=new Element();e.dataset.page=page;return e;});
const context=vm.createContext({
  document:{getElementById(id){if(!elements.has(id))elements.set(id,new Element());return elements.get(id);},querySelectorAll(){return nodes;},createElement(){return new Element();}},
  window:new Element(),location:{hash:'#executive'},URLSearchParams,AbortController,Intl,console,
  URL,Response,Blob,DecompressionStream,TextDecoder,DOMException,setTimeout,
  fetch:(path,opts)=>fetch(new URL(path,origin+'/'),opts)
});
if(isStatic){
  vm.runInContext(fs.readFileSync(new URL('../docs/engine.js',import.meta.url),'utf8'),context);
  vm.runInContext(fs.readFileSync(new URL('../docs/static-api.js',import.meta.url),'utf8'),context);
}
const source=fs.readFileSync(new URL('../dashboard/app.js',import.meta.url),'utf8');
vm.runInContext(source.replace(/init\(\);\s*$/,'globalThis.ready=init();'),context);
await context.ready;
assert.equal(elements.get('message').className,'message');
assert.match(elements.get('dashboard').innerHTML,/99,441/);
for(const page of ['executive','sales','delivery','experience']){
  vm.runInContext(`current='${page}';render();`,context);
  const html=elements.get('dashboard').innerHTML;
  assert.ok(html.length>1500,page+' has complete panels');
  assert.doesNotMatch(html,/undefined|NaN|Infinity/);
  assert.equal(nodes.find(n=>n.dataset.page===page).attributes['aria-current'],'page');
}
elements.get('state').value='SP';elements.get('category').value='health_beauty';
await vm.runInContext('load()',context);
assert.match(elements.get('message').textContent,/Category filter/);
assert.match(elements.get('filter-state').textContent,/selected orders/);
elements.get('state').value='does_not_exist';
await vm.runInContext('load()',context);
for(const page of ['executive','sales','delivery','experience']){
  vm.runInContext(`current='${page}';render();`,context);
  assert.match(elements.get('dashboard').innerHTML,/No eligible records/);
  assert.doesNotMatch(elements.get('dashboard').innerHTML,/undefined|NaN|Infinity/);
}
elements.get('start').value='2018-02-01';elements.get('end').value='2018-01-01';
await vm.runInContext('load()',context);
assert.match(elements.get('message').textContent,/end date on or after/);
console.log('PASS: all four page renderers, live data, category filtering, empty selections and date errors. Visual browser QA not performed.');
