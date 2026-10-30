SELECT is_late, count(*) eligible_reviewed_orders, avg(review_score) mean_review,
 avg((review_score<=2)::INTEGER) low_review_rate,
 avg(delivery_days) mean_delivery_days
FROM fact_orders WHERE is_late IS NOT NULL AND review_score IS NOT NULL
GROUP BY 1 ORDER BY 1;
