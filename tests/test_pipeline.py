"""Synthetic fixtures are explicitly artificial; integration tests use the real build."""
from pathlib import Path
import json
import pandas as pd
import pytest
import duckdb
from src.pipeline import clean, build_database, ROOT
from src.quality import audit
from src.reporting import wilson

@pytest.fixture
def synthetic():
    # SYNTHETIC TEST DATA: two orders; deliberate 2 items x 2 payments x 2 reviews fanout.
    return {
      'orders':pd.DataFrame({'order_id':['o1','o2'],'customer_id':['c1','c2'],'order_status':['delivered','canceled'],
        'order_purchase_timestamp':['2018-01-01 10:00:00','2018-01-02'],
        'order_delivered_customer_date':['2018-01-05 20:00:00',None],
        'order_estimated_delivery_date':['2018-01-05',None]}),
      'customers':pd.DataFrame({'customer_id':['c1','c2'],'customer_unique_id':['u1','u1'],
        'customer_state':['SP','RJ'],'customer_city':['a','b']}),
      'items':pd.DataFrame({'order_id':['o1','o1'],'order_item_id':[1,2],
        'product_id':['p1','p1'],'seller_id':['s1','s1'],'price':[10.,20.],'freight_value':[1.,2.]}),
      'payments':pd.DataFrame({'order_id':['o1','o1'],'payment_sequential':[1,2],
        'payment_value':[11.,22.],'payment_type':['voucher','credit_card'],'payment_installments':[1,1]}),
      'reviews':pd.DataFrame({'order_id':['o1','o1'],'review_id':['r1','r2'],'review_score':[1,5],
        'review_answer_timestamp':['2018-01-06','2018-01-07'],'review_creation_date':['2018-01-06','2018-01-07']}),
      'products':pd.DataFrame({'product_id':['p1'],'product_category_name':[None],
        'product_weight_g':[10.],'product_length_cm':[1.],'product_height_cm':[1.],'product_width_cm':[1.]}),
      'translation':pd.DataFrame({'product_category_name':['x'],'product_category_name_english':['X']}),
      'sellers':pd.DataFrame({'seller_id':['s1']}),
      'geolocation':pd.DataFrame({'geolocation_zip_code_prefix':['00001','00001']})}

@pytest.fixture
def small_db(synthetic):
    con=build_database(clean(synthetic), ':memory:')
    yield con
    con.close()

def test_fanout_protection_and_money(small_db):
    row=small_db.sql("SELECT gmv_cents,freight_cents,payment_cents,item_count,payment_count,review_score FROM fact_orders WHERE order_id='o1'").fetchone()
    assert row==(3000,300,3300,2,2,5)
    assert small_db.sql('SELECT count(*) FROM fact_orders').fetchone()[0]==2

def test_calendar_day_and_missing_outcomes(small_db):
    assert small_db.sql("SELECT is_late FROM fact_orders WHERE order_id='o1'").fetchone()[0] is False
    assert small_db.sql("SELECT is_late,payment_cents,review_score,gmv_cents FROM fact_orders WHERE order_id='o2'").fetchone()==(None,None,None,0)
    assert small_db.sql('SELECT DISTINCT category FROM dim_products').fetchone()[0]=='Unknown'

def test_audit_before_cleaning(synthetic,tmp_path):
    a=audit(synthetic,tmp_path)
    assert a['review_duplicate_order_rows']==1
    assert a['tables']['geolocation']['exact_duplicates']==1
    assert synthetic['orders']['order_purchase_timestamp'].dtype==object
    assert (tmp_path/'DATA_QUALITY.md').exists()

@pytest.mark.parametrize('problem',['duplicate','orphan','null_key'])
def test_schema_gate(synthetic,tmp_path,problem):
    if problem=='duplicate':
        synthetic['orders']=pd.concat([synthetic['orders'],synthetic['orders'].iloc[[0]]])
    elif problem=='orphan':
        synthetic['items'].loc[0,'order_id']='missing'
    else:
        synthetic['orders'].loc[0,'order_id']=None
    with pytest.raises(ValueError):
        audit(synthetic,tmp_path)
    assert (tmp_path/'quality.json').exists()

@pytest.mark.parametrize('amount',[None,-1])
def test_no_missing_price_imputation(synthetic,amount):
    synthetic['items'].loc[0,'price']=amount
    with pytest.raises(ValueError):
        clean(synthetic)

def test_invalid_date_rejected(synthetic):
    synthetic['orders'].loc[0,'order_purchase_timestamp']='broken'
    with pytest.raises(ValueError):
        clean(synthetic)

def test_confidence_interval():
    lo,hi=wilson(50,100)
    assert lo==pytest.approx(.4038315,abs=1e-6)
    assert hi==pytest.approx(.5961685,abs=1e-6)
    assert wilson(0,0)==[None,None]

def test_aov_and_repeat_denominators(small_db):
    rows=small_db.sql((ROOT/'sql/02_aov.sql').read_text()).df()
    delivered=rows[rows.order_status=='delivered'].iloc[0]
    assert delivered.aov_item_bearing_brl==30
    assert rows[rows.order_status=='canceled'].iloc[0].gmv_per_placed_order_brl==0
    # Both synthetic customer_id records refer to u1; only delivered orders count.
    repeat=small_db.sql((ROOT/'sql/09_repeat_customers.sql').read_text()).fetchall()
    assert repeat==[(1,1,30.0)]
    small_db.execute("UPDATE fact_orders SET order_status='delivered' WHERE order_id='o2'")
    assert small_db.sql((ROOT/'sql/09_repeat_customers.sql').read_text()).fetchall()==[(2,1,30.0)]

def test_reconciliation_missing_payment_denominator(small_db):
    small_db.execute("UPDATE fact_orders SET gmv_cents=500 WHERE order_id='o2'")
    r=small_db.sql((ROOT/'sql/12_reconciliation.sql').read_text()).df().iloc[0]
    assert r.missing_payment_orders==1
    assert r.payment_item_gap_brl==0
    assert r.whole_ledger_gap_brl==-5

def test_monthly_growth_calendar_gap(small_db):
    small_db.execute("UPDATE fact_orders SET purchase_date='2018-03-02' WHERE order_id='o2'")
    rows=small_db.sql((ROOT/'sql/01_monthly_growth.sql').read_text()).df()
    assert rows.orders.tolist()==[1,0,1]
    assert rows.order_growth.iloc[1]==-1
    assert pd.isna(rows.order_growth.iloc[0])
    assert pd.isna(rows.order_growth.iloc[2])

@pytest.fixture(scope='module')
def real_db():
    path=ROOT/'data/olist.duckdb'
    if not path.exists():
        pytest.skip('Real data unavailable: run python -m src.pipeline first')
    con=duckdb.connect(str(path),read_only=True)
    yield con
    con.close()

def test_real_grains_and_fk(real_db):
    for table,key in [('orders','order_id'),('fact_orders','order_id'),('customers','customer_id'),('dim_products','product_id')]:
        n,unique=real_db.sql(f'SELECT count(*),count(DISTINCT {key}) FROM {table}').fetchone()
        assert n==unique
    for child,col,parent,key in [('items','order_id','orders','order_id'),('payments','order_id','orders','order_id'),('reviews','order_id','orders','order_id'),('items','product_id','products','product_id')]:
        assert real_db.sql(f'SELECT count(*) FROM {child} c LEFT JOIN {parent} p ON c.{col}=p.{key} WHERE p.{key} IS NULL').fetchone()[0]==0

def test_real_reconciliation(real_db):
    for source,amount,target in [('items','price_cents','gmv_cents'),('items','freight_cents','freight_cents'),('payments','payment_cents','payment_cents')]:
        assert real_db.sql(f'SELECT sum({amount}) FROM {source}').fetchone()[0]==real_db.sql(f'SELECT sum({target}) FROM fact_orders').fetchone()[0]

def test_real_sql_all_execute(real_db):
    for path in (ROOT/'sql').glob('[0-9]*.sql'):
        assert len(real_db.sql(path.read_text()).df())>0

def test_real_exports_and_kpi(real_db):
    m=json.loads((ROOT/'reports/metrics.json').read_text())
    n=real_db.sql('SELECT count(*) FROM fact_orders').fetchone()[0]
    assert m['placed_orders']==n
    assert len(pd.read_csv(ROOT/'powerbi/exports/DimOrder.csv'))==n
    assert len(pd.read_csv(ROOT/'powerbi/exports/FactOrders.csv'))==n
    late,total=real_db.sql('SELECT count(*) FILTER(WHERE is_late),count(is_late) FROM fact_orders').fetchone()
    assert m['late_rate']==pytest.approx(late/total)
    assert m['delivered_aov_brl']==pytest.approx(real_db.sql("SELECT sum(gmv_cents)/100.0/count(*) FILTER(WHERE item_count>0) FROM fact_orders WHERE order_status='delivered'").fetchone()[0])
