from __future__ import annotations

import copy
import json
import re
import secrets
import zipfile
from pathlib import Path


ROOT = Path(r"D:\olist-marketplace-analytics\powerbi")
SOURCE = ROOT / "Olist_Marketplace_Analytics.pbix"
CANDIDATE = ROOT / "Olist_Marketplace_Analytics_dashboard_candidate.pbix"


MEASURE_FORMATS = {
    "Total Orders": "#,0",
    "GMV": '"R$" #,0.00',
    "AOV": '"R$" #,0.00',
    "Active Sellers": "#,0",
    "Seller Orders": "#,0",
    "Orders per Seller": "0.00",
    "Seller GMV": '"R$" #,0.00',
    "Total Freight": '"R$" #,0.00',
    "Freight-to-GMV Ratio": "0.00%",
    "Total Leads": "#,0",
    "Won Leads": "#,0",
    "Lead-to-Close Rate": "0.00%",
    "Activated Sellers": "#,0",
    "Activation Rate": "0.00%",
    "Median Lead-to-Close Days": "0.00",
    "Median Days to First Sale": "0.00",
    "Delivered Orders": "#,0",
    "On-Time Orders": "#,0",
    "Late Orders": "#,0",
    "On-Time Delivery Rate": "0.00%",
    "Late Delivery Rate": "0.00%",
    "Average Delivery Days": "0.00",
    "Average Review Score": "0.00",
    "Seller Delivered Orders": "#,0",
    "Seller Late Orders": "#,0",
    "Seller Late Delivery Rate": "0.00%",
}


def hx(n: int = 20) -> str:
    return secrets.token_hex((n + 1) // 2)[:n]


def parse_json(value):
    if isinstance(value, str):
        return json.loads(value)
    return copy.deepcopy(value)


def dump_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def replace_json(value, replacements: dict[str, str]):
    def walk(item):
        if isinstance(item, dict):
            return {key: walk(child) for key, child in item.items()}
        if isinstance(item, list):
            return [walk(child) for child in item]
        if isinstance(item, str):
            for old in sorted(replacements, key=len, reverse=True):
                item = item.replace(old, replacements[old])
            return item
        return item

    return walk(copy.deepcopy(value))


def config_of(visual):
    return parse_json(visual["config"])


def visual_type(visual) -> str:
    return config_of(visual).get("singleVisual", {}).get("visualType", "")


def visual_measure(visual) -> str | None:
    transforms = parse_json(visual.get("dataTransforms", "{}"))
    for item in transforms.get("selects", []):
        expr = item.get("expr", {})
        if "Measure" in expr:
            return expr["Measure"].get("Property")
    return None


def set_visual_id(visual):
    cfg = config_of(visual)
    cfg["name"] = hx()
    visual["config"] = dump_json(cfg)


def set_position(visual, x, y, width, height, z):
    visual.update(x=float(x), y=float(y), width=float(width), height=float(height), z=float(z))
    # Power BI stores the desktop position twice: on the visual container and
    # inside config.layouts.  Updating only the outer values looks correct in
    # static inspection, but Desktop still renders the visual at its old
    # position.  Keep both representations in sync.
    cfg = config_of(visual)
    layouts = cfg.setdefault("layouts", [{"id": 0, "position": {}}])
    for layout in layouts:
        position = layout.setdefault("position", {})
        position.update(
            x=float(x),
            y=float(y),
            width=float(width),
            height=float(height),
            z=float(z),
            tabOrder=int(z),
        )
    visual["config"] = dump_json(cfg)


def set_title(visual, title: str | None):
    cfg = config_of(visual)
    single = cfg.setdefault("singleVisual", {})
    vc = single.setdefault("vcObjects", {})
    if not title:
        vc.pop("title", None)
    else:
        vc["title"] = [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": repr(title)}}},
                    "alignment": {"expr": {"Literal": {"Value": "'left'"}}},
                }
            }
        ]
    visual["config"] = dump_json(cfg)


def set_visual_type(visual, new_type: str):
    cfg = config_of(visual)
    cfg.setdefault("singleVisual", {})["visualType"] = new_type
    visual["config"] = dump_json(cfg)


def clone_visual(template, x, y, width, height, z, title=None):
    visual = copy.deepcopy(template)
    set_visual_id(visual)
    visual["filters"] = "[]"
    set_position(visual, x, y, width, height, z)
    set_title(visual, title)
    return visual


def remap_measure(visual, old_measure: str, new_measure: str):
    old_format = MEASURE_FORMATS.get(old_measure, "#,0")
    new_format = MEASURE_FORMATS.get(new_measure, old_format)
    replacements = {
        f"_Measures.{old_measure}": f"_Measures.{new_measure}",
        old_measure: new_measure,
        old_format: new_format,
    }
    for key in ("config", "query", "dataTransforms"):
        obj = parse_json(visual.get(key, "{}"))
        visual[key] = dump_json(replace_json(obj, replacements))


def remap_column(visual, old_table: str, old_column: str, new_table: str, new_column: str):
    replacements = {
        f"{old_table}.{old_column}": f"{new_table}.{new_column}",
        old_table: new_table,
        old_column: new_column,
    }
    for key in ("config", "query", "dataTransforms"):
        obj = parse_json(visual.get(key, "{}"))
        visual[key] = dump_json(replace_json(obj, replacements))


def card(card_templates, measure, x, y, width, height, z):
    template = card_templates.get(measure)
    if template is None:
        fmt = MEASURE_FORMATS[measure]
        if "%" in fmt:
            base = "On-Time Delivery Rate"
        elif "R$" in fmt:
            base = "GMV"
        elif "." in fmt:
            base = "AOV"
        else:
            base = "Total Orders"
        template = card_templates[base]
        old_measure = base
    else:
        old_measure = measure
    visual = clone_visual(template, x, y, width, height, z)
    if old_measure != measure:
        remap_measure(visual, old_measure, measure)
    return visual


def one_category_visual(
    template,
    old_table,
    old_column,
    old_measure,
    table,
    column,
    measure,
    title,
    x,
    y,
    width,
    height,
    z,
    new_type=None,
):
    visual = clone_visual(template, x, y, width, height, z, title)
    remap_column(visual, old_table, old_column, table, column)
    remap_measure(visual, old_measure, measure)
    if new_type:
        set_visual_type(visual, new_type)
    # remap_measure also replaces text inside the title.  Re-apply the intended
    # final title so names such as "Monthly Seller GMV" are not duplicated.
    set_title(visual, title)
    return visual


def two_measure_visual(
    template,
    table,
    column,
    measure1,
    measure2,
    title,
    x,
    y,
    width,
    height,
    z,
    new_type="lineChart",
):
    visual = clone_visual(template, x, y, width, height, z, title)
    remap_column(visual, "DimOrigin", "origin", table, column)
    remap_measure(visual, "Total Leads", measure1)
    remap_measure(visual, "Won Leads", measure2)
    set_visual_type(visual, new_type)
    # The acquisition template is ranked by its first measure.  A time-series
    # chart must instead be ordered chronologically by the category column.
    query = parse_json(visual["query"])
    semantic_query = query["Commands"][0]["SemanticQueryDataShapeCommand"]["Query"]
    source = next(item["Name"] for item in semantic_query["From"] if item.get("Entity") == table)
    semantic_query["OrderBy"] = [
        {
            "Direction": 1,
            "Expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Source": source}},
                    "Property": column,
                }
            },
        }
    ]
    visual["query"] = dump_json(query)
    cfg = config_of(visual)
    prototype = cfg["singleVisual"]["prototypeQuery"]
    prototype_source = next(item["Name"] for item in prototype["From"] if item.get("Entity") == table)
    prototype["OrderBy"] = [
        {
            "Direction": 1,
            "Expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Source": prototype_source}},
                    "Property": column,
                }
            },
        }
    ]
    visual["config"] = dump_json(cfg)
    transforms = parse_json(visual["dataTransforms"])
    for index, item in enumerate(transforms.get("selects", [])):
        item.pop("sort", None)
        item.pop("sortOrder", None)
        if index == 0:
            item["sort"] = 1
            item["sortOrder"] = 0
    visual["dataTransforms"] = dump_json(transforms)
    set_title(visual, title)
    return visual


def text_slicer(template, table, column, x, y, width, height, z):
    visual = clone_visual(template, x, y, width, height, z)
    cfg = config_of(visual)
    single = cfg["singleVisual"]
    source = table[:1].lower()
    select = {
        "Column": {
            "Expression": {"SourceRef": {"Source": source}},
            "Property": column,
        },
        "Name": f"{table}.{column}",
        "NativeReferenceName": column,
    }
    query_base = {"Version": 2, "From": [{"Name": source, "Entity": table, "Type": 0}], "Select": [select]}
    single.setdefault("projections", {})["Values"] = [{"queryRef": f"{table}.{column}", "active": True}]
    single["prototypeQuery"] = copy.deepcopy(query_base)
    single["objects"] = {
        "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}]
    }
    visual["config"] = dump_json(cfg)
    visual["query"] = dump_json(
        {
            "Commands": [
                {
                    "SemanticQueryDataShapeCommand": {
                        "Query": copy.deepcopy(query_base),
                        "Binding": {
                            "Primary": {"Groupings": [{"Projections": [0]}]},
                            "DataReduction": {"DataVolume": 3, "Primary": {"Window": {"Count": 500}}},
                            "IncludeEmptyGroups": True,
                            "Version": 1,
                        },
                        "ExecutionMetricsKind": 1,
                    }
                }
            ]
        }
    )
    visual["dataTransforms"] = dump_json(
        {
            "objects": {"data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}]},
            "projectionOrdering": {"Values": [0]},
            "projectionActiveItems": {"Values": [{"queryRef": f"{table}.{column}", "suppressConcat": False}]},
            "queryMetadata": {
                "Select": [{"Restatement": column, "Name": f"{table}.{column}", "Type": 2048}],
                "Filters": [
                    {
                        "type": 0,
                        "expression": {
                            "Column": {
                                "Expression": {"SourceRef": {"Entity": table}},
                                "Property": column,
                            }
                        },
                    }
                ],
            },
            "visualElements": [{"DataRoles": [{"Name": "Values", "Projection": 0, "isActive": True}]}],
            "selects": [
                {
                    "displayName": column,
                    "queryName": f"{table}.{column}",
                    "roles": {"Values": True},
                    "type": {"category": None, "underlyingType": 1},
                    "expr": {
                        "Column": {
                            "Expression": {"SourceRef": {"Entity": table}},
                            "Property": column,
                        }
                    },
                }
            ],
        }
    )
    return visual


def year_slicer(template, x, y, width, height, z):
    return clone_visual(template, x, y, width, height, z)


def new_page(base_section, display_name, ordinal, visible=True):
    page = copy.deepcopy(base_section)
    page["id"] = ordinal + 1
    page["name"] = hx(20)
    page["displayName"] = display_name
    page["ordinal"] = ordinal
    page["visualContainers"] = []
    page["filters"] = []
    page["config"] = {} if visible else {"visibility": 1}
    page["displayOption"] = 1
    page["width"] = 1280
    page["height"] = 720
    return page


def rewrite_pbix(source: Path, target: Path, layout: dict):
    layout_bytes = dump_json(layout).encode("utf-16le")
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(target, "w") as zout:
        for info in zin.infolist():
            if info.filename == "SecurityBindings":
                continue
            data = zin.read(info.filename)
            if info.filename == "Report/Layout":
                data = layout_bytes
            elif info.filename == "[Content_Types].xml":
                text = data.decode("utf-8-sig")
                text = re.sub(r'<Override PartName="/SecurityBindings" ContentType=""\s*/>', "", text)
                data = ("\ufeff" + text).encode("utf-8")
            zout.writestr(info, data)


def main():
    with zipfile.ZipFile(SOURCE) as z:
        layout = json.loads(z.read("Report/Layout").decode("utf-16le"))

    if len(layout["sections"]) != 2:
        raise RuntimeError("Expected the two-page starting report.")

    executive = layout["sections"][0]
    acquisition = layout["sections"][1]
    executive_visuals = executive["visualContainers"]
    acquisition_visuals = acquisition["visualContainers"]

    card_templates = {}
    for section in layout["sections"]:
        for visual in section["visualContainers"]:
            if visual_type(visual) == "cardVisual":
                measure = visual_measure(visual)
                if measure:
                    card_templates[measure] = visual

    required_card_bases = {
        "Total Orders",
        "GMV",
        "AOV",
        "On-Time Delivery Rate",
        "Average Review Score",
    }
    if not required_card_bases.issubset(card_templates):
        raise RuntimeError(f"Missing card templates: {required_card_bases - set(card_templates)}")

    line_template = executive_visuals[6]
    column_template = executive_visuals[7]
    donut_template = executive_visuals[8]
    year_slicer_template = executive_visuals[9]
    two_measure_template = acquisition_visuals[7]

    # Finish acquisition page and make its layout consistent.
    card_x = [0, 182, 364, 546, 728, 910, 1092]
    for i in range(7):
        set_position(acquisition_visuals[i], card_x[i], 5, 176, 125, i)
    set_position(acquisition_visuals[7], 0, 150, 470, 250, 7)
    set_title(acquisition_visuals[7], "Leads and Wins by Acquisition Channel")

    acquisition_visuals[8] = one_category_visual(
        column_template,
        "DimDate",
        "Year Month",
        "Total Orders",
        "DimOrigin",
        "origin",
        "Lead-to-Close Rate",
        "Channel Conversion Rate",
        480,
        150,
        390,
        250,
        8,
        "clusteredBarChart",
    )
    acquisition_visuals.extend(
        [
            two_measure_visual(
                two_measure_template,
                "DimDate",
                "Year Month",
                "Total Leads",
                "Won Leads",
                "Monthly Acquisition Trend",
                0,
                415,
                870,
                290,
                9,
            ),
            year_slicer(year_slicer_template, 885, 150, 180, 145, 10),
            text_slicer(year_slicer_template, "DimOrigin", "origin", 1075, 150, 195, 145, 11),
        ]
    )

    # Seller Performance page.
    seller_page = new_page(executive, "03 Seller Performance", 2)
    seller_cards = [
        "Active Sellers",
        "Seller Orders",
        "Seller GMV",
        "Orders per Seller",
        "Average Review Score",
        "Seller Late Delivery Rate",
    ]
    seller_card_layout = [
        (0, 190),
        (200, 190),
        (400, 250),
        (660, 190),
        (860, 190),
        (1060, 210),
    ]
    for i, (measure, (x, width)) in enumerate(zip(seller_cards, seller_card_layout)):
        seller_page["visualContainers"].append(card(card_templates, measure, x, 5, width, 135, i))
    seller_page["visualContainers"].extend(
        [
            one_category_visual(
                column_template,
                "DimDate",
                "Year Month",
                "Total Orders",
                "DimSeller",
                "seller_state",
                "Seller GMV",
                "Seller GMV by State",
                0,
                155,
                500,
                245,
                6,
                "clusteredBarChart",
            ),
            one_category_visual(
                line_template,
                "DimDate",
                "Year Month",
                "GMV",
                "DimDate",
                "Year Month",
                "Seller GMV",
                "Monthly Seller GMV",
                510,
                155,
                500,
                245,
                7,
                "lineChart",
            ),
            one_category_visual(
                column_template,
                "DimDate",
                "Year Month",
                "Total Orders",
                "DimSeller",
                "seller_state",
                "Seller Late Delivery Rate",
                "Late Delivery Risk by Seller State",
                0,
                415,
                500,
                285,
                8,
                "clusteredBarChart",
            ),
            one_category_visual(
                column_template,
                "DimDate",
                "Year Month",
                "Total Orders",
                "DimSeller",
                "seller_state",
                "Seller Orders",
                "Seller Orders by State",
                510,
                415,
                500,
                285,
                9,
                "clusteredColumnChart",
            ),
            year_slicer(year_slicer_template, 1020, 155, 245, 145, 10),
            text_slicer(year_slicer_template, "DimSeller", "seller_state", 1020, 315, 245, 145, 11),
        ]
    )

    # Fulfilment and customer experience page.
    fulfilment_page = new_page(executive, "04 Fulfilment and CX", 3)
    fulfilment_cards = [
        "Delivered Orders",
        "On-Time Delivery Rate",
        "Late Delivery Rate",
        "Average Delivery Days",
        "Average Review Score",
        "Freight-to-GMV Ratio",
    ]
    for i, measure in enumerate(fulfilment_cards):
        fulfilment_page["visualContainers"].append(card(card_templates, measure, i * 212, 5, 202, 135, i))
    fulfilment_page["visualContainers"].extend(
        [
            one_category_visual(
                donut_template,
                "FactOrders",
                "order_status",
                "Total Orders",
                "FactOrders",
                "delivery_status",
                "Total Orders",
                "Delivery Status Distribution",
                0,
                155,
                350,
                245,
                6,
                "donutChart",
            ),
            two_measure_visual(
                two_measure_template,
                "DimDate",
                "Year Month",
                "On-Time Delivery Rate",
                "Late Delivery Rate",
                "On-Time vs Late Delivery Trend",
                360,
                155,
                650,
                245,
                7,
            ),
            one_category_visual(
                column_template,
                "DimDate",
                "Year Month",
                "Total Orders",
                "FactOrders",
                "customer_state",
                "Late Delivery Rate",
                "Late Delivery Rate by Customer State",
                0,
                415,
                500,
                285,
                8,
                "clusteredBarChart",
            ),
            one_category_visual(
                column_template,
                "DimDate",
                "Year Month",
                "Total Orders",
                "FactOrders",
                "delivery_status",
                "Average Review Score",
                "Review Score by Delivery Outcome",
                510,
                415,
                500,
                285,
                9,
                "clusteredColumnChart",
            ),
            year_slicer(year_slicer_template, 1020, 155, 245, 145, 10),
        ]
    )

    # Focused seller page. A seller slicer keeps the page usable without relying
    # on an unsupported direct edit of Power BI's native drillthrough metadata.
    detail_page = new_page(executive, "05 Seller Detail", 4, visible=True)
    detail_cards = ["Seller Orders", "Seller GMV", "Average Review Score", "Seller Late Delivery Rate"]
    for i, measure in enumerate(detail_cards):
        detail_page["visualContainers"].append(card(card_templates, measure, i * 315, 5, 300, 140, i))
    detail_page["visualContainers"].extend(
        [
            one_category_visual(
                line_template,
                "DimDate",
                "Year Month",
                "GMV",
                "DimDate",
                "Year Month",
                "Seller GMV",
                "Selected Seller GMV Trend",
                0,
                165,
                620,
                250,
                4,
                "lineChart",
            ),
            one_category_visual(
                column_template,
                "DimDate",
                "Year Month",
                "Total Orders",
                "DimDate",
                "Year Month",
                "Seller Orders",
                "Selected Seller Order Trend",
                630,
                165,
                620,
                250,
                5,
                "clusteredColumnChart",
            ),
            one_category_visual(
                column_template,
                "DimDate",
                "Year Month",
                "Total Orders",
                "FactOrderSeller",
                "delivery_status",
                "Seller Orders",
                "Selected Seller Delivery Outcomes",
                0,
                430,
                620,
                270,
                6,
                "clusteredBarChart",
            ),
            text_slicer(year_slicer_template, "DimSeller", "seller_id", 630, 430, 400, 160, 7),
            year_slicer(year_slicer_template, 1040, 430, 210, 160, 8),
        ]
    )

    layout["sections"] = [executive, acquisition, seller_page, fulfilment_page, detail_page]
    for index, section in enumerate(layout["sections"]):
        section["ordinal"] = index

    # Return to the executive page when the candidate opens.
    report_cfg = parse_json(layout["config"])
    report_cfg["activeSectionIndex"] = 0
    layout["config"] = dump_json(report_cfg)

    rewrite_pbix(SOURCE, CANDIDATE, layout)

    # Static verification of the generated archive and report layout.
    with zipfile.ZipFile(CANDIDATE) as z:
        result = json.loads(z.read("Report/Layout").decode("utf-16le"))
        if "SecurityBindings" in z.namelist():
            raise RuntimeError("SecurityBindings was not removed from the modified package.")
    expected = {
        "01 Executive Overview": 10,
        "02 Acquisition Funnel": 12,
        "03 Seller Performance": 12,
        "04 Fulfilment and CX": 11,
        "05 Seller Detail": 9,
    }
    actual = {section["displayName"]: len(section["visualContainers"]) for section in result["sections"]}
    if actual != expected:
        raise RuntimeError(f"Visual inventory mismatch: {actual}")
    for section in result["sections"]:
        names = [config_of(v).get("name") for v in section["visualContainers"]]
        if len(names) != len(set(names)):
            raise RuntimeError(f"Duplicate visual IDs in {section['displayName']}")
        for visual in section["visualContainers"]:
            parse_json(visual["config"])
            parse_json(visual.get("query", "{}"))
            parse_json(visual.get("dataTransforms", "{}"))
    print(json.dumps({"candidate": str(CANDIDATE), "pages": actual}, indent=2))


if __name__ == "__main__":
    main()
