-- Purpose: Standardise the raw order records for downstream analysis.
-- Grain: one row per order_id.

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_staging.stg_orders` AS

SELECT
  order_id,
  customer_id,
  LOWER(TRIM(order_status)) AS order_status,
  order_purchase_timestamp,
  order_approved_at,
  order_delivered_carrier_date,
  order_delivered_customer_date,
  order_estimated_delivery_date,
  DATE(order_purchase_timestamp) AS purchase_date,
  DATE_TRUNC(DATE(order_purchase_timestamp), MONTH) AS purchase_month
FROM `olist-marketplace-analytics.olist_raw.orders`
WHERE order_id IS NOT NULL
  AND customer_id IS NOT NULL;

-- Reconcile raw and staging row counts.
-- Observed result: 99,441 rows in both layers.
SELECT
  (
    SELECT COUNT(*)
    FROM `olist-marketplace-analytics.olist_raw.orders`
  ) AS raw_rows,
  (
    SELECT COUNT(*)
    FROM `olist-marketplace-analytics.olist_staging.stg_orders`
  ) AS staging_rows;
