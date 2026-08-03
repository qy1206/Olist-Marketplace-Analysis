-- Purpose: Build an order-seller mart for seller revenue, fulfilment,
-- product-category, and review analysis.
-- Grain: One row per (order_id, seller_id).

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_marts.mart_order_seller` AS

WITH order_seller_summary AS (
  SELECT
    i.order_id,
    i.seller_id,
    COUNT(*) AS item_count,
    COUNT(DISTINCT i.product_id) AS product_count,
    SUM(i.item_price) AS product_value,
    SUM(i.freight_value) AS freight_value,
    SUM(i.item_total_value) AS item_total_value,
    STRING_AGG(
      DISTINCT COALESCE(
        LOWER(TRIM(t.product_category_name_english)),
        LOWER(TRIM(p.product_category_name)),
        'unknown'
      ),
      ', '
      ORDER BY COALESCE(
        LOWER(TRIM(t.product_category_name_english)),
        LOWER(TRIM(p.product_category_name)),
        'unknown'
      )
    ) AS product_categories
  FROM `olist-marketplace-analytics.olist_staging.stg_order_items` AS i
  LEFT JOIN `olist-marketplace-analytics.olist_raw.products` AS p
    ON i.product_id = p.product_id
  LEFT JOIN
    `olist-marketplace-analytics.olist_raw.product_category_translation` AS t
    ON p.product_category_name = t.product_category_name
  GROUP BY
    i.order_id,
    i.seller_id
),

review_summary AS (
  SELECT
    order_id,
    COUNT(*) AS review_row_count,
    COUNT(DISTINCT review_id) AS review_count,
    ROUND(AVG(review_score), 2) AS average_review_score
  FROM `olist-marketplace-analytics.olist_raw.order_reviews`
  GROUP BY order_id
)

SELECT
  os.order_id,
  os.seller_id,
  LOWER(TRIM(s.seller_city)) AS seller_city,
  s.seller_state,
  o.order_status,
  o.purchase_date,
  o.purchase_month,
  o.order_delivered_customer_date,
  o.order_estimated_delivery_date,
  os.item_count,
  os.product_count,
  os.product_value,
  os.freight_value,
  os.item_total_value,
  os.product_categories,
  r.review_row_count,
  r.review_count,
  r.average_review_score,
  DATE_DIFF(
    DATE(o.order_delivered_customer_date),
    o.purchase_date,
    DAY
  ) AS delivery_days,
  CASE
    WHEN o.order_delivered_customer_date IS NULL THEN 'not_delivered'
    WHEN o.order_delivered_customer_date
      <= o.order_estimated_delivery_date THEN 'on_time'
    ELSE 'late'
  END AS delivery_status
FROM order_seller_summary AS os
LEFT JOIN `olist-marketplace-analytics.olist_staging.stg_orders` AS o
  ON os.order_id = o.order_id
LEFT JOIN `olist-marketplace-analytics.olist_raw.sellers` AS s
  ON os.seller_id = s.seller_id
LEFT JOIN review_summary AS r
  ON os.order_id = r.order_id;

-- Validation observed:
-- 100,010 mart rows = 100,010 unique order-seller pairs; 3,095 sellers.
SELECT
  COUNT(*) AS mart_rows,
  COUNT(
    DISTINCT CONCAT(order_id, '|', seller_id)
  ) AS unique_order_seller_pairs,
  COUNT(DISTINCT seller_id) AS seller_count
FROM `olist-marketplace-analytics.olist_marts.mart_order_seller`;
