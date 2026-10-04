"""Power BI report definition helpers adapted from the existing portfolio project."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "powerbi" / "project"
REPORT = PROJECT / "Operations.Report"
MODEL = PROJECT / "Operations.SemanticModel"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/"
FACT = "FactRequests"
BLUE = "#087D77"
ORANGE = "#E57939"
INK = "#182F35"
MUTED = "#647477"
WIDTH, HEIGHT = 1280, 720


def write(path: Path, content: str | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, dict):
        content = json.dumps(content, ensure_ascii=False, indent=2) + "\n"
    path.write_text(content, encoding="utf-8")


def identifier(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()[:20]


def literal(value: str | bool | int | float) -> dict:
    if isinstance(value, bool):
        text = str(value).lower()
    elif isinstance(value, str):
        text = "'" + value.replace("'", "''") + "'"
    else:
        text = f"{value}D"
    return {"expr": {"Literal": {"Value": text}}}


def color(value: str) -> dict:
    return {"solid": {"color": literal(value)}}


def object_properties(properties: dict, selector: dict | None = None) -> list:
    result = {"properties": properties}
    if selector:
        result["selector"] = selector
    return [result]


def field(kind: str, table: str, name: str, source: bool = False) -> dict:
    return {kind: {"Expression": {"SourceRef": {"Source" if source else "Entity": table}}, "Property": name}}


def projection(kind: str, table: str, name: str, display: str | None = None) -> dict:
    result = {"field": field(kind, table, name), "queryRef": f"{table}.{name}", "nativeQueryRef": name}
    if display:
        result["displayName"] = display
    if kind == "Column":
        result["active"] = True
    return result


def query(**roles: list) -> dict:
    return {"queryState": {role: {"projections": ps} for role, ps in roles.items()}}


def sort_by(query_definition: dict, expression: dict, direction: str = "Ascending") -> None:
    query_definition["sortDefinition"] = {"sort": [{"field": expression, "direction": direction}], "isDefaultSort": False}


def filter_definition(table: str, column: str, values: list[str], date: bool = False) -> dict:
    literals = [f"datetime'{v}T00:00:00'" if date else "'" + v.replace("'", "''") + "'" for v in values]
    return {
        "Version": 2,
        "From": [{"Name": "s", "Entity": table, "Type": 0}],
        "Where": [{"Condition": {"In": {
            "Expressions": [field("Column", "s", column, source=True)],
            "Values": [[{"Literal": {"Value": value}}] for value in literals],
        }}}],
    }


def container(title: str = "", alt: str = "", background: bool = True) -> dict:
    return {
        "title": object_properties({"show": literal(bool(title)), "text": literal(title), "fontSize": literal(13), "fontFamily": literal("Segoe UI"), "fontColor": color(INK), "alignment": literal("left"), "titleWrap": literal(True)}),
        "background": object_properties({"show": literal(background), "color": color("#FFFFFF"), "transparency": literal(0)}),
        "border": object_properties({"show": literal(background), "color": color("#E1E7F0"), "radius": literal(8)}),
        "padding": object_properties({key: literal(12) for key in ("top", "bottom", "left", "right")}),
        "general": object_properties({"altText": literal(alt or title)}),
    }


def add_visual(page: str, label: str, typ: str, x: int, y: int, w: int, h: int, order: int, q: dict | None = None, objects: dict | None = None, framing: dict | None = None, filters: dict | None = None) -> str:
    name = identifier(page + "/" + label)
    visual = {"visualType": typ, "visualContainerObjects": framing or container()}
    if q is not None:
        visual["query"] = q
    if objects:
        visual["objects"] = objects
    item = {"$schema": SCHEMA + "item/report/definition/visualContainer/2.4.0/schema.json", "name": name,
            "position": {"x": x, "y": y, "z": order, "width": w, "height": h, "tabOrder": order}, "visual": visual}
    if filters:
        item["filterConfig"] = filters
    write(REPORT / "definition" / "pages" / page / "visuals" / name / "visual.json", item)
    return name


def text(page: str, label: str, value: str, x: int, y: int, w: int, h: int, order: int, size: int = 12, shade: str = MUTED) -> str:
    framing = container(value, value, background=False)
    framing["title"][0]["properties"].update({"fontSize": literal(size), "fontColor": color(shade)})
    framing["border"][0]["properties"]["show"] = literal(False)
    framing["padding"] = object_properties({key: literal(0) for key in ("top", "bottom", "left", "right")})
    return add_visual(page, label, "textbox", x, y, w, h, order,
                      objects={"general": object_properties({"paragraphs": [{"textRuns": [{"value": ""}]}]})}, framing=framing)

