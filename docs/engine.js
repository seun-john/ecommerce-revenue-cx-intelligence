/* Shared browser/Node analytics engine. All money is accumulated in centavos. */
(function(root){
 'use strict';
 const ratio=(a,b)=>b?a/b:null;
 const sumOrNull=(n,sum)=>n?sum:null;
 const quantile=(a,p)=>{if(!a.length)return null;const s=[...a].sort((x,y)=>x-y),h=(s.length-1)*p,l=Math.floor(h);return s[l]+(s[Math.ceil(h)]-s[l])*(h-l);};
 const tally=()=>({orders:0,eligible:0,late:0,reviewed:0,reviewSum:0,low:0,days:0,dayCount:0,gmv:0});
 function orderStats(t,o){t.orders++;if(o[9]!==null){t.eligible++;t.late+=o[9];}if(o[8]!==null){t.reviewed++;t.reviewSum+=o[8];t.low+=o[8]<=2?1:0;}if(o[10]!==null){t.days+=o[10]/86400;t.dayCount++;}}
 function analyse(pack,filters={}){
  const {orders,items,states,statuses,categories,sellers}=pack;
  const category=filters.category?categories.indexOf(filters.category):-1;
  const categoryActive=Boolean(filters.category),matches=new Set();
  if(categoryActive)for(const i of items)if(i[1]===category)matches.add(i[0]);
  const selected=new Uint8Array(orders.length),summary=tally(),months=new Map(),regions=new Map(),scores=new Map(),comparisons=new Map(),statusCounts=new Map(),customers=new Map(),durations=new Map(),durationValues=[];
  let gmvCents=0,freightCents=0,payCents=0,payCount=0,gapCents=0,itemBearing=0,delivered=0,canceled=0,missingPay=0;
  for(let idx=0;idx<orders.length;idx++){
   const o=orders[idx],date=o[0],state=states[o[2]],status=statuses[o[3]];
   if(filters.start&&date<filters.start||filters.end&&date>filters.end||filters.state&&state!==filters.state||filters.status&&status!==filters.status||categoryActive&&!matches.has(idx))continue;
   selected[idx]=1;orderStats(summary,o);gmvCents+=o[4];freightCents+=o[5];if(o[7]>0)itemBearing++;
   if(status==='delivered'){delivered++;customers.set(o[1],(customers.get(o[1])||0)+1);}if(status==='canceled')canceled++;
   if(o[6]===null)missingPay++;else{payCount++;payCents+=o[6];gapCents+=o[6]-o[4]-o[5];}
   const m=date.slice(0,7)+'-01';if(!months.has(m))months.set(m,tally());orderStats(months.get(m),o);
   if(!regions.has(state))regions.set(state,tally());orderStats(regions.get(state),o);
   scores.set(o[8],(scores.get(o[8])||0)+1);statusCounts.set(status,(statusCounts.get(status)||0)+1);
   if(o[9]!==null&&o[8]!==null){if(!comparisons.has(o[9]))comparisons.set(o[9],tally());orderStats(comparisons.get(o[9]),o);}
   if(o[10]!==null){const days=o[10]/86400,bucket=Math.floor(days/5)*5;durationValues.push(days);durations.set(bucket,(durations.get(bucket)||0)+1);}
  }
  let itemCents=0,itemFreight=0,itemCount=0;const itemOrders=new Set(),cats=new Map(),sellerOrders=new Map();
  for(const i of items){
   if(!selected[i[0]]||categoryActive&&i[1]!==category)continue;
   const o=orders[i[0]],cat=categories[i[1]],state=states[o[2]];
   itemCount++;itemCents+=i[3];itemFreight+=i[4];itemOrders.add(i[0]);
   months.get(o[0].slice(0,7)+'-01').gmv+=i[3];regions.get(state).gmv+=i[3];
   if(!cats.has(cat))cats.set(cat,{category:cat,items:0,orderSet:new Set(),cents:0,freightCents:0});
   const c=cats.get(cat);c.items++;c.orderSet.add(i[0]);c.cents+=i[3];c.freightCents+=i[4];
   if(statuses[o[3]]==='delivered'){
    const key=i[2]+':'+i[0];if(!sellerOrders.has(key))sellerOrders.set(key,{seller:i[2],order:i[0],cents:0});sellerOrders.get(key).cents+=i[3];
   }
  }
  const sellerMap=new Map();for(const row of sellerOrders.values()){
   if(!sellerMap.has(row.seller))sellerMap.set(row.seller,tally());
   const s=sellerMap.get(row.seller);orderStats(s,orders[row.order]);s.gmv+=row.cents;
  }
  const repeatDist=new Map();let repeatCount=0;for(const n of customers.values()){if(n>1)repeatCount++;repeatDist.set(n,(repeatDist.get(n)||0)+1);}
  return {
   filters,
   summary:{orders:summary.orders,order_gmv:sumOrNull(summary.orders,gmvCents/100),order_freight:sumOrNull(summary.orders,freightCents/100),item_bearing_orders:itemBearing,
    delivered_orders:delivered,canceled_orders:canceled,cancellation_rate:ratio(canceled,summary.orders),delivery_eligible:summary.eligible,late_orders:summary.late,late_rate:ratio(summary.late,summary.eligible),
    mean_delivery_days:ratio(summary.days,summary.dayCount),p90_delivery_days:quantile(durationValues,.9),reviewed_orders:summary.reviewed,mean_review:ratio(summary.reviewSum,summary.reviewed),low_review_rate:ratio(summary.low,summary.reviewed),
    payments:sumOrNull(payCount,payCents/100),matched_payment_gap:sumOrNull(payCount,gapCents/100),missing_payment_orders:missingPay,
    items:itemCount,item_gmv:sumOrNull(itemCount,itemCents/100),item_freight:sumOrNull(itemCount,itemFreight/100),selected_item_orders:itemOrders.size,aov:ratio(itemCents/100,itemOrders.size),freight_ratio:ratio(itemFreight,itemCents),
    delivered_customers:customers.size,repeat_customers:repeatCount,repeat_share:ratio(repeatCount,customers.size)},
   monthly:[...months].sort(([a],[b])=>a.localeCompare(b)).map(([month,t])=>({month,orders:t.orders,eligible:t.eligible,late_rate:ratio(t.late,t.eligible),mean_review:ratio(t.reviewSum,t.reviewed),gmv:t.gmv/100})),
   categories:[...cats.values()].map(c=>({category:c.category,items:c.items,orders:c.orderSet.size,gmv:c.cents/100,freight:c.freightCents/100,freight_ratio:ratio(c.freightCents,c.cents)})).sort((a,b)=>b.gmv-a.gmv||a.category.localeCompare(b.category)),
   regions:[...regions].map(([state,t])=>({state,orders:t.orders,eligible:t.eligible,late_rate:ratio(t.late,t.eligible),mean_days:ratio(t.days,t.dayCount),mean_review:ratio(t.reviewSum,t.reviewed),gmv:t.gmv/100})).sort((a,b)=>b.gmv-a.gmv||a.state.localeCompare(b.state)),
   reviews:[...scores].sort(([a],[b])=>a===null?1:b===null?-1:a-b).map(([score,orders])=>({score,orders})),
   comparison:[...comparisons].sort(([a],[b])=>a-b).map(([late,t])=>({late:Boolean(late),orders:t.orders,mean_review:ratio(t.reviewSum,t.reviewed),low_review_rate:ratio(t.low,t.reviewed)})),
   sellers:[...sellerMap].filter(([,t])=>t.eligible>=30).map(([id,t])=>({seller_id:sellers[id][0],city:sellers[id][1],orders:t.orders,gmv:t.gmv/100,eligible:t.eligible,late_rate:ratio(t.late,t.eligible),reviewed_orders:t.reviewed,mean_review:ratio(t.reviewSum,t.reviewed)})).sort((a,b)=>b.gmv-a.gmv||a.seller_id.localeCompare(b.seller_id)).slice(0,50),
   statuses:[...statusCounts].map(([status,orders])=>({status,orders})).sort((a,b)=>b.orders-a.orders||a.status.localeCompare(b.status)),
   repeats:[...repeatDist].sort(([a],[b])=>a-b).map(([purchases,customers])=>({purchases,customers})),
   durations:[...durations].sort(([a],[b])=>a-b).map(([days,orders])=>({days,orders}))
  };
 }
 root.OlistEngine={analyse,quantile};
 if(typeof module!=='undefined'&&module.exports)module.exports=root.OlistEngine;
})(globalThis);
