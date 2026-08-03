-- Purpose: Connect closed marketing leads to their post-win marketplace
-- activity and measure seller activation and fulfilment performance.
-- Grain: One row per won marketing-qualified lead (mql_id).

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_marts.mart_seller_lifecycle` AS

WITH seller_activity AS (
  SELECT
    funnel.mql_id,
    funnel.seller_id,
    MIN(performance.purchase_date) AS first_post_win_order_date,
    COUNT(DISTINCT performance.order_id) AS post_win_order_count,
    SUM(performance.item_count) AS post_win_item_count,
    SUM(performance.product_value) AS post_win_product_value,
    SUM(performance.freight_value) AS post_win_freight_value,
    ROUND(AVG(performance.average_review_score), 2)
      AS average_review_score,
    COUNTIF(performance.delivery_status = 'on_time')
      AS on_time_order_count,
    COUNTIF(performance.delivery_status = 'late')
      AS late_order_count,
    ROUND(
      SAFE_DIVIDE(
        COUNTIF(performance.delivery_status = 'on_time'),
        COUNTIF(performance.delivery_status IN ('on_time', 'late'))
      ) * 100,
      2
    ) AS on_time_delivery_rate_pct
  FROM `olist-marketplace-analytics.olist_staging.stg_marketing_funnel`
    AS funnel
  LEFT JOIN `olist-marketplace-analytics.olist_marts.mart_order_seller`
    AS performance
    ON funnel.seller_id = performance.seller_id
    AND performance.purchase_date >= DATE(funnel.won_date)
  WHERE funnel.is_won
  GROUP BY
    funnel.mql_id,
    funnel.seller_id
)

SELECT
  funnel.mql_id,
  funnel.seller_id,
  funnel.first_contact_date,
  DATE_TRUNC(funnel.first_contact_date, MONTH) AS contact_month,
  funnel.origin,
  funnel.won_date,
  funnel.days_to_close,
  funnel.business_segment,
  funnel.lead_type,
  funnel.lead_behaviour_profile,
  funnel.business_type,
  activity.first_post_win_order_date,
  CASE
    WHEN activity.first_post_win_order_date IS NOT NULL
    THEN DATE_DIFF(
      activity.first_post_win_order_date,
      DATE(funnel.won_date),
      DAY
    )
    ELSE NULL
  END AS days_to_first_sale,
  COALESCE(activity.post_win_order_count, 0) AS post_win_order_count,
  COALESCE(activity.post_win_item_count, 0) AS post_win_item_count,
  COALESCE(activity.post_win_product_value, 0)
    AS post_win_product_value,
  COALESCE(activity.post_win_freight_value, 0)
    AS post_win_freight_value,
  activity.average_review_score,
  COALESCE(activity.on_time_order_count, 0) AS on_time_order_count,
  COALESCE(activity.late_order_count, 0) AS late_order_count,
  activity.on_time_delivery_rate_pct,
  activity.first_post_win_order_date IS NOT NULL AS is_activated,
  CASE
    WHEN activity.first_post_win_order_date IS NOT NULL THEN 'activated'
    ELSE 'not_activated'
  END AS activation_status
FROM `olist-marketplace-analytics.olist_staging.stg_marketing_funnel`
  AS funnel
LEFT JOIN seller_activity AS activity
  ON funnel.mql_id = activity.mql_id
WHERE funnel.is_won;

-- Validation: expected 842 closed leads and 380 activated sellers.
SELECT
  COUNT(*) AS closed_leads,
  COUNTIF(is_activated) AS activated_sellers,
  ROUND(
    SAFE_DIVIDE(COUNTIF(is_activated), COUNT(*)) * 100,
    2
  ) AS closed_to_activation_rate_pct
FROM `olist-marketplace-analytics.olist_marts.mart_seller_lifecycle`;
