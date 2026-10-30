-- Seller-order grain for service metrics; multi-seller order scores are shared, not attribution.
WITH s AS (SELECT seller_id,order_id, sum(price_cents) gmv_cents,
 max(is_late::INTEGER) late, max(review_score) review
 FROM item_analysis WHERE order_status='delivered' GROUP BY 1,2)
SELECT seller_id, count(*) delivered_orders, sum(gmv_cents)/100.0 gmv_brl,
 count(late) delivery_eligible_orders, avg(late) late_rate,
 count(review) reviewed_orders, avg(review) mean_review
FROM s GROUP BY 1 HAVING count(late)>=30 ORDER BY gmv_brl DESC;
