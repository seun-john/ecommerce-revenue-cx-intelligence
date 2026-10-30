"""Local, read-only dashboard API. No credentials or network dependencies."""
import argparse
import csv
from datetime import date, datetime
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import logging
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import duckdb
from .acquire import ROOT

STATIC = ROOT / 'dashboard'
DATABASE = ROOT / 'data/olist.duckdb'

def records(db, sql, params=None):
    cur = db.execute(sql, params or [])
    columns = [c[0] for c in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]

def serial(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(type(value).__name__)

def filters(query):
    allowed = {'start','end','state','status','category','page','table'}
    if set(query) - allowed:
        raise ValueError('Unknown filter parameter')
    values = {}
    for key, val in query.items():
        if len(val) != 1 or len(val[0]) > 150:
            raise ValueError('Each filter must have one value of at most 150 characters')
        values[key] = val[0]
    for key in ('start','end'):
        if values.get(key):
            try:
                date.fromisoformat(values[key])
            except ValueError:
                raise ValueError('Dates must use YYYY-MM-DD') from None
    if values.get('start') and values.get('end') and values['start'] > values['end']:
        raise ValueError('Start date must not be after end date')
    clauses, params = [], []
    for key, expr in [('start','o.purchase_date >= ?::DATE'),('end','o.purchase_date <= ?::DATE'),('state','o.customer_state = ?'),('status','o.order_status = ?')]:
        if values.get(key):
            clauses.append(expr)
            params.append(values[key])
    return values, (' AND '.join(clauses) or 'TRUE'), params

def metadata(db):
    result = records(db,'SELECT min(purchase_date) AS start, max(purchase_date) AS "end", count(*) source_orders FROM fact_orders')[0]
    for name, table, col in [('states','fact_orders','customer_state'),('statuses','fact_orders','order_status'),('categories','dim_products','category')]:
        result[name] = [r[0] for r in db.execute(f'SELECT DISTINCT {col} FROM {table} ORDER BY 1').fetchall()]
    status = ROOT/'reports/run_status.json'
    result['build'] = json.loads(status.read_text()) if status.exists() else {'status':'unknown'}
    return result

def analyse(db, query):
    values, where, params = filters(query)
    if values.get('category'):
        # Service metrics use entire orders containing the category. Item metrics
        # use selected category items only. EXISTS prevents order multiplication.
        where += ' AND EXISTS (SELECT 1 FROM items i JOIN dim_products p USING(product_id) WHERE i.order_id=o.order_id AND p.category=?)'
        params.append(values['category'])
    db.execute('CREATE OR REPLACE TEMP TABLE selected_orders AS SELECT o.* FROM fact_orders o WHERE '+where, params)
    item_sql = 'CREATE OR REPLACE TEMP TABLE selected_items AS SELECT i.*,p.category FROM items i JOIN selected_orders o USING(order_id) JOIN dim_products p USING(product_id)'
    db.execute(item_sql + (' WHERE p.category=?' if values.get('category') else ''), [values['category']] if values.get('category') else [])
    summary = records(db,"""SELECT count(*) orders, sum(gmv_cents)/100.0 order_gmv,
      sum(freight_cents)/100.0 order_freight, count(*) FILTER(WHERE item_count>0) item_bearing_orders,
      count(*) FILTER(WHERE order_status='delivered') delivered_orders,
      count(*) FILTER(WHERE order_status='canceled') canceled_orders,
      avg((order_status='canceled')::INT) cancellation_rate,
      count(is_late) delivery_eligible, count(*) FILTER(WHERE is_late) late_orders,
      avg(is_late::INT) late_rate, avg(delivery_days) mean_delivery_days,
      quantile_cont(delivery_days,0.9) p90_delivery_days,
      count(review_score) reviewed_orders, avg(review_score) mean_review,
      avg(CASE WHEN review_score IS NOT NULL THEN (review_score<=2)::INT END) low_review_rate,
      sum(payment_cents)/100.0 payments,
      sum(payment_cents-gmv_cents-freight_cents)/100.0 matched_payment_gap,
      count(*) FILTER(WHERE payment_cents IS NULL) missing_payment_orders
      FROM selected_orders""")[0]
    summary.update(records(db,"""SELECT count(*) items, sum(price_cents)/100.0 item_gmv,
      sum(freight_cents)/100.0 item_freight, count(DISTINCT order_id) selected_item_orders,
      sum(price_cents)/100.0/nullif(count(DISTINCT order_id),0) aov,
      sum(freight_cents)::DOUBLE/nullif(sum(price_cents),0) freight_ratio
      FROM selected_items""")[0])
    summary.update(records(db,"""WITH c AS (SELECT customer_unique_id,count(*) n FROM selected_orders
      WHERE order_status='delivered' GROUP BY 1)
      SELECT count(*) delivered_customers, count(*) FILTER(WHERE n>1) repeat_customers,
      avg((n>1)::INT) repeat_share FROM c""")[0])
    monthly = records(db,"""WITH o AS (SELECT date_trunc('month',purchase_date)::DATE AS month,
      count(*) orders, count(is_late) eligible, avg(is_late::INT) late_rate,
      avg(review_score) mean_review FROM selected_orders GROUP BY 1),
      i AS (SELECT date_trunc('month',o.purchase_date)::DATE AS month, sum(i.price_cents)/100.0 gmv
      FROM selected_items i JOIN selected_orders o USING(order_id) GROUP BY 1)
      SELECT o.*,coalesce(i.gmv,0) gmv FROM o LEFT JOIN i USING(month) ORDER BY month""")
    categories = records(db,"""SELECT category, count(*) items, count(DISTINCT order_id) orders,
      sum(price_cents)/100.0 gmv, sum(freight_cents)/100.0 freight,
      sum(freight_cents)::DOUBLE/nullif(sum(price_cents),0) freight_ratio
      FROM selected_items GROUP BY 1 ORDER BY gmv DESC""")
    regions = records(db,"""WITH o AS (SELECT customer_state state,count(*) orders,count(is_late) eligible,
      avg(is_late::INT) late_rate,avg(delivery_days) mean_days,avg(review_score) mean_review
      FROM selected_orders GROUP BY 1), i AS (
      SELECT o.customer_state state,sum(i.price_cents)/100.0 gmv FROM selected_items i
      JOIN selected_orders o USING(order_id) GROUP BY 1)
      SELECT o.*,coalesce(i.gmv,0) gmv FROM o LEFT JOIN i USING(state) ORDER BY gmv DESC""")
    reviews = records(db,'SELECT review_score score,count(*) orders FROM selected_orders GROUP BY 1 ORDER BY 1')
    comparison = records(db,"""SELECT is_late late,count(*) orders,avg(review_score) mean_review,
      avg((review_score<=2)::INT) low_review_rate FROM selected_orders
      WHERE is_late IS NOT NULL AND review_score IS NOT NULL GROUP BY 1 ORDER BY 1""")
    sellers = records(db,"""WITH s AS (SELECT i.seller_id,o.order_id,sum(i.price_cents) cents,
      max(o.is_late::INT) late,max(o.review_score) review FROM selected_items i
      JOIN selected_orders o USING(order_id) WHERE o.order_status='delivered' GROUP BY 1,2)
      SELECT s.seller_id,coalesce(max(d.seller_city),'Unknown') city,count(*) orders,
      sum(cents)/100.0 gmv,count(late) eligible,avg(late) late_rate,
      count(review) reviewed_orders,avg(review) mean_review FROM s
      LEFT JOIN sellers d USING(seller_id) GROUP BY 1 HAVING count(late)>=30
      ORDER BY gmv DESC LIMIT 50""")
    statuses = records(db,'SELECT order_status status,count(*) orders FROM selected_orders GROUP BY 1 ORDER BY orders DESC')
    repeats = records(db,"""WITH c AS (SELECT customer_unique_id,count(*) orders FROM selected_orders
      WHERE order_status='delivered' GROUP BY 1) SELECT orders purchases,count(*) customers
      FROM c GROUP BY 1 ORDER BY 1""")
    durations = records(db,"""SELECT cast(floor(delivery_days/5)*5 AS INT) AS days,count(*) orders
      FROM selected_orders WHERE delivery_days IS NOT NULL GROUP BY 1 ORDER BY 1""")
    return {'filters':values,'summary':summary,'monthly':monthly,'categories':categories,
      'regions':regions,'reviews':reviews,'comparison':comparison,'sellers':sellers,
      'statuses':statuses,'repeats':repeats,'durations':durations}

class Handler(BaseHTTPRequestHandler):
    def send(self, code, data, content_type='application/json; charset=utf-8', download=None):
        self.send_response(code)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        if download:
            self.send_header('Content-Disposition',f'attachment; filename="{download}"')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url=urlsplit(self.path)
        try:
            if url.path in ('/api/meta','/api/dashboard','/api/export'):
                if not DATABASE.exists():
                    self.send(503,b'{"error":"Build the data first: python -m src.pipeline"}')
                    return
                with duckdb.connect(str(DATABASE),read_only=True) as db:
                    query=parse_qs(url.query,keep_blank_values=True)
                    data=metadata(db) if url.path=='/api/meta' else analyse(db,query)
                if url.path=='/api/export':
                    table=query.get('table',['monthly'])[0]
                    if table not in {'monthly','categories','regions','reviews','comparison','sellers','statuses','repeats','durations'}:
                        raise ValueError('Unsupported export table')
                    rows=data[table]
                    out=io.StringIO(newline='')
                    if rows:
                        writer=csv.DictWriter(out,fieldnames=list(rows[0]))
                        writer.writeheader()
                        writer.writerows(rows)
                    self.send(200,out.getvalue().encode('utf-8-sig'),'text/csv; charset=utf-8',f'olist_{table}.csv')
                else:
                    self.send(200,json.dumps(data,default=serial,allow_nan=False).encode())
                return
            files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/styles.css':('styles.css','text/css; charset=utf-8')}
            if url.path not in files:
                self.send(404,b'{"error":"Not found"}')
                return
            filename,mime=files[url.path]
            self.send(200,(STATIC/filename).read_bytes(),mime)
        except ValueError as exc:
            self.send(400,json.dumps({'error':str(exc)}).encode())
        except Exception:
            logging.exception('Dashboard request failed')
            self.send(500,b'{"error":"Query failed. Check the database and restart the dashboard."}')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Olist dashboard: http://127.0.0.1:{args.port} (Ctrl+C to stop)',flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__=='__main__':
    main()
