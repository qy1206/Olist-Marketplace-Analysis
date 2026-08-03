-- Purpose: Summarise marketing acquisition and closed-deal conversion
-- by first-contact month and acquisition origin.
-- Grain: One row per (contact_month, origin).

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_marts.mart_marketing_funnel` AS

SELECT
  DATE_TRUNC(first_contact_date, MONTH) AS contact_month,
  origin,
  COUNT(*) AS total_leads,
  COUNTIF(is_won) AS won_leads,
  COUNTIF(NOT is_won) AS not_won_leads,
  COUNT(DISTINCT seller_id) AS closed_seller_count,
  ROUND(
    SAFE_DIVIDE(COUNTIF(is_won), COUNT(*)) * 100,
    2
  ) AS conversion_rate_pct,
  ROUND(
    AVG(
      CASE
        WHEN is_won THEN days_to_close
        ELSE NULL
      END
    ),
    2
  ) AS average_days_to_close
FROM `olist-marketplace-analytics.olist_staging.stg_marketing_funnel`
GROUP BY
  contact_month,
  origin;

-- Validation: totals must reconcile to the lead-level staging view.
SELECT
  SUM(total_leads) AS total_leads,
  SUM(won_leads) AS won_leads
FROM `olist-marketplace-analytics.olist_marts.mart_marketing_funnel`;
