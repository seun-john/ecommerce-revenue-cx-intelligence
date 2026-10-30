"""Run raw audit -> validated staging -> DuckDB -> SQL -> exports -> evidence."""
from pathlib import Path
import json
import platform
import os
from datetime import datetime, timezone
import importlib.metadata
import numpy as np
import pandas as pd
import duckdb
from .acquire import ROOT, acquire
from .quality import audit

NAMES = {'orders':'olist_orders_dataset.csv','items':'olist_order_items_dataset.csv',
 'payments':'olist_order_payments_dataset.csv','reviews':'olist_order_reviews_dataset.csv',
 'customers':'olist_customers_dataset.csv','products':'olist_products_dataset.csv',
 'sellers':'olist_sellers_dataset.csv','geolocation':'olist_geolocation_dataset.csv',
 'translation':'product_category_name_translation.csv'}

def load(raw):
    # Preserve leading zero ZIP prefixes and opaque identifiers.
    frames = {}
    for name, filename in NAMES.items():
        header = pd.read_csv(raw/filename, nrows=0).columns
        dtype = {c:'string' for c in header if c.endswith('_id') or 'zip_code_prefix' in c}
        frames[name] = pd.read_csv(raw/filename, dtype=dtype)
    return frames

def clean(frames):
    out = {k:v.copy() for k,v in frames.items()}
    out['products']['product_category_name'] = out['products']['product_category_name'].astype('string')
    for name, df in out.items():
        for col in df:
            if any(s in col for s in ['timestamp','_date','shipping_limit']) or col=='order_approved_at':
                parsed = pd.to_datetime(df[col], errors='coerce', format='mixed')
                if (df[col].notna() & parsed.isna()).any():
                    raise ValueError(f'Invalid date: {name}.{col}')
                df[col] = parsed
    for table, col, target in [('items','price','price_cents'),('items','freight_value','freight_cents'),('payments','payment_value','payment_cents')]:
        values = pd.to_numeric(out[table][col], errors='coerce')
        if values.isna().any() or (values<0).any():
            raise ValueError(f'Invalid monetary amount: {table}.{col}')
        out[table][target] = (values*100).round().astype('int64')
    if not out['reviews']['review_score'].between(1,5).all():
        raise ValueError('Review scores must be in 1..5')
    return out

def build_database(frames, path):
    con = duckdb.connect(str(path))
    for name, df in frames.items():
        con.register('_incoming', df)
        con.execute(f'CREATE OR REPLACE TABLE {name} AS SELECT * FROM _incoming')
        con.unregister('_incoming')
    con.execute((ROOT/'sql/schema.sql').read_text(encoding='utf-8'))
    if con.sql('SELECT count(*)-count(DISTINCT order_id) FROM fact_orders').fetchone()[0] != 0:
        raise ValueError('Order grain validation failed')
    for source, amount, target in [('items','price_cents','gmv_cents'),('items','freight_cents','freight_cents'),('payments','payment_cents','payment_cents')]:
        raw_total=con.sql(f'SELECT sum({amount}) FROM {source}').fetchone()[0]
        model_total=con.sql(f'SELECT sum({target}) FROM fact_orders').fetchone()[0]
        if raw_total != model_total:
            raise ValueError(f'Reconciliation failed: {source}.{amount}')
    return con

def export_bi(con, folder):
    folder.mkdir(parents=True, exist_ok=True)
    # DimOrder is the shared order filter hub; facts never directly filter one another.
    exports = {
      'DimOrder': "SELECT order_id,customer_id,customer_state,order_status,purchase_date FROM fact_orders",
      'FactOrders': "SELECT * EXCLUDE(customer_unique_id,customer_state,customer_city,order_status,purchase_date) FROM fact_orders",
      'FactItems': 'SELECT * FROM items',
      'FactPayments': 'SELECT * FROM payments',
      'DimProduct':'SELECT * FROM dim_products',
      'DimSeller':'SELECT * FROM sellers',
      'DimCustomer':'SELECT customer_id,customer_unique_id,customer_city,customer_state FROM customers',
      'DimState':'SELECT DISTINCT customer_state FROM customers',
      'DimStatus':'SELECT DISTINCT order_status FROM orders',
      'DimDate': "SELECT d::DATE AS date, year(d) AS year, quarter(d) AS quarter, month(d) AS month_number, strftime(d,'%Y-%m') AS year_month FROM generate_series((SELECT min(purchase_date) FROM fact_orders),(SELECT max(purchase_date) FROM fact_orders), INTERVAL 1 DAY) t(d)"
    }
    for name, sql in exports.items():
        con.sql(sql).df().to_csv(folder/f'{name}.csv', index=False)

def run_pipeline():
    acquire()
    reports = ROOT/'reports'
    results = reports/'sql'
    results.mkdir(parents=True, exist_ok=True)
    frames = load(ROOT/'data/raw')
    audit(frames, reports)  # Persisted before any cleaning or transformation.
    cleaned = clean(frames)
    building = ROOT/'data/olist.building.duckdb'
    con = build_database(cleaned, building)
    outputs = {}
    for path in sorted((ROOT/'sql').glob('[0-9]*.sql')):
        df = con.sql(path.read_text(encoding='utf-8')).df()
        df.to_csv(results/f'{path.stem}.csv', index=False)
        outputs[path.stem] = df
    export_bi(con, ROOT/'powerbi/exports')
    f = con.sql('SELECT * FROM fact_orders').df()
    log = {'raw_review_rows':len(frames['reviews']), 'selected_reviews':int(f.review_score.notna().sum()),
       'delivered_missing_actual_date':int(((f.order_status=='delivered') & f.order_delivered_customer_date.isna()).sum()),
       'negative_delivery_duration_rows':int((f.order_delivered_customer_date<f.order_purchase_timestamp).sum()),
       'unknown_product_category_rows':int(frames['products'].product_category_name.isna().sum())}
    (reports/'cleaning_log.json').write_text(json.dumps(log, indent=2),encoding='utf-8')
    from .reporting import generate
    generate(f, outputs, reports)
    run = {'status':'success','completed_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),'packages':{p:importlib.metadata.version(p) for p in ['pandas','duckdb','matplotlib','scipy','pytest']},'source_manifest':'source_manifest.json','orders':len(f)}
    con.close()
    os.replace(building, ROOT/'data/olist.duckdb')
    (reports/'run_manifest.json').write_text(json.dumps(run,indent=2),encoding='utf-8')
    print(f'Complete: {len(f):,} orders; {len(outputs)} SQL analyses; BI exports and evidence saved.')

def main():
    reports=ROOT/'reports'
    reports.mkdir(exist_ok=True)
    status=reports/'run_status.json'
    status.write_text(json.dumps({'status':'running','started_utc':datetime.now(timezone.utc).isoformat()}),encoding='utf-8')
    try:
        run_pipeline()
    except Exception as exc:
        status.write_text(json.dumps({'status':'failed','error':str(exc)}),encoding='utf-8')
        raise
    status.write_text(json.dumps({'status':'success','completed_utc':datetime.now(timezone.utc).isoformat()}),encoding='utf-8')

if __name__=='__main__':
    main()
