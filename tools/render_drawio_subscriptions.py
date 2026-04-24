#!/usr/bin/env python3

from __future__ import annotations

import argparse
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_IDS = {
    "zone": "VcAaCNgKio1ltA4P-1JS-1",
    "zone_title": "VcAaCNgKio1ltA4P-1JS-2",
    "consumer_capability": "VcAaCNgKio1ltA4P-1JS-3",
    "emitter_capability": "VcAaCNgKio1ltA4P-1JS-4",
    "event_group": "VcAaCNgKio1ltA4P-1JS-7",
    "event_image": "VcAaCNgKio1ltA4P-1JS-5",
    "event_text": "VcAaCNgKio1ltA4P-1JS-6",
    "edge_emitter_to_event": "VcAaCNgKio1ltA4P-1JS-8",
    "edge_event_to_consumer": "VcAaCNgKio1ltA4P-1JS-9",
}

CAPABILITY_BOX_W = 130
CAPABILITY_BOX_H = 50


def _uid() -> str:
    return "cell-" + uuid.uuid4().hex[:12]


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"[FATAL] Impossible de lire/parse {path}: {exc}")


def _add_vertex(
    root: ET.Element,
    cell_id: str,
    value: str,
    style: str,
    x: float,
    y: float,
    w: float,
    h: float,
    parent: str = "1",
    connectable: str | None = None,
) -> ET.Element:
    cell = ET.SubElement(root, "mxCell")
    cell.set("id", cell_id)
    cell.set("value", value)
    cell.set("style", style)
    cell.set("vertex", "1")
    cell.set("parent", parent)
    if connectable is not None:
        cell.set("connectable", connectable)

    geo = ET.SubElement(cell, "mxGeometry")
    geo.set("x", f"{x:g}")
    geo.set("y", f"{y:g}")
    geo.set("width", f"{w:g}")
    geo.set("height", f"{h:g}")
    geo.set("as", "geometry")
    return cell


def _add_edge(
    root: ET.Element,
    cell_id: str,
    style: str,
    source: str,
    target: str,
    parent: str = "1",
) -> ET.Element:
    cell = ET.SubElement(root, "mxCell")
    cell.set("id", cell_id)
    cell.set("style", style)
    cell.set("edge", "1")
    cell.set("parent", parent)
    cell.set("source", source)
    cell.set("target", target)

    geo = ET.SubElement(cell, "mxGeometry")
    geo.set("relative", "1")
    geo.set("as", "geometry")
    return cell


def _style_with_overrides(style: str, overrides: dict[str, str]) -> str:
    chunks = [chunk for chunk in style.split(";") if chunk]
    current: dict[str, str] = {}
    for chunk in chunks:
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        current[key] = value
    current.update(overrides)
    return ";".join(f"{k}={v}" for k, v in current.items()) + ";"


def _distributed_entry_x(position_index: int, total: int) -> str:
    if total <= 0:
        return "0.5"
    value = (position_index + 1) / (total + 1)
    return f"{value:.3f}"


def _capability_id_for_filename(capability_id: str) -> str:
    if capability_id.startswith("CAP."):
        return capability_id[len("CAP.") :]
    return capability_id


def load_template_spec(template_file: Path) -> dict[str, Any]:
    xml_root = ET.fromstring(template_file.read_text(encoding="utf-8"))
    diagram = xml_root.find("diagram")
    if diagram is None:
        raise SystemExit(f"[FATAL] Template invalide (diagram manquant): {template_file}")

    graph_model = diagram.find("mxGraphModel")
    if graph_model is None:
        raise SystemExit(f"[FATAL] Template invalide (mxGraphModel manquant): {template_file}")

    root_el = graph_model.find("root")
    if root_el is None:
        raise SystemExit(f"[FATAL] Template invalide (root manquant): {template_file}")

    by_id = {cell.get("id"): cell for cell in root_el.findall("mxCell") if cell.get("id")}

    missing = [name for name, template_id in TEMPLATE_IDS.items() if template_id not in by_id]
    if missing:
        raise SystemExit(
            f"[FATAL] Template incomplet: id(s) introuvable(s) pour {', '.join(missing)}"
        )

    def _cell_style(name: str) -> str:
        return by_id[TEMPLATE_IDS[name]].get("style", "")

    def _cell_value(name: str) -> str:
        return by_id[TEMPLATE_IDS[name]].get("value", "")

    def _geometry(name: str) -> tuple[float, float, float, float]:
        geo = by_id[TEMPLATE_IDS[name]].find("mxGeometry")
        if geo is None:
            raise SystemExit(f"[FATAL] Géométrie manquante pour {name} dans {template_file}")
        return (
            float(geo.get("x", "0")),
            float(geo.get("y", "0")),
            float(geo.get("width", "0")),
            float(geo.get("height", "0")),
        )

    zone_x, zone_y, zone_w, zone_h = _geometry("zone")
    zone_title_x, zone_title_y, zone_title_w, zone_title_h = _geometry("zone_title")
    emitter_x, emitter_y, _, _ = _geometry("emitter_capability")
    consumer_x, consumer_y, _, _ = _geometry("consumer_capability")
    event_group_x, event_group_y, event_group_w, event_group_h = _geometry("event_group")

    image_geo = by_id[TEMPLATE_IDS["event_image"]].find("mxGeometry")
    text_geo = by_id[TEMPLATE_IDS["event_text"]].find("mxGeometry")
    if image_geo is None or text_geo is None:
        raise SystemExit("[FATAL] Géométrie de l'image/texte événement introuvable dans le template")

    return {
        "mx_attrs": {k: v for k, v in graph_model.attrib.items()},
        "styles": {
            "zone": _cell_style("zone"),
            "zone_title": _cell_style("zone_title"),
            "capability": _cell_style("emitter_capability"),
            "event_group": _cell_style("event_group"),
            "event_image": _cell_style("event_image"),
            "event_text": _cell_style("event_text"),
            "edge_emitter_to_event": _cell_style("edge_emitter_to_event"),
            "edge_event_to_consumer": _cell_style("edge_event_to_consumer"),
        },
        "defaults": {
            "zone_title": _cell_value("zone_title"),
        },
        "geometry": {
            "block": {"w": zone_w, "h": zone_h},
            "zone": {"x": 0.0, "y": 0.0, "w": zone_w, "h": zone_h},
            "zone_title": {
                "x": zone_title_x - zone_x,
                "y": zone_title_y - zone_y,
                "w": zone_title_w,
                "h": zone_title_h,
            },
            "emitter": {
                "x": emitter_x - zone_x,
                "y": emitter_y - zone_y,
                "w": CAPABILITY_BOX_W,
                "h": CAPABILITY_BOX_H,
            },
            "consumer": {
                "x": consumer_x - zone_x,
                "y": consumer_y - zone_y,
                "w": CAPABILITY_BOX_W,
                "h": CAPABILITY_BOX_H,
            },
            "event_group": {
                "x": event_group_x - zone_x,
                "y": event_group_y - zone_y,
                "w": event_group_w,
                "h": event_group_h,
            },
            "event_image": {
                "x": float(image_geo.get("x", "0")),
                "y": float(image_geo.get("y", "0")),
                "w": float(image_geo.get("width", "0")),
                "h": float(image_geo.get("height", "0")),
            },
            "event_text": {
                "x": float(text_geo.get("x", "0")),
                "y": float(text_geo.get("y", "0")),
                "w": float(text_geo.get("width", "0")),
                "h": float(text_geo.get("height", "0")),
            },
        },
    }


def load_capabilities_by_id(bcm_dir: Path) -> dict[str, dict[str, Any]]:
    capabilities: dict[str, dict[str, Any]] = {}
    for file_path in sorted(bcm_dir.glob("capabilities-*.yaml")):
        data = load_yaml(file_path) or {}
        for capability in data.get("capabilities", []):
            if isinstance(capability, dict) and capability.get("id"):
                capabilities[capability["id"]] = capability
    if not capabilities:
        raise SystemExit(f"[FATAL] Aucune capacité trouvée dans {bcm_dir}/capabilities-*.yaml")
    return capabilities


def load_business_events_by_id(events_dir: Path) -> dict[str, dict[str, Any]]:
    business_events: dict[str, dict[str, Any]] = {}
    for file_path in sorted(events_dir.rglob("business-event-*.yaml")):
        if file_path.name.startswith("template-"):
            continue
        data = load_yaml(file_path) or {}
        for event in data.get("business_events", []):
            if isinstance(event, dict) and event.get("id"):
                business_events[event["id"]] = event
    return business_events


def load_business_subscriptions(events_dir: Path) -> list[dict[str, Any]]:
    subscriptions: list[dict[str, Any]] = []
    for file_path in sorted(events_dir.rglob("business-subscription-*.yaml")):
        if file_path.name.startswith("template-"):
            continue
        data = load_yaml(file_path) or {}
        for subscription in data.get("business_subscriptions", []):
            if isinstance(subscription, dict):
                subscription = dict(subscription)
                subscription["_source"] = str(file_path.relative_to(events_dir))
                subscriptions.append(subscription)
    return sorted(subscriptions, key=lambda item: item.get("id", ""))


def capability_display_name(capabilities_by_id: dict[str, dict[str, Any]], capability_id: str) -> str:
    capability = capabilities_by_id.get(capability_id) or {}
    return capability.get("name") or capability_id


def resolve_l1_parent(capabilities_by_id: dict[str, dict[str, Any]], capability_id: str) -> str | None:
    capability = capabilities_by_id.get(capability_id)
    if not capability:
        return None
    level = capability.get("level")
    if level == "L1":
        return capability_id
    parent = capability.get("parent")
    return parent if isinstance(parent, str) else None


def build_drawio(
    subscriptions: list[dict[str, Any]],
    capabilities_by_id: dict[str, dict[str, Any]],
    business_events_by_id: dict[str, dict[str, Any]],
    template_spec: dict[str, Any],
    diagram_name: str,
    consumer_capability_id: str | None = None,
) -> str:
    if consumer_capability_id:
        return build_drawio_for_consumer(
            subscriptions=subscriptions,
            capabilities_by_id=capabilities_by_id,
            business_events_by_id=business_events_by_id,
            template_spec=template_spec,
            diagram_name=diagram_name,
            consumer_capability_id=consumer_capability_id,
        )

    return build_drawio_grid(
        subscriptions=subscriptions,
        capabilities_by_id=capabilities_by_id,
        business_events_by_id=business_events_by_id,
        template_spec=template_spec,
        diagram_name=diagram_name,
    )


def build_drawio_grid(
    subscriptions: list[dict[str, Any]],
    capabilities_by_id: dict[str, dict[str, Any]],
    business_events_by_id: dict[str, dict[str, Any]],
    template_spec: dict[str, Any],
    diagram_name: str,
) -> str:
    block = template_spec["geometry"]["block"]
    block_w = block["w"]
    block_h = block["h"]

    cols = 2
    gap_x = 80.0
    gap_y = 80.0
    margin_x = 40.0
    margin_y = 40.0

    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "version": "26.0.4"})
    diagram = ET.SubElement(mxfile, "diagram", {"name": diagram_name, "id": _uid()})

    model = ET.SubElement(diagram, "mxGraphModel", template_spec["mx_attrs"])

    page_w = int(margin_x * 2 + cols * block_w + (cols - 1) * gap_x)
    row_count = max(1, (len(subscriptions) + cols - 1) // cols)
    page_h = int(margin_y * 2 + row_count * block_h + max(0, row_count - 1) * gap_y)
    model.set("pageWidth", str(page_w))
    model.set("pageHeight", str(page_h))

    root_el = ET.SubElement(model, "root")
    ET.SubElement(root_el, "mxCell", {"id": "0"})
    ET.SubElement(root_el, "mxCell", {"id": "1", "parent": "0"})

    for index, subscription in enumerate(subscriptions):
        row = index // cols
        col = index % cols
        base_x = margin_x + col * (block_w + gap_x)
        base_y = margin_y + row * (block_h + gap_y)

        subscribed_event = subscription.get("subscribed_event") or {}
        event_id = subscribed_event.get("id", "")
        emitter_id = subscribed_event.get("emitting_capability", "")
        consumer_id = subscription.get("consumer_capability", "")

        event_name = (business_events_by_id.get(event_id) or {}).get("name") or event_id
        emitter_name = capability_display_name(capabilities_by_id, emitter_id)
        consumer_name = capability_display_name(capabilities_by_id, consumer_id)

        emitter_parent = resolve_l1_parent(capabilities_by_id, emitter_id)
        consumer_parent = resolve_l1_parent(capabilities_by_id, consumer_id)

        if emitter_parent and consumer_parent and emitter_parent == consumer_parent:
            parent_name = capability_display_name(capabilities_by_id, emitter_parent)
        elif emitter_parent and consumer_parent:
            parent_name = (
                f"{capability_display_name(capabilities_by_id, emitter_parent)} "
                f"↔ {capability_display_name(capabilities_by_id, consumer_parent)}"
            )
        else:
            parent_name = template_spec["defaults"]["zone_title"]

        zone_id = _uid()
        zone_geo = template_spec["geometry"]["zone"]
        _add_vertex(
            root_el,
            zone_id,
            "",
            template_spec["styles"]["zone"],
            base_x + zone_geo["x"],
            base_y + zone_geo["y"],
            zone_geo["w"],
            zone_geo["h"],
        )

        title_geo = template_spec["geometry"]["zone_title"]
        _add_vertex(
            root_el,
            _uid(),
            f"<b>{parent_name}</b>",
            template_spec["styles"]["zone_title"],
            base_x + title_geo["x"],
            base_y + title_geo["y"],
            title_geo["w"],
            title_geo["h"],
        )

        emitter_geo = template_spec["geometry"]["emitter"]
        emitter_cell_id = _uid()
        _add_vertex(
            root_el,
            emitter_cell_id,
            emitter_name,
            template_spec["styles"]["capability"],
            base_x + emitter_geo["x"],
            base_y + emitter_geo["y"],
            emitter_geo["w"],
            emitter_geo["h"],
        )

        consumer_geo = template_spec["geometry"]["consumer"]
        consumer_cell_id = _uid()
        _add_vertex(
            root_el,
            consumer_cell_id,
            consumer_name,
            template_spec["styles"]["capability"],
            base_x + consumer_geo["x"],
            base_y + consumer_geo["y"],
            consumer_geo["w"],
            consumer_geo["h"],
        )

        event_group_geo = template_spec["geometry"]["event_group"]
        event_group_id = _uid()
        _add_vertex(
            root_el,
            event_group_id,
            "",
            template_spec["styles"]["event_group"],
            base_x + event_group_geo["x"],
            base_y + event_group_geo["y"],
            event_group_geo["w"],
            event_group_geo["h"],
            connectable="0",
        )

        event_image_geo = template_spec["geometry"]["event_image"]
        event_image_id = _uid()
        _add_vertex(
            root_el,
            event_image_id,
            "",
            template_spec["styles"]["event_image"],
            event_image_geo["x"],
            event_image_geo["y"],
            event_image_geo["w"],
            event_image_geo["h"],
            parent=event_group_id,
        )

        event_text_geo = template_spec["geometry"]["event_text"]
        _add_vertex(
            root_el,
            _uid(),
            event_name,
            template_spec["styles"]["event_text"],
            event_text_geo["x"],
            event_text_geo["y"],
            event_text_geo["w"],
            event_text_geo["h"],
            parent=event_group_id,
        )

        emitter_edge_style = _style_with_overrides(
            template_spec["styles"]["edge_emitter_to_event"],
            {
                "exitX": "0.5",
                "exitY": "0",
                "entryX": "0",
                "entryY": "0.5",
                "exitDx": "0",
                "exitDy": "0",
                "entryDx": "0",
                "entryDy": "0",
            },
        )
        _add_edge(
            root_el,
            _uid(),
            emitter_edge_style,
            source=emitter_cell_id,
            target=event_image_id,
        )

        consumer_above_event = consumer_geo["y"] < event_group_geo["y"]
        subscriber_edge_style = _style_with_overrides(
            template_spec["styles"]["edge_event_to_consumer"],
            {
                "exitX": "0.5",
                "exitY": "0.5",
                "entryX": "0.5",
                "entryY": "1" if consumer_above_event else "0",
                "exitDx": "0",
                "exitDy": "0",
                "entryDx": "0",
                "entryDy": "0",
            },
        )
        _add_edge(
            root_el,
            _uid(),
            subscriber_edge_style,
            source=event_image_id,
            target=consumer_cell_id,
        )

    ET.indent(mxfile, space="  ")
    return ET.tostring(mxfile, encoding="unicode")


def build_drawio_for_consumer(
    subscriptions: list[dict[str, Any]],
    capabilities_by_id: dict[str, dict[str, Any]],
    business_events_by_id: dict[str, dict[str, Any]],
    template_spec: dict[str, Any],
    diagram_name: str,
    consumer_capability_id: str,
) -> str:
    zone_geo = template_spec["geometry"]["zone"]
    title_geo = template_spec["geometry"]["zone_title"]
    emitter_geo = template_spec["geometry"]["emitter"]
    consumer_geo = template_spec["geometry"]["consumer"]
    event_group_geo = template_spec["geometry"]["event_group"]
    event_image_geo = template_spec["geometry"]["event_image"]
    event_text_geo = template_spec["geometry"]["event_text"]

    margin_x = 40.0
    margin_y = 40.0
    inner_pad = 24.0
    row_gap = 120.0
    event_vertical_offset = 38.0
    title_top_margin = 12.0

    row_count = len(subscriptions)
    dynamic_title_y = title_top_margin
    dynamic_title_h = title_geo["h"]
    dynamic_title_x = inner_pad
    dynamic_title_w = max(100.0, zone_geo["w"] - 2 * inner_pad)

    first_row_center_y = max(
        dynamic_title_y + dynamic_title_h + inner_pad + event_vertical_offset + event_group_geo["h"] / 2,
        consumer_geo["y"] + consumer_geo["h"] / 2 - ((row_count - 1) * row_gap) / 2,
    )
    last_row_center_y = first_row_center_y + (row_count - 1) * row_gap

    rows_bottom = last_row_center_y + emitter_geo["h"] / 2
    consumer_bottom = consumer_geo["y"] + consumer_geo["h"]
    content_bottom = max(rows_bottom, consumer_bottom)

    dynamic_zone_h = max(zone_geo["h"], content_bottom + inner_pad)
    dynamic_zone_w = zone_geo["w"]

    page_w = int(margin_x * 2 + dynamic_zone_w)
    page_h = int(margin_y * 2 + dynamic_zone_h)

    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "version": "26.0.4"})
    diagram = ET.SubElement(mxfile, "diagram", {"name": diagram_name, "id": _uid()})
    model = ET.SubElement(diagram, "mxGraphModel", template_spec["mx_attrs"])
    model.set("pageWidth", str(page_w))
    model.set("pageHeight", str(page_h))

    root_el = ET.SubElement(model, "root")
    ET.SubElement(root_el, "mxCell", {"id": "0"})
    ET.SubElement(root_el, "mxCell", {"id": "1", "parent": "0"})

    base_x = margin_x
    base_y = margin_y

    _add_vertex(
        root_el,
        _uid(),
        "",
        template_spec["styles"]["zone"],
        base_x + zone_geo["x"],
        base_y + zone_geo["y"],
        dynamic_zone_w,
        dynamic_zone_h,
    )

    consumer_name = capability_display_name(capabilities_by_id, consumer_capability_id)
    consumer_parent = resolve_l1_parent(capabilities_by_id, consumer_capability_id)
    if consumer_parent:
        parent_name = capability_display_name(capabilities_by_id, consumer_parent)
        title_value = f"<b>{parent_name}</b>"
    else:
        title_value = template_spec["defaults"]["zone_title"]

    _add_vertex(
        root_el,
        _uid(),
        title_value,
        template_spec["styles"]["zone_title"],
        base_x + dynamic_title_x,
        base_y + dynamic_title_y,
        dynamic_title_w,
        dynamic_title_h,
    )

    consumer_cell_id = _uid()
    _add_vertex(
        root_el,
        consumer_cell_id,
        consumer_name,
        template_spec["styles"]["capability"],
        base_x + consumer_geo["x"],
        base_y + consumer_geo["y"],
        consumer_geo["w"],
        consumer_geo["h"],
    )

    consumer_mid_y = consumer_geo["y"] + consumer_geo["h"] / 2
    consumer_above_event_flags: list[bool] = []
    for index in range(row_count):
        emitter_center_y = first_row_center_y + index * row_gap
        event_center_y = emitter_center_y - event_vertical_offset
        consumer_above_event_flags.append(consumer_mid_y < event_center_y)

    total_bottom_entries = sum(1 for is_consumer_above in consumer_above_event_flags if is_consumer_above)
    total_top_entries = row_count - total_bottom_entries
    bottom_entry_counter = 0
    top_entry_counter = 0

    for index, subscription in enumerate(subscriptions):
        emitter_center_y = first_row_center_y + index * row_gap

        subscribed_event = subscription.get("subscribed_event") or {}
        event_id = subscribed_event.get("id", "")
        emitter_id = subscribed_event.get("emitting_capability", "")

        event_name = (business_events_by_id.get(event_id) or {}).get("name") or event_id
        emitter_name = capability_display_name(capabilities_by_id, emitter_id)

        emitter_y = emitter_center_y - emitter_geo["h"] / 2
        event_center_y = emitter_center_y - event_vertical_offset
        event_group_y = event_center_y - event_group_geo["h"] / 2

        emitter_cell_id = _uid()
        _add_vertex(
            root_el,
            emitter_cell_id,
            emitter_name,
            template_spec["styles"]["capability"],
            base_x + emitter_geo["x"],
            base_y + emitter_y,
            emitter_geo["w"],
            emitter_geo["h"],
        )

        event_group_id = _uid()
        _add_vertex(
            root_el,
            event_group_id,
            "",
            template_spec["styles"]["event_group"],
            base_x + event_group_geo["x"],
            base_y + event_group_y,
            event_group_geo["w"],
            event_group_geo["h"],
            connectable="0",
        )

        event_image_id = _uid()
        _add_vertex(
            root_el,
            event_image_id,
            "",
            template_spec["styles"]["event_image"],
            event_image_geo["x"],
            event_image_geo["y"],
            event_image_geo["w"],
            event_image_geo["h"],
            parent=event_group_id,
        )

        _add_vertex(
            root_el,
            _uid(),
            event_name,
            template_spec["styles"]["event_text"],
            event_text_geo["x"],
            event_text_geo["y"],
            event_text_geo["w"],
            event_text_geo["h"],
            parent=event_group_id,
        )

        emitter_edge_style = _style_with_overrides(
            template_spec["styles"]["edge_emitter_to_event"],
            {
                "exitX": "0.5",
                "exitY": "0",
                "entryX": "0",
                "entryY": "0.5",
                "exitDx": "0",
                "exitDy": "0",
                "entryDx": "0",
                "entryDy": "0",
            },
        )
        _add_edge(
            root_el,
            _uid(),
            emitter_edge_style,
            source=emitter_cell_id,
            target=event_image_id,
        )

        consumer_above_event = consumer_above_event_flags[index]
        if consumer_above_event:
            entry_y = "1"
            entry_x = _distributed_entry_x(bottom_entry_counter, total_bottom_entries)
            bottom_entry_counter += 1
        else:
            entry_y = "0"
            entry_x = _distributed_entry_x(top_entry_counter, total_top_entries)
            top_entry_counter += 1

        subscriber_edge_style = _style_with_overrides(
            template_spec["styles"]["edge_event_to_consumer"],
            {
                "exitX": "0.5",
                "exitY": "0.5",
                "entryX": entry_x,
                "entryY": entry_y,
                "exitDx": "0",
                "exitDy": "0",
                "entryDx": "0",
                "entryDy": "0",
            },
        )
        _add_edge(
            root_el,
            _uid(),
            subscriber_edge_style,
            source=event_image_id,
            target=consumer_cell_id,
        )

    ET.indent(mxfile, space="  ")
    return ET.tostring(mxfile, encoding="unicode")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Génère une vue Draw.io des abonnements métier en répliquant "
            "la géométrie/styles de views/template-abonnement.drawio."
        )
    )
    parser.add_argument("--bcm-dir", default="bcm", help="Répertoire des fichiers capabilities-*.yaml")
    parser.add_argument(
        "--events-dir",
        default="bcm/business-event",
        help="Répertoire racine contenant business-event-*.yaml et business-subscription-*.yaml",
    )
    parser.add_argument(
        "--template",
        default="views/template-abonnement.drawio",
        help="Template draw.io de référence",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Fichier .drawio de sortie (mode mono-capacité uniquement, avec --consumer-capability)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="views/abonnements",
        help="Répertoire de sortie des rendus draw.io (défaut: views/abonnements)",
    )
    parser.add_argument(
        "--focus-parent-l1",
        default=None,
        help="Filtre optionnel: ne garde que les abonnements dont émetteur et consommateur appartiennent à ce parent L1",
    )
    parser.add_argument(
        "--consumer-capability",
        default=None,
        help=(
            "Capacité souscriptrice cible (ex: CAP.COEUR.005.CAD). "
            "Si fournie, le rendu consolide toutes ses abonnements dans une même brique."
        ),
    )
    parser.add_argument("--diagram-name", default="Abonnements metier", help="Nom de l'onglet draw.io")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    bcm_dir = ROOT / args.bcm_dir
    events_dir = ROOT / args.events_dir
    template_file = ROOT / args.template
    output_dir = ROOT / args.output_dir

    if not bcm_dir.exists():
        raise SystemExit(f"[FATAL] Répertoire introuvable: {bcm_dir}")
    if not events_dir.exists():
        raise SystemExit(f"[FATAL] Répertoire introuvable: {events_dir}")
    if not template_file.exists():
        raise SystemExit(f"[FATAL] Template introuvable: {template_file}")

    template_spec = load_template_spec(template_file)
    capabilities_by_id = load_capabilities_by_id(bcm_dir)
    business_events_by_id = load_business_events_by_id(events_dir)
    subscriptions = load_business_subscriptions(events_dir)

    if args.focus_parent_l1:
        filtered: list[dict[str, Any]] = []
        for subscription in subscriptions:
            subscribed_event = subscription.get("subscribed_event") or {}
            emitter_id = subscribed_event.get("emitting_capability", "")
            consumer_id = subscription.get("consumer_capability", "")
            emitter_parent = resolve_l1_parent(capabilities_by_id, emitter_id)
            consumer_parent = resolve_l1_parent(capabilities_by_id, consumer_id)
            if emitter_parent == args.focus_parent_l1 and consumer_parent == args.focus_parent_l1:
                filtered.append(subscription)
        subscriptions = filtered

    if args.consumer_capability and args.consumer_capability not in capabilities_by_id:
        raise SystemExit(
            f"[FATAL] Capacité souscriptrice introuvable dans les capabilities: {args.consumer_capability}"
        )

    if not subscriptions:
        raise SystemExit("[FATAL] Aucune abonnement métier à rendre.")

    output_dir.mkdir(parents=True, exist_ok=True)

    if args.consumer_capability:
        selected_subscriptions = [
            subscription
            for subscription in subscriptions
            if subscription.get("consumer_capability") == args.consumer_capability
        ]
        if not selected_subscriptions:
            raise SystemExit(
                f"[FATAL] Aucune abonnement métier trouvée pour {args.consumer_capability}."
            )

        xml_output = build_drawio(
            subscriptions=selected_subscriptions,
            capabilities_by_id=capabilities_by_id,
            business_events_by_id=business_events_by_id,
            template_spec=template_spec,
            diagram_name=args.diagram_name,
            consumer_capability_id=args.consumer_capability,
        )

        if args.output:
            output_file = ROOT / args.output
        else:
            short_capability_id = _capability_id_for_filename(args.consumer_capability)
            output_file = output_dir / f"{short_capability_id}-abonnements.drawio"

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(xml_output, encoding="utf-8")

        print("[OK] Draw.io généré")
        print(f"  • template      : {template_file.relative_to(ROOT)}")
        print(f"  • souscriptrice : {args.consumer_capability}")
        print(f"  • abonnements : {len(selected_subscriptions)}")
        print(f"  • sortie        : {output_file.relative_to(ROOT)}")
        return 0

    if args.output:
        raise SystemExit(
            "[FATAL] --output n'est pas compatible avec le mode batch (sans --consumer-capability). "
            "Utiliser --output-dir."
        )

    consumer_ids = sorted(
        {
            subscription.get("consumer_capability")
            for subscription in subscriptions
            if subscription.get("consumer_capability")
        }
    )
    if not consumer_ids:
        raise SystemExit("[FATAL] Aucune capacité souscriptrice détectée dans les abonnements métier.")

    rendered_files: list[Path] = []
    for consumer_id in consumer_ids:
        selected_subscriptions = [
            subscription
            for subscription in subscriptions
            if subscription.get("consumer_capability") == consumer_id
        ]
        if not selected_subscriptions:
            continue

        xml_output = build_drawio(
            subscriptions=selected_subscriptions,
            capabilities_by_id=capabilities_by_id,
            business_events_by_id=business_events_by_id,
            template_spec=template_spec,
            diagram_name=args.diagram_name,
            consumer_capability_id=consumer_id,
        )

        short_capability_id = _capability_id_for_filename(consumer_id)
        output_file = output_dir / f"{short_capability_id}-abonnements.drawio"
        output_file.write_text(xml_output, encoding="utf-8")
        rendered_files.append(output_file)

    print("[OK] Draw.io généré (mode batch)")
    print(f"  • template      : {template_file.relative_to(ROOT)}")
    print(f"  • capacités     : {len(rendered_files)}")
    print(f"  • sortie dir    : {output_dir.relative_to(ROOT)}")
    for rendered_file in rendered_files:
        print(f"    - {rendered_file.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
