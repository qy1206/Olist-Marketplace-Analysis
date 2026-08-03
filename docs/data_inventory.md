# Olist Raw Data Inventory

Generated from the downloaded CSV files. Raw files were read only.

## File Inventory

| File | Rows | Columns | Candidate key | Duplicate key rows | Schema |
|---|---:|---:|---|---:|---|
| `olist_closed_deals_dataset.csv` | 842 | 14 | mql_id | 0 | PASS |
| `olist_customers_dataset.csv` | 99,441 | 5 | customer_id | 0 | PASS |
| `olist_geolocation_dataset.csv` | 1,000,163 | 5 | Not tested | Not tested | PASS |
| `olist_marketing_qualified_leads_dataset.csv` | 8,000 | 4 | mql_id | 0 | PASS |
| `olist_order_items_dataset.csv` | 112,650 | 7 | order_id, order_item_id | 0 | PASS |
| `olist_order_payments_dataset.csv` | 103,886 | 5 | order_id, payment_sequential | 0 | PASS |
| `olist_order_reviews_dataset.csv` | 99,224 | 7 | review_id | 814 | PASS |
| `olist_orders_dataset.csv` | 99,441 | 8 | order_id | 0 | PASS |
| `olist_products_dataset.csv` | 32,951 | 9 | product_id | 0 | PASS |
| `olist_sellers_dataset.csv` | 3,095 | 4 | seller_id | 0 | PASS |
| `product_category_name_translation.csv` | 71 | 2 | product_category_name | 0 | PASS |

## Join Coverage

| Relationship | Distinct left keys | Matched | Unmatched | Match rate |
|---|---:|---:|---:|---:|
| orders.customer_id -> customers.customer_id | 99,441 | 99,441 | 0 | 100.00% |
| order_items.order_id -> orders.order_id | 98,666 | 98,666 | 0 | 100.00% |
| payments.order_id -> orders.order_id | 99,440 | 99,440 | 0 | 100.00% |
| reviews.order_id -> orders.order_id | 98,673 | 98,673 | 0 | 100.00% |
| order_items.product_id -> products.product_id | 32,951 | 32,951 | 0 | 100.00% |
| order_items.seller_id -> sellers.seller_id | 3,095 | 3,095 | 0 | 100.00% |
| closed_deals.mql_id -> MQL.mql_id | 842 | 842 | 0 | 100.00% |
| closed_deals.seller_id -> sellers.seller_id | 842 | 380 | 462 | 45.13% |
| closed_deals.seller_id -> order_items.seller_id | 842 | 380 | 462 | 45.13% |

## Seller Activation Feasibility

- Closed deals: 842
- Closed sellers found in order items: 380
- Sellers with at least one order on or after won_date: 380
- Median days from won_date to first post-win sale: 44.0
- Sellers with at least one pre-win order: 0

| Origin | MQLs | Closed deals | Post-win activated sellers | MQL-to-close | Closed-to-activation |
|---|---:|---:|---:|---:|---:|
| direct_traffic | 499 | 56 | 31 | 11.22% | 55.36% |
| display | 118 | 6 | 2 | 5.08% | 33.33% |
| email | 493 | 15 | 6 | 3.04% | 40.00% |
| organic_search | 2,296 | 271 | 113 | 11.80% | 41.70% |
| other | 150 | 4 | 2 | 2.67% | 50.00% |
| other_publicities | 65 | 3 | 0 | 4.62% | 0.00% |
| paid_search | 1,586 | 195 | 101 | 12.30% | 51.79% |
| referral | 284 | 24 | 9 | 8.45% | 37.50% |
| social | 1,350 | 75 | 31 | 5.56% | 41.33% |
| unknown | 1,159 | 193 | 85 | 16.65% | 44.04% |

## Interpretation

- `closed_deals.seller_id -> order_items.seller_id` measures how many closed sellers later appear in an order item. This is the initial seller-activation feasibility check.
- A missing foreign-key match must be investigated before modelling; it is not automatically deleted.
- The geolocation table is not expected to have a unique row per ZIP-code prefix, so no primary-key uniqueness test is applied.
- Raw CSV files remain unchanged. Cleaning rules belong in SQL staging models.
