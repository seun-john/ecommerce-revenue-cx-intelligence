/* GitHub Pages adapter: calculations are local to the visitor's browser. */
(function(){
 'use strict';
 let ready;
 async function dataset(){
  if(!ready)ready=(async()=>{
   const response=await fetch('analytics.json.gz');if(!response.ok)throw new Error('Could not download the analytical data. Please reload.');
   if(!globalThis.DecompressionStream)throw new Error('This dashboard needs a current version of Edge, Chrome, Firefox or Safari.');
   const bytes=new Uint8Array(await response.arrayBuffer());
   // Some hosts serve .gz with Content-Encoding, which browsers already decode.
   if(bytes[0]!==0x1f||bytes[1]!==0x8b)return JSON.parse(new TextDecoder().decode(bytes));
   const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
   return JSON.parse(await new Response(stream).text());
  })().catch(error=>{ready=null;throw error;});
  return ready;
 }
 function abort(signal){if(signal?.aborted)throw new DOMException('Request canceled','AbortError');}
 globalThis.OLIST_STATIC={
  async request(path,options={}){
   const pack=await dataset();abort(options.signal);
   const url=new URL(path,'https://local.invalid');
   if(url.pathname==='/api/meta')return {ok:true,json:async()=>pack.meta};
   const filters=Object.fromEntries(url.searchParams);delete filters.table;
   const result=OlistEngine.analyse(pack,filters);abort(options.signal);
   return {ok:true,json:async()=>result};
  },
  async download(table,params){
   const pack=await dataset(),result=OlistEngine.analyse(pack,Object.fromEntries(params));
   const rows=result[table];if(!Array.isArray(rows))throw new Error('Unknown export table');
   const fields=rows.length?Object.keys(rows[0]):[];
   const csvCell=value=>'"'+String(value??'').replaceAll('"','""')+'"';
   const csv='\uFEFF'+[fields.map(csvCell).join(','),...rows.map(row=>fields.map(field=>csvCell(row[field])).join(','))].join('\r\n');
   const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),link=document.createElement('a');
   link.href=url;link.download='olist_'+table+'.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
 };
})();
