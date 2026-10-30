"""Create a portable GitHub Pages build from validated, minimised source analytics."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import html as html_module
import pandas as pd
import duckdb
from .acquire import ROOT
from .dashboard import metadata,analyse,serial

CASES=[{}, {'status':['delivered']}, {'state':['SP'],'status':['delivered']},
 {'category':['health_beauty'],'state':['SP'],'start':['2018-01-01'],'end':['2018-03-31']},
 {'status':['canceled']}, {'state':['no_matching_state']},
 {'category':['bed_bath_table']}, {'start':['2017-11-01'],'end':['2017-11-30']},
 {'status':['unavailable']}, {'category':['Unknown']},
 {'start':['2016-11-01'],'end':['2016-11-30']}]

def build():
    dest=ROOT/'docs'
    manifest=json.loads((ROOT/'reports/run_status.json').read_text())
    if manifest['status']!='success':
        raise RuntimeError('A successful pipeline build is required before publication')
    with duckdb.connect(str(ROOT/'data/olist.duckdb'),read_only=True) as db:
        meta=metadata(db)
        states=meta['states'];statuses=meta['statuses'];categories=meta['categories']
        raw=db.execute('SELECT * FROM fact_orders ORDER BY order_id').df()
        order_map={value:i for i,value in enumerate(raw.order_id)}
        customers={value:i for i,value in enumerate(sorted(raw.customer_unique_id.unique()))}
        seller_rows=db.execute('SELECT seller_id,seller_city FROM sellers ORDER BY seller_id').fetchall()
        seller_map={value[0]:i for i,value in enumerate(seller_rows)}
        # Public seller pseudonyms are stable within this extract. No source order,
        # customer or seller identifiers, review text, ZIPs or coordinates are shipped.
        sellers=[[f'S{i+1:04d}',city] for i,(_,city) in enumerate(seller_rows)]
        orders=[]
        for r in raw.itertuples():
            late=None if pd.isna(r.is_late) else int(r.is_late)
            seconds=None if pd.isna(r.delivery_days) else round(r.delivery_days*86400)
            orders.append([str(r.purchase_date.date()),customers[r.customer_unique_id],states.index(r.customer_state),
              statuses.index(r.order_status),int(r.gmv_cents),int(r.freight_cents),
              None if pd.isna(r.payment_cents) else int(r.payment_cents),int(r.item_count),
              None if pd.isna(r.review_score) else int(r.review_score),late,seconds])
        items=[]
        for oid,category,sid,price,freight in db.execute('SELECT i.order_id,p.category,i.seller_id,i.price_cents,i.freight_cents FROM items i JOIN dim_products p USING(product_id) ORDER BY i.order_id,i.order_item_id').fetchall():
            items.append([order_map[oid],categories.index(category),seller_map[sid],price,freight])
        pack={'schema_version':1,'meta':meta,'states':states,'statuses':statuses,'categories':categories,'sellers':sellers,
          'order_columns':['purchase_date','customer_code','state_index','status_index','gmv_cents','freight_cents','payment_cents','item_count','review_score','is_late','delivery_seconds'],
          'item_columns':['order_index','category_index','seller_index','price_cents','freight_cents'],
          'orders':orders,'items':items,
          'licence':'CC BY-NC-SA 4.0; Olist; derived analytical extract; source identifiers replaced; no review text'}
        content=json.dumps(pack,default=serial,separators=(',',':'),allow_nan=False).encode()
        (dest/'analytics.json.gz').write_bytes(gzip.compress(content,compresslevel=9,mtime=0))
        fixtures=[]
        for query in CASES:
            expected=analyse(db,query)
            for seller in expected['sellers']:
                seller['seller_id']=sellers[seller_map[seller['seller_id']]][0]
            fixtures.append({'filters':{k:v[0] for k,v in query.items()},'expected':expected})
        fixture_dir=ROOT/'tests/fixtures';fixture_dir.mkdir(exist_ok=True)
        (fixture_dir/'pages-parity.json').write_text(json.dumps(fixtures,default=serial,separators=(',',':')),encoding='utf-8')
    for name in ['app.js','styles.css','engine.js','static-api.js']:
        shutil.copyfile(ROOT/'dashboard'/name,dest/name)
    html=(ROOT/'dashboard/index.html').read_text(encoding='utf-8')
    html=html.replace('href="/styles.css"','href="styles.css"').replace('src="/app.js"','src="app.js"')
    html=html.replace('<script src="app.js" defer></script>','<script src="engine.js" defer></script>\n  <script src="static-api.js" defer></script>\n  <script src="app.js" defer></script>')
    html=html.replace('LOCAL WORKSPACE','PUBLIC PORTFOLIO').replace('Local, read-only analytics','Historical, read-only analytics')
    html=html.replace('</footer>','<a href="attribution.html">Data licence &amp; attribution</a></footer>')
    shutil.copyfile(ROOT/'DATA_LICENSE.md',dest/'DATA_LICENSE.md')
    attribution='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Olist dataset attribution</title><style>body{max-width:800px;margin:50px auto;padding:0 24px;font:16px/1.7 system-ui;color:#203344}a{color:#007c78}pre{white-space:pre-wrap;font:inherit}</style></head><body><a href="./">← Dashboard</a><h1>Dataset attribution &amp; licence</h1><p>Original dataset: <a href="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce">Brazilian E-Commerce Public Dataset by Olist</a>.</p><p>Derived analytical data and graphics: <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>. Independent, noncommercial portfolio analysis; no Olist endorsement is implied.</p><pre>'''
    attribution+=html_module.escape((ROOT/'DATA_LICENSE.md').read_text(encoding='utf-8'))+'</pre></body></html>'
    (dest/'attribution.html').write_text(attribution,encoding='utf-8')
    app=(dest/'app.js').read_text(encoding='utf-8').replace("['seller_id','Seller ID']","['seller_id','Seller code']")
    app=app.replace('top 50 by selected-item GMV','top 50 by selected-item GMV · seller codes are pseudonyms')
    (dest/'app.js').write_text(app,encoding='utf-8')
    # Asset versions prevent visitors retaining an older UI after deployment.
    for name in ['styles.css','engine.js','static-api.js','app.js']:
        version=hashlib.sha256((dest/name).read_bytes()).hexdigest()[:12]
        html=html.replace('"'+name+'"','"'+name+'?v='+version+'"')
    (dest/'index.html').write_text(html,encoding='utf-8')
    (dest/'.nojekyll').touch()
    info={'orders':len(orders),'items':len(items),'json_bytes':len(content),'gzip_bytes':(dest/'analytics.json.gz').stat().st_size,
      'source':'Original Olist dataset; see reports/source_manifest.json','source_identifiers_included':False,'review_text_included':False,
      'schema_version':1,'parity_filter_cases':len(CASES)}
    (ROOT/'reports/pages_build.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    print(json.dumps(info,indent=2))

if __name__=='__main__':
    build()
