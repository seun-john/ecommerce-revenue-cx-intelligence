SELECT order_status, count(*) orders, sum(gmv_cents)/100.0 gmv_brl,
 avg(gmv_cents)/100.0 gmv_per_placed_order_brl,
 sum(gmv_cents)/100.0/nullif(count(*) FILTER(WHERE item_count>0),0) aov_item_bearing_brl
FROM fact_orders GROUP BY 1 ORDER BY orders DESC;
