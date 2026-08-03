# Olist Marketplace Growth, Seller Onboarding & Fulfilment Analytics

An end-to-end data analytics portfolio project built with **BigQuery SQL** and
**Power BI**. It connects Olist's marketing funnel data to marketplace orders
through `seller_id` to evaluate acquisition quality, seller activation,
commercial performance, fulfilment, and customer experience.

## Business question

> Which acquisition channels produce sellers who close, activate, generate
> strong GMV, and fulfil customer orders reliably?

## Portfolio deliverables

- [Final Power BI report](powerbi/Olist_Marketplace_Analytics_Portfolio.pbix)
- [15-file SQL pipeline](sql/)
- [Raw-data inventory and join audit](docs/data_inventory.md)
- [Automated repository and PBIX checks](tests/test_repository.py)

## Dashboard preview

The screenshots below are direct captures from the packaged PBIX. They let a
reviewer assess the report without installing Power BI or refreshing BigQuery.

### Executive Overview

![Executive Overview dashboard showing marketplace KPIs and monthly trends](docs/images/executive-overview.png)

### Acquisition Funnel

![Acquisition Funnel dashboard showing leads, wins, activation and channel conversion](docs/images/acquisition-funnel.png)

### Semantic model

![Power BI semantic model with shared date, seller and origin dimensions](docs/images/data-model.png)

The downloadable PBIX also contains **Seller Performance**, **Fulfilment and
CX**, and a seller-level **Seller Detail** drill-through page.

## Solution architecture

```mermaid
flowchart LR
    A["11 Olist CSV files"] --> B["BigQuery raw layer"]
    B --> C["Staging views"]
    C --> D["Four analytical marts"]
    D --> E["Power BI semantic model"]
    E --> F["Five report pages"]
    C --> G["Analysis views"]
    D --> H["KPI and fanout checks"]
```

The SQL design deliberately separates raw data, cleaning, analytical marts,
business analysis, and reconciliation checks. Power BI consumes the marts—not
the eleven raw tables directly.

## SQL pipeline

| Stage | Files | Purpose |
|---|---:|---|
| `00_source_profiling` | 2 | Inventory tables, inspect keys, NULLs, and duplicate risks |
| `01_staging` | 4 | Standardise orders, items, payments, and marketing leads |
| `02_marts` | 4 | Build order, order-seller, marketing, and seller-lifecycle marts |
| `03_analysis` | 3 | Analyse acquisition, seller activation, delivery, and reviews |
| `04_quality_checks` | 2 | Reconcile join fanout and final portfolio KPIs |

Important SQL techniques include `JOIN`, CTEs, conditional aggregation,
`COUNTIF`, `CASE`, `SAFE_DIVIDE`, date calculations, string cleaning, window
functions, and explicit grain management.

## Power BI report

The final report contains **five decision-focused pages**:

1. **Executive Overview** — orders, GMV, AOV, active sellers, delivery, and reviews
2. **Acquisition Funnel** — leads, wins, conversion, activation, and channel quality
3. **Seller Performance** — seller GMV, orders, geography, reviews, and fulfilment risk
4. **Fulfilment and CX** — delivery speed, late-delivery rates, freight, and review outcomes
5. **Seller Detail** — seller-level drill-through for performance investigation

The semantic model uses shared `DimDate`, `DimSeller`, and `DimOrigin`
dimensions with one-to-many, single-direction relationships to the analytical
marts.

## Selected validated facts

- 99,441 orders and 112,650 order-item rows
- 8,000 marketing-qualified leads and 842 closed deals
- 380 closed sellers found in marketplace order activity
- Median time from a seller win to first post-win sale: 44 days
- All critical relationships listed in the data inventory achieved 100% match
  coverage, except the intentionally investigated closed-seller activation link

See [the full data inventory](docs/data_inventory.md) for row counts, candidate
keys, duplicate findings, and join coverage.

## Business findings and recommendations

| Evidence-backed finding | Decision implication |
|---|---|
| **Paid search** converted 1,586 leads into 195 wins (**12.30%**) and 101 activated sellers; its closed-to-activation rate was **51.79%**. | Treat paid search as a scalable acquisition channel, while monitoring seller value and fulfilment quality before increasing spend. |
| **Organic search** produced the largest identifiable-channel volume: 2,296 leads, 271 wins, and **113 activated sellers**. Its lead-to-close rate was **11.80%**, but closed-to-activation was lower at **41.70%**. | Preserve organic investment, then strengthen post-close onboarding to convert more won sellers into marketplace activity. |
| **Direct traffic** had the strongest closed-to-activation rate among material, attributable channels at **55.36%** (31 of 56 won leads), despite only 499 leads. | Investigate what makes direct-intent sellers activate successfully and reuse those onboarding signals in higher-volume channels. |
| **Social** generated 1,350 leads but only 75 wins (**5.56%**) and 31 activations. | Tighten targeting and lead qualification; volume alone is not producing comparable commercial progression. |
| The **unknown** origin category recorded the highest apparent lead-to-close rate (**16.65%**) across 1,159 leads, so attribution gaps materially affect channel comparison. | Fix source tagging before reallocating budget based solely on channel rankings. |

These findings are descriptive, not causal. Channel recommendations should be
validated against acquisition cost, which is not included in the public Olist
dataset.

## KPI definitions

| KPI | Portfolio definition |
|---|---|
| **Product GMV** | Sum of `item_price` across order items. It excludes freight charges and is kept separate from payment value. |
| **AOV** | Product GMV divided by distinct orders in the current filter context. |
| **Active seller** | Distinct `seller_id` values appearing in marketplace order items in the selected period. |
| **Won lead / closed deal** | A marketing-qualified lead with a matching record in `closed_deals`. |
| **Activated seller** | A won lead whose `seller_id` has at least one marketplace order on or after `won_date`. |
| **Lead-to-close rate** | Won leads divided by total marketing-qualified leads. |
| **Closed-to-activation rate** | Activated sellers divided by won leads. |
| **On-time delivery** | A delivered order where `order_delivered_customer_date <= order_estimated_delivery_date`. |
| **Late delivery** | A delivered order where `order_delivered_customer_date > order_estimated_delivery_date`. |
| **Reviewed order** | An `order_id` with at least one distinct `review_id`; review metrics are aggregated to order level before joining. |
| **Post-win sales** | Orders attributed to a closed seller where `purchase_date >= DATE(won_date)`. |

## Repository structure

```text
olist-marketplace-analytics/
|-- docs/                 # Published data inventory and join audit
|-- powerbi/              # Final PBIX report and reusable theme
|-- scripts/              # Raw-data profiling helper
|-- sql/                  # 15 ordered BigQuery SQL files
|-- tests/                # Repository and PBIX integrity checks
`-- README.md
```

## Reproduce the project

1. Download the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
   and place the eleven CSV files under `data/raw/`. Raw data is intentionally
   excluded from GitHub.
2. In BigQuery, create datasets named `olist_raw`, `olist_staging`,
   `olist_marts`, `olist_analysis`, and `olist_quality` in the same location.
3. Upload the CSV files into `olist_raw` using the table names referenced by the
   SQL files.
4. Execute the SQL files in folder and filename order, from
   `00_source_profiling` through `04_quality_checks`.
5. Open `powerbi/Olist_Marketplace_Analytics_Portfolio.pbix`, authenticate the
   BigQuery connection, and refresh the model.
6. Confirm that the quality views report zero failed reconciliation checks.

## Local validation

The checks use Python's standard library only:

```bash
python -m unittest discover -s tests -v
```

They verify the expected SQL structure, final PBIX integrity, report page and
visual counts, embedded theme, and GitHub's 100 MiB single-file limit.

## Data and analytical limitations

- The public dataset covers historical Brazilian marketplace activity and does
  not represent current Olist performance.
- Monetary values are presented in Brazilian reais (`R$`).
- Reviews are recorded at order level. A multi-seller order can therefore
  expose more than one seller to the same review; seller-level review findings
  are associations and must not be presented as causal effects.
- Seller activation is defined as a closed seller appearing in marketplace
  activity on or after `won_date`.
- Raw CSV files are not redistributed in this repository.

## Technology

`Google BigQuery` · `GoogleSQL` · `Power BI` · `DAX` · `Power Query` · `Python`
