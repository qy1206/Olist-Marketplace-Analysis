-- Purpose: Standardise order-item monetary fields for accurate analysis.
-- Grain: one row per (order_id, order_item_id).

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_staging.stg_order_items` AS

SELECT
  order_id,
  order_item_id,
  product_id,
  seller_id,
  shipping_limit_date,
  CAST(price AS NUMERIC) AS item_price,
  CAST(freight_value AS NUMERIC) AS freight_value,
  CAST(price AS NUMERIC)
    + CAST(freight_value AS NUMERIC) AS item_total_value
FROM `olist-marketplace-analytics.olist_raw.order_items`
WHERE order_id IS NOT NULL
  AND order_item_id IS NOT NULL
  AND product_id IS NOT NULL
  AND seller_id IS NOT NULL
  AND price >= 0
  AND freight_value >= 0;

-- Reconcile raw and staging row counts.
-- Observed result: 112,650 rows in both layers.
SELECT
  (
    SELECT COUNT(*)
    FROM `olist-marketplace-analytics.olist_raw.order_items`
  ) AS raw_rows,
  (
    SELECT COUNT(*)
    FROM `olist-marketplace-analytics.olist_staging.stg_order_items`
  ) AS staging_rows;
