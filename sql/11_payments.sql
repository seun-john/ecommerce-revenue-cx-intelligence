SELECT payment_type, count(*) payment_rows, count(DISTINCT order_id) orders,
 sum(payment_cents)/100.0 payment_value_brl, avg(payment_installments) mean_installments
FROM payments GROUP BY 1 ORDER BY payment_value_brl DESC;
