-- Purpose: Compare acquisition origins across lead generation, closing,
-- seller activation, post-win sales, reviews, and fulfilment quality.
-- Grain: One row per acquisition origin.

CREATE SCHEMA IF NOT EXISTS
  `olist-marketplace-analytics.olist_analysis`
OPTIONS(location = 'US');

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_analysis.acquisition_channel_quality` AS

WITH lead_metrics AS (
  SELECT
    origin,
    SUM(total_leads) AS total_leads,
    SUM(won_leads) AS won_leads,
    ROUND(
      SAFE_DIVIDE(SUM(won_leads), SUM(total_leads)) * 100,
      2
    ) AS lead_to_close_rate_pct
  FROM `olist-marketplace-analytics.olist_marts.mart_marketing_funnel`
  GROUP BY origin
),

seller_metrics AS (
  SELECT
    origin,
    COUNT(*) AS closed_leads,
    COUNTIF(is_activated) AS activated_sellers,
    ROUND(
      SAFE_DIVIDE(COUNTIF(is_activated), COUNT(*)) * 100,
      2
    ) AS closed_to_activation_rate_pct,
    ROUND(
      AVG(
        CASE
          WHEN is_activated THEN days_to_first_sale
          ELSE NULL
        END
      ),
      2
    ) AS average_days_to_first_sale,
    SUM(post_win_order_count) AS post_win_order_count,
    SUM(post_win_product_value) AS post_win_product_value,
    ROUND(
      SAFE_DIVIDE(
        SUM(post_win_product_value),
        COUNTIF(is_activated)
      ),
      2
    ) AS product_value_per_activated_seller,
    ROUND(
      AVG(
        CASE
          WHEN is_activated THEN average_review_score
          ELSE NULL
        END
      ),
      2
    ) AS average_review_score,
    ROUND(
      SAFE_DIVIDE(
        SUM(on_time_order_count),
        SUM(on_time_order_count) + SUM(late_order_count)
      ) * 100,
      2
    ) AS on_time_delivery_rate_pct
  FROM `olist-marketplace-analytics.olist_marts.mart_seller_lifecycle`
  GROUP BY origin
)

SELECT
  leads.origin,
  leads.total_leads,
  leads.won_leads,
  leads.lead_to_close_rate_pct,
  COALESCE(sellers.activated_sellers, 0) AS activated_sellers,
  sellers.closed_to_activation_rate_pct,
  sellers.average_days_to_first_sale,
  COALESCE(sellers.post_win_order_count, 0) AS post_win_order_count,
  COALESCE(sellers.post_win_product_value, 0) AS post_win_product_value,
  sellers.product_value_per_activated_seller,
  sellers.average_review_score,
  sellers.on_time_delivery_rate_pct
FROM lead_metrics AS leads
LEFT JOIN seller_metrics AS sellers
  ON leads.origin = sellers.origin;

-- Validation: totals must reconcile across the acquisition lifecycle.
SELECT
  SUM(total_leads) AS total_leads,
  SUM(won_leads) AS won_leads,
  SUM(activated_sellers) AS activated_sellers
FROM
  `olist-marketplace-analytics.olist_analysis.acquisition_channel_quality`;
