-- Historical observed repeat, not a fixed-horizon retention estimate.
WITH c AS (SELECT customer_unique_id, count(*) delivered_orders,
 sum(gmv_cents) gmv_cents FROM fact_orders WHERE order_status='delivered' GROUP BY 1)
SELECT delivered_orders, count(*) customers, sum(gmv_cents)/100.0 gmv_brl
FROM c GROUP BY 1 ORDER BY 1;
