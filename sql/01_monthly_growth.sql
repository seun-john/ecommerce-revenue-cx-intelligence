-- Calendar month spine: absent months are zero, not silently skipped by LAG.
-- All placed orders; item GMV by purchase month. Boundary months are partial.
WITH actual AS (
 SELECT date_trunc('month',purchase_date)::DATE AS month_start,
 count(*) orders, sum(gmv_cents)/100.0 gmv_brl FROM fact_orders GROUP BY 1
), calendar AS (
 SELECT d::DATE month_start FROM generate_series(
 (SELECT min(month_start) FROM actual), (SELECT max(month_start) FROM actual), INTERVAL 1 MONTH) t(d)
), m AS (
 SELECT c.month_start, coalesce(a.orders,0) orders, coalesce(a.gmv_brl,0) gmv_brl
 FROM calendar c LEFT JOIN actual a USING(month_start)
)
SELECT *, orders/nullif(lag(orders) OVER(ORDER BY month_start),0)-1 order_growth,
 gmv_brl/nullif(lag(gmv_brl) OVER(ORDER BY month_start),0)-1 gmv_growth FROM m ORDER BY month_start;
