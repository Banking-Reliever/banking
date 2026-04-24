#!/usr/bin/env python3
"""
render_drawio.py — Génère un diagramme draw.io (.drawio) à partir d'un
fichier capabilities YAML (ex. capabilities-L1.yaml).

Usage :
    python tools/render_drawio.py
    python tools/render_drawio.py --input bcm/capabilities-L1.yaml --output views/BCM-L1-generated.drawio
    python tools/render_drawio.py --help

Le script :
  1. Lit le fichier YAML des capacités
  2. Regroupe les capacités par zoning
  3. Génère un fichier .drawio avec un diagramme de type Business Capability Map
     (zones colorées, boîtes L1 disposées en grille)

Pré-requis :
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
# Palette de couleurs pastels distinctives pour les boîtes L1
# (fill, stroke) — cycle si plus de capacités que de couleurs
# ──────────────────────────────────────────────────────────────

CAPABILITY_PALETTE = [
    ("#fff2cc", "#d6b656"),   # jaune pâle
    ("#dae8fc", "#6c8ebf"),   # bleu ciel
    ("#ffe6cc", "#d79b00"),   # pêche
    ("#e1d5e7", "#9673a6"),   # lavande
    ("#f8cecc", "#b85450"),   # rose
    ("#d5e8d4", "#82b366"),   # vert d'eau
    ("#f5f5f5", "#666666"),   # gris clair
    ("#d4e1f5", "#3a7bbf"),   # bleu pervenche
    ("#fce5cd", "#c27b30"),   # abricot
    ("#cfe2f3", "#6fa8dc"),   # bleu pastel
    ("#d9ead3", "#6aa84f"),   # vert amande
    ("#ead1dc", "#a64d79"),   # rose ancien
    ("#d0e0e3", "#45818e"),   # turquoise pâle
    ("#fce8b2", "#bf9000"),   # doré doux
    ("#e6d8f0", "#7b57a0"),   # violet pastel
    ("#c9daf8", "#3d78d8"),   # bleu layette
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

# Zones empilées verticalement au centre
CENTER_ZONES = [
    "SERVICES_COEUR",
    "SUPPORT",
    "REFERENTIEL",
]

# Zones latérales (occupent toute la hauteur du centre)
LEFT_ZONE = "ECHANGE_B2B"
RIGHT_ZONE = "CANAL"

# Zones pleine largeur (haut et bas)
TOP_ZONE = "PILOTAGE"
BOTTOM_ZONE = "DATA_ANALYTIQUE"

# ──────────────────────────────────────────────────────────────
# Dimensions
# ──────────────────────────────────────────────────────────────

BOX_W = 130          # largeur d'une boîte capacité
BOX_H = 60           # hauteur d'une boîte capacité
GAP = 20             # espacement entre boîtes
ZONE_PAD = 30        # padding interne d'une zone
LABEL_H = 35         # hauteur réservée au label de zone
ZONE_GAP = 15        # espacement entre zones
SIDE_COLS = 1        # colonnes dans les zones latérales (B2B, Canal)
CENTER_COLS = 4      # colonnes dans les zones centrales
FULL_COLS = 6        # colonnes dans les zones pleine largeur


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _uid() -> str:
    """Génère un identifiant unique pour une cellule draw.io."""
    return "cell-" + uuid.uuid4().hex[:12]


def _zone_content_size(n_caps: int, cols: int) -> tuple[int, int]:
    """Retourne (width, height) du contenu d'une zone (hors padding et label)."""
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
    """Ajoute un mxCell au root XML."""
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

    # Tailles des zones latérales — hauteur = hauteur centre
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
        """Rend une zone (fond + label + boîtes capacités)."""
        cfg = ZONE_CONFIG.get(zone_key, {
            "label": zone_key,
            "zone_fill": "#f5f5f5",
            "zone_stroke": "#999999",
        })
        caps = caps_by_zone.get(zone_key, [])
        n = len(caps)

        # Taille réelle
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

        # Boîtes capacités — chaque L1 reçoit une couleur pastel distinctive
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

    # ── Sérialisation ──────────────────────────────────────

    ET.indent(mxfile, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        mxfile, encoding="unicode"
    )


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Génère un diagramme draw.io à partir d'un fichier capabilities YAML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python tools/render_drawio.py
  python tools/render_drawio.py --input bcm/capabilities-L1.yaml
  python tools/render_drawio.py --input bcm/capabilities-L1.yaml --output views/mon-bcm.drawio
  python tools/render_drawio.py --cols 3
        """,
    )
    p.add_argument(
        "-i", "--input",
        type=Path,
        default=ROOT / "bcm" / "capabilities-L1.yaml",
        help="Chemin vers le fichier YAML des capacités (défaut : bcm/capabilities-L1.yaml)",
    )
    p.add_argument(
        "-o", "--output",
        type=Path,
        default=ROOT / "views" / "BCM-L1-generated.drawio",
        help="Chemin de sortie du fichier .drawio (défaut : views/BCM-L1-generated.drawio)",
    )
    p.add_argument(
        "--cols",
        type=int,
        default=CENTER_COLS,
        help=f"Nombre de colonnes dans les zones centrales (défaut : {CENTER_COLS})",
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
        print(f"[ERREUR] Fichier introuvable : {input_path}")
        raise SystemExit(1)

    caps = load_capabilities(input_path)
    caps_by_zone = group_by_zone(caps)

    xml_str = build_drawio(caps_by_zone)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(xml_str, encoding="utf-8")

    # Résumé
    total = sum(len(v) for v in caps_by_zone.values())
    zones_used = [z for z in ZONE_CONFIG if caps_by_zone.get(z)]
    print(f"[OK] {total} capacités dans {len(zones_used)} zone(s) → {output_path}")
    for z in ZONE_CONFIG:
        n = len(caps_by_zone.get(z, []))
        if n:
            print(f"  • {ZONE_CONFIG[z]['label']}: {n} capacité(s)")


if __name__ == "__main__":
    main()
