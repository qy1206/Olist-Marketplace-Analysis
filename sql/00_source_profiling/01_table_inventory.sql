-- Purpose: Inventory all raw Olist tables after CSV ingestion.
-- Expected result: 11 tables with their row counts and storage sizes.

SELECT
  table_id AS table_name,
  row_count,
  ROUND(size_bytes / 1024 / 1024, 2) AS size_mb
FROM `olist-marketplace-analytics.olist_raw.__TABLES__`
ORDER BY table_name;
