-- Purpose: Validate critical keys, missing values, and duplicate risks.
-- Observed after the initial load:
--   * orders has 99,441 rows and 99,441 unique order IDs.
--   * critical order fields have no NULL values.
--   * (order_id, order_item_id) is unique in order_items.
--   * review_id is not a reliable unique key across orders.
--   * 547 orders have more than one review row.

-- 1. Validate the orders table grain: one row per order.
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT order_id) AS unique_order_ids
FROM `olist-marketplace-analytics.olist_raw.orders`;

-- 2. Check critical order fields for missing values.
SELECT
  COUNTIF(order_id IS NULL) AS missing_order_id,
  COUNTIF(customer_id IS NULL) AS missing_customer_id,
  COUNTIF(order_purchase_timestamp IS NULL) AS missing_purchase_timestamp
FROM `olist-marketplace-analytics.olist_raw.orders`;

-- 3. Find duplicated order-item combinations.
-- Expected result: no rows.
SELECT
  order_id,
  order_item_id,
  COUNT(*) AS row_count
FROM `olist-marketplace-analytics.olist_raw.order_items`
GROUP BY order_id, order_item_id
HAVING COUNT(*) > 1;

-- 4. Count review IDs that appear more than once.
SELECT
  COUNT(*) AS duplicated_review_ids
FROM (
  SELECT review_id
  FROM `olist-marketplace-analytics.olist_raw.order_reviews`
  GROUP BY review_id
  HAVING COUNT(*) > 1
);

-- 5. Diagnose whether repeated review IDs belong to different orders.
SELECT
  review_id,
  COUNT(*) AS row_count,
  COUNT(DISTINCT order_id) AS order_count,
  COUNT(DISTINCT review_score) AS score_count
FROM `olist-marketplace-analytics.olist_raw.order_reviews`
GROUP BY review_id
HAVING COUNT(*) > 1
ORDER BY row_count DESC
LIMIT 20;

-- 6. Count orders that have multiple review rows.
SELECT
  COUNT(*) AS orders_with_multiple_reviews
FROM (
  SELECT order_id
  FROM `olist-marketplace-analytics.olist_raw.order_reviews`
  GROUP BY order_id
  HAVING COUNT(*) > 1
);
