SELECT count(*) orders, count(*) FILTER(WHERE payment_cents IS NULL) missing_payment_orders,
 sum(gmv_cents)/100.0 gmv_brl, sum(freight_cents)/100.0 freight_brl,
 sum(payment_cents)/100.0 payments_brl,
 sum(payment_cents-gmv_cents-freight_cents)/100.0 payment_item_gap_brl,
 (sum(payment_cents)-sum(gmv_cents)-sum(freight_cents))/100.0 whole_ledger_gap_brl,
 count(*) FILTER(WHERE payment_cents IS NOT NULL AND abs(payment_cents-gmv_cents-freight_cents)>1) gap_over_one_cent_orders
FROM fact_orders;
