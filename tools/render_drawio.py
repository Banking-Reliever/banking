#!/usr/bin/env python3
"""
render_drawio.py — Generates a draw.io diagram (.drawio) from a
capabilities YAML file (e.g. capabilities-L1.yaml).

Usage:
    python tools/render_drawio.py
    python tools/render_drawio.py --input bcm/capabilities-L1.yaml --output views/BCM-L1-generated.drawio
    python tools/render_drawio.py --help

The script:
  1. Reads the capabilities YAML file
  2. Groups capabilities by zoning
  3. Generates a .drawio file with a Business Capability Map diagram
     (colored zones, L1 boxes arranged in a grid)

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
# Configuration visuelle des zones
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
# Distinctive pastel color palette for L1 boxes
# (fill, stroke) — cycles if more capabilities than colors
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

# Ordre d'affichage des zones dans la disposition BCM classique :
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

# Zones stacked vertically in the center
CENTER_ZONES = [
    "SERVICES_COEUR",
    "SUPPORT",
    "REFERENTIEL",
]

# Lateral zones (span the full height of the center)
LEFT_ZONE = "ECHANGE_B2B"
RIGHT_ZONE = "CANAL"

# Full-width zones (top and bottom)
TOP_ZONE = "PILOTAGE"
BOTTOM_ZONE = "DATA_ANALYTIQUE"

# ──────────────────────────────────────────────────────────────
# Dimensions
# ──────────────────────────────────────────────────────────────

BOX_W = 130          # width of a capability box
BOX_H = 60           # height of a capability box
GAP = 20             # spacing between boxes
ZONE_PAD = 30        # internal padding of a zone
LABEL_H = 35         # height reserved for the zone label
ZONE_GAP = 15        # spacing between zones
SIDE_COLS = 1        # columns in lateral zones (B2B, Channel)
CENTER_COLS = 4      # columns in central zones
FULL_COLS = 6        # columns in full-width zones


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _uid() -> str:
    """Generates a unique identifier for a draw.io cell."""
    return "cell-" + uuid.uuid4().hex[:12]


def _zone_content_size(n_caps: int, cols: int) -> tuple[int, int]:
    """Returns (width, height) of a zone's content (excluding padding and label)."""
    if n_caps == 0:
        return (cols * (BOX_W + GAP) - GAP, BOX_H)
    rows = math.ceil(n_caps / cols)
    w = cols * (BOX_W + GAP) - GAP
    h = rows * (BOX_H + GAP) - GAP
    return (w, h)


def _zone_outer_size(n_caps: int, cols: int) -> tuple[int, int]:
    """Retourne (width, height) totale d'une zone."""
    cw, ch = _zone_content_size(n_caps, cols)
    w = cw + 2 * ZONE_PAD
    h = ch + 2 * ZONE_PAD + LABEL_H
    return (w, h)


# ──────────────────────────────────────────────────────────────
# Chargement YAML
# ──────────────────────────────────────────────────────────────

def load_capabilities(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("capabilities", [])


def group_by_zone(caps: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for c in caps:
        zone = c.get("zoning", "UNKNOWN")
        groups[zone].append(c)
    # Tri par id dans chaque zone
    for zone in groups:
        groups[zone].sort(key=lambda c: c["id"])
    return groups


# ──────────────────────────────────────────────────────────────
# Construction XML draw.io
# ──────────────────────────────────────────────────────────────

def _add_cell(root_el: ET.Element, cell_id: str, value: str,
              style: str, x: int, y: int, w: int, h: int,
              parent: str = "1", vertex: bool = True) -> ET.Element:
    """Adds an mxCell to the XML root."""
    cell = ET.SubElement(root_el, "mxCell")
    cell.set("id", cell_id)
    cell.set("value", value)
    cell.set("style", style)
    if vertex:
        cell.set("vertex", "1")
    cell.set("parent", parent)
    geo = ET.SubElement(cell, "mxGeometry")
    geo.set("x", str(x))
    geo.set("y", str(y))
    geo.set("width", str(w))
    geo.set("height", str(h))
    geo.set("as", "geometry")
    return cell


def _zone_bg_style(fill: str, stroke: str) -> str:
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={fill};strokeColor={stroke};"
        f"movable=1;resizable=1;rotatable=1;deletable=1;"
        f"editable=1;locked=0;connectable=1;"
    )


def _zone_label_style() -> str:
    return (
        "text;html=1;align=center;verticalAlign=middle;"
        "whiteSpace=wrap;rounded=0;"
    )


def _cap_box_style(fill: str, stroke: str) -> str:
    return (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={fill};strokeColor={stroke};"
    )


def build_drawio(caps_by_zone: dict[str, list[dict]]) -> str:
    """Construit le XML draw.io complet."""

    # ── Calcul des tailles ──────────────────────────────────

    def _n(zone: str) -> int:
        return len(caps_by_zone.get(zone, []))

    def _cols(zone: str) -> int:
        if zone in (LEFT_ZONE, RIGHT_ZONE):
            return SIDE_COLS
        if zone in (TOP_ZONE, BOTTOM_ZONE):
            return FULL_COLS
        return CENTER_COLS

    # Tailles des zones centrales
    center_sizes = {}
    for z in CENTER_ZONES:
        center_sizes[z] = _zone_outer_size(_n(z), _cols(z))

    center_w = max(s[0] for s in center_sizes.values()) if center_sizes else 400
    center_total_h = sum(s[1] for s in center_sizes.values()) + ZONE_GAP * (len(CENTER_ZONES) - 1)

    # Lateral zone sizes — height = center height
    left_caps = _n(LEFT_ZONE)
    right_caps = _n(RIGHT_ZONE)
    left_w = _zone_outer_size(left_caps, SIDE_COLS)[0] if left_caps else 180
    right_w = _zone_outer_size(right_caps, SIDE_COLS)[0] if right_caps else 180

    total_w = left_w + ZONE_GAP + center_w + ZONE_GAP + right_w

    # Zone top & bottom : pleine largeur
    top_h = _zone_outer_size(_n(TOP_ZONE), _cols(TOP_ZONE))[1] if _n(TOP_ZONE) else 120
    bottom_h = _zone_outer_size(_n(BOTTOM_ZONE), _cols(BOTTOM_ZONE))[1] if _n(BOTTOM_ZONE) else 120

    # ── Positions absolues ──────────────────────────────────

    origin_x = 0
    origin_y = 0

    # Top zone
    top_x = origin_x
    top_y = origin_y
    top_w_actual = total_w

    # Middle row
    mid_y = top_y + top_h + ZONE_GAP

    left_x = origin_x
    left_y = mid_y

    center_x = left_x + left_w + ZONE_GAP
    center_y = mid_y

    right_x = center_x + center_w + ZONE_GAP
    right_y = mid_y

    # Bottom zone
    bottom_y = mid_y + center_total_h + ZONE_GAP
    bottom_x = origin_x
    bottom_w_actual = total_w

    # ── Construction XML ────────────────────────────────────

    mxfile = ET.Element("mxfile")
    mxfile.set("host", "render_drawio.py")
    mxfile.set("agent", "BCM tools")
    mxfile.set("version", "1.0")

    diagram = ET.SubElement(mxfile, "diagram")
    diagram.set("name", "BCM L1")
    diagram.set("id", "bcm-l1")

    model = ET.SubElement(diagram, "mxGraphModel")
    model.set("dx", "1400")
    model.set("dy", "900")
    model.set("grid", "1")
    model.set("gridSize", "10")
    model.set("guides", "1")
    model.set("tooltips", "1")
    model.set("connect", "1")
    model.set("arrows", "1")
    model.set("fold", "1")
    model.set("page", "1")
    model.set("pageScale", "1")
    model.set("pageWidth", "1600")
    model.set("pageHeight", "1200")
    model.set("math", "0")
    model.set("shadow", "0")

    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell").set("id", "0")
    cell1 = ET.SubElement(root, "mxCell")
    cell1.set("id", "1")
    cell1.set("parent", "0")

    def _render_zone(zone_key: str, zx: int, zy: int,
                     zw: int | None, zh: int | None,
                     cols: int):
        """Renders a zone (background + label + capability boxes)."""
        cfg = ZONE_CONFIG.get(zone_key, {
            "label": zone_key,
            "zone_fill": "#f5f5f5",
            "zone_stroke": "#999999",
        })
        caps = caps_by_zone.get(zone_key, [])
        n = len(caps)

        # Actual size
        computed_w, computed_h = _zone_outer_size(n, cols)
        final_w = zw if zw is not None else computed_w
        final_h = zh if zh is not None else computed_h

        # Fond de zone
        _add_cell(root, _uid(), "",
                  _zone_bg_style(cfg["zone_fill"], cfg["zone_stroke"]),
                  zx, zy, final_w, final_h)

        # Label
        label_val = f'<font style="font-size: 18px;">{html.escape(cfg["label"])}</font>'
        _add_cell(root, _uid(), label_val,
                  _zone_label_style(),
                  zx + final_w // 2 - 140, zy + ZONE_PAD // 2,
                  280, 30)

        # Capability boxes — each L1 gets a distinctive pastel color
        content_x0 = zx + ZONE_PAD
        content_y0 = zy + ZONE_PAD + LABEL_H
        for i, cap in enumerate(caps):
            col = i % cols
            row = i // cols
            bx = content_x0 + col * (BOX_W + GAP)
            by = content_y0 + row * (BOX_H + GAP)
            cap_label = html.escape(cap["name"])
            cap_fill, cap_stroke = CAPABILITY_PALETTE[i % len(CAPABILITY_PALETTE)]
            _add_cell(root, _uid(), cap_label,
                      _cap_box_style(cap_fill, cap_stroke),
                      bx, by, BOX_W, BOX_H)

    # ── Rendre chaque zone ──────────────────────────────────

    # TOP — Pilotage
    _render_zone(TOP_ZONE, top_x, top_y, top_w_actual, top_h, _cols(TOP_ZONE))

    # LEFT — B2B Exchange
    _render_zone(LEFT_ZONE, left_x, left_y, left_w, center_total_h, SIDE_COLS)

    # CENTER — COEUR, Support, Referentiel
    cy = center_y
    for z in CENTER_ZONES:
        zw, zh = center_sizes[z]
        _render_zone(z, center_x, cy, center_w, zh, _cols(z))
        cy += zh + ZONE_GAP

    # RIGHT — Canal
    _render_zone(RIGHT_ZONE, right_x, right_y, right_w, center_total_h, SIDE_COLS)

    # BOTTOM — Data & Analytique
    _render_zone(BOTTOM_ZONE, bottom_x, bottom_y, bottom_w_actual, bottom_h, _cols(BOTTOM_ZONE))

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
        description="Generates a draw.io diagram from a capabilities YAML file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/render_drawio.py
  python tools/render_drawio.py --input bcm/capabilities-L1.yaml
  python tools/render_drawio.py --input bcm/capabilities-L1.yaml --output views/my-bcm.drawio
  python tools/render_drawio.py --cols 3
        """,
    )
    p.add_argument(
        "-i", "--input",
        type=Path,
        default=ROOT / "bcm" / "capabilities-L1.yaml",
        help="Path to the capabilities YAML file (default: bcm/capabilities-L1.yaml)",
    )
    p.add_argument(
        "-o", "--output",
        type=Path,
        default=ROOT / "views" / "BCM-L1-generated.drawio",
        help="Output path for the .drawio file (default: views/BCM-L1-generated.drawio)",
    )
    p.add_argument(
        "--cols",
        type=int,
        default=CENTER_COLS,
        help=f"Number of columns in central zones (default: {CENTER_COLS})",
    )
    return p.parse_args()


def main():
    args = parse_args()

    global CENTER_COLS
    CENTER_COLS = args.cols

    input_path: Path = args.input
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    output_path: Path = args.output
    if not output_path.is_absolute():
        output_path = ROOT / output_path

    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}")
        raise SystemExit(1)

    caps = load_capabilities(input_path)
    caps_by_zone = group_by_zone(caps)

    xml_str = build_drawio(caps_by_zone)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(xml_str, encoding="utf-8")

    # Summary
    total = sum(len(v) for v in caps_by_zone.values())
    zones_used = [z for z in ZONE_CONFIG if caps_by_zone.get(z)]
    print(f"[OK] {total} capabilities in {len(zones_used)} zone(s) → {output_path}")
    for z in ZONE_CONFIG:
        n = len(caps_by_zone.get(z, []))
        if n:
            print(f"  • {ZONE_CONFIG[z]['label']}: {n} capability(ies)")


if __name__ == "__main__":
    main()
