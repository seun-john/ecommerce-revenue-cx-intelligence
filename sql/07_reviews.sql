-- One selected review per order; missing reviews are not zeros.
SELECT review_score, count(*) orders FROM fact_orders GROUP BY 1 ORDER BY 1;
