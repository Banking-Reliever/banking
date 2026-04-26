#!/usr/bin/env python3

from __future__ import annotations

import argparse
import uuid
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CAPABILITY_BOX_W = 130.0
CAPABILITY_BOX_H = 50.0


def _uid() -> str:
    return "cell-" + uuid.uuid4().hex[:12]


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"[FATAL] Cannot read/parse {path}: {exc}")


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


def _distributed(min_value: float, max_value: float, index: int, total: int) -> float:
    if total <= 1:
        return (min_value + max_value) / 2
    return min_value + (max_value - min_value) * (index / (total - 1))


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


def _cell_geometry(cell: ET.Element) -> tuple[float, float, float, float]:
    geo = cell.find("mxGeometry")
    if geo is None:
        return (0.0, 0.0, 0.0, 0.0)
    return (
        float(geo.get("x", "0")),
        float(geo.get("y", "0")),
        float(geo.get("width", "0")),
        float(geo.get("height", "0")),
    )


def load_template_spec(template_file: Path) -> dict[str, Any]:
    xml_root = ET.fromstring(template_file.read_text(encoding="utf-8"))
    diagram = xml_root.find("diagram")
    if diagram is None:
        raise SystemExit(f"[FATAL] Invalid template (diagram missing): {template_file}")

    graph_model = diagram.find("mxGraphModel")
    if graph_model is None:
        raise SystemExit(f"[FATAL] Invalid template (mxGraphModel missing): {template_file}")

    root_el = graph_model.find("root")
    if root_el is None:
        raise SystemExit(f"[FATAL] Invalid template (root missing): {template_file}")

    all_cells = root_el.findall("mxCell")

    zone_cell = next(
        (
            c
            for c in all_cells
            if c.get("vertex") == "1"
            and "fillColor=#f8cecc" in (c.get("style") or "")
            and (c.get("value") or "") == ""
        ),
        None,
    )
    if zone_cell is None:
        raise SystemExit("[FATAL] Main zone not found in template")

    title_cell = next(
        (
            c
            for c in all_cells
            if c.get("vertex") == "1"
            and "fontStyle=1" in (c.get("style") or "")
            and "text;" in (c.get("style") or "")
        ),
        None,
    )
    if title_cell is None:
        raise SystemExit("[FATAL] Zone title not found in template")

    capability_cells = [
        c
        for c in all_cells
        if c.get("vertex") == "1" and "fillColor=#ffe6cc" in (c.get("style") or "")
    ]
    capability_cell = next((c for c in capability_cells), None)
    if capability_cell is None:
        raise SystemExit("[FATAL] Capability style not found in template")

    event_group_cell = next(
        (
            c
            for c in all_cells
            if c.get("vertex") == "1"
            and (c.get("style") or "") == "group"
            and c.get("connectable") == "0"
        ),
        None,
    )
    if event_group_cell is None:
        raise SystemExit("[FATAL] Event group not found in template")

    event_group_id = event_group_cell.get("id", "")
    event_image_cell = next(
        (
            c
            for c in all_cells
            if c.get("vertex") == "1"
            and c.get("parent") == event_group_id
            and "shape=image" in (c.get("style") or "")
        ),
        None,
    )
    event_text_cell = next(
        (
            c
            for c in all_cells
            if c.get("vertex") == "1"
            and c.get("parent") == event_group_id
            and "text;" in (c.get("style") or "")
        ),
        None,
    )
    if event_image_cell is None or event_text_cell is None:
        raise SystemExit("[FATAL] Event image/text not found in template")

    edge_solid = next(
        (c for c in all_cells if c.get("edge") == "1" and "dashed=1" not in (c.get("style") or "")),
        None,
    )
    edge_dashed = next(
        (c for c in all_cells if c.get("edge") == "1" and "dashed=1" in (c.get("style") or "")),
        None,
    )
    if edge_solid is None or edge_dashed is None:
        raise SystemExit("[FATAL] Arrow styles not found in template")

    zone_x, zone_y, zone_w, zone_h = _cell_geometry(zone_cell)
    title_x, title_y, title_w, title_h = _cell_geometry(title_cell)
    _, _, capability_w, capability_h = _cell_geometry(capability_cell)
    capability_positions = [_cell_geometry(c) for c in capability_cells]
    event_group_x, event_group_y, event_group_w, event_group_h = _cell_geometry(event_group_cell)
    event_image_x, event_image_y, event_image_w, event_image_h = _cell_geometry(event_image_cell)
    event_text_x, event_text_y, event_text_w, event_text_h = _cell_geometry(event_text_cell)

    return {
        "mx_attrs": {k: v for k, v in graph_model.attrib.items()},
        "styles": {
            "zone": zone_cell.get("style", ""),
            "zone_title": title_cell.get("style", ""),
            "capability": capability_cell.get("style", ""),
            "event_group": event_group_cell.get("style", "group"),
            "event_image": event_image_cell.get("style", ""),
            "event_text": event_text_cell.get("style", ""),
            "edge_emitter_to_event": edge_solid.get("style", ""),
            "edge_event_to_consumer": edge_dashed.get("style", ""),
        },
        "geometry": {
            "zone": {"x": zone_x, "y": zone_y, "w": zone_w, "h": zone_h},
            "zone_title": {"x": title_x, "y": title_y, "w": title_w, "h": title_h},
            "capability": {"w": capability_w or CAPABILITY_BOX_W, "h": capability_h or CAPABILITY_BOX_H},
            "capability_positions": [
                {"x": x, "y": y, "w": w, "h": h} for (x, y, w, h) in capability_positions
            ],
            "event_group": {
                "x": event_group_x,
                "y": event_group_y,
                "w": event_group_w,
                "h": event_group_h,
            },
            "event_image": {
                "x": event_image_x,
                "y": event_image_y,
                "w": event_image_w,
                "h": event_image_h,
            },
            "event_text": {
                "x": event_text_x,
                "y": event_text_y,
                "w": event_text_w,
                "h": event_text_h,
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
        raise SystemExit(f"[FATAL] No capability found in {bcm_dir}/capabilities-*.yaml")
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
                subscriptions.append(dict(subscription))
    return sorted(subscriptions, key=lambda item: item.get("id", ""))


def capability_display_name(capabilities_by_id: dict[str, dict[str, Any]], capability_id: str) -> str:
    capability = capabilities_by_id.get(capability_id) or {}
    return capability.get("name") or capability_id


def resolve_l1_parent(capabilities_by_id: dict[str, dict[str, Any]], capability_id: str) -> str | None:
    current = capabilities_by_id.get(capability_id)
    visited: set[str] = set()
    while current and current.get("id") not in visited:
        visited.add(current.get("id"))
        if current.get("level") == "L1":
            return current.get("id")
        parent_id = current.get("parent")
        if not isinstance(parent_id, str):
            break
        current = capabilities_by_id.get(parent_id)
    return None


def _short_capability_id(capability_id: str) -> str:
    if capability_id.startswith("CAP."):
        return capability_id[len("CAP.") :]
    return capability_id


def _longest_path_dag(nodes: list[str], edge_pairs: list[tuple[str, str]]) -> list[str]:
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    indegree: dict[str, int] = {node: 0 for node in nodes}
    for source, target in edge_pairs:
        if source == target:
            continue
        if target not in adjacency[source]:
            adjacency[source].append(target)
            indegree[target] += 1

    queue = deque(sorted([node for node in nodes if indegree[node] == 0]))
    topo: list[str] = []
    while queue:
        node = queue.popleft()
        topo.append(node)
        for target in adjacency[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)

    if len(topo) != len(nodes):
        return []

    dist: dict[str, int] = {node: 0 for node in nodes}
    prev: dict[str, str | None] = {node: None for node in nodes}
    for node in topo:
        for target in adjacency[node]:
            if dist[node] + 1 > dist[target]:
                dist[target] = dist[node] + 1
                prev[target] = node

    end = max(nodes, key=lambda node: dist[node]) if nodes else None
    if end is None or dist[end] == 0:
        return []

    path: list[str] = []
    cursor: str | None = end
    while cursor is not None:
        path.append(cursor)
        cursor = prev[cursor]
    path.reverse()
    return path


def _rectangles_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float], pad: float = 4.0) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw + pad <= bx or bx + bw + pad <= ax or ay + ah + pad <= by or by + bh + pad <= ay)


def _event_x_offset(dx: float) -> float:
    return max(140.0, min(170.0, dx - 70.0))


def _axis_anchor(index: int, total: int) -> float:
    return _distributed(0.2, 0.8, index, max(1, total))


def _border_anchor(
    source_rect: tuple[float, float, float, float],
    target_rect: tuple[float, float, float, float],
    rank: int,
    total: int,
) -> tuple[float, float]:
    sx, sy, sw, sh = source_rect
    tx, ty, tw, th = target_rect
    source_center = (sx + sw / 2, sy + sh / 2)
    target_center = (tx + tw / 2, ty + th / 2)
    dx = target_center[0] - source_center[0]
    dy = target_center[1] - source_center[1]

    if abs(dx) >= abs(dy):
        if dx >= 0:
            return 1.0, _axis_anchor(rank, total)
        return 0.0, _axis_anchor(rank, total)

    if dy >= 0:
        return _axis_anchor(rank, total), 1.0
    return _axis_anchor(rank, total), 0.0


def _point_close(a: tuple[float, float], b: tuple[float, float], eps: float = 1e-6) -> bool:
    return abs(a[0] - b[0]) <= eps and abs(a[1] - b[1]) <= eps


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], eps: float = 1e-9) -> int:
    value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    if abs(value) <= eps:
        return 0
    return 1 if value > 0 else 2


def _on_segment(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], eps: float = 1e-9) -> bool:
    return (
        min(a[0], c[0]) - eps <= b[0] <= max(a[0], c[0]) + eps
        and min(a[1], c[1]) - eps <= b[1] <= max(a[1], c[1]) + eps
    )


def _segments_intersect(
    p1: tuple[float, float],
    q1: tuple[float, float],
    p2: tuple[float, float],
    q2: tuple[float, float],
) -> bool:
    o1 = _orientation(p1, q1, p2)
    o2 = _orientation(p1, q1, q2)
    o3 = _orientation(p2, q2, p1)
    o4 = _orientation(p2, q2, q1)

    if o1 != o2 and o3 != o4:
        return True

    if o1 == 0 and _on_segment(p1, p2, q1):
        return True
    if o2 == 0 and _on_segment(p1, q2, q1):
        return True
    if o3 == 0 and _on_segment(p2, p1, q2):
        return True
    if o4 == 0 and _on_segment(p2, q1, q2):
        return True
    return False


def _routes_cross(
    candidate: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    existing_routes: list[tuple[tuple[float, float], tuple[float, float], tuple[float, float]]],
) -> bool:
    candidate_segments = [(candidate[0], candidate[1]), (candidate[1], candidate[2])]
    for route in existing_routes:
        route_segments = [(route[0], route[1]), (route[1], route[2])]
        for a1, a2 in candidate_segments:
            for b1, b2 in route_segments:
                if _point_close(a1, b1) or _point_close(a1, b2) or _point_close(a2, b1) or _point_close(a2, b2):
                    continue
                if _segments_intersect(a1, a2, b1, b2):
                    return True
    return False


def build_drawio_for_l1(
    l1_capability_id: str,
    capabilities_by_id: dict[str, dict[str, Any]],
    business_events_by_id: dict[str, dict[str, Any]],
    subscriptions: list[dict[str, Any]],
    template_spec: dict[str, Any],
    diagram_name: str,
) -> str:
    zone_geo = template_spec["geometry"]["zone"]
    title_geo = template_spec["geometry"]["zone_title"]
    capability_geo = template_spec["geometry"]["capability"]
    event_group_geo = template_spec["geometry"]["event_group"]
    event_image_geo = template_spec["geometry"]["event_image"]
    event_text_geo = template_spec["geometry"]["event_text"]

    cap_w = capability_geo["w"] or CAPABILITY_BOX_W
    cap_h = capability_geo["h"] or CAPABILITY_BOX_H

    template_cap_positions = template_spec["geometry"].get("capability_positions", [])
    template_rows = sorted(
        {
            round(float(position.get("y", 0.0)), 3)
            for position in template_cap_positions
            if isinstance(position, dict)
        }
    )
    if len(template_rows) >= 4:
        y_upper, y_upper_mid, y_mid, y_low = template_rows[0], template_rows[1], template_rows[2], template_rows[3]
    else:
        y_upper = 320.0
        y_upper_mid = 440.0
        y_mid = 530.0
        y_low = 650.0

    l2_capability_ids = sorted(
        [
            capability_id
            for capability_id, capability in capabilities_by_id.items()
            if capability.get("parent") == l1_capability_id
        ]
    )
    if not l2_capability_ids:
        raise SystemExit(f"[FATAL] No L2 capability found for {l1_capability_id}")

    relevant_subscriptions: list[dict[str, Any]] = []
    for subscription in subscriptions:
        subscribed_event = subscription.get("subscribed_event") or {}
        emitter_id = subscribed_event.get("emitting_capability", "")
        consumer_id = subscription.get("consumer_capability", "")
        if emitter_id in l2_capability_ids and consumer_id in l2_capability_ids:
            relevant_subscriptions.append(subscription)

    edge_pairs: list[tuple[str, str]] = []
    in_degree: dict[str, int] = {capability_id: 0 for capability_id in l2_capability_ids}
    out_degree: dict[str, int] = {capability_id: 0 for capability_id in l2_capability_ids}
    for subscription in relevant_subscriptions:
        subscribed_event = subscription.get("subscribed_event") or {}
        emitter_id = subscribed_event.get("emitting_capability", "")
        consumer_id = subscription.get("consumer_capability", "")
        if emitter_id in in_degree and consumer_id in in_degree and emitter_id != consumer_id:
            edge_pairs.append((emitter_id, consumer_id))
            out_degree[emitter_id] += 1
            in_degree[consumer_id] += 1

    main_path = _longest_path_dag(l2_capability_ids, edge_pairs)
    if not main_path:
        main_path = [
            capability_id
            for capability_id in l2_capability_ids
            if in_degree.get(capability_id, 0) == 0 and out_degree.get(capability_id, 0) > 0
        ]
    if not main_path:
        main_path = l2_capability_ids[:]

    main_set = set(main_path)
    main_sink = main_path[-1] if main_path else None
    pre_main_sink = main_path[-2] if len(main_path) >= 2 else None

    cap_x_start = zone_geo["x"] + 20.0
    available_width = zone_geo["w"] - 40.0 - cap_w
    main_gap = 260.0
    if len(main_path) > 1:
        main_gap = min(260.0, available_width / (len(main_path) - 1))

    positions: dict[str, tuple[float, float]] = {}

    for index, capability_id in enumerate(main_path):
        x = cap_x_start + index * main_gap
        y = y_mid
        if main_sink and capability_id == main_sink:
            y = y_upper_mid
        elif pre_main_sink and capability_id == pre_main_sink:
            y = y_low
        positions[capability_id] = (x, y)

    isolated = [
        capability_id
        for capability_id in l2_capability_ids
        if capability_id not in main_set and in_degree[capability_id] == 0 and out_degree[capability_id] == 0
    ]
    extra_sources = [
        capability_id
        for capability_id in l2_capability_ids
        if capability_id not in main_set and in_degree[capability_id] == 0 and out_degree[capability_id] > 0
    ]
    extra_sinks = [
        capability_id
        for capability_id in l2_capability_ids
        if capability_id not in main_set and in_degree[capability_id] > 0 and out_degree[capability_id] == 0
    ]
    others = [
        capability_id
        for capability_id in l2_capability_ids
        if capability_id not in main_set and capability_id not in isolated and capability_id not in extra_sources and capability_id not in extra_sinks
    ]

    low_slots = [positions[node_id][0] for node_id in main_path[1:-1]]
    if not low_slots:
        low_slots = [cap_x_start + 260.0 * i for i in range(1, max(2, len(isolated) + len(others) + 1))]

    for index, capability_id in enumerate(sorted(isolated, key=lambda cid: capability_display_name(capabilities_by_id, cid))):
        x = low_slots[index] if index < len(low_slots) else low_slots[-1] + 260.0 * (index - len(low_slots) + 1)
        positions[capability_id] = (x, y_low)

    for index, capability_id in enumerate(sorted(extra_sources, key=lambda cid: capability_display_name(capabilities_by_id, cid))):
        if main_sink and main_sink in positions:
            x = max(cap_x_start, positions[main_sink][0] - 260.0 - index * 150.0)
        else:
            x = cap_x_start + 260.0 * (len(main_path) - 1)
        positions[capability_id] = (x, y_upper)

    for index, capability_id in enumerate(sorted(extra_sinks, key=lambda cid: capability_display_name(capabilities_by_id, cid))):
        if main_sink and main_sink in positions:
            x = positions[main_sink][0] - 130.0 + index * 90.0
        else:
            x = cap_x_start + 260.0 * max(0, len(main_path) - 2)
        positions[capability_id] = (x, y_upper_mid)

    for index, capability_id in enumerate(sorted(others, key=lambda cid: capability_display_name(capabilities_by_id, cid))):
        x = low_slots[index] if index < len(low_slots) else low_slots[-1] + 220.0 * (index - len(low_slots) + 1)
        positions[capability_id] = (x, y_low)

    min_x = zone_geo["x"] + 20.0
    max_x = zone_geo["x"] + zone_geo["w"] - cap_w - 20.0
    for capability_id, (x, y) in list(positions.items()):
        positions[capability_id] = (max(min_x, min(max_x, x)), y)

    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "version": "26.0.4"})
    diagram = ET.SubElement(mxfile, "diagram", {"name": diagram_name, "id": _uid()})
    model = ET.SubElement(diagram, "mxGraphModel", template_spec["mx_attrs"])

    page_w = int(zone_geo["x"] + zone_geo["w"] + 40)
    page_h = int(zone_geo["y"] + zone_geo["h"] + 40)
    model.set("pageWidth", str(page_w))
    model.set("pageHeight", str(page_h))

    root_el = ET.SubElement(model, "root")
    ET.SubElement(root_el, "mxCell", {"id": "0"})
    ET.SubElement(root_el, "mxCell", {"id": "1", "parent": "0"})

    _add_vertex(
        root_el,
        _uid(),
        "",
        template_spec["styles"]["zone"],
        zone_geo["x"],
        zone_geo["y"],
        zone_geo["w"],
        zone_geo["h"],
    )

    l1_name = capability_display_name(capabilities_by_id, l1_capability_id)
    _add_vertex(
        root_el,
        _uid(),
        f"<b>{l1_name}</b>",
        template_spec["styles"]["zone_title"],
        title_geo["x"],
        title_geo["y"],
        title_geo["w"],
        title_geo["h"],
    )

    capability_cell_ids: dict[str, str] = {}
    for capability_id in sorted(l2_capability_ids, key=lambda cid: (positions[cid][1], positions[cid][0])):
        x, y = positions[capability_id]
        capability_cell_id = _uid()
        capability_cell_ids[capability_id] = capability_cell_id
        _add_vertex(
            root_el,
            capability_cell_id,
            capability_display_name(capabilities_by_id, capability_id),
            template_spec["styles"]["capability"],
            x,
            y,
            cap_w,
            cap_h,
        )

    event_subscriptions: dict[tuple[str, str], list[int]] = defaultdict(list)
    consume_groups: dict[str, list[int]] = defaultdict(list)
    for index, subscription in enumerate(relevant_subscriptions):
        subscribed_event = subscription.get("subscribed_event") or {}
        event_id = subscribed_event.get("id", "")
        emitter_id = subscribed_event.get("emitting_capability", "")
        consumer_id = subscription.get("consumer_capability", "")
        if emitter_id not in positions or consumer_id not in positions:
            continue
        event_key = (event_id, emitter_id)
        event_subscriptions[event_key].append(index)
        consume_groups[consumer_id].append(index)

    event_rectangles: dict[tuple[str, str], tuple[float, float, float, float]] = {}
    event_image_ids: dict[tuple[str, str], str] = {}
    placed_event_rectangles: list[tuple[float, float, float, float]] = []
    placed_routes: list[tuple[tuple[float, float], tuple[float, float], tuple[float, float]]] = []

    placement_order = sorted(
        list(event_subscriptions.keys()),
        key=lambda key: (
            positions[key[1]][0],
            sum(positions[relevant_subscriptions[idx].get("consumer_capability", "")][0] for idx in event_subscriptions[key])
            / max(1, len(event_subscriptions[key])),
            key[0],
        ),
    )

    for event_key in placement_order:
        event_id, emitter_id = event_key
        emitter_x, emitter_y = positions[emitter_id]

        consumer_positions = [
            positions[relevant_subscriptions[idx].get("consumer_capability", "")]
            for idx in event_subscriptions[event_key]
            if relevant_subscriptions[idx].get("consumer_capability", "") in positions
        ]
        if not consumer_positions:
            continue

        consumer_x = sum(position[0] for position in consumer_positions) / len(consumer_positions)
        consumer_y = sum(position[1] for position in consumer_positions) / len(consumer_positions)

        dx = max(80.0, consumer_x - emitter_x)
        event_x = emitter_x + _event_x_offset(dx)
        event_y = max(270.0, emitter_y - (80.0 if emitter_y >= 500 else 50.0))

        event_rect = (event_x, event_y, event_group_geo["w"], event_group_geo["h"])
        attempts = 0
        while True:
            overlap = any(_rectangles_overlap(event_rect, placed, pad=8.0) for placed in placed_event_rectangles)
            candidate_route = (
                (emitter_x + cap_w, emitter_y + cap_h / 2),
                (event_rect[0] + event_group_geo["w"] / 2, event_rect[1] + event_group_geo["h"] / 2),
                (consumer_x, consumer_y + cap_h / 2),
            )
            crossing = _routes_cross(candidate_route, placed_routes)
            if not overlap and not crossing:
                break

            event_y -= 40.0
            if event_y < zone_geo["y"] + 32.0:
                event_y = zone_geo["y"] + zone_geo["h"] - event_group_geo["h"] - 16.0
            attempts += 1
            if attempts % 9 == 0:
                event_x = min(max_x, event_x + 20.0)
            event_rect = (event_x, event_y, event_group_geo["w"], event_group_geo["h"])

        event_rectangles[event_key] = event_rect
        placed_event_rectangles.append(event_rect)
        placed_routes.append(candidate_route)

        event_group_id = _uid()
        _add_vertex(
            root_el,
            event_group_id,
            "",
            template_spec["styles"]["event_group"],
            event_x,
            event_y,
            event_group_geo["w"],
            event_group_geo["h"],
            connectable="0",
        )

        event_image_id = _uid()
        event_image_ids[event_key] = event_image_id
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

        event_name = (business_events_by_id.get(event_id) or {}).get("name") or event_id
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

    emitter_event_groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for event_key in event_rectangles:
        emitter_event_groups[event_key[1]].append(event_key)
    sorted_emitter_event_groups: dict[str, list[tuple[str, str]]] = {}
    for emitter_id, keys in emitter_event_groups.items():
        sorted_emitter_event_groups[emitter_id] = sorted(
            keys,
            key=lambda key: (
                event_rectangles[key][0],
                event_rectangles[key][1],
                key[0],
            ),
        )

    sorted_event_subscription_groups: dict[tuple[str, str], list[int]] = {}
    for event_key, indexes in event_subscriptions.items():
        if event_key not in event_rectangles:
            continue
        sorted_event_subscription_groups[event_key] = sorted(
            indexes,
            key=lambda idx: (
                positions[relevant_subscriptions[idx].get("consumer_capability", "")][1],
                positions[relevant_subscriptions[idx].get("consumer_capability", "")][0],
                idx,
            ),
        )

    sorted_consume_groups: dict[str, list[int]] = {}
    for consumer_id, indexes in consume_groups.items():
        sorted_consume_groups[consumer_id] = sorted(
            indexes,
            key=lambda idx: (
                event_rectangles[
                    (
                        (relevant_subscriptions[idx].get("subscribed_event") or {}).get("id", ""),
                        (relevant_subscriptions[idx].get("subscribed_event") or {}).get("emitting_capability", ""),
                    )
                ][1],
                positions[(relevant_subscriptions[idx].get("subscribed_event") or {}).get("emitting_capability", "")][0],
                idx,
            ),
        )

    for emitter_id, event_keys in sorted_emitter_event_groups.items():
        emitter_rect = (positions[emitter_id][0], positions[emitter_id][1], cap_w, cap_h)
        for event_key in event_keys:
            event_rank = event_keys.index(event_key)
            event_geo = event_rectangles[event_key]
            event_rect = (event_geo[0], event_geo[1], event_group_geo["w"], event_group_geo["h"])

            emitter_exit_x, emitter_exit_y = _border_anchor(
                source_rect=emitter_rect,
                target_rect=event_rect,
                rank=event_rank,
                total=max(1, len(event_keys)),
            )
            event_entry_x, event_entry_y = _border_anchor(
                source_rect=event_rect,
                target_rect=emitter_rect,
                rank=event_rank,
                total=max(1, len(event_keys)),
            )

            solid_style = _style_with_overrides(
                template_spec["styles"]["edge_emitter_to_event"],
                {
                    "exitX": f"{emitter_exit_x:.3f}",
                    "exitY": f"{emitter_exit_y:.3f}",
                    "exitPerimeter": "1",
                    "entryX": f"{event_entry_x:.3f}",
                    "entryY": f"{event_entry_y:.3f}",
                    "entryPerimeter": "1",
                    "exitDx": "0",
                    "exitDy": "0",
                    "entryDx": "0",
                    "entryDy": "0",
                    "curved": "1",
                },
            )
            _add_edge(
                root_el,
                _uid(),
                solid_style,
                source=capability_cell_ids[emitter_id],
                target=event_image_ids[event_key],
            )

    for index, subscription in enumerate(relevant_subscriptions):
        subscribed_event = subscription.get("subscribed_event") or {}
        event_key = (subscribed_event.get("id", ""), subscribed_event.get("emitting_capability", ""))
        consumer_id = subscription.get("consumer_capability", "")

        if event_key not in event_image_ids or consumer_id not in capability_cell_ids:
            continue

        event_indexes = sorted_event_subscription_groups.get(event_key, [])
        consumer_indexes = sorted_consume_groups.get(consumer_id, [])
        event_rank = event_indexes.index(index) if index in event_indexes else 0
        consumer_rank = consumer_indexes.index(index) if index in consumer_indexes else 0
        consumer_total = max(1, len(consumer_indexes))

        event_geo = event_rectangles[event_key]
        event_rect = (event_geo[0], event_geo[1], event_group_geo["w"], event_group_geo["h"])
        consumer_rect = (positions[consumer_id][0], positions[consumer_id][1], cap_w, cap_h)

        local_rank = event_rank
        local_total = max(1, len(event_indexes))
        event_exit_x = 1.0
        event_exit_y = _axis_anchor(consumer_rank, consumer_total)

        consumer_x = positions[consumer_id][0]
        event_x = event_rect[0]
        consumer_entry_x = 0.0 if consumer_x >= event_x else 1.0
        consumer_entry_y = _axis_anchor(consumer_rank, consumer_total)

        dashed_style = _style_with_overrides(
            template_spec["styles"]["edge_event_to_consumer"],
            {
                "exitX": f"{event_exit_x:.3f}",
                "exitY": f"{event_exit_y:.3f}",
                "exitPerimeter": "1",
                "entryX": f"{consumer_entry_x:.3f}",
                "entryY": f"{consumer_entry_y:.3f}",
                "entryPerimeter": "1",
                "exitDx": "0",
                "exitDy": "0",
                "entryDx": "0",
                "entryDy": "0",
                "curved": "1",
            },
        )
        _add_edge(
            root_el,
            _uid(),
            dashed_style,
            source=event_image_ids[event_key],
            target=capability_cell_ids[consumer_id],
        )

    ET.indent(mxfile, space="  ")
    return ET.tostring(mxfile, encoding="unicode")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generates a draw.io production/consumption chain diagram for an L1 "
            "(capabilities + events + business subscriptions)."
        )
    )
    parser.add_argument("--bcm-dir", default="bcm", help="Directory containing capabilities-*.yaml files")
    parser.add_argument(
        "--events-dir",
        default="bcm/business-event",
        help="Root directory containing business-event-*.yaml and business-subscription-*.yaml",
    )
    parser.add_argument(
        "--template",
        default="views/capacites/COEUR.005-chaine-abonnements-template.drawio",
        help="Reference draw.io template for styles and geometry",
    )
    parser.add_argument(
        "--l1-capability",
        default=None,
        help="Target L1 capability (e.g. CAP.COEUR.005). If omitted: batch for all L1s with internal subscriptions.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output .drawio file (single-capability mode only, with --l1-capability)",
    )
    parser.add_argument(
        "--output-dir",
        default="views/capacites",
        help="Output directory for draw.io renders (default: views/capacites)",
    )
    parser.add_argument("--diagram-name", default="L1 capability chain", help="Name of the draw.io tab")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    bcm_dir = ROOT / args.bcm_dir
    events_dir = ROOT / args.events_dir
    template_file = ROOT / args.template
    output_dir = ROOT / args.output_dir

    if not bcm_dir.exists():
        raise SystemExit(f"[FATAL] Directory not found: {bcm_dir}")
    if not events_dir.exists():
        raise SystemExit(f"[FATAL] Directory not found: {events_dir}")
    if not template_file.exists():
        raise SystemExit(f"[FATAL] Template not found: {template_file}")

    template_spec = load_template_spec(template_file)
    capabilities_by_id = load_capabilities_by_id(bcm_dir)
    business_events_by_id = load_business_events_by_id(events_dir)
    subscriptions = load_business_subscriptions(events_dir)

    if not subscriptions:
        raise SystemExit("[FATAL] No business subscription detected.")

    l1_with_internal_subs: set[str] = set()
    for subscription in subscriptions:
        subscribed_event = subscription.get("subscribed_event") or {}
        emitter_id = subscribed_event.get("emitting_capability", "")
        consumer_id = subscription.get("consumer_capability", "")
        emitter_l1 = resolve_l1_parent(capabilities_by_id, emitter_id)
        consumer_l1 = resolve_l1_parent(capabilities_by_id, consumer_id)
        if emitter_l1 and consumer_l1 and emitter_l1 == consumer_l1:
            l1_with_internal_subs.add(emitter_l1)

    if args.l1_capability:
        if args.l1_capability not in capabilities_by_id:
            raise SystemExit(f"[FATAL] Capability not found: {args.l1_capability}")
        if args.l1_capability not in l1_with_internal_subs:
            raise SystemExit(
                f"[FATAL] No internal subscription detected for {args.l1_capability}."
            )

    output_dir.mkdir(parents=True, exist_ok=True)

    if args.l1_capability:
        xml_output = build_drawio_for_l1(
            l1_capability_id=args.l1_capability,
            capabilities_by_id=capabilities_by_id,
            business_events_by_id=business_events_by_id,
            subscriptions=subscriptions,
            template_spec=template_spec,
            diagram_name=args.diagram_name,
        )

        if args.output:
            output_file = ROOT / args.output
        else:
            output_file = output_dir / f"{_short_capability_id(args.l1_capability)}-chaine-abonnements.drawio"

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(xml_output, encoding="utf-8")

        print("[OK] Draw.io chain generated")
        print(f"  • template   : {template_file.relative_to(ROOT)}")
        print(f"  • capability : {args.l1_capability}")
        print(f"  • output     : {output_file.relative_to(ROOT)}")
        return 0

    if args.output:
        raise SystemExit(
            "[FATAL] --output is not compatible with batch mode (without --l1-capability). "
            "Use --output-dir instead."
        )

    rendered_files: list[Path] = []
    for l1_capability_id in sorted(l1_with_internal_subs):
        xml_output = build_drawio_for_l1(
            l1_capability_id=l1_capability_id,
            capabilities_by_id=capabilities_by_id,
            business_events_by_id=business_events_by_id,
            subscriptions=subscriptions,
            template_spec=template_spec,
            diagram_name=args.diagram_name,
        )
        output_file = output_dir / f"{_short_capability_id(l1_capability_id)}-chaine-abonnements.drawio"
        output_file.write_text(xml_output, encoding="utf-8")
        rendered_files.append(output_file)

    print("[OK] Draw.io chain generated (batch mode)")
    print(f"  • template    : {template_file.relative_to(ROOT)}")
    print(f"  • capabilities: {len(rendered_files)}")
    print(f"  • output dir  : {output_dir.relative_to(ROOT)}")
    for rendered_file in rendered_files:
        print(f"    - {rendered_file.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
