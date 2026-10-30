"""Real-data dashboard reconciliation plus local HTTP boundary checks."""
import json
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from http.server import ThreadingHTTPServer
import duckdb
import pytest
from src.dashboard import analyse,metadata,filters,Handler,DATABASE
from src.acquire import ROOT

@pytest.fixture
def dashboard_db():
    if not DATABASE.exists():
        pytest.skip('Build real Olist model first')
    with duckdb.connect(str(DATABASE),read_only=True) as db:
        yield db

def test_dashboard_source_totals(dashboard_db):
    d=analyse(dashboard_db,{})
    m=json.loads((ROOT/'reports/metrics.json').read_text())
    assert d['summary']['orders']==m['placed_orders']
    assert d['summary']['item_gmv']==pytest.approx(m['gmv_brl'])
    assert d['summary']['order_gmv']==pytest.approx(m['gmv_brl'])
    assert d['summary']['late_rate']==pytest.approx(m['late_rate'])
    assert d['summary']['repeat_share']==pytest.approx(m['repeat_customer_rate'])
    assert sum(r['gmv'] for r in d['categories'])==pytest.approx(m['gmv_brl'])
    assert sum(r['orders'] for r in d['reviews'])==m['placed_orders']
    assert all(r['eligible']>=30 for r in d['sellers'])

def test_dashboard_delivered_filter(dashboard_db):
    s=analyse(dashboard_db,{'status':['delivered']})['summary']
    m=json.loads((ROOT/'reports/metrics.json').read_text())
    assert s['orders']==m['delivered_orders']
    assert s['item_gmv']==pytest.approx(m['delivered_gmv_brl'])
    assert s['aov']==pytest.approx(m['delivered_aov_brl'])
    assert s['canceled_orders']==0

def test_dashboard_combined_category_filter(dashboard_db):
    query={'start':['2018-01-01'],'end':['2018-03-31'],'state':['SP'],'category':['health_beauty']}
    d=analyse(dashboard_db,query)
    expected=dashboard_db.execute("""SELECT count(DISTINCT o.order_id),sum(i.price_cents)/100.0
      FROM items i JOIN fact_orders o USING(order_id) JOIN dim_products p USING(product_id)
      WHERE purchase_date BETWEEN '2018-01-01' AND '2018-03-31'
      AND customer_state='SP' AND p.category='health_beauty'""").fetchone()
    assert d['summary']['orders']==expected[0]
    assert d['summary']['item_gmv']==pytest.approx(expected[1])
    assert [r['category'] for r in d['categories']]==['health_beauty']
    assert [r['state'] for r in d['regions']]==['SP']
    assert sum(r['gmv'] for r in d['monthly'])==pytest.approx(expected[1])

def test_dashboard_missing_values_and_empty(dashboard_db):
    s=analyse(dashboard_db,{'status':['canceled']})['summary']
    assert s['delivery_eligible']==0
    assert s['late_rate'] is None
    assert s['mean_delivery_days'] is None
    empty=analyse(dashboard_db,{'state':["SP' OR 1=1 --"]})
    assert empty['summary']['orders']==0
    assert empty['summary']['aov'] is None
    assert empty['categories']==[]

@pytest.mark.parametrize('query',[{'start':['bad']},{'start':['2018-01-02'],'end':['2018-01-01']},{'state':['SP','RJ']},{'sql':['SELECT 1']},{'state':['a'*151]}])
def test_filter_validation(query):
    with pytest.raises(ValueError):
        filters(query)

@pytest.fixture
def http_server():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)

def test_http_static_and_no_directory_exposure(http_server):
    for path,mime in [('/','text/html'),('/app.js','text/javascript'),('/styles.css','text/css')]:
        with urlopen(http_server+path,timeout=15) as r:
            assert r.status==200
            assert r.headers['Content-Type'].startswith(mime)
            assert len(r.read())>100
    for path in ['/data/olist.duckdb','/../README.md','/.git/config']:
        with pytest.raises(HTTPError) as e:
            urlopen(http_server+path,timeout=15)
        assert e.value.code==404

def test_http_dashboard_export_and_error(http_server,dashboard_db):
    with urlopen(http_server+'/api/meta',timeout=15) as r:
        meta=json.load(r)
    assert meta['source_orders']==99441
    with urlopen(http_server+'/api/dashboard?status=delivered',timeout=30) as r:
        assert json.load(r)['summary']['orders']==96478
    with urlopen(http_server+'/api/export?table=categories&status=delivered',timeout=30) as r:
        assert 'attachment' in r.headers['Content-Disposition']
        assert 'health_beauty' in r.read().decode('utf-8-sig')
    with pytest.raises(HTTPError) as e:
        urlopen(http_server+'/api/dashboard?start=bad',timeout=15)
    assert e.value.code==400
