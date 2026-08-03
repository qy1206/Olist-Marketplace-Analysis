-- Purpose: Compare customer review outcomes across delivery-delay buckets.
-- This identifies association, not proof that delay caused a review score.
-- Grain: One row per delivery-delay bucket.

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_analysis.delivery_review_analysis` AS

WITH review_summary AS (
  SELECT
    order_id,
    COUNT(*) AS review_row_count,
    COUNT(DISTINCT review_id) AS review_count,
    AVG(review_score) AS average_review_score
  FROM `olist-marketplace-analytics.olist_raw.order_reviews`
  GROUP BY order_id
),

order_review_base AS (
  SELECT
    orders.order_id,
    orders.delivery_status,
    DATE_DIFF(
      DATE(orders.order_delivered_customer_date),
      DATE(orders.order_estimated_delivery_date),
      DAY
    ) AS delivery_delay_days,
    reviews.review_row_count,
    reviews.review_count,
    reviews.average_review_score,
    CASE
      WHEN orders.order_delivered_customer_date IS NULL
        THEN 'not_delivered'
      WHEN DATE(orders.order_delivered_customer_date)
        <= DATE(orders.order_estimated_delivery_date)
        THEN 'on_time_or_early'
      WHEN DATE_DIFF(
        DATE(orders.order_delivered_customer_date),
        DATE(orders.order_estimated_delivery_date),
        DAY
      ) <= 3
        THEN 'late_1_3_days'
      WHEN DATE_DIFF(
        DATE(orders.order_delivered_customer_date),
        DATE(orders.order_estimated_delivery_date),
        DAY
      ) <= 7
        THEN 'late_4_7_days'
      ELSE 'late_8_plus_days'
    END AS delivery_delay_bucket
  FROM `olist-marketplace-analytics.olist_marts.mart_orders` AS orders
  LEFT JOIN review_summary AS reviews
    ON orders.order_id = reviews.order_id
)

SELECT
  delivery_delay_bucket,
  COUNT(*) AS order_count,
  COUNTIF(average_review_score IS NOT NULL) AS reviewed_order_count,
  ROUND(AVG(average_review_score), 2) AS average_review_score,
  ROUND(
    SAFE_DIVIDE(
      COUNTIF(average_review_score <= 2),
      COUNTIF(average_review_score IS NOT NULL)
    ) * 100,
    2
  ) AS low_review_rate_pct,
  ROUND(
    SAFE_DIVIDE(
      COUNTIF(average_review_score >= 4),
      COUNTIF(average_review_score IS NOT NULL)
    ) * 100,
    2
  ) AS high_review_rate_pct,
  ROUND(
    AVG(
      CASE
        WHEN delivery_delay_days > 0 THEN delivery_delay_days
        ELSE NULL
      END
    ),
    2
  ) AS average_late_days
FROM order_review_base
GROUP BY delivery_delay_bucket;

-- Validation: expected 99,441 total orders and 98,673 reviewed orders.
SELECT
  SUM(order_count) AS total_orders,
  SUM(reviewed_order_count) AS reviewed_orders
FROM
  `olist-marketplace-analytics.olist_analysis.delivery_review_analysis`;
