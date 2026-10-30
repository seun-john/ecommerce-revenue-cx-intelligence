# KPI definitions

All monetary values are nominal Brazilian reais (BRL). Source decimals are rounded to integer centavos before aggregation. No exchange-rate or inflation adjustment is applied. No cost or recognised revenue data is available.

| Metric | Numerator / value | Denominator / population |
|---|---|---|
| Placed orders | Order count | All source orders, including canceled, unavailable and undated delivery outcomes |
| GMV | Sum of item price | Items of selected orders; freight excluded; canceled items retained unless delivered filter is explicit |
| Delivered GMV | Sum of item price | Items whose order status is delivered |
| AOV | Item GMV | Distinct item-bearing orders in selection; no-item orders excluded |
| GMV per placed order | Order-level GMV | All selected placed orders; no-item orders contribute zero GMV |
| Freight to GMV | Sum freight / sum item price | Selected items; customer shipping charge proxy, not logistics cost or profit |
| Payment value | Sum payment_value | Payment rows, including multiple methods/installments per order; not GMV |
| Payment/item gap | Payment less item price less freight | Orders with payment records; missing payments counted separately |
| Cancellation rate | Status canceled orders | All selected placed orders; unavailable is separate |
| Late rate | Actual delivery calendar date after estimated date | Delivered orders with both actual and estimated delivery dates |
| Delivery duration | Actual delivery minus purchase, fractional days | Delivered orders with nonnegative duration; null/negative duration excluded |
| Review mean | Mean selected review score (1–5) | Orders with a selected review; one latest answered review per order |
| Low review rate | Selected score 1 or 2 | Reviewed orders in the selection |
| Repeat share | Unique customers with >1 delivered order | Unique customers with >=1 delivered order, using customer_unique_id |
| MoM growth | Current / previous month − 1 | Previous calendar-month amount/order count; zero/missing previous denominator yields blank |
| Seller late/review metrics | Order-level outcome per seller-order | Distinct eligible seller-orders; multi-seller outcomes shared, not causal attribution |

The customer_id identifies an order-specific customer record; customer_unique_id connects purchases. Do not count customer_id as repeat identity. Category order counts overlap when an order contains multiple categories; seller counts overlap on multi-seller orders. Those counts cannot be added across categories/sellers. Freight share and average selling price are commercial proxies only, not profitability. Payment installments count is not an item quantity. One item row represents one purchased unit.

Review selection: latest review_answer_timestamp, then review_creation_date, review_id and review_score descending, with null timestamps last. All review records remain in the raw table. This choice represents latest observed feedback, not necessarily first experience. Unreviewed orders remain in the model.

SQL monthly growth uses observed purchase months; sparse boundary months must not be interpreted as full-month demand. The date dimension is contiguous so Power BI time intelligence can distinguish calendar months. Filter to mature full months when comparing trends.
