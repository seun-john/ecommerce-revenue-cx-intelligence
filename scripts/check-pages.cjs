// Compare the browser engine with DuckDB output for every panel and KPI.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const zlib=require('node:zlib');
const engine=require('../dashboard/engine.js');
const pack=JSON.parse(zlib.gunzipSync(fs.readFileSync('docs/analytics.json.gz')));
const cases=JSON.parse(fs.readFileSync('tests/fixtures/pages-parity.json','utf8'));
const keys={monthly:'month',categories:'category',regions:'state',reviews:'score',comparison:'late',sellers:'seller_id',statuses:'status',repeats:'purchases',durations:'days'};
function compare(actual,expected,path){
 if(typeof expected==='number'){assert.ok(typeof actual==='number'&&Math.abs(actual-expected)<=Math.max(1e-8,Math.abs(expected)*1e-10),`${path}: ${actual} != ${expected}`);return;}
 if(expected===null||typeof expected!=='object'){assert.equal(actual,expected,path);return;}
 if(Array.isArray(expected)){assert.equal(actual.length,expected.length,path+' length');expected.forEach((v,i)=>compare(actual[i],v,path+'['+i+']'));return;}
 for(const key of Object.keys(expected))compare(actual[key],expected[key],path+'.'+key);
}
for(const [index,c] of cases.entries()){
 const actual=engine.analyse(pack,c.filters);
 compare(actual.summary,c.expected.summary,`case ${index}.summary`);
 for(const [table,key] of Object.entries(keys)){
  const sort=rows=>[...rows].sort((a,b)=>String(a[key]).localeCompare(String(b[key])));
  compare(sort(actual[table]),sort(c.expected[table]),`case ${index}.${table}`);
 }
 console.log('PASS case',index,JSON.stringify(c.filters));
}
// Explicitly verify the minimised public schema and exact source population.
assert.equal(pack.orders.length,99441);assert.equal(pack.items.length,112650);
assert.ok(pack.orders.every(r=>r.length===11&&Number.isInteger(r[1])));
assert.ok(pack.items.every(r=>r.length===5));
assert.ok(pack.sellers.every(r=>/^S\d{4}$/.test(r[0])));
console.log('PASS: 11 filter populations; all KPIs and nine analytical tables match DuckDB. Public schema minimised.');
