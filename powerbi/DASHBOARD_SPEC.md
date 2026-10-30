# Power BI implementation guide

## Build status

No PBIX has been created. Power BI Desktop was not found in the executable search path or standard x64/x86 installation locations. The project provides real-data CSV exports, import function, DAX, theme and this four-page specification. Python figures are actual analytical outputs, not Power BI screenshots. DAX and Power Query require validation inside Desktop; the Python/SQL calculations are the reference oracle.

## Windows build procedure

1. Install current Power BI Desktop for Windows 11 from Microsoft's official distribution. Run `scripts/run.ps1` from the project to create `powerbi/exports`.
2. Open Desktop, create a blank report and disable automatic date/time and automatic relationship detection for this file. In Transform data, create a Text parameter `ExportFolder` containing the absolute path of `powerbi\exports` (no trailing slash).
3. Create a blank query named `LoadTable`, paste `load_table.pq` in Advanced Editor. Create ten blank queries, named exactly `DimOrder`, `FactOrders`, `FactItems`, `FactPayments`, `DimProduct`, `DimSeller`, `DimCustomer`, `DimState`, `DimStatus`, `DimDate`; each calls `= LoadTable("TableName")`. Disable load for the function.
4. **Set types explicitly** before Close & Apply. All `*_id`, state, city, status, category, ZIP prefix, payment type and year_month fields: Text. `purchase_date`, DimDate.date: Date. Columns containing timestamp and order_delivered_customer_date/order_estimated_delivery_date: Date/Time. Centavo, item_count, payment_count, order_item_id, payment_sequential, payment_installments, review_score, delay_days, year, quarter, month_number: Whole Number. `is_late`: True/False; blank remains null. delivery_days, price, freight_value, payment_value and dimensions/weight: Decimal Number. Remove automatic Changed Type steps that convert IDs to numbers. Do not replace null reviews or is_late with zero/false.
5. Create only the relationships below, all active with single-direction filtering from parent to child. Set one-to-one DimOrder→FactOrders to **one-to-many** explicitly, even though both current keys are unique. This preserves single-direction filtering. Do not create direct relationships between facts.
6. Mark DimDate as the date table using date. Sort year_month by an added integer YearMonthSort (`year*100 + month_number`); sort month names by month_number if added. Add the year→quarter→year_month→date hierarchy.
7. Add each definition in `measures.dax` separately with New measure. Create a dedicated Measures display folder. Hide centavo source columns, redundant foreign keys and raw decimal monetary columns from report view. Format rates as 0.0%, review and duration as 0.00, money as BRL with separators.
8. View → Themes → Browse for themes → select `theme.json`. Set page size 1440×900 and build the layouts below. Use standard built-in visuals, titles and alt text; no external visual dependencies.
9. Validate the unfiltered totals against `reports/metrics.json`, SQL 02/06/07 and SQL 12. Validate date/state/status filters on every page. Validate that category/seller selections affect item measures only unless explicitly using a selected-item-order measure. Save as `Ecommerce_Revenue_CX.pbix` locally. Publishing requires owner approval.

## Relationships and filter scope

| Parent (one) | Child (many) | Key |
|---|---|---|
| DimDate.date | DimOrder.purchase_date | Date |
| DimState.customer_state | DimOrder.customer_state | Customer destination state |
| DimStatus.order_status | DimOrder.order_status | Status |
| DimCustomer.customer_id | DimOrder.customer_id | Order-specific customer |
| DimOrder.order_id | FactOrders.order_id | Order |
| DimOrder.order_id | FactItems.order_id | Order |
| DimOrder.order_id | FactPayments.order_id | Order |
| DimProduct.product_id | FactItems.product_id | Product |
| DimSeller.seller_id | FactItems.seller_id | Seller |

This is a shared order dimension with a small dimension hierarchy (snowflake), ready for a star-style semantic model. DimOrder is the sole common filter hub. DimProduct and DimSeller do not filter FactOrders or FactPayments. Avoid category/seller slicers on executive/CX pages. On the product/operations page, service cards must use the explicit selected-item-order measures below and say “orders containing selected items”. An order containing multiple categories/sellers may appear in multiple groups; no attribution of its score to an individual item is implied. Payment-type filtering belongs only to payment visuals, unless an explicit eligible-order bridge is added.

```dax
Selected Item Orders = DISTINCTCOUNT(FactItems[order_id])

Selected Item Order Late Rate =
CALCULATE([Late Rate], KEEPFILTERS(TREATAS(VALUES(FactItems[order_id]), FactOrders[order_id])))

Selected Item Order Mean Review =
CALCULATE([Mean Review], KEEPFILTERS(TREATAS(VALUES(FactItems[order_id]), FactOrders[order_id])))
```

## Visual system

Use a 32 px outer margin, 20 px gutters, navy heading, white panels and light grey canvas. Header: x32 y24 w1376 h60. Page subtitle states population, metric definition and historical date scope. Slicer rail: x32 y100 w1376 h64. KPI row: four cards at y188, widths 329 and height 112. Main row: x32/y324/w868/h360 and x920/y324/w488/h360. Lower strip: x32/y708/w1376/h140 for exceptions or a concise note. Use teal for business volume, orange plus the word “Late” for misses. Never rely on colour alone; label units and values. Provide keyboard tab order, alt text and high-contrast labels. Truncate long category names only with full-name tooltips.

## Page 1 — Executive Overview

- Slicers: purchase date Between; customer state; status. Sync these slicers to all pages. Default to all data with an annotation that boundary months are partial; provide a saved full-month bookmark for Jan 2017–Aug 2018.
- Cards: GMV BRL, Placed Orders, AOV BRL, Late Rate. Tooltips show item-bearing order count and delivery eligible count, respectively.
- Main left: line chart DimDate.year_month vs GMV BRL, with Orders as a separate small multiple (avoid misleading dual scales). Drill to date; show MoM growth in tooltip.
- Main right: ranked state bars with GMV BRL; show placed orders and late rate in tooltip.
- Lower strip: cancellation rate, selected review mean, payment/item gap and a definition note. Button navigation to other pages. No category slicer here.

## Page 2 — Sales and Product Performance

- Additional slicers: category and seller; default status delivered. This status affects other pages only if deliberately synced—keep this page's delivered filter local.
- Cards: Delivered GMV BRL, Delivered AOV BRL, item count (`COUNTROWS(FactItems)`), Freight to GMV.
- Main left: horizontal category bars, delivered GMV; drill category→product_id. Top 10 with an “All categories” table bookmark; show remaining share explicitly.
- Main right: scatter mean item price vs freight-to-GMV, bubble by item count, category detail. Use ratio of summed freight to summed item price. Label it “shipping-charge burden proxy”; no profit label.
- Lower strip: category table with delivered GMV, distinct item-bearing orders, item count, freight ratio. Category counts can overlap. Seller drill-through filtered by seller_id with GMV and selected-item-order service measures.

## Page 3 — Delivery and Operational Performance

- Slicers: purchase date, destination state, status (default delivered), optional seller. Seller service cards use TREATAS measures, not unfiltered FactOrders measures.
- Cards without seller selection: Delivery Eligible Orders, Late Rate, Mean Delivery Days, P90 Delivery Days. Under seller selection use equivalents with the selected-item-order filter.
- Main left: monthly late-rate line with eligible-order counts in tooltip and missing-date count beside the chart. Drill month→day.
- Main right: state matrix with eligible orders, late count, late rate and mean duration; conditional formatting includes text and numbers. Suppress ranking when eligible n < 30; still show the count.
- Lower strip: seller exception table with >=30 eligible orders, late rate, mean review and delivered GMV. Counts refer to seller-orders; multi-seller outcomes are shared. Drill through to order_id and dates to investigate, without claiming seller causation.

## Page 4 — Customer Experience

- Slicers: purchase date, state and status; no product/seller filter unless using explicit selected-order measures.
- Cards: Mean Review, Reviewed Orders, Low Review Rate, Observed Repeat Share.
- Main left: column chart review_score 1–5 vs reviewed order count. Add a separate unreviewed count; do not put missing reviews in score zero.
- Main right: on-time vs late mean review with eligible reviewed counts; filter both delivery outcome and review to nonblank. Add tooltip for low-review rate. This chart shows association.
- Lower strip: dynamic table with DimCustomer.customer_unique_id, Customer Delivered Orders and order-grain GMV; filter Customer Delivered Orders > 1. This responds to date/state/status filters. SQL 09 is a full-extract distribution cross-check; do not label observed repeat as retention. A static SQL summary, if imported, must be labelled full-extract and must not appear to respond to slicers.

## Acceptance checks in Desktop

- Unfiltered GMV equals sum of all exported item centavos /100 and equals Python order GMV; delivered figures match metrics.json.
- Adding payment method to a payment visual does not change GMV; adding category/seller changes item GMV without multiplying order amounts.
- Two review rows for an order do not change review/order counts; latest review is already selected upstream.
- Late rate denominator excludes unknown dates; canceled orders never enter delivery eligibility.
- MoM first period returns blank; date filter slicing does not silently compare sparse boundary months as complete demand.
- Repeat share uses customer_unique_id; compare unfiltered delivered counts to SQL 09.
- Navigate all four pages and drill-through; check tab order, data labels and high-contrast view. Export actual Desktop screenshots only after these checks.

## Reference documentation

Microsoft's [relationship guidance](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-relationships-understand) explains active relationships and cross-filter direction. [TREATAS](https://learn.microsoft.com/en-us/dax/treatas-function-dax) provides the explicit selected-order filter used above. These files specify a report; Desktop validation and the PBIX remain a manual completion step.
