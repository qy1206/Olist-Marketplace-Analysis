from __future__ import annotations

import copy
import json
import re
import zipfile
from pathlib import Path


ROOT = Path(r"D:\olist-marketplace-analytics\powerbi")
SOURCE = ROOT / "Olist_Marketplace_Analytics.pbix"
TARGET = ROOT / "Olist_Marketplace_Analytics_Styled.pbix"
THEME_EXPORT = ROOT / "Olist_Portfolio_Theme.json"

PAGE_NAME = "01 Executive Overview"
CANVAS = "#F4F7FB"
INK = "#0F172A"
MUTED = "#64748B"
BORDER = "#DCE4EE"
WHITE = "#FFFFFF"
BLUE = "#2563EB"
TEAL = "#0F766E"
AMBER = "#D97706"
VIOLET = "#7C3AED"
GREEN = "#16A34A"
RED = "#DC2626"


def dump_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def lit(value: str | int | float | bool) -> dict:
    if isinstance(value, bool):
        encoded = "true" if value else "false"
    elif isinstance(value, str):
        encoded = "'" + value.replace("'", "''") + "'"
    else:
        encoded = f"{value}D"
    return {"expr": {"Literal": {"Value": encoded}}}


def solid(color: str) -> dict:
    return {"solid": {"color": lit(color)}}


def parse_config(visual: dict) -> dict:
    return json.loads(visual["config"])


def save_config(visual: dict, config: dict) -> None:
    visual["config"] = dump_json(config)


def visual_type(visual: dict) -> str:
    return parse_config(visual).get("singleVisual", {}).get("visualType", "")


def measure_name(visual: dict) -> str | None:
    transforms = json.loads(visual.get("dataTransforms", "{}"))
    for item in transforms.get("queryMetadata", {}).get("Select", []):
        name = item.get("Name", "")
        if name.startswith("_Measures."):
            return name.split(".", 1)[1]
    return None


def set_position(visual: dict, x: float, y: float, width: float, height: float, z: int) -> None:
    visual.update(x=float(x), y=float(y), width=float(width), height=float(height), z=float(z))
    config = parse_config(visual)
    layouts = config.setdefault("layouts", [{"id": 0, "position": {}}])
    position = layouts[0].setdefault("position", {})
    position.update(
        x=float(x),
        y=float(y),
        width=float(width),
        height=float(height),
        z=float(z * 1000),
        tabOrder=float(z * 1000),
    )
    save_config(visual, config)


def set_container_style(
    visual: dict,
    *,
    background: str = WHITE,
    border: str = BORDER,
    radius: int = 10,
    title_size: int = 13,
) -> None:
    config = parse_config(visual)
    single = config.setdefault("singleVisual", {})
    vc = single.setdefault("vcObjects", {})
    vc["background"] = [
        {
            "properties": {
                "show": lit(True),
                "color": solid(background),
                "transparency": lit(0),
            }
        }
    ]
    vc["border"] = [
        {
            "properties": {
                "show": lit(True),
                "color": solid(border),
                "radius": lit(radius),
                "width": lit(1),
            }
        }
    ]
    vc["visualHeader"] = [{"properties": {"show": lit(False)}}]
    if "title" in vc:
        title = vc["title"][0].setdefault("properties", {})
        title.update(
            show=lit(True),
            fontColor=solid(INK),
            fontFamily=lit("Segoe UI Semibold"),
            fontSize=lit(title_size),
            alignment=lit("left"),
            background=solid(WHITE),
        )
    save_config(visual, config)


def set_card_style(visual: dict, *, background: str, accent: str) -> None:
    set_container_style(visual, background=background, border=BORDER, radius=12)
    config = parse_config(visual)
    single = config["singleVisual"]
    objects = single.setdefault("objects", {})
    value_entries = objects.setdefault("value", [{"properties": {}}])
    for entry in value_entries:
        properties = entry.setdefault("properties", {})
        properties.update(
            fontSize=lit(25),
            fontFamily=lit("Segoe UI Semibold"),
            fontColor=solid(accent),
        )
    objects["label"] = [
        {
            "properties": {
                "show": lit(True),
                "position": lit("belowValue"),
                "fontSize": lit(10),
                "fontFamily": lit("Segoe UI"),
                "fontColor": solid(MUTED),
            },
            "selector": {"id": "default"},
        }
    ]
    objects["layout"] = [
        {
            "properties": {
                "backgroundShow": lit(False),
                "paddingUniform": lit(14),
                "paddingIndividual": lit(False),
            },
            "selector": {"id": "default"},
        }
    ]
    save_config(visual, config)


def set_chart_style(visual: dict, *, accent: str) -> None:
    set_container_style(visual, background=WHITE, border=BORDER, radius=10, title_size=13)
    config = parse_config(visual)
    single = config["singleVisual"]
    objects = single.setdefault("objects", {})
    objects["categoryAxis"] = [
        {
            "properties": {
                "show": lit(True),
                "showAxisTitle": lit(False),
                "labelColor": solid(MUTED),
                "fontSize": lit(9),
                "gridlineStyle": lit("dotted"),
            }
        }
    ]
    objects["valueAxis"] = [
        {
            "properties": {
                "show": lit(True),
                "showAxisTitle": lit(False),
                "labelColor": solid(MUTED),
                "fontSize": lit(9),
                "gridlineColor": solid("#E8EEF5"),
                "gridlineStyle": lit("dotted"),
            }
        }
    ]
    objects["dataPoint"] = [
        {
            "properties": {
                "defaultColor": solid(accent),
                "fill": solid(accent),
            }
        }
    ]
    if single.get("visualType") == "lineChart":
        objects["lineStyles"] = [
            {
                "properties": {
                    "strokeWidth": lit(3),
                    "showMarker": lit(True),
                    "markerSize": lit(5),
                }
            }
        ]
    save_config(visual, config)


def set_donut_style(visual: dict) -> None:
    set_container_style(visual, background=WHITE, border=BORDER, radius=10, title_size=13)
    config = parse_config(visual)
    objects = config["singleVisual"].setdefault("objects", {})
    objects["legend"] = [
        {
            "properties": {
                "show": lit(True),
                "position": lit("RightCenter"),
                "fontColor": solid(MUTED),
                "fontSize": lit(9),
            }
        }
    ]
    objects["labels"] = [
        {
            "properties": {
                "show": lit(True),
                "labelStyle": lit("Percent of total"),
                "fontColor": solid(INK),
                "fontSize": lit(9),
            }
        }
    ]
    save_config(visual, config)


def set_slicer_style(visual: dict) -> None:
    set_container_style(visual, background=WHITE, border=BORDER, radius=10, title_size=12)
    config = parse_config(visual)
    single = config["singleVisual"]
    objects = single.setdefault("objects", {})
    data = objects.setdefault("data", [{"properties": {}}])
    data[0].setdefault("properties", {})["mode"] = lit("Dropdown")
    objects["header"] = [
        {
            "properties": {
                "show": lit(True),
                "fontColor": solid(INK),
                "textSize": lit(11),
                "background": solid(WHITE),
                "outlineColor": solid(BORDER),
            }
        }
    ]
    objects["items"] = [
        {
            "properties": {
                "fontColor": solid(MUTED),
                "textSize": lit(10),
                "background": solid(WHITE),
            }
        }
    ]
    save_config(visual, config)


def build_theme(base: dict) -> dict:
    theme = copy.deepcopy(base)
    theme.update(
        name="Olist Portfolio Theme",
        dataColors=[BLUE, "#14B8A6", AMBER, VIOLET, RED, "#64748B", "#0EA5E9", GREEN],
        background=WHITE,
        foreground=INK,
        tableAccent=BLUE,
        good=GREEN,
        neutral=AMBER,
        bad=RED,
        textClasses={
            "callout": {"fontSize": 24, "fontFace": "Segoe UI Semibold", "color": INK},
            "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": INK},
            "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": INK},
            "label": {"fontSize": 9, "fontFace": "Segoe UI", "color": MUTED},
        },
    )
    styles = theme.setdefault("visualStyles", {})
    wildcard = styles.setdefault("*", {}).setdefault("*", {})
    wildcard["background"] = [{"show": True, "color": {"solid": {"color": WHITE}}, "transparency": 0}]
    wildcard["border"] = [
        {"show": True, "color": {"solid": {"color": BORDER}}, "radius": 10, "width": 1}
    ]
    wildcard["visualHeader"] = [{"show": False}]
    wildcard["title"] = [
        {
            "show": True,
            "fontColor": {"solid": {"color": INK}},
            "fontFamily": "Segoe UI Semibold",
            "fontSize": 12,
            "alignment": "left",
            "titleWrap": True,
        }
    ]
    page = styles.setdefault("page", {}).setdefault("*", {})
    page["outspace"] = [{"color": {"solid": {"color": CANVAS}}}]
    page["background"] = [
        {"color": {"solid": {"color": CANVAS}}, "transparency": 0}
    ]
    return theme


def rewrite_pbix(source: Path, target: Path, layout: dict, theme_name: str, theme: dict) -> None:
    layout_bytes = dump_json(layout).encode("utf-16le")
    theme_bytes = json.dumps(theme, ensure_ascii=False, indent=2).encode("utf-8")
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(target, "w") as zout:
        for info in zin.infolist():
            if info.filename == "SecurityBindings":
                continue
            data = zin.read(info.filename)
            if info.filename == "Report/Layout":
                data = layout_bytes
            elif info.filename == theme_name:
                data = theme_bytes
            elif info.filename == "[Content_Types].xml":
                text = data.decode("utf-8-sig")
                text = re.sub(r'<Override PartName="/SecurityBindings" ContentType=""\s*/>', "", text)
                data = ("\ufeff" + text).encode("utf-8")
            zout.writestr(info, data)


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    with zipfile.ZipFile(SOURCE, "r") as archive:
        layout = json.loads(archive.read("Report/Layout").decode("utf-16le"))
        theme_name = next(name for name in archive.namelist() if "BaseThemes" in name and name.endswith(".json"))
        base_theme = json.loads(archive.read(theme_name).decode("utf-8-sig"))

    page = next(section for section in layout["sections"] if section.get("displayName") == PAGE_NAME)
    if len(page["visualContainers"]) != 10:
        raise RuntimeError(f"Expected 10 visuals on {PAGE_NAME}, found {len(page['visualContainers'])}")

    page["width"] = 1280
    page["height"] = 720
    page["displayOption"] = 1
    page["config"] = {
        "objects": {
            "background": [
                {
                    "properties": {
                        "color": {"solid": {"color": CANVAS}},
                        "transparency": 0,
                    }
                }
            ]
        }
    }

    visuals = page["visualContainers"]
    cards = [visual for visual in visuals if visual_type(visual) == "cardVisual"]
    by_measure = {measure_name(visual): visual for visual in cards}
    card_specs = [
        ("Total Orders", 20, "#EFF6FF", "#1D4ED8"),
        ("GMV", 228, "#ECFDF5", TEAL),
        ("AOV", 436, "#FFFBEB", "#B45309"),
        ("Active Sellers", 644, "#F5F3FF", "#6D28D9"),
        ("On-Time Delivery Rate", 852, "#F0FDF4", "#15803D"),
        ("Average Review Score", 1060, "#FFF7ED", "#C2410C"),
    ]
    for z, (measure, x, background, accent) in enumerate(card_specs):
        visual = by_measure.get(measure)
        if visual is None:
            raise RuntimeError(f"Missing KPI card: {measure}")
        set_position(visual, x, 20, 200, 120, z)
        set_card_style(visual, background=background, accent=accent)

    line = next(visual for visual in visuals if visual_type(visual) == "lineChart")
    column = next(visual for visual in visuals if visual_type(visual) == "clusteredColumnChart")
    donut = next(visual for visual in visuals if visual_type(visual) == "donutChart")
    slicer = next(visual for visual in visuals if visual_type(visual) == "slicer")

    set_position(line, 20, 160, 820, 330, 6)
    set_chart_style(line, accent=BLUE)
    set_position(donut, 860, 160, 400, 330, 7)
    set_donut_style(donut)
    set_position(column, 20, 510, 820, 190, 8)
    set_chart_style(column, accent="#14B8A6")
    set_position(slicer, 860, 510, 400, 190, 9)
    set_slicer_style(slicer)

    theme = build_theme(base_theme)
    rewrite_pbix(SOURCE, TARGET, layout, theme_name, theme)
    THEME_EXPORT.write_text(json.dumps(theme, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created: {TARGET}")
    print(f"Theme:   {THEME_EXPORT}")


if __name__ == "__main__":
    main()
