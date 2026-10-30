'use strict';
const $=id=>document.getElementById(id);
const request=(path,options)=>globalThis.OLIST_STATIC?OLIST_STATIC.request(path,options):fetch(path,options);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=value=>value===null||value===undefined?'—':new Intl.NumberFormat('en-GB',{maximumFractionDigits:0}).format(value);
const decimal=(value,d=2)=>value===null||value===undefined?'—':Number(value).toLocaleString('en-GB',{minimumFractionDigits:d,maximumFractionDigits:d});
const money=value=>value===null||value===undefined?'—':'R$ '+decimal(value);
const compact=value=>value===null||value===undefined?'—':new Intl.NumberFormat('en-GB',{notation:'compact',maximumFractionDigits:2}).format(value);
const pct=value=>value===null||value===undefined?'—':decimal(value*100,1)+'%';
const human=value=>String(value).replaceAll('_',' ');
const PAGE={
 executive:{title:'Executive overview',subtitle:'The commercial picture, with the customer experience behind it.',table:'regions'},
 sales:{title:'Sales & product performance',subtitle:'Understand category contribution and the shipping charges behind each sale.',table:'categories'},
 delivery:{title:'Delivery & operations',subtitle:'Track promise accuracy, delivery duration and operational exceptions.',table:'sellers'},
 experience:{title:'Customer experience',subtitle:'Connect customer feedback, delivery outcomes and observed repeat purchasing.',table:'comparison'}
};
let meta,data,current='executive',active=new URLSearchParams(),controller,sequence=0;
const card=(label,value,note,amber=false)=>`<article class="kpi ${amber?'amber':''}"><p class="kpi-label">${esc(label)}</p><div class="kpi-value">${value}</div><div class="kpi-unit">${note}</div></article>`;
const panel=(title,subtitle,body,tag='')=>`<section class="panel"><div class="panel-header"><div><h2>${esc(title)}</h2><p class="panel-sub">${esc(subtitle)}</p></div>${tag?`<span class="tag">${esc(tag)}</span>`:''}</div>${body}</section>`;
const empty=()=>'<p class="empty">No eligible records in this selection.</p>';

function bars(rows,label,value,format=compact,action='',limit=8){
 if(!rows.length)return empty();
 const shown=rows.slice(0,limit),max=Math.max(...shown.map(r=>Number(r[value])||0),1);
 return '<div class="bars">'+shown.map(r=>{
  const attrs=action?` data-filter="${action}" data-value="${esc(r[label])}"`:'';
  const tag=action?'button':'div';
  return `<${tag} class="bar-row ${action?'clickable':''}"${attrs} title="${esc(human(r[label]))}: ${esc(format(r[value]))}"><span class="bar-label">${esc(human(r[label]))}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(0,Number(r[value])||0)/max*100}%"></div></div><span class="bar-number">${esc(format(r[value]))}</span></${tag}>`;
 }).join('')+'</div>';
}

function line(rows,key,label,format=compact,orange=false){
 const valid=rows.filter(r=>r[key]!==null&&r[key]!==undefined);
 if(!valid.length)return empty();
 const w=650,h=245,left=52,right=18,top=20,bottom=40,plotW=w-left-right,plotH=h-top-bottom;
 const dateAt=r=>Date.parse(String(r.month).slice(0,10)+'T00:00:00Z');
 const lo=Math.min(...rows.map(dateAt)),hi=Math.max(...rows.map(dateAt));
 const max=Math.max(...valid.map(r=>r[key]),key==='late_rate'?.01:1)*1.15;
 const x=r=>left+(dateAt(r)-lo)/(hi-lo||1)*plotW,y=v=>top+plotH-(v/max)*plotH;
 const points=valid.map(r=>`${x(r)},${y(r[key])}`).join(' ');
 const desc=valid.map(r=>`${String(r.month).slice(0,7)}: ${format(r[key])}`).join('; ');
 let svg=`<svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(label)}"><title>${esc(label)}</title><desc>${esc(desc)}</desc>`;
 for(let i=0;i<=4;i++){let v=max*i/4,yy=y(v);svg+=`<line class="gridline" x1="${left}" x2="${w-right}" y1="${yy}" y2="${yy}"/><text x="${left-8}" y="${yy+4}" text-anchor="end">${esc(format(v))}</text>`;}
 if(valid.length>1)svg+=`<polygon class="area" points="${x(valid[0])},${top+plotH} ${points} ${x(valid.at(-1))},${top+plotH}"/>`;
 svg+=`<polyline class="line ${orange?'orange':''}" points="${points}"/>`;
 valid.forEach((r,i)=>{svg+=`<circle class="point" cx="${x(r)}" cy="${y(r[key])}" r="3"><title>${esc(String(r.month).slice(0,7))}: ${esc(format(r[key]))}</title></circle>`;if(i%Math.max(1,Math.ceil(valid.length/5))===0||i===valid.length-1)svg+=`<text x="${x(r)}" y="${h-14}" text-anchor="middle">${esc(String(r.month).slice(0,7))}</text>`;});
 return svg+'</svg>';
}

function table(rows,columns,limit=50){
 if(!rows.length)return empty();
 return `<div class="table-wrap"><table><thead><tr>${columns.map(c=>`<th scope="col" class="${c[2]?'number':''}">${esc(c[1])}</th>`).join('')}</tr></thead><tbody>${rows.slice(0,limit).map(r=>'<tr>'+columns.map(c=>{
 const value=c[2]?c[2](r[c[0]]):esc(human(r[c[0]]));
 return `<td class="${c[2]?'number':'long'}" title="${esc(r[c[0]])}">${c[3]?`<button class="table-action" data-filter="${c[3]}" data-value="${esc(r[c[0]])}">${value}</button>`:value}</td>`;
 }).join('')+'</tr>').join('')}</tbody></table></div>`;
}

function compare(rows){
 if(!rows.length)return empty();
 return rows.map(r=>`<div class="score-row"><span>${r.late?'Late':'On time'}</span><div class="score-track"><div class="score-fill ${r.late?'late':''}" style="width:${r.mean_review/5*100}%"></div></div><strong>${decimal(r.mean_review)}</strong></div><p class="small-note">${r.late?'Late':'On time'}: ${num(r.orders)} reviewed orders · ${pct(r.low_review_rate)} low scores</p>`).join('')+'<p class="small-note">Score scale: 1–5. These groups show an association, not a causal effect.</p>';
}

function trendRows(rows){
 // A calendar spine prevents a missing month from being skipped by trend lines.
 if(!rows.length)return [];
 const start=new Date(active.get('start').slice(0,7)+'-01T00:00:00Z'),end=new Date(active.get('end').slice(0,7)+'-01T00:00:00Z');
 const by=new Map(rows.map(r=>[String(r.month).slice(0,7),r]));
 const result=[];
 for(let d=new Date(start);d<=end;d.setUTCMonth(d.getUTCMonth()+1)){
  const k=d.toISOString().slice(0,7);result.push(by.get(k)||{month:k+'-01',orders:0,gmv:0,late_rate:null,mean_review:null});
 }
 return result;
}

function executive(d){
 const s=d.summary,monthly=trendRows(d.monthly);
 return `<div class="kpis">${card('ITEM GROSS MERCHANDISE VALUE',money(s.item_gmv),'Selected item prices · freight excluded')}${card('PLACED ORDERS',num(s.orders),`${num(s.delivered_orders)} delivered orders`)}${card('AVERAGE ORDER VALUE',money(s.aov),`${num(s.selected_item_orders)} selected item-bearing orders`)}${card('DELIVERY PROMISE MISSES',pct(s.late_rate),`${num(s.late_orders)} late / ${num(s.delivery_eligible)} eligible`,true)}</div>
 <div class="grid">${panel('Merchandise value over time','Purchase month · nominal BRL',line(monthly,'gmv','Monthly item GMV'),'MONTHLY')}${panel('Where sales are concentrated','Top 8 destination states · click a state to filter',bars(d.regions,'state','gmv',v=>'R$ '+compact(v),'state'),'REGIONAL')}</div>
 <div class="strip"><div><strong>${pct(s.cancellation_rate)}</strong><span>Cancellation rate · ${num(s.canceled_orders)} canceled / ${num(s.orders)} placed</span></div><div><strong>${decimal(s.mean_review)} / 5</strong><span>Selected review mean · ${num(s.reviewed_orders)} reviewed orders</span></div><div><strong>${money(s.matched_payment_gap)}</strong><span>Matched-order payment gap · ${num(s.missing_payment_orders)} orders without payments</span></div></div>
 ${panel('Regional performance','All destination states in the current selection',table(d.regions,[['state','State',null,'state'],['orders','Orders',num],['gmv','Item GMV',money],['eligible','Delivery eligible',num],['late_rate','Late rate',pct],['mean_review','Review / 5',decimal]]))}`;
}

function sales(d){
 const s=d.summary;
 return `<div class="kpis">${card('SELECTED ITEM GMV',money(s.item_gmv),'Current status selection applies')}${card('ITEMS SOLD',num(s.items),`${num(s.selected_item_orders)} distinct item-bearing orders`)}${card('ITEM-BEARING ORDER AOV',money(s.aov),'Selected item GMV / selected item orders')}${card('FREIGHT / MERCHANDISE VALUE',pct(s.freight_ratio),'Shipping-charge burden proxy · not margin',true)}</div>
 <div class="grid">${panel('Category contribution','Top 10 by selected item GMV · click to drill into category',bars(d.categories,'category','gmv',v=>'R$ '+compact(v),'category',10),'ITEM GRAIN')}${panel('Shipping-charge burden','Top categories by freight / GMV · at least 30 items',bars(d.categories.filter(r=>r.items>=30).sort((a,b)=>(b.freight_ratio||0)-(a.freight_ratio||0)),'category','freight_ratio',pct,'category',10),'PROXY ONLY')}</div>
 <div class="insight"><strong>Commercial interpretation.</strong> High merchandise value does not establish profitability. Compare category scale with freight burden, then add cost, commission and refund data before making margin decisions. Category order counts overlap on multi-category orders.</div>
 ${panel('Product category detail','All categories in selection · select a category to filter every page',table(d.categories,[['category','Category',null,'category'],['items','Items',num],['orders','Item-bearing orders',num],['gmv','Item GMV',money],['freight','Freight charge',money],['freight_ratio','Freight / GMV',pct]],100))}`;
}

function delivery(d){
 const s=d.summary,eligible=d.regions.filter(r=>r.eligible>=30).sort((a,b)=>(b.late_rate||0)-(a.late_rate||0));
 return `<div class="kpis">${card('DELIVERY-ELIGIBLE ORDERS',num(s.delivery_eligible),`${num(s.delivered_orders-s.delivery_eligible)} delivered orders missing required dates`)}${card('LATE DELIVERY RATE',pct(s.late_rate),`${num(s.late_orders)} missed calendar-day promises`,true)}${card('MEAN DELIVERY DURATION',decimal(s.mean_delivery_days)+' days','Purchase to delivery · nonnegative elapsed time')}${card('P90 DELIVERY DURATION',decimal(s.p90_delivery_days)+' days','90% of eligible durations at or below this value')}</div>
 <div class="grid">${panel('Promise accuracy over time','Late / delivered orders with both dates · purchase month',line(trendRows(d.monthly),'late_rate','Monthly late delivery rate',pct,true),'DELIVERY')}${panel('Regions needing attention','Highest late rates · minimum 30 eligible orders',bars(eligible,'state','late_rate',pct,'state'),'EXCEPTIONS')}</div>
 <div class="insight"><strong>Act on volume and rate together.</strong> Use the seller table to prioritise investigation, then inspect carrier lanes and order timelines. An order-level delivery outcome shared by multiple sellers does not establish which seller caused a delay.</div>
 ${panel('Seller operational review','Delivered seller-orders · minimum 30 delivery-eligible orders · top 50 by selected-item GMV · seller codes are pseudonyms',table(d.sellers,[['seller_id','Seller code'],['city','Seller city'],['orders','Delivered orders',num],['gmv','Item GMV',money],['eligible','Delivery eligible',num],['late_rate','Late rate',pct],['mean_review','Review / 5',decimal]]))}
 <div class="grid equal">${panel('Delivery duration distribution','Five-day buckets; all nonnegative durations retained',bars(d.durations,'days','orders',num,'',15)+'<p class="small-note">Bucket label is the lower bound in days. First 15 buckets displayed; export contains all buckets.</p>')}${panel('Order status mix','Cancellation and unavailable are separate outcomes',bars(d.statuses,'status','orders',num))}</div>`;
}

function experience(d){
 const s=d.summary,reviewed=d.reviews.filter(r=>r.score!==null).map(r=>({...r,label:'Score '+r.score}));
 const repeat=d.repeats.map(r=>({...r,label:r.purchases+' purchase'+(r.purchases===1?'':'s')}));
 return `<div class="kpis">${card('MEAN SELECTED REVIEW',decimal(s.mean_review)+' / 5',`${num(s.reviewed_orders)} reviewed orders`)}${card('LOW REVIEW SHARE',pct(s.low_review_rate),'Scores 1–2 / reviewed orders',true)}${card('OBSERVED REPEAT SHARE',pct(s.repeat_share),`${num(s.repeat_customers)} repeat / ${num(s.delivered_customers)} delivered customers`)}${card('UNREVIEWED ORDERS',num(s.orders-s.reviewed_orders),'Missing reviews are not score zero')}</div>
 <div class="grid equal">${panel('Customer review distribution','Latest answered review per order · scores 1–5',bars(reviewed,'label','orders',num),'FEEDBACK')}${panel('Delivery outcomes & review scores','Reviewed delivered orders with known delivery outcome',compare(d.comparison),'ASSOCIATION')}</div>
 <div class="insight"><strong>Test interventions, do not infer their impact.</strong> Delivery outcome and review scores may share drivers such as geography, product category and season. A controlled pilot is needed to estimate the benefit of proactive messaging or delivery changes.</div>
 <div class="grid equal">${panel('Observed purchases per customer','Delivered purchases in the current selection · customer_unique_id',bars(repeat,'label','customers',num,'',10)+'<p class="small-note">Unequal observation windows. This is observed repeat purchasing, not fixed-horizon retention.</p>')}${panel('Delivery and review comparison','Group denominators exclude unknown delivery outcomes and missing scores',table(d.comparison.map(r=>({...r,outcome:r.late?'Late':'On time'})),[['outcome','Outcome'],['orders','Reviewed orders',num],['mean_review','Mean / 5',decimal],['low_review_rate','Low scores',pct]]))}</div>`;
}

function render(){
 const name=PAGE[current];
 $('title').textContent=name.title;$('subtitle').textContent=name.subtitle;$('breadcrumb').textContent=name.title;
 document.querySelectorAll('[data-page]').forEach(a=>{if(a.dataset.page===current)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 if(!data)return;
 const renderer={executive,sales,delivery,experience}[current];
 $('dashboard').innerHTML=renderer(data)+`<p class="page-note">Population: ${esc(active.get('start'))} to ${esc(active.get('end'))} · ${esc(active.get('state')||'All states')} · ${esc(human(active.get('status')||'All statuses'))}${active.get('category')?' · Orders containing '+esc(human(active.get('category'))):''}. Historical, observational records; boundary months may be partial. All figures respond to the applied filters.</p>`;
 $('filter-state').textContent=num(data.summary.orders)+' selected orders';
 $('export').disabled=false;
}

function collect(){const p=new URLSearchParams();for(const id of ['start','end','state','status','category'])if($(id).value)p.set(id,$(id).value);return p;}
async function load(){
 const form=$('filters');if(!form.reportValidity())return;
 const candidate=collect();if(candidate.get('start')>candidate.get('end')){$('message').textContent='Choose an end date on or after the start date.';$('message').className='message error';return;}
 if(controller)controller.abort();controller=new AbortController();const ticket=++sequence;
 $('dashboard').setAttribute('aria-busy','true');$('export').disabled=true;$('message').className='message';$('message').textContent='Calculating filtered results…';
 try{
  const response=await request('/api/dashboard?'+candidate,{signal:controller.signal});const result=await response.json();if(!response.ok)throw new Error(result.error||'Could not load analysis');if(ticket!==sequence)return;
  active=candidate;data=result;render();
  const scope=active.get('category')?' Category filter: item amounts use matching items; order/service metrics use entire orders containing them.':'';
  $('message').textContent=(data.summary.orders?'Showing '+num(data.summary.orders)+' orders from the original Olist extract.':'No orders match these filters. Try a wider range or reset.')+scope;
 }catch(error){if(error.name==='AbortError')return;$('message').className='message error';$('message').textContent=error.message+(globalThis.OLIST_STATIC?' Reload the page to retry.':' Start the local server if it has stopped.')+' Previous results are hidden until a request succeeds.';$('dashboard').innerHTML='';data=null;}
 finally{if(ticket===sequence)$('dashboard').setAttribute('aria-busy','false');}
}

function setRange(start,end){$('start').value=start;$('end').value=end;}
async function init(){
 current=PAGE[location.hash.slice(1)]?location.hash.slice(1):'executive';render();
 try{
  const response=await request('/api/meta');meta=await response.json();if(!response.ok)throw new Error(meta.error||'Could not load metadata');
  for(const [id,key] of [['state','states'],['status','statuses'],['category','categories']])for(const value of meta[key]){const option=document.createElement('option');option.value=value;option.textContent=human(value);$(id).append(option);}
  for(const id of ['start','end']){$(id).min=meta.start;$(id).max=meta.end;}
  setRange(meta.start,meta.end);
  if(meta.build.status!=='success')throw new Error('The latest data build is not successful. Run python -m src.pipeline before using the dashboard.');
  await load();
 }catch(error){$('message').className='message error';$('message').textContent=error.message;$('dashboard').setAttribute('aria-busy','false');}
}
$('filters').addEventListener('submit',event=>{event.preventDefault();load();});
$('filters').addEventListener('change',()=>{$('filter-state').textContent='Filters changed · click Apply filters';});
$('reset').addEventListener('click',()=>{if(!meta)return;setRange(meta.start,meta.end);for(const id of ['state','status','category'])$(id).value='';load();});
$('full-range').addEventListener('click',()=>{if(meta){setRange(meta.start,meta.end);load();}});
$('full-months').addEventListener('click',()=>{setRange('2017-01-01','2018-08-31');load();});
window.addEventListener('hashchange',()=>{current=PAGE[location.hash.slice(1)]?location.hash.slice(1):'executive';render();});
$('dashboard').addEventListener('click',event=>{const button=event.target.closest('[data-filter]');if(!button)return;$(button.dataset.filter).value=button.dataset.value;load();});
$('export').addEventListener('click',async()=>{if(!data)return;if(globalThis.OLIST_STATIC){try{await OLIST_STATIC.download(PAGE[current].table,active);}catch(error){$('message').textContent='Export failed: '+error.message;}return;}const p=new URLSearchParams(active);p.set('table',PAGE[current].table);const a=document.createElement('a');a.href='/api/export?'+p;a.download='olist_'+PAGE[current].table+'.csv';a.click();});
$('definitions-open').addEventListener('click',()=>$('definitions').showModal());
$('definitions-close').addEventListener('click',()=>$('definitions').close());
init();
