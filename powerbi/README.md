# Power BI report

## Published portfolio artifact

`Olist_Marketplace_Analytics_Portfolio.pbix` is the only PBIX intended for
GitHub. It contains five report pages, 54 visual objects, the semantic model,
DAX measures, and the embedded `Olist Portfolio Theme`.

## Supporting files

- `Olist_Portfolio_Theme.json` — reusable report theme
- `style_all_pages.py` — applies the portfolio layout and styling to all pages
- `style_executive_overview.py` — shared PBIX layout and theme helpers
- `build_dashboard_layout.py` — reproducible report-page construction helper
- `configure_measures.ps1` — local Power BI measure configuration helper

Other PBIX files in this folder are local working copies or recovery files and
are excluded by `.gitignore`.

## Validation scope

The automated test checks PBIX container integrity, the presence of the report
layout and data model, all five expected pages, 54 visual objects, and the
embedded theme. Visual rendering must still be inspected in Power BI Desktop
because it is version-dependent.
