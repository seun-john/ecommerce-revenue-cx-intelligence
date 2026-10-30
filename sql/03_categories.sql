-- Delivered item grain. Freight share is a burden proxy, not a margin.
SELECT category, count(*) items, count(DISTINCT order_id) orders,
 sum(price_cents)/100.0 gmv_brl, avg(price_cents)/100.0 mean_item_price_brl,
 sum(freight_cents)::DOUBLE/nullif(sum(price_cents),0) freight_to_gmv
FROM item_analysis WHERE order_status='delivered' GROUP BY 1 ORDER BY gmv_brl DESC;
