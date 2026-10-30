SELECT date_trunc('month',purchase_date)::DATE AS month_start, count(*) delivered_orders,
 count(is_late) eligible_orders, avg(is_late::INTEGER) late_rate,
 avg(delivery_days) mean_delivery_days, median(delivery_days) median_delivery_days,
 quantile_cont(delivery_days,0.9) p90_delivery_days,
 avg(delay_days) mean_days_vs_promise
FROM fact_orders WHERE order_status='delivered' GROUP BY 1 ORDER BY 1;
