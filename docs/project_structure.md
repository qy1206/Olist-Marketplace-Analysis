# Project Structure

```text
olist-marketplace-analytics/
|-- data/
|   |-- raw/
|   |   |-- ecommerce/          # 9 original Olist e-commerce CSV files
|   |   |-- marketing/          # 2 original Olist marketing CSV files
|   |   `-- downloads/          # Optional original ZIP downloads
|   |-- processed/              # SQL/local validated intermediate exports
|   `-- powerbi_exports/        # Final marts exported for Power BI
|-- sql/
|   |-- 00_source_profiling/
|   |-- 01_staging/
|   |-- 02_marts/
|   |-- 03_analysis/
|   `-- 04_quality_checks/
|-- powerbi/                    # Final .pbix report
|-- docs/                       # Plan, inventory, dictionary, architecture
|-- scripts/                    # Lightweight repeatable validation helpers
|-- tests/                      # Automated checks where useful
|-- outputs/                    # Screenshots and portfolio-ready exports
|-- .gitignore
`-- README.md
```

## Fixed SQL file plan

### 00_source_profiling

1. `01_table_inventory.sql`
2. `02_source_quality_and_keys.sql`

### 01_staging

3. `01_stg_orders.sql`
4. `02_stg_order_items.sql`
5. `03_stg_order_payments.sql`
6. `04_stg_marketing_funnel.sql`

### 02_marts

7. `01_mart_orders.sql`
8. `02_mart_order_seller.sql`
9. `03_mart_marketing_funnel.sql`
10. `04_mart_seller_lifecycle.sql`

### 03_analysis

11. `01_acquisition_channel_quality.sql`
12. `02_seller_activation_performance.sql`
13. `03_delivery_review_analysis.sql`

### 04_quality_checks

14. `01_join_fanout_reconciliation.sql`
15. `02_final_kpi_validation.sql`

## File-placement rules

- `data/raw/` contains original files only. Never edit them.
- `data/processed/` contains intermediate validated outputs, not downloads.
- `data/powerbi_exports/` contains only the final four analytical marts.
- SQL files move forward through profiling, staging, marts, analysis, and
  quality checks.
- Power BI must consume marts rather than all eleven raw CSV files.
- Large raw data and generated exports are excluded from Git.
