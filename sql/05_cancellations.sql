SELECT date_trunc('month',purchase_date)::DATE AS month_start, count(*) placed_orders,
 count(*) FILTER(WHERE order_status='canceled') canceled_orders,
 avg((order_status='canceled')::INTEGER) cancellation_rate,
 count(*) FILTER(WHERE order_status='unavailable') unavailable_orders
FROM fact_orders GROUP BY 1 ORDER BY 1;
