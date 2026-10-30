-- Source tables retain original CSV grain. Derived order aggregates prevent fanout.
CREATE OR REPLACE TABLE fact_orders AS
WITH i AS (
 SELECT order_id, count(*) item_count, sum(price_cents) gmv_cents,
 sum(freight_cents) freight_cents FROM items GROUP BY order_id
), p AS (
 SELECT order_id, count(*) payment_count, sum(payment_cents) payment_cents
 FROM payments GROUP BY order_id
), r AS (
 SELECT * EXCLUDE(rn) FROM (
  SELECT *, row_number() OVER(PARTITION BY order_id ORDER BY review_answer_timestamp DESC NULLS LAST,
  review_creation_date DESC NULLS LAST, review_id DESC, review_score DESC) rn
  FROM (SELECT DISTINCT * FROM reviews)
 ) WHERE rn=1
)
SELECT o.order_id, o.customer_id, c.customer_unique_id,
 c.customer_state, c.customer_city, o.order_status,
 cast(o.order_purchase_timestamp AS DATE) purchase_date,
 o.order_purchase_timestamp, o.order_delivered_customer_date, o.order_estimated_delivery_date,
 coalesce(i.item_count,0) item_count, coalesce(i.gmv_cents,0) gmv_cents,
 coalesce(i.freight_cents,0) freight_cents,
 coalesce(p.payment_count,0) payment_count, p.payment_cents,
 r.review_score, r.review_id,
 CASE WHEN o.order_status='delivered' AND o.order_delivered_customer_date IS NOT NULL
 AND o.order_estimated_delivery_date IS NOT NULL
 THEN cast(o.order_delivered_customer_date AS DATE)>cast(o.order_estimated_delivery_date AS DATE) END is_late,
 CASE WHEN o.order_status='delivered' AND o.order_delivered_customer_date>=o.order_purchase_timestamp
 THEN epoch(o.order_delivered_customer_date-o.order_purchase_timestamp)/86400.0 END delivery_days,
 CASE WHEN o.order_status='delivered' AND o.order_delivered_customer_date IS NOT NULL
 AND o.order_estimated_delivery_date IS NOT NULL
 THEN date_diff('day',cast(o.order_estimated_delivery_date AS DATE),cast(o.order_delivered_customer_date AS DATE)) END delay_days
FROM orders o JOIN customers c USING(customer_id)
LEFT JOIN i USING(order_id) LEFT JOIN p USING(order_id) LEFT JOIN r USING(order_id);

CREATE OR REPLACE TABLE dim_products AS
SELECT p.product_id, p.product_category_name,
 coalesce(t.product_category_name_english,p.product_category_name,'Unknown') category,
 p.product_weight_g, p.product_length_cm,p.product_height_cm,p.product_width_cm
FROM products p LEFT JOIN translation t USING(product_category_name);

CREATE OR REPLACE VIEW item_analysis AS
SELECT i.*, p.category, o.order_status, o.purchase_date, o.customer_state,
 o.is_late, o.review_score, o.delivery_days
FROM items i JOIN fact_orders o USING(order_id) JOIN dim_products p USING(product_id);
