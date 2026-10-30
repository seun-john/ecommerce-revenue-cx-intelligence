SELECT customer_state, count(*) orders, sum(gmv_cents)/100.0 gmv_brl,
 avg(gmv_cents)/100.0 gmv_per_order_brl,
 count(is_late) delivery_eligible_orders, avg(is_late::INTEGER) late_rate,
 avg(delivery_days) delivery_days
FROM fact_orders GROUP BY 1 ORDER BY gmv_brl DESC;
