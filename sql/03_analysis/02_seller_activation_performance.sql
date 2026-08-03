-- Purpose: Rank activated sellers by post-win commercial performance
-- overall and within their acquisition origin.
-- Grain: One row per activated seller/closed lead.

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_analysis.seller_activation_performance` AS

SELECT
  mql_id,
  seller_id,
  origin,
  business_segment,
  won_date,
  first_post_win_order_date,
  days_to_first_sale,
  post_win_order_count,
  post_win_item_count,
  post_win_product_value,
  post_win_freight_value,
  ROUND(
    SAFE_DIVIDE(post_win_product_value, post_win_order_count),
    2
  ) AS product_value_per_order,
  average_review_score,
  on_time_delivery_rate_pct,
  RANK() OVER (
    ORDER BY post_win_product_value DESC
  ) AS overall_product_value_rank,
  RANK() OVER (
    PARTITION BY origin
    ORDER BY post_win_product_value DESC
  ) AS origin_product_value_rank,
  RANK() OVER (
    ORDER BY post_win_order_count DESC
  ) AS overall_order_count_rank
FROM `olist-marketplace-analytics.olist_marts.mart_seller_lifecycle`
WHERE is_activated;

-- Validation: expected 380 activated seller rows with unique seller IDs.
SELECT
  COUNT(*) AS activated_seller_rows,
  COUNT(DISTINCT seller_id) AS unique_activated_sellers,
  MIN(overall_product_value_rank) AS best_rank
FROM
  `olist-marketplace-analytics.olist_analysis.seller_activation_performance`;
