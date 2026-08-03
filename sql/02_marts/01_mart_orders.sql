-- Purpose: Build one order-level mart for revenue, customer, payment,
-- and delivery analysis without one-to-many join fanout.
-- Grain: One row per order_id.

CREATE SCHEMA IF NOT EXISTS
  `olist-marketplace-analytics.olist_marts`
OPTIONS(location = 'US');

CREATE OR REPLACE VIEW
  `olist-marketplace-analytics.olist_marts.mart_orders` AS

WITH item_summary AS (
  SELECT
    order_id,
    COUNT(*) AS item_count,
    COUNT(DISTINCT product_id) AS product_count,
    COUNT(DISTINCT seller_id) AS seller_count,
    SUM(item_price) AS product_value,
    SUM(freight_value) AS freight_value,
    SUM(item_total_value) AS item_total_value
  FROM `olist-marketplace-analytics.olist_staging.stg_order_items`
  GROUP BY order_id
),

payment_summary AS (
  SELECT
    order_id,
    COUNT(*) AS payment_record_count,
    STRING_AGG(
      DISTINCT payment_type,
      ', '
      ORDER BY payment_type
    ) AS payment_types,
    MAX(payment_installments) AS maximum_installments,
    SUM(payment_value) AS payment_value
  FROM `olist-marketplace-analytics.olist_staging.stg_order_payments`
  GROUP BY order_id
)

SELECT
  o.order_id,
  o.customer_id,
  c.customer_unique_id,
  LOWER(TRIM(c.customer_city)) AS customer_city,
  c.customer_state,
  o.order_status,
  o.purchase_date,
  o.purchase_month,
  o.order_purchase_timestamp,
  o.order_delivered_customer_date,
  o.order_estimated_delivery_date,
  COALESCE(i.item_count, 0) AS item_count,
  COALESCE(i.product_count, 0) AS product_count,
  COALESCE(i.seller_count, 0) AS seller_count,
  COALESCE(i.product_value, 0) AS product_value,
  COALESCE(i.freight_value, 0) AS freight_value,
  COALESCE(i.item_total_value, 0) AS item_total_value,
  COALESCE(p.payment_record_count, 0) AS payment_record_count,
  p.payment_types,
  p.maximum_installments,
  COALESCE(p.payment_value, 0) AS payment_value,
  DATE_DIFF(
    DATE(o.order_delivered_customer_date),
    o.purchase_date,
    DAY
  ) AS delivery_days,
  CASE
    WHEN o.order_delivered_customer_date IS NULL THEN 'not_delivered'
    WHEN o.order_delivered_customer_date
      <= o.order_estimated_delivery_date THEN 'on_time'
    ELSE 'late'
  END AS delivery_status
FROM `olist-marketplace-analytics.olist_staging.stg_orders` AS o
LEFT JOIN item_summary AS i
  ON o.order_id = i.order_id
LEFT JOIN payment_summary AS p
  ON o.order_id = p.order_id
LEFT JOIN `olist-marketplace-analytics.olist_raw.customers` AS c
  ON o.customer_id = c.customer_id;

-- Validation: the mart must remain at one row per order.
SELECT
  COUNT(*) AS mart_rows,
  COUNT(DISTINCT order_id) AS unique_orders
FROM `olist-marketplace-analytics.olist_marts.mart_orders`;
