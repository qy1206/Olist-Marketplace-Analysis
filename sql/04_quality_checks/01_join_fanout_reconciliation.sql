-- Purpose: Detect row multiplication and duplicated monetary values caused
-- by one-to-many joins between staging and analytical marts.
-- Expected result: every comparison has difference = 0 and status = PASS.

CREATE SCHEMA IF NOT EXISTS
  `olist-marketplace-analytics.olist_quality`
OPTIONS(location = 'US');

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_quality.join_fanout_reconciliation` AS

WITH comparisons AS (
  SELECT
    'order_row_count' AS metric_name,
    CAST((
      SELECT COUNT(*)
      FROM `olist-marketplace-analytics.olist_staging.stg_orders`
    ) AS NUMERIC) AS source_value,
    CAST((
      SELECT COUNT(*)
      FROM `olist-marketplace-analytics.olist_marts.mart_orders`
    ) AS NUMERIC) AS model_value

  UNION ALL

  SELECT
    'order_product_value',
    (
      SELECT SUM(item_price)
      FROM `olist-marketplace-analytics.olist_staging.stg_order_items`
    ),
    (
      SELECT SUM(product_value)
      FROM `olist-marketplace-analytics.olist_marts.mart_orders`
    )

  UNION ALL

  SELECT
    'order_freight_value',
    (
      SELECT SUM(freight_value)
      FROM `olist-marketplace-analytics.olist_staging.stg_order_items`
    ),
    (
      SELECT SUM(freight_value)
      FROM `olist-marketplace-analytics.olist_marts.mart_orders`
    )

  UNION ALL

  SELECT
    'order_payment_value',
    (
      SELECT SUM(payment_value)
      FROM `olist-marketplace-analytics.olist_staging.stg_order_payments`
    ),
    (
      SELECT SUM(payment_value)
      FROM `olist-marketplace-analytics.olist_marts.mart_orders`
    )

  UNION ALL

  SELECT
    'order_seller_product_value',
    (
      SELECT SUM(item_price)
      FROM `olist-marketplace-analytics.olist_staging.stg_order_items`
    ),
    (
      SELECT SUM(product_value)
      FROM `olist-marketplace-analytics.olist_marts.mart_order_seller`
    )

  UNION ALL

  SELECT
    'order_seller_freight_value',
    (
      SELECT SUM(freight_value)
      FROM `olist-marketplace-analytics.olist_staging.stg_order_items`
    ),
    (
      SELECT SUM(freight_value)
      FROM `olist-marketplace-analytics.olist_marts.mart_order_seller`
    )
)

SELECT
  metric_name,
  source_value,
  model_value,
  model_value - source_value AS difference,
  CASE
    WHEN model_value = source_value THEN 'PASS'
    ELSE 'FAIL'
  END AS check_status
FROM comparisons;

-- Validation observed: six passed checks and zero failed checks.
SELECT
  COUNT(*) AS total_checks,
  COUNTIF(check_status = 'PASS') AS passed_checks,
  COUNTIF(check_status = 'FAIL') AS failed_checks
FROM
  `olist-marketplace-analytics.olist_quality.join_fanout_reconciliation`;
