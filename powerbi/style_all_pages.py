from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import style_executive_overview as base


ROOT = Path(r"D:\olist-marketplace-analytics\powerbi")
SOURCE = ROOT / "Olist_Marketplace_Analytics_Styled.pbix"
TARGET = ROOT / "Olist_Marketplace_Analytics_Portfolio.pbix"
THEME_EXPORT = ROOT / "Olist_Portfolio_Theme.json"


CARD_COLORS = {
    "Total Orders": ("#EFF6FF", "#1D4ED8"),
    "GMV": ("#ECFDF5", base.TEAL),
    "AOV": ("#FFFBEB", "#B45309"),
    "Active Sellers": ("#F5F3FF", "#6D28D9"),
    "On-Time Delivery Rate": ("#F0FDF4", "#15803D"),
    "Average Review Score": ("#FFF7ED", "#C2410C"),
    "Total Leads": ("#EFF6FF", "#1D4ED8"),
    "Won Leads": ("#ECFDF5", base.TEAL),
    "Lead-to-Close Rate": ("#F5F3FF", "#6D28D9"),
    "Activated Sellers": ("#F0FDF4", "#15803D"),
    "Activation Rate": ("#ECFEFF", "#0E7490"),
    "Median Lead-to-Close Days": ("#FFFBEB", "#B45309"),
    "Median Days to First Sale": ("#FFF7ED", "#C2410C"),
    "Seller Orders": ("#EFF6FF", "#1D4ED8"),
    "Seller Seller GMV": ("#ECFDF5", base.TEAL),
    "Orders per Seller": ("#F5F3FF", "#6D28D9"),
    "Seller Late Delivery Rate": ("#FEF2F2", "#B91C1C"),
    "Delivered Orders": ("#EFF6FF", "#1D4ED8"),
    "Late Delivery Rate": ("#FEF2F2", "#B91C1C"),
    "Average Delivery Days": ("#FFFBEB", "#B45309"),
    "Freight-to-GMV Ratio": ("#F5F3FF", "#6D28D9"),
}


PAGE_ACCENTS = {
    "01 Executive Overview": [base.BLUE, "#14B8A6"],
    "02 Acquisition Funnel": ["#7C3AED", base.BLUE, "#14B8A6"],
    "03 Seller Performance": [base.TEAL, base.BLUE, "#7C3AED", "#DC2626"],
    "04 Fulfilment and CX": ["#16A34A", "#D97706", "#DC2626", base.BLUE],
    "05 Seller Detail": [base.BLUE, base.TEAL, "#7C3AED"],
}


def set_page_background(page: dict) -> None:
    page["width"] = 1280
    page["height"] = 720
    page["displayOption"] = 1
    page["config"] = {
        "objects": {
            "background": [
                {
                    "properties": {
                        "color": {"solid": {"color": base.CANVAS}},
                        "transparency": 0,
                    }
                }
            ]
        }
    }


def set_card_font_size(visual: dict, size: int) -> None:
    config = base.parse_config(visual)
    objects = config["singleVisual"].setdefault("objects", {})
    for entry in objects.get("value", []):
        entry.setdefault("properties", {})["fontSize"] = base.lit(size)
    base.save_config(visual, config)


def style_card(visual: dict, *, compact: bool = False) -> None:
    measure = base.measure_name(visual) or ""
    background, accent = CARD_COLORS.get(measure, ("#EFF6FF", base.BLUE))
    base.set_card_style(visual, background=background, accent=accent)
    set_card_font_size(visual, 21 if compact else 24)


def order_by_measure(visuals: list[dict], measures: list[str]) -> list[dict]:
    by_measure = {base.measure_name(visual): visual for visual in visuals}
    missing = [name for name in measures if name not in by_measure]
    if missing:
        raise RuntimeError(f"Missing KPI cards: {missing}")
    return [by_measure[name] for name in measures]


def place_cards(page: dict, measures: list[str], *, y: int, height: int) -> None:
    cards = [v for v in page["visualContainers"] if base.visual_type(v) == "cardVisual"]
    cards = order_by_measure(cards, measures)
    gap = 10
    margin = 20
    width = (1280 - 2 * margin - gap * (len(cards) - 1)) / len(cards)
    for index, visual in enumerate(cards):
        x = margin + index * (width + gap)
        base.set_position(visual, x, y, width, height, index)
        style_card(visual, compact=len(cards) >= 6)


def visuals_of_type(page: dict, kind: str) -> list[dict]:
    return [v for v in page["visualContainers"] if base.visual_type(v) == kind]


def position_and_style(
    visual: dict,
    position: tuple[int, int, int, int],
    z: int,
    accent: str,
) -> None:
    x, y, width, height = position
    base.set_position(visual, x, y, width, height, z)
    kind = base.visual_type(visual)
    if kind == "donutChart":
        base.set_donut_style(visual)
    elif kind == "slicer":
        base.set_slicer_style(visual)
    else:
        base.set_chart_style(visual, accent=accent)


def style_page_01(page: dict) -> None:
    measures = [
        "Total Orders",
        "GMV",
        "AOV",
        "Active Sellers",
        "On-Time Delivery Rate",
        "Average Review Score",
    ]
    place_cards(page, measures, y=20, height=120)
    position_and_style(visuals_of_type(page, "lineChart")[0], (20, 160, 820, 330), 6, base.BLUE)
    position_and_style(visuals_of_type(page, "donutChart")[0], (860, 160, 400, 330), 7, base.TEAL)
    position_and_style(
        visuals_of_type(page, "clusteredColumnChart")[0], (20, 510, 820, 190), 8, "#14B8A6"
    )
    position_and_style(visuals_of_type(page, "slicer")[0], (860, 510, 400, 190), 9, base.BLUE)


def style_page_02(page: dict) -> None:
    measures = [
        "Total Leads",
        "Won Leads",
        "Lead-to-Close Rate",
        "Activated Sellers",
        "Activation Rate",
        "Median Lead-to-Close Days",
        "Median Days to First Sale",
    ]
    place_cards(page, measures, y=20, height=115)
    bars = visuals_of_type(page, "clusteredBarChart")
    slicers = visuals_of_type(page, "slicer")
    position_and_style(bars[0], (20, 155, 470, 245), 7, "#7C3AED")
    position_and_style(bars[1], (510, 155, 350, 245), 8, base.BLUE)
    position_and_style(slicers[0], (880, 155, 380, 115), 9, base.BLUE)
    position_and_style(slicers[1], (880, 285, 380, 115), 10, "#7C3AED")
    position_and_style(visuals_of_type(page, "lineChart")[0], (20, 420, 1240, 280), 11, base.TEAL)


def style_page_03(page: dict) -> None:
    measures = [
        "Active Sellers",
        "Seller Orders",
        "Seller Seller GMV",
        "Orders per Seller",
        "Average Review Score",
        "Seller Late Delivery Rate",
    ]
    place_cards(page, measures, y=20, height=120)
    bars = visuals_of_type(page, "clusteredBarChart")
    slicers = visuals_of_type(page, "slicer")
    position_and_style(bars[0], (20, 160, 485, 250), 6, base.TEAL)
    position_and_style(visuals_of_type(page, "lineChart")[0], (520, 160, 485, 250), 7, base.BLUE)
    position_and_style(slicers[0], (1020, 160, 240, 120), 8, base.BLUE)
    position_and_style(slicers[1], (1020, 295, 240, 115), 9, base.TEAL)
    position_and_style(bars[1], (20, 430, 485, 270), 10, base.RED)
    position_and_style(
        visuals_of_type(page, "clusteredColumnChart")[0], (520, 430, 740, 270), 11, "#7C3AED"
    )


def style_page_04(page: dict) -> None:
    measures = [
        "Delivered Orders",
        "On-Time Delivery Rate",
        "Late Delivery Rate",
        "Average Delivery Days",
        "Average Review Score",
        "Freight-to-GMV Ratio",
    ]
    place_cards(page, measures, y=20, height=120)
    position_and_style(visuals_of_type(page, "donutChart")[0], (20, 160, 360, 240), 6, base.GREEN)
    position_and_style(visuals_of_type(page, "lineChart")[0], (400, 160, 605, 240), 7, base.GREEN)
    position_and_style(visuals_of_type(page, "slicer")[0], (1020, 160, 240, 120), 8, base.BLUE)
    position_and_style(
        visuals_of_type(page, "clusteredBarChart")[0], (20, 420, 485, 280), 9, base.RED
    )
    position_and_style(
        visuals_of_type(page, "clusteredColumnChart")[0], (520, 420, 740, 280), 10, "#D97706"
    )


def style_page_05(page: dict) -> None:
    measures = [
        "Seller Orders",
        "Seller Seller GMV",
        "Average Review Score",
        "Seller Late Delivery Rate",
    ]
    place_cards(page, measures, y=20, height=120)
    position_and_style(visuals_of_type(page, "lineChart")[0], (20, 160, 610, 250), 4, base.TEAL)
    position_and_style(
        visuals_of_type(page, "clusteredColumnChart")[0], (650, 160, 610, 250), 5, base.BLUE
    )
    position_and_style(
        visuals_of_type(page, "clusteredBarChart")[0], (20, 430, 610, 270), 6, "#7C3AED"
    )
    slicers = visuals_of_type(page, "slicer")
    position_and_style(slicers[0], (650, 430, 400, 270), 7, base.TEAL)
    position_and_style(slicers[1], (1070, 430, 190, 270), 8, base.BLUE)


def validate_layout(layout: dict) -> None:
    expected = {
        "01 Executive Overview": 10,
        "02 Acquisition Funnel": 12,
        "03 Seller Performance": 12,
        "04 Fulfilment and CX": 11,
        "05 Seller Detail": 9,
    }
    pages = {page.get("displayName"): page for page in layout["sections"]}
    if set(pages) != set(expected):
        raise RuntimeError(f"Unexpected page set: {sorted(pages)}")
    for name, count in expected.items():
        page = pages[name]
        visuals = page.get("visualContainers", [])
        if len(visuals) != count:
            raise RuntimeError(f"{name}: expected {count} visuals, found {len(visuals)}")
        ids: set[str] = set()
        for visual in visuals:
            config = base.parse_config(visual)
            visual_id = config.get("name")
            if visual_id in ids:
                raise RuntimeError(f"{name}: duplicate visual id {visual_id}")
            ids.add(visual_id)
            json.loads(visual.get("query", "{}"))
            json.loads(visual.get("dataTransforms", "{}"))
            x = float(visual.get("x", 0))
            y = float(visual.get("y", 0))
            width = float(visual.get("width", 0))
            height = float(visual.get("height", 0))
            if x < 0 or y < 0 or x + width > 1280.01 or y + height > 720.01:
                raise RuntimeError(f"{name}: visual outside canvas: {(x, y, width, height)}")


def sha256_member(path: Path, member: str) -> str:
    with zipfile.ZipFile(path, "r") as archive:
        return hashlib.sha256(archive.read(member)).hexdigest()


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    with zipfile.ZipFile(SOURCE, "r") as archive:
        layout = json.loads(archive.read("Report/Layout").decode("utf-16le"))
        theme_name = next(
            name for name in archive.namelist() if "BaseThemes" in name and name.endswith(".json")
        )
        base_theme = json.loads(archive.read(theme_name).decode("utf-8-sig"))

    pages = {page["displayName"]: page for page in layout["sections"]}
    for page in pages.values():
        set_page_background(page)
    style_page_01(pages["01 Executive Overview"])
    style_page_02(pages["02 Acquisition Funnel"])
    style_page_03(pages["03 Seller Performance"])
    style_page_04(pages["04 Fulfilment and CX"])
    style_page_05(pages["05 Seller Detail"])
    validate_layout(layout)

    theme = base.build_theme(base_theme)
    base.rewrite_pbix(SOURCE, TARGET, layout, theme_name, theme)
    THEME_EXPORT.write_text(json.dumps(theme, ensure_ascii=False, indent=2), encoding="utf-8")

    with zipfile.ZipFile(TARGET, "r") as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise RuntimeError(f"Corrupt PBIX member: {corrupt}")
        output_layout = json.loads(archive.read("Report/Layout").decode("utf-16le"))
    validate_layout(output_layout)
    if sha256_member(SOURCE, "DataModel") != sha256_member(TARGET, "DataModel"):
        raise RuntimeError("DataModel changed while styling the report")

    print(f"Created: {TARGET}")
    print(f"Pages: {len(output_layout['sections'])}")
    print(f"Visuals: {sum(len(page['visualContainers']) for page in output_layout['sections'])}")
    print(f"DataModel SHA256: {sha256_member(TARGET, 'DataModel')}")
    print(f"PBIX SHA256: {hashlib.sha256(TARGET.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
