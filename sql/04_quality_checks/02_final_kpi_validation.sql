-- Purpose: Reconcile the final portfolio KPIs between raw sources,
-- analytical marts, and business-analysis views.
-- Expected result: every comparison has difference = 0 and status = PASS.

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_quality.final_kpi_validation` AS

WITH comparisons AS (
  SELECT
    'total_orders' AS metric_name,
    (
      SELECT COUNT(*)
      FROM `olist-marketplace-analytics.olist_raw.orders`
    ) AS source_value,
    (
      SELECT COUNT(*)
      FROM `olist-marketplace-analytics.olist_marts.mart_orders`
    ) AS final_value

  UNION ALL

  SELECT
    'total_marketing_leads',
    (
      SELECT COUNT(*)
      FROM
        `olist-marketplace-analytics.olist_raw.marketing_qualified_leads`
    ),
    (
      SELECT SUM(total_leads)
      FROM
        `olist-marketplace-analytics.olist_marts.mart_marketing_funnel`
    )

  UNION ALL

  SELECT
    'closed_leads',
    (
      SELECT COUNT(*)
      FROM `olist-marketplace-analytics.olist_raw.closed_deals`
    ),
    (
      SELECT COUNT(*)
      FROM
        `olist-marketplace-analytics.olist_marts.mart_seller_lifecycle`
    )

  UNION ALL

  SELECT
    'activated_sellers',
    (
      SELECT COUNTIF(is_activated)
      FROM
        `olist-marketplace-analytics.olist_marts.mart_seller_lifecycle`
    ),
    (
      SELECT SUM(activated_sellers)
      FROM
        `olist-marketplace-analytics.olist_analysis.acquisition_channel_quality`
    )

  UNION ALL

  SELECT
    'marketplace_sellers',
    (
      SELECT COUNT(*)
      FROM `olist-marketplace-analytics.olist_raw.sellers`
    ),
    (
      SELECT COUNT(DISTINCT seller_id)
      FROM `olist-marketplace-analytics.olist_marts.mart_order_seller`
    )

  UNION ALL

  SELECT
    'reviewed_orders',
    (
      SELECT COUNT(DISTINCT order_id)
      FROM `olist-marketplace-analytics.olist_raw.order_reviews`
    ),
    (
      SELECT SUM(reviewed_order_count)
      FROM
        `olist-marketplace-analytics.olist_analysis.delivery_review_analysis`
    )
)

SELECT
  metric_name,
  source_value,
  final_value,
  final_value - source_value AS difference,
  CASE
    WHEN final_value = source_value THEN 'PASS'
    ELSE 'FAIL'
  END AS check_status
FROM comparisons;

-- Validation observed: six passed checks and zero failed checks.
SELECT
  COUNT(*) AS total_checks,
  COUNTIF(check_status = 'PASS') AS passed_checks,
  COUNTIF(check_status = 'FAIL') AS failed_checks
FROM `olist-marketplace-analytics.olist_quality.final_kpi_validation`;
