#!/usr/bin/env python3
"""
render_drawio_l2.py — Generates a draw.io diagram (.drawio) showing L2
capabilities grouped within their L1 capabilities, which are in turn within their zones.

The script:
  1. Reads all capabilities-*.yaml files from the bcm/ directory
  2. Groups capabilities by zoning → L1 → L2
  3. Generates a .drawio file with a Business Capability Map diagram
     where each L1 is a draw.io group containing its L2 boxes.

Usage:
    python tools/render_drawio_l2.py
    python tools/render_drawio_l2.py --input-dir bcm --output views/BCM-L2-generated.drawio
    python tools/render_drawio_l2.py --l2-cols 3
    python tools/render_drawio_l2.py --help

Prerequisites:
    pip install pyyaml
"""

from __future__ import annotations

import argparse
import html
import math
import uuid
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# ──────────────────────────────────────────────────────────────
# Visual zone configuration  (identical to render_drawio.py)
# ──────────────────────────────────────────────────────────────

ZONE_CONFIG = {
    "PILOTAGE": {
        "label": "Pilotage",
        "zone_fill": "#A9C4EB",
        "zone_stroke": "#6c8ebf",
    },
    "SERVICES_COEUR": {
        "label": "Business Service Production",
        "zone_fill": "#d5e8d4",
        "zone_stroke": "#82b366",
    },
    "SUPPORT": {
        "label": "Support",
        "zone_fill": "#f5f5f5",
        "zone_stroke": "#666666",
    },
    "REFERENTIEL": {
        "label": "Referentiel",
        "zone_fill": "#f8cecc",
        "zone_stroke": "#b85450",
    },
    "ECHANGE_B2B": {
        "label": "B2B Exchange",
        "zone_fill": "#ffe6cc",
        "zone_stroke": "#d79b00",
    },
    "CANAL": {
        "label": "Canal",
        "zone_fill": "#fff2cc",
        "zone_stroke": "#d6b656",
    },
    "DATA_ANALYTIQUE": {
        "label": "Data & Analytique",
        "zone_fill": "#e1d5e7",
        "zone_stroke": "#9673a6",
    },
}

# ──────────────────────────────────────────────────────────────
# Pastel palette for L1 group backgrounds
# (identical to render_drawio.py)
# ──────────────────────────────────────────────────────────────

CAPABILITY_PALETTE = [
    ("#fff2cc", "#d6b656"),   # pale yellow
    ("#dae8fc", "#6c8ebf"),   # sky blue
    ("#ffe6cc", "#d79b00"),   # peach
    ("#e1d5e7", "#9673a6"),   # lavender
    ("#f8cecc", "#b85450"),   # pink
    ("#d5e8d4", "#82b366"),   # seafoam green
    ("#f5f5f5", "#666666"),   # light gray
    ("#d4e1f5", "#3a7bbf"),   # periwinkle blue
    ("#fce5cd", "#c27b30"),   # apricot
    ("#cfe2f3", "#6fa8dc"),   # pastel blue
    ("#d9ead3", "#6aa84f"),   # almond green
    ("#ead1dc", "#a64d79"),   # antique rose
    ("#d0e0e3", "#45818e"),   # pale teal
    ("#fce8b2", "#bf9000"),   # soft gold
    ("#e6d8f0", "#7b57a0"),   # pastel violet
    ("#c9daf8", "#3d78d8"),   # baby blue
]

# ──────────────────────────────────────────────────────────────
# L2 colors by zone  (extracted from BCM L2 template.drawio)
# ──────────────────────────────────────────────────────────────

L2_ZONE_COLORS: dict[str, tuple[str, str]] = {
    "PILOTAGE":                    ("#dae8fc", "#6c8ebf"),  # sky blue
    "SERVICES_COEUR": ("#ffe6cc", "#d79b00"),  # peach
    "SUPPORT":                     ("#ffe6cc", "#d79b00"),  # peach
    "REFERENTIEL":                 ("#ffe6cc", "#d79b00"),  # peach
    "ECHANGE_B2B":                ("#FFE599", "#d6b656"),  # gold
    "CANAL":                     ("#FFE599", "#d6b656"),  # gold
    "DATA_ANALYTIQUE":              ("#e1d5e7", "#9673a6"),  # pastel lavender
}

# ──────────────────────────────────────────────────────────────
# Zone layout  (identical to render_drawio.py)
# ──────────────────────────────────────────────────────────────
#
#   ┌──────────────────────────────────────────────────────┐
#   │                    PILOTAGE                          │
#   ├──────────┬──────────────────────────────┬────────────┤
#   │          │  SERVICES_COEUR  │            │
#   │  B2B     ├──────────────────────────────┤  CANAL   │
#   │ EXCHANGE │       SUPPORT                │            │
#   │          ├──────────────────────────────┤            │
#   │          │      REFERENTIEL             │            │
#   ├──────────┴──────────────────────────────┴────────────┤
#   │                 DATA_ANALYTIQUE                       │
#   └──────────────────────────────────────────────────────┘

CENTER_ZONES = [
    "SERVICES_COEUR",
    "SUPPORT",
    "REFERENTIEL",
]
LEFT_ZONE = "ECHANGE_B2B"
RIGHT_ZONE = "CANAL"
TOP_ZONE = "PILOTAGE"
BOTTOM_ZONE = "DATA_ANALYTIQUE"

# ──────────────────────────────────────────────────────────────
# Dimensions
# ──────────────────────────────────────────────────────────────

# L2 boxes inside an L1 group
L2_BOX_W = 130       # width of an L2 box
L2_BOX_H = 50        # height of an L2 box
L2_GAP = 10          # spacing between L2 boxes
L2_COLS = 2          # L2 columns per L1 group

# L1 groups
GROUP_PAD = 15       # internal padding of an L1 group
GROUP_TITLE_H = 35   # height of the L1 title within the group
GROUP_GAP = 20       # spacing between L1 groups

# Zones
ZONE_PAD = 30        # internal padding of a zone
ZONE_LABEL_H = 35    # height reserved for the zone label
ZONE_GAP = 15        # spacing between zones

# L1 groups per row depending on zone position
L1_COLS_CENTER = 3   # center zones (COEUR, Support, Referentiel)
L1_COLS_SIDE = 1     # side zones (B2B, Canal)
L1_COLS_FULL = 4     # full-width zones (Pilotage, Data)

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


def _uid() -> str:
    """Generates a unique identifier for a draw.io cell."""
    return "cell-" + uuid.uuid4().hex[:12]


# ──────────────────────────────────────────────────────────────
# YAML loading
# ──────────────────────────────────────────────────────────────


def load_all_capabilities(input_dir: Path) -> list[dict]:
    """Loads all capabilities from capabilities-*.yaml files."""
    caps: list[dict] = []
    found_files: list[Path] = []
    for f in sorted(input_dir.glob("capabilities-*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        file_caps = data.get("capabilities", [])
        caps.extend(file_caps)
        found_files.append(f)
        print(f"  • {f.name}: {len(file_caps)} capability(ies)")
    if not found_files:
        print(f"[WARN] No capabilities-*.yaml file found in {input_dir}")
    return caps


def build_hierarchy(caps: list[dict]) -> dict[str, list[dict]]:
    """
    Builds the zoning → L1 → L2 hierarchy.

    Returns a dict zone_key → [L1 caps], each L1 having a
    "children" key containing the ordered list of its L2s.
    """
    l1_map: dict[str, dict] = {}
    l2_list: list[dict] = []

    for c in caps:
        level = c.get("level", "L1")
        if level == "L1":
            c = dict(c)  # copy to avoid mutating the original
            c["children"] = []
            l1_map[c["id"]] = c
        elif level == "L2":
            l2_list.append(c)

    # Attach L2s to their parent L1
    orphans = 0
    for l2 in l2_list:
        parent_id = l2.get("parent")
        if parent_id and parent_id in l1_map:
            l1_map[parent_id]["children"].append(l2)
        else:
            orphans += 1
    if orphans:
        print(f"[WARN] {orphans} L2 capability(ies) without a valid L1 parent (ignored)")

    # Group by zone
    by_zone: dict[str, list[dict]] = defaultdict(list)
    for l1 in l1_map.values():
        zone = l1.get("zoning", "UNKNOWN")
        by_zone[zone].append(l1)

    # Sort by id
    for zone in by_zone:
        by_zone[zone].sort(key=lambda c: c["id"])
        for l1 in by_zone[zone]:
            l1["children"].sort(key=lambda c: c["id"])

    return dict(by_zone)


# ──────────────────────────────────────────────────────────────
# Calcul de taille
# ──────────────────────────────────────────────────────────────


def _l1_group_size(l1: dict) -> tuple[int, int]:
    """Returns (width, height) of an L1 group including its L2s."""
    n = len(l1.get("children", []))
    if n == 0:
        # L1 without L2: minimal space (1 placeholder box)
        content_w = L2_BOX_W
        content_h = L2_BOX_H
    else:
        rows = math.ceil(n / L2_COLS)
        content_w = L2_COLS * (L2_BOX_W + L2_GAP) - L2_GAP
        content_h = rows * (L2_BOX_H + L2_GAP) - L2_GAP

    w = content_w + 2 * GROUP_PAD
    h = content_h + 2 * GROUP_PAD + GROUP_TITLE_H
    return (w, h)


def _zone_l2_size(l1s: list[dict], group_cols: int) -> tuple[int, int]:
    """Returns (width, height) of a zone containing L1 groups."""
    if not l1s:
        return (300, 100)

    sizes = [_l1_group_size(l1) for l1 in l1s]

    # Arrange groups in rows of `group_cols`
    rows_of_sizes: list[list[tuple[int, int]]] = []
    for i in range(0, len(sizes), group_cols):
        rows_of_sizes.append(sizes[i : i + group_cols])

    max_row_w = 0
    total_h = 0
    for row in rows_of_sizes:
        row_w = sum(s[0] for s in row) + GROUP_GAP * (len(row) - 1)
        max_row_w = max(max_row_w, row_w)
        row_h = max(s[1] for s in row)
        total_h += row_h
    total_h += GROUP_GAP * max(0, len(rows_of_sizes) - 1)

    w = max_row_w + 2 * ZONE_PAD
    h = total_h + 2 * ZONE_PAD + ZONE_LABEL_H
    return (w, h)


# ──────────────────────────────────────────────────────────────
# Construction XML draw.io
# ──────────────────────────────────────────────────────────────


def _add_cell(
    root_el: ET.Element,
    cell_id: str,
    value: str,
    style: str,
    x: int,
    y: int,
    w: int,
    h: int,
    parent: str = "1",
) -> ET.Element:
    """Adds an mxCell (vertex) to the XML."""
    cell = ET.SubElement(root_el, "mxCell")
    cell.set("id", cell_id)
    cell.set("value", value)
    cell.set("style", style)
    cell.set("vertex", "1")
    cell.set("parent", parent)
    geo = ET.SubElement(cell, "mxGeometry")
    geo.set("x", str(x))
    geo.set("y", str(y))
    geo.set("width", str(w))
    geo.set("height", str(h))
    geo.set("as", "geometry")
    return cell


def _add_group(
    root_el: ET.Element,
    group_id: str,
    x: int,
    y: int,
    w: int,
    h: int,
    parent: str = "1",
) -> ET.Element:
    """Adds a draw.io group (L1 container)."""
    cell = ET.SubElement(root_el, "mxCell")
    cell.set("id", group_id)
    cell.set("value", "")
    cell.set("style", "group")
    cell.set("vertex", "1")
    cell.set("connectable", "0")
    cell.set("parent", parent)
    geo = ET.SubElement(cell, "mxGeometry")
    geo.set("x", str(x))
    geo.set("y", str(y))
    geo.set("width", str(w))
    geo.set("height", str(h))
    geo.set("as", "geometry")
    return cell


# ── Styles ──────────────────────────────────────────────────


def _zone_bg_style(fill: str, stroke: str) -> str:
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={fill};strokeColor={stroke};"
        f"verticalAlign=top;align=left;"
        f"movable=1;resizable=1;rotatable=1;deletable=1;"
        f"editable=1;locked=0;connectable=1;"
    )


def _zone_label_style() -> str:
    return (
        "text;html=1;align=center;verticalAlign=middle;"
        "whiteSpace=wrap;rounded=0;"
    )


def _group_bg_style(fill: str, stroke: str) -> str:
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={fill};strokeColor={stroke};"
    )


def _group_label_style() -> str:
    return (
        "text;html=1;align=center;verticalAlign=middle;"
        "whiteSpace=wrap;rounded=0;fontStyle=1;fontSize=13;"
    )


def _l2_box_style(fill: str, stroke: str) -> str:
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={fill};strokeColor={stroke};"
        f"fontSize=11;"
    )


# ── Build ──────────────────────────────────────────────────


def build_drawio_l2(by_zone: dict[str, list[dict]]) -> str:
    """Builds the complete draw.io XML for the L2 view."""

    def _group_cols(zone: str) -> int:
        if zone in (LEFT_ZONE, RIGHT_ZONE):
            return L1_COLS_SIDE
        if zone in (TOP_ZONE, BOTTOM_ZONE):
            return L1_COLS_FULL
        return L1_COLS_CENTER

    def _l1s(zone: str) -> list[dict]:
        return by_zone.get(zone, [])

    # ── Size calculations ──────────────────────────────────

    center_sizes: dict[str, tuple[int, int]] = {}
    for z in CENTER_ZONES:
        center_sizes[z] = _zone_l2_size(_l1s(z), _group_cols(z))

    center_w = max((s[0] for s in center_sizes.values()), default=400)
    center_total_h = (
        sum(s[1] for s in center_sizes.values())
        + ZONE_GAP * max(0, len(CENTER_ZONES) - 1)
    )

    left_l1s = _l1s(LEFT_ZONE)
    right_l1s = _l1s(RIGHT_ZONE)
    left_w = _zone_l2_size(left_l1s, L1_COLS_SIDE)[0] if left_l1s else 200
    right_w = _zone_l2_size(right_l1s, L1_COLS_SIDE)[0] if right_l1s else 200

    total_w = left_w + ZONE_GAP + center_w + ZONE_GAP + right_w

    top_l1s = _l1s(TOP_ZONE)
    bottom_l1s = _l1s(BOTTOM_ZONE)
    top_h = _zone_l2_size(top_l1s, _group_cols(TOP_ZONE))[1] if top_l1s else 120
    bottom_h = (
        _zone_l2_size(bottom_l1s, _group_cols(BOTTOM_ZONE))[1]
        if bottom_l1s
        else 120
    )

    # ── Absolute positions ──────────────────────────────────

    top_x, top_y = 0, 0
    mid_y = top_y + top_h + ZONE_GAP

    left_x = 0
    left_y = mid_y
    center_x = left_x + left_w + ZONE_GAP
    center_y = mid_y
    right_x = center_x + center_w + ZONE_GAP
    right_y = mid_y

    bottom_x = 0
    bottom_y = mid_y + center_total_h + ZONE_GAP

    # ── XML construction ────────────────────────────────────

    mxfile = ET.Element("mxfile")
    mxfile.set("host", "render_drawio_l2.py")
    mxfile.set("agent", "BCM tools")
    mxfile.set("version", "1.0")

    diagram = ET.SubElement(mxfile, "diagram")
    diagram.set("name", "BCM L2")
    diagram.set("id", "bcm-l2")

    model = ET.SubElement(diagram, "mxGraphModel")
    for attr, val in [
        ("dx", "1600"),
        ("dy", "1200"),
        ("grid", "1"),
        ("gridSize", "10"),
        ("guides", "1"),
        ("tooltips", "1"),
        ("connect", "1"),
        ("arrows", "1"),
        ("fold", "1"),
        ("page", "1"),
        ("pageScale", "1"),
        ("pageWidth", "2400"),
        ("pageHeight", "1800"),
        ("math", "0"),
        ("shadow", "0"),
    ]:
        model.set(attr, val)

    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell").set("id", "0")
    cell1 = ET.SubElement(root, "mxCell")
    cell1.set("id", "1")
    cell1.set("parent", "0")

    # Global counter for the palette (shared across all zones)
    palette_idx = [0]

    def _render_zone(
        zone_key: str,
        zx: int,
        zy: int,
        zw: int,
        zh: int,
        group_cols: int,
    ) -> None:
        """Renders a zone: background + label + L1 groups containing the L2s."""
        cfg = ZONE_CONFIG.get(
            zone_key,
            {"label": zone_key, "zone_fill": "#f5f5f5", "zone_stroke": "#999999"},
        )
        l1s = by_zone.get(zone_key, [])
        l2_fill, l2_stroke = L2_ZONE_COLORS.get(zone_key, ("#ffe6cc", "#d79b00"))

        # Zone background
        _add_cell(
            root,
            _uid(),
            "",
            _zone_bg_style(cfg["zone_fill"], cfg["zone_stroke"]),
            zx,
            zy,
            zw,
            zh,
        )

        # Zone label
        label_html = (
            f'<font style="font-size: 18px;">'
            f"{html.escape(cfg['label'])}</font>"
        )
        _add_cell(
            root,
            _uid(),
            label_html,
            _zone_label_style(),
            zx + zw // 2 - 140,
            zy + ZONE_PAD // 2,
            280,
            30,
        )

        if not l1s:
            return

        # ── Layout of L1 groups ──────────────────────
        sizes = [_l1_group_size(l1) for l1 in l1s]

        content_x0 = zx + ZONE_PAD
        content_y0 = zy + ZONE_PAD + ZONE_LABEL_H

        gx, gy = content_x0, content_y0
        col_idx = 0
        row_max_h = 0

        for i, l1 in enumerate(l1s):
            gw, gh = sizes[i]
            fill, stroke = CAPABILITY_PALETTE[
                palette_idx[0] % len(CAPABILITY_PALETTE)
            ]
            palette_idx[0] += 1

            # draw.io group (L1 container)
            group_id = _uid()
            _add_group(root, group_id, gx, gy, gw, gh)

            # L1 group background
            _add_cell(
                root,
                _uid(),
                "",
                _group_bg_style(fill, stroke),
                0,
                0,
                gw,
                gh,
                parent=group_id,
            )

            # L1 title
            l1_label = f"<b>{html.escape(l1['name'])}</b>"
            _add_cell(
                root,
                _uid(),
                l1_label,
                _group_label_style(),
                0,
                5,
                gw,
                GROUP_TITLE_H - 5,
                parent=group_id,
            )

            # L2 boxes
            children = l1.get("children", [])
            if children:
                for j, l2 in enumerate(children):
                    l2_col = j % L2_COLS
                    l2_row = j // L2_COLS
                    bx = GROUP_PAD + l2_col * (L2_BOX_W + L2_GAP)
                    by = GROUP_TITLE_H + GROUP_PAD + l2_row * (L2_BOX_H + L2_GAP)
                    l2_label = html.escape(l2["name"])
                    _add_cell(
                        root,
                        _uid(),
                        l2_label,
                        _l2_box_style(l2_fill, l2_stroke),
                        bx,
                        by,
                        L2_BOX_W,
                        L2_BOX_H,
                        parent=group_id,
                    )
            else:
                # L1 without L2: one placeholder box
                bx = GROUP_PAD
                by = GROUP_TITLE_H + GROUP_PAD
                _add_cell(
                    root,
                    _uid(),
                    "<i>(no L2 defined)</i>",
                    _l2_box_style("#f5f5f5", "#999999"),
                    bx,
                    by,
                    L2_BOX_W,
                    L2_BOX_H,
                    parent=group_id,
                )

            # Advance position
            gx += gw + GROUP_GAP
            row_max_h = max(row_max_h, gh)
            col_idx += 1
            if col_idx >= group_cols:
                col_idx = 0
                gx = content_x0
                gy += row_max_h + GROUP_GAP
                row_max_h = 0

    # ── Render each zone ────────────────────────────────────

    # TOP — Pilotage
    _render_zone(TOP_ZONE, top_x, top_y, total_w, top_h, _group_cols(TOP_ZONE))

    # LEFT — B2B Exchange
    _render_zone(LEFT_ZONE, left_x, left_y, left_w, center_total_h, L1_COLS_SIDE)

    # CENTER — COEUR, Support, Referentiel
    cy = center_y
    for z in CENTER_ZONES:
        _, zh = center_sizes[z]
        _render_zone(z, center_x, cy, center_w, zh, _group_cols(z))
        cy += zh + ZONE_GAP

    # RIGHT — Canal
    _render_zone(
        RIGHT_ZONE, right_x, right_y, right_w, center_total_h, L1_COLS_SIDE
    )

    # BOTTOM — Data & Analytique
    _render_zone(
        BOTTOM_ZONE, bottom_x, bottom_y, total_w, bottom_h, _group_cols(BOTTOM_ZONE)
    )

    # ── Serialization ──────────────────────────────────────

    ET.indent(mxfile, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        mxfile, encoding="unicode"
    )


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Generates a draw.io L2 diagram from capabilities-*.yaml files "
            "in the bcm/ directory."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/render_drawio_l2.py
  python tools/render_drawio_l2.py --input-dir bcm
  python tools/render_drawio_l2.py --input-dir bcm --output views/BCM-L2.drawio
  python tools/render_drawio_l2.py --l2-cols 3
  python tools/render_drawio_l2.py --l1-cols 4

Colors:
  - Zones     : color codes identical to render_drawio.py (ZONE_CONFIG)
  - L1 groups : rotating pastel palette (CAPABILITY_PALETTE)
  - L2 boxes  : color per zone from BCM L2 template.drawio
                 (e.g. peach #ffe6cc for COEUR, sky blue #dae8fc for Pilotage)
        """,
    )
    p.add_argument(
        "-d",
        "--input-dir",
        type=Path,
        default=ROOT / "bcm",
        help="Directory containing capabilities-*.yaml files (default: bcm/)",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=ROOT / "views" / "BCM-L2-generated.drawio",
        help="Output path for the .drawio file (default: views/BCM-L2-generated.drawio)",
    )
    p.add_argument(
        "--l2-cols",
        type=int,
        default=L2_COLS,
        help=f"Number of L2 columns within an L1 group (default: {L2_COLS})",
    )
    p.add_argument(
        "--l1-cols",
        type=int,
        default=L1_COLS_CENTER,
        help=f"Number of L1 groups per row in center zones (default: {L1_COLS_CENTER})",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    global L2_COLS, L1_COLS_CENTER
    L2_COLS = args.l2_cols
    L1_COLS_CENTER = args.l1_cols

    input_dir: Path = args.input_dir
    if not input_dir.is_absolute():
        input_dir = ROOT / input_dir

    output_path: Path = args.output
    if not output_path.is_absolute():
        output_path = ROOT / output_path

    if not input_dir.exists():
        print(f"[ERROR] Directory not found: {input_dir}")
        raise SystemExit(1)

    print(f"[INFO] Reading capabilities from {input_dir}/capabilities-*.yaml ...")
    caps = load_all_capabilities(input_dir)
    if not caps:
        print("[ERROR] No capabilities found.")
        raise SystemExit(1)

    by_zone = build_hierarchy(caps)

    xml_str = build_drawio_l2(by_zone)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(xml_str, encoding="utf-8")

    # ── Summary ──────────────────────────────────────────────
    total_l1 = sum(len(v) for v in by_zone.values())
    total_l2 = sum(
        len(l1.get("children", []))
        for l1s in by_zone.values()
        for l1 in l1s
    )
    zones_used = [z for z in ZONE_CONFIG if by_zone.get(z)]
    print(
        f"\n[OK] {total_l1} L1, {total_l2} L2 in {len(zones_used)} zone(s) "
        f"→ {output_path}"
    )
    for z in ZONE_CONFIG:
        l1s = by_zone.get(z, [])
        if l1s:
            n_l2 = sum(len(l1.get("children", [])) for l1 in l1s)
            print(
                f"  • {ZONE_CONFIG[z]['label']}: "
                f"{len(l1s)} L1, {n_l2} L2"
            )


if __name__ == "__main__":
    main()
