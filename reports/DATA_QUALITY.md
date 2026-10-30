# Source data quality audit

Generated from original CSV rows before cleaning. Null counts are preserved; raw data is never overwritten.

## orders: 99,441 rows

Exact duplicate rows: 0; expected key: ['order_id']; duplicate keys: 0.

| Column | Source dtype | Missing |
|---|---|---:|
| order_id | string | 0 |
| customer_id | string | 0 |
| order_status | object | 0 |
| order_purchase_timestamp | object | 0 |
| order_approved_at | object | 160 |
| order_delivered_carrier_date | object | 1,783 |
| order_delivered_customer_date | object | 2,965 |
| order_estimated_delivery_date | object | 0 |

Date ranges: `{"order_purchase_timestamp": {"min": "2016-09-04 21:15:19", "max": "2018-10-17 17:30:18", "invalid": 0}, "order_approved_at": {"min": "2016-09-15 12:16:38", "max": "2018-09-03 17:40:06", "invalid": 0}, "order_delivered_carrier_date": {"min": "2016-10-08 10:34:01", "max": "2018-09-11 19:48:28", "invalid": 0}, "order_delivered_customer_date": {"min": "2016-10-11 13:46:32", "max": "2018-10-17 13:22:46", "invalid": 0}, "order_estimated_delivery_date": {"min": "2016-09-30 00:00:00", "max": "2018-11-12 00:00:00", "invalid": 0}}`

Distinct identifier counts: `{"order_id": 99441, "customer_id": 99441}`

## items: 112,650 rows

Exact duplicate rows: 0; expected key: ['order_id', 'order_item_id']; duplicate keys: 0.

| Column | Source dtype | Missing |
|---|---|---:|
| order_id | string | 0 |
| order_item_id | string | 0 |
| product_id | string | 0 |
| seller_id | string | 0 |
| shipping_limit_date | object | 0 |
| price | float64 | 0 |
| freight_value | float64 | 0 |

Date ranges: `{"shipping_limit_date": {"min": "2016-09-19 00:15:34", "max": "2020-04-09 22:35:08", "invalid": 0}}`

Distinct identifier counts: `{"order_id": 98666, "order_item_id": 21, "product_id": 32951, "seller_id": 3095}`

## payments: 103,886 rows

Exact duplicate rows: 0; expected key: ['order_id', 'payment_sequential']; duplicate keys: 0.

| Column | Source dtype | Missing |
|---|---|---:|
| order_id | string | 0 |
| payment_sequential | int64 | 0 |
| payment_type | object | 0 |
| payment_installments | int64 | 0 |
| payment_value | float64 | 0 |

Date ranges: `{}`

Distinct identifier counts: `{"order_id": 99440}`

## reviews: 99,224 rows

Exact duplicate rows: 0; expected key: None; duplicate keys: None.

| Column | Source dtype | Missing |
|---|---|---:|
| review_id | string | 0 |
| order_id | string | 0 |
| review_score | int64 | 0 |
| review_comment_title | object | 87,656 |
| review_comment_message | object | 58,247 |
| review_creation_date | object | 0 |
| review_answer_timestamp | object | 0 |

Date ranges: `{"review_creation_date": {"min": "2016-10-02 00:00:00", "max": "2018-08-31 00:00:00", "invalid": 0}, "review_answer_timestamp": {"min": "2016-10-07 18:32:28", "max": "2018-10-29 12:27:35", "invalid": 0}}`

Distinct identifier counts: `{"review_id": 98410, "order_id": 98673}`

## customers: 99,441 rows

Exact duplicate rows: 0; expected key: ['customer_id']; duplicate keys: 0.

| Column | Source dtype | Missing |
|---|---|---:|
| customer_id | string | 0 |
| customer_unique_id | string | 0 |
| customer_zip_code_prefix | string | 0 |
| customer_city | object | 0 |
| customer_state | object | 0 |

Date ranges: `{}`

Distinct identifier counts: `{"customer_id": 99441, "customer_unique_id": 96096}`

## products: 32,951 rows

Exact duplicate rows: 0; expected key: ['product_id']; duplicate keys: 0.

| Column | Source dtype | Missing |
|---|---|---:|
| product_id | string | 0 |
| product_category_name | object | 610 |
| product_name_lenght | float64 | 610 |
| product_description_lenght | float64 | 610 |
| product_photos_qty | float64 | 610 |
| product_weight_g | float64 | 2 |
| product_length_cm | float64 | 2 |
| product_height_cm | float64 | 2 |
| product_width_cm | float64 | 2 |

Date ranges: `{}`

Distinct identifier counts: `{"product_id": 32951}`

## sellers: 3,095 rows

Exact duplicate rows: 0; expected key: ['seller_id']; duplicate keys: 0.

| Column | Source dtype | Missing |
|---|---|---:|
| seller_id | string | 0 |
| seller_zip_code_prefix | string | 0 |
| seller_city | object | 0 |
| seller_state | object | 0 |

Date ranges: `{}`

Distinct identifier counts: `{"seller_id": 3095}`

## geolocation: 1,000,163 rows

Exact duplicate rows: 261831; expected key: None; duplicate keys: None.

| Column | Source dtype | Missing |
|---|---|---:|
| geolocation_zip_code_prefix | string | 0 |
| geolocation_lat | float64 | 0 |
| geolocation_lng | float64 | 0 |
| geolocation_city | object | 0 |
| geolocation_state | object | 0 |

Date ranges: `{}`

Distinct identifier counts: `{}`

## translation: 71 rows

Exact duplicate rows: 0; expected key: ['product_category_name']; duplicate keys: 0.

| Column | Source dtype | Missing |
|---|---|---:|
| product_category_name | object | 0 |
| product_category_name_english | object | 0 |

Date ranges: `{}`

Distinct identifier counts: `{}`

## Review identifiers

Repeated order rows beyond the first review: 551. Repeated review_id rows beyond the first: 814. Neither order_id nor review_id is asserted as a raw review primary key.

## Referential integrity

```json
{
  "orders.customer_id -> customers.customer_id": 0,
  "items.order_id -> orders.order_id": 0,
  "payments.order_id -> orders.order_id": 0,
  "reviews.order_id -> orders.order_id": 0,
  "items.product_id -> products.product_id": 0,
  "items.seller_id -> sellers.seller_id": 0
}
```

## Decisions

- Orders, items and payments must satisfy their declared keys; invalid keys or orphan relationships stop the build after this audit is saved.
- Reviews have multiple records per order and review IDs can recur. Preserve all raw review rows; select the latest answered review per order, then creation timestamp and review ID as deterministic tie breakers. Exact duplicate rows are removed only for review selection.
- Missing product categories become Unknown; untranslated categories retain their Portuguese label. Missing delivery timestamps remain unknown, never on-time.
- ZIP prefixes remain strings. Geolocation contains repeated prefixes and is audited but excluded from the BI model to avoid multiplication.
- Monetary values become integer centavos; missing or negative required amounts fail validation. No missing price is imputed as zero.
- Calendar-day lateness compares actual and estimated delivery dates; estimated midnight is treated as the promised calendar day.
- Date parsing failures fail validation. Status-specific missing dates remain null; negative elapsed times are excluded from duration metrics and counted in the cleaning log.
