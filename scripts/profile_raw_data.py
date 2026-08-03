"""Profile the downloaded Olist CSV files without changing the raw data."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import median


EXPECTED_COLUMNS = {
    "olist_customers_dataset.csv": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "olist_geolocation_dataset.csv": [
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
    ],
    "olist_order_items_dataset.csv": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ],
    "olist_order_payments_dataset.csv": [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ],
    "olist_orders_dataset.csv": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_products_dataset.csv": [
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    "olist_sellers_dataset.csv": [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ],
    "product_category_name_translation.csv": [
        "product_category_name",
        "product_category_name_english",
    ],
    "olist_closed_deals_dataset.csv": [
        "mql_id",
        "seller_id",
        "sdr_id",
        "sr_id",
        "won_date",
        "business_segment",
        "lead_type",
        "lead_behaviour_profile",
        "has_company",
        "has_gtin",
        "average_stock",
        "business_type",
        "declared_product_catalog_size",
        "declared_monthly_revenue",
    ],
    "olist_marketing_qualified_leads_dataset.csv": [
        "mql_id",
        "first_contact_date",
        "landing_page_id",
        "origin",
    ],
}

KEY_FIELDS = {
    "olist_customers_dataset.csv": ("customer_id",),
    "olist_order_items_dataset.csv": ("order_id", "order_item_id"),
    "olist_order_payments_dataset.csv": ("order_id", "payment_sequential"),
    "olist_order_reviews_dataset.csv": ("review_id",),
    "olist_orders_dataset.csv": ("order_id",),
    "olist_products_dataset.csv": ("product_id",),
    "olist_sellers_dataset.csv": ("seller_id",),
    "product_category_name_translation.csv": ("product_category_name",),
    "olist_closed_deals_dataset.csv": ("mql_id",),
    "olist_marketing_qualified_leads_dataset.csv": ("mql_id",),
}

TRACK_FIELDS = {
    "olist_customers_dataset.csv": ("customer_id",),
    "olist_order_items_dataset.csv": ("order_id", "product_id", "seller_id"),
    "olist_order_payments_dataset.csv": ("order_id",),
    "olist_order_reviews_dataset.csv": ("order_id",),
    "olist_orders_dataset.csv": ("order_id", "customer_id"),
    "olist_products_dataset.csv": ("product_id",),
    "olist_sellers_dataset.csv": ("seller_id",),
    "olist_closed_deals_dataset.csv": ("mql_id", "seller_id"),
    "olist_marketing_qualified_leads_dataset.csv": ("mql_id",),
}


def find_csv(input_dir: Path, filename: str) -> Path:
    matches = list(input_dir.rglob(filename))
    if len(matches) != 1:
        raise SystemExit(
            f"Expected exactly one {filename} below {input_dir}; found {len(matches)}"
        )
    return matches[0]


def profile_csv(path: Path) -> tuple[dict, dict[str, set[str]]]:
    expected = EXPECTED_COLUMNS[path.name]
    key_fields = KEY_FIELDS.get(path.name)
    tracked = {field: set() for field in TRACK_FIELDS.get(path.name, ())}
    key_values: set[tuple[str, ...]] = set()
    duplicate_key_rows = 0
    row_count = 0
    null_counts: dict[str, int] = {}

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        null_counts = {column: 0 for column in columns}

        for row in reader:
            row_count += 1
            for column in columns:
                if row.get(column, "") == "":
                    null_counts[column] += 1

            if key_fields:
                key = tuple(row.get(field, "") for field in key_fields)
                if key in key_values:
                    duplicate_key_rows += 1
                else:
                    key_values.add(key)

            for field in tracked:
                value = row.get(field, "")
                if value:
                    tracked[field].add(value)

    profile = {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "rows": row_count,
        "columns": columns,
        "column_count": len(columns),
        "missing_expected_columns": [column for column in expected if column not in columns],
        "unexpected_columns": [column for column in columns if column not in expected],
        "candidate_key": list(key_fields) if key_fields else None,
        "duplicate_candidate_key_rows": duplicate_key_rows if key_fields else None,
        "null_counts": null_counts,
    }
    return profile, tracked


def coverage(
    name: str,
    left_values: set[str],
    right_values: set[str],
    left_label: str,
    right_label: str,
) -> dict:
    matched = left_values & right_values
    total = len(left_values)
    return {
        "relationship": name,
        "left": left_label,
        "right": right_label,
        "distinct_left_keys": total,
        "matched_left_keys": len(matched),
        "unmatched_left_keys": total - len(matched),
        "match_rate": round(len(matched) / total, 6) if total else None,
    }


def seller_activation_feasibility(input_dir: Path) -> dict:
    mql_origin: dict[str, str] = {}
    mql_counts: Counter[str] = Counter()
    with find_csv(input_dir, "olist_marketing_qualified_leads_dataset.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            origin = row["origin"] or "unknown"
            mql_origin[row["mql_id"]] = origin
            mql_counts[origin] += 1

    closed_deals = []
    with find_csv(input_dir, "olist_closed_deals_dataset.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            closed_deals.append(
                {
                    "mql_id": row["mql_id"],
                    "seller_id": row["seller_id"],
                    "won_date": datetime.fromisoformat(row["won_date"]).date(),
                    "origin": mql_origin.get(row["mql_id"], "unknown"),
                }
            )

    closed_sellers = {row["seller_id"] for row in closed_deals}
    seller_order_ids: dict[str, set[str]] = defaultdict(set)
    relevant_order_ids: set[str] = set()
    with find_csv(input_dir, "olist_order_items_dataset.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            seller_id = row["seller_id"]
            if seller_id in closed_sellers:
                order_id = row["order_id"]
                seller_order_ids[seller_id].add(order_id)
                relevant_order_ids.add(order_id)

    order_dates: dict[str, date] = {}
    with find_csv(input_dir, "olist_orders_dataset.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            order_id = row["order_id"]
            if order_id in relevant_order_ids:
                order_dates[order_id] = datetime.fromisoformat(
                    row["order_purchase_timestamp"]
                ).date()

    closed_counts: Counter[str] = Counter()
    any_order_counts: Counter[str] = Counter()
    post_win_counts: Counter[str] = Counter()
    activation_delays: list[int] = []
    sellers_with_pre_win_orders = 0

    for deal in closed_deals:
        origin = deal["origin"]
        seller_id = deal["seller_id"]
        won_date = deal["won_date"]
        closed_counts[origin] += 1
        dates = sorted(
            order_dates[order_id]
            for order_id in seller_order_ids.get(seller_id, set())
            if order_id in order_dates
        )
        if dates:
            any_order_counts[origin] += 1
        if any(order_date < won_date for order_date in dates):
            sellers_with_pre_win_orders += 1
        post_win_dates = [order_date for order_date in dates if order_date >= won_date]
        if post_win_dates:
            post_win_counts[origin] += 1
            activation_delays.append((post_win_dates[0] - won_date).days)

    origins = sorted(mql_counts)
    by_origin = []
    for origin in origins:
        closed = closed_counts[origin]
        activated = post_win_counts[origin]
        by_origin.append(
            {
                "origin": origin,
                "mqls": mql_counts[origin],
                "closed_deals": closed,
                "closed_sellers_with_any_order": any_order_counts[origin],
                "post_win_activated_sellers": activated,
                "mql_to_close_rate": round(closed / mql_counts[origin], 6)
                if mql_counts[origin]
                else None,
                "closed_to_activation_rate": round(activated / closed, 6)
                if closed
                else None,
            }
        )

    return {
        "closed_deals": len(closed_deals),
        "closed_sellers_with_any_order": sum(any_order_counts.values()),
        "post_win_activated_sellers": sum(post_win_counts.values()),
        "sellers_with_pre_win_orders": sellers_with_pre_win_orders,
        "median_days_to_first_post_win_sale": median(activation_delays)
        if activation_delays
        else None,
        "minimum_days_to_first_post_win_sale": min(activation_delays)
        if activation_delays
        else None,
        "maximum_days_to_first_post_win_sale": max(activation_delays)
        if activation_delays
        else None,
        "by_origin": by_origin,
    }


def build_markdown(report: dict) -> str:
    lines = [
        "# Olist Raw Data Inventory",
        "",
        "Generated from the downloaded CSV files. Raw files were read only.",
        "",
        "## File Inventory",
        "",
        "| File | Rows | Columns | Candidate key | Duplicate key rows | Schema |",
        "|---|---:|---:|---|---:|---|",
    ]
    for item in report["files"]:
        key = ", ".join(item["candidate_key"] or []) or "Not tested"
        duplicates = item["duplicate_candidate_key_rows"]
        duplicate_text = str(duplicates) if duplicates is not None else "Not tested"
        schema = (
            "PASS"
            if not item["missing_expected_columns"] and not item["unexpected_columns"]
            else "REVIEW"
        )
        lines.append(
            f"| `{item['file']}` | {item['rows']:,} | {item['column_count']} | "
            f"{key} | {duplicate_text} | {schema} |"
        )

    lines.extend(
        [
            "",
            "## Join Coverage",
            "",
            "| Relationship | Distinct left keys | Matched | Unmatched | Match rate |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for item in report["join_coverage"]:
        rate = "N/A" if item["match_rate"] is None else f"{item['match_rate']:.2%}"
        lines.append(
            f"| {item['relationship']} | {item['distinct_left_keys']:,} | "
            f"{item['matched_left_keys']:,} | {item['unmatched_left_keys']:,} | {rate} |"
        )

    lines.extend(
        [
            "",
            "## Seller Activation Feasibility",
            "",
            f"- Closed deals: {report['seller_activation_feasibility']['closed_deals']:,}",
            f"- Closed sellers found in order items: {report['seller_activation_feasibility']['closed_sellers_with_any_order']:,}",
            f"- Sellers with at least one order on or after won_date: {report['seller_activation_feasibility']['post_win_activated_sellers']:,}",
            f"- Median days from won_date to first post-win sale: {report['seller_activation_feasibility']['median_days_to_first_post_win_sale']}",
            f"- Sellers with at least one pre-win order: {report['seller_activation_feasibility']['sellers_with_pre_win_orders']:,}",
            "",
            "| Origin | MQLs | Closed deals | Post-win activated sellers | MQL-to-close | Closed-to-activation |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for item in report["seller_activation_feasibility"]["by_origin"]:
        close_rate = (
            "N/A"
            if item["mql_to_close_rate"] is None
            else f"{item['mql_to_close_rate']:.2%}"
        )
        activation_rate = (
            "N/A"
            if item["closed_to_activation_rate"] is None
            else f"{item['closed_to_activation_rate']:.2%}"
        )
        lines.append(
            f"| {item['origin']} | {item['mqls']:,} | {item['closed_deals']:,} | "
            f"{item['post_win_activated_sellers']:,} | {close_rate} | {activation_rate} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `closed_deals.seller_id -> order_items.seller_id` measures how many closed sellers later appear in an order item. This is the initial seller-activation feasibility check.",
            "- A missing foreign-key match must be investigated before modelling; it is not automatically deleted.",
            "- The geolocation table is not expected to have a unique row per ZIP-code prefix, so no primary-key uniqueness test is applied.",
            "- Raw CSV files remain unchanged. Cleaning rules belong in SQL staging models.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    actual_paths = list(args.input_dir.rglob("*.csv"))
    actual_files = sorted(path.name for path in actual_paths)
    if len(actual_files) != len(set(actual_files)):
        raise SystemExit("Duplicate CSV filenames were found below the input directory.")
    expected_files = sorted(EXPECTED_COLUMNS)
    missing_files = sorted(set(expected_files) - set(actual_files))
    extra_files = sorted(set(actual_files) - set(expected_files))
    if missing_files or extra_files:
        raise SystemExit(
            f"CSV set mismatch. Missing={missing_files}; extra={extra_files}"
        )

    profiles = []
    tracked_by_file: dict[str, dict[str, set[str]]] = {}
    for filename in expected_files:
        profile, tracked = profile_csv(find_csv(args.input_dir, filename))
        profiles.append(profile)
        tracked_by_file[filename] = tracked

    joins = [
        coverage(
            "orders.customer_id -> customers.customer_id",
            tracked_by_file["olist_orders_dataset.csv"]["customer_id"],
            tracked_by_file["olist_customers_dataset.csv"]["customer_id"],
            "orders.customer_id",
            "customers.customer_id",
        ),
        coverage(
            "order_items.order_id -> orders.order_id",
            tracked_by_file["olist_order_items_dataset.csv"]["order_id"],
            tracked_by_file["olist_orders_dataset.csv"]["order_id"],
            "order_items.order_id",
            "orders.order_id",
        ),
        coverage(
            "payments.order_id -> orders.order_id",
            tracked_by_file["olist_order_payments_dataset.csv"]["order_id"],
            tracked_by_file["olist_orders_dataset.csv"]["order_id"],
            "payments.order_id",
            "orders.order_id",
        ),
        coverage(
            "reviews.order_id -> orders.order_id",
            tracked_by_file["olist_order_reviews_dataset.csv"]["order_id"],
            tracked_by_file["olist_orders_dataset.csv"]["order_id"],
            "reviews.order_id",
            "orders.order_id",
        ),
        coverage(
            "order_items.product_id -> products.product_id",
            tracked_by_file["olist_order_items_dataset.csv"]["product_id"],
            tracked_by_file["olist_products_dataset.csv"]["product_id"],
            "order_items.product_id",
            "products.product_id",
        ),
        coverage(
            "order_items.seller_id -> sellers.seller_id",
            tracked_by_file["olist_order_items_dataset.csv"]["seller_id"],
            tracked_by_file["olist_sellers_dataset.csv"]["seller_id"],
            "order_items.seller_id",
            "sellers.seller_id",
        ),
        coverage(
            "closed_deals.mql_id -> MQL.mql_id",
            tracked_by_file["olist_closed_deals_dataset.csv"]["mql_id"],
            tracked_by_file["olist_marketing_qualified_leads_dataset.csv"]["mql_id"],
            "closed_deals.mql_id",
            "MQL.mql_id",
        ),
        coverage(
            "closed_deals.seller_id -> sellers.seller_id",
            tracked_by_file["olist_closed_deals_dataset.csv"]["seller_id"],
            tracked_by_file["olist_sellers_dataset.csv"]["seller_id"],
            "closed_deals.seller_id",
            "sellers.seller_id",
        ),
        coverage(
            "closed_deals.seller_id -> order_items.seller_id",
            tracked_by_file["olist_closed_deals_dataset.csv"]["seller_id"],
            tracked_by_file["olist_order_items_dataset.csv"]["seller_id"],
            "closed_deals.seller_id",
            "order_items.seller_id",
        ),
    ]

    report = {
        "input_directory": str(args.input_dir.resolve()),
        "csv_count": len(actual_files),
        "missing_files": missing_files,
        "extra_files": extra_files,
        "files": profiles,
        "join_coverage": joins,
        "seller_activation_feasibility": seller_activation_feasibility(
            args.input_dir
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "data_inventory.json"
    markdown_path = args.output_dir / "data_inventory.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_path.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
