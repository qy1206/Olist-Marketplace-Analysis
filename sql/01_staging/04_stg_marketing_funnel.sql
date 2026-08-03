-- Purpose: Join all marketing-qualified leads to their closed-deal outcomes.
-- Grain: One row per marketing-qualified lead (mql_id).

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_staging.stg_marketing_funnel` AS

SELECT
  mql.mql_id,
  mql.first_contact_date,
  mql.landing_page_id,
  COALESCE(
    NULLIF(LOWER(TRIM(mql.origin)), ''),
    'unknown'
  ) AS origin,
  deal.seller_id,
  deal.sdr_id,
  deal.sr_id,
  deal.won_date,
  DATE_DIFF(
    DATE(deal.won_date),
    mql.first_contact_date,
    DAY
  ) AS days_to_close,
  LOWER(TRIM(deal.business_segment)) AS business_segment,
  LOWER(TRIM(deal.lead_type)) AS lead_type,
  LOWER(TRIM(deal.lead_behaviour_profile)) AS lead_behaviour_profile,
  LOWER(TRIM(deal.business_type)) AS business_type,
  deal.mql_id IS NOT NULL AS is_won,
  CASE
    WHEN deal.mql_id IS NOT NULL THEN 'won'
    ELSE 'not_won'
  END AS lead_status
FROM `olist-marketplace-analytics.olist_raw.marketing_qualified_leads` AS mql
LEFT JOIN `olist-marketplace-analytics.olist_raw.closed_deals` AS deal
  ON mql.mql_id = deal.mql_id
WHERE mql.mql_id IS NOT NULL;

-- Validation: expected 8,000 leads, 842 won leads, and 10.53% conversion.
SELECT
  COUNT(*) AS total_leads,
  COUNTIF(is_won) AS won_leads,
  ROUND(
    SAFE_DIVIDE(COUNTIF(is_won), COUNT(*)) * 100,
    2
  ) AS conversion_rate_pct
FROM `olist-marketplace-analytics.olist_staging.stg_marketing_funnel`;
