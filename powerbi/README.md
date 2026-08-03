# Power BI report

## Published portfolio artifact

`Olist_Marketplace_Analytics_Portfolio.pbix` is the only PBIX intended for
GitHub. It contains five report pages, 54 visual objects, the semantic model,
DAX measures, and the embedded `Olist Portfolio Theme`.

## Supporting file

- `Olist_Portfolio_Theme.json` — reusable report theme matching the published
  PBIX.

Working copies and recovery files are excluded by `.gitignore`.

## Validation scope

The automated test checks PBIX container integrity, the presence of the report
layout and data model, all five expected pages, 54 visual objects, and the
embedded theme. Visual rendering must still be inspected in Power BI Desktop
because it is version-dependent.
