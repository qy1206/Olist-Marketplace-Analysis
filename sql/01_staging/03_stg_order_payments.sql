-- Purpose: Standardise payment fields and correct invalid credit-card instalments.
-- Grain: One row per order payment sequence (order_id, payment_sequential).

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_staging.stg_order_payments` AS

SELECT
  order_id,
  payment_sequential,
  LOWER(TRIM(payment_type)) AS payment_type,
  payment_installments AS original_payment_installments,
  CASE
    WHEN LOWER(TRIM(payment_type)) = 'credit_card'
      AND payment_installments <= 0
    THEN 1
    ELSE payment_installments
  END AS payment_installments,
  payment_installments <= 0 AS installment_corrected_flag,
  CAST(payment_value AS NUMERIC) AS payment_value
FROM `olist-marketplace-analytics.olist_raw.order_payments`
WHERE order_id IS NOT NULL
  AND payment_sequential IS NOT NULL
  AND payment_value IS NOT NULL
  AND payment_value >= 0;

-- Validation: raw and staging row counts should match; two rows were corrected.
SELECT
  (
    SELECT COUNT(*)
    FROM `olist-marketplace-analytics.olist_raw.order_payments`
  ) AS raw_rows,
  COUNT(*) AS staging_rows,
  COUNTIF(installment_corrected_flag) AS corrected_rows
FROM `olist-marketplace-analytics.olist_staging.stg_order_payments`;
