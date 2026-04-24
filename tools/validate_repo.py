#!/usr/bin/env python3
"""
validate_repo.py — Validation structurelle du référentiel BCM.

Vérifie :
  1. Présence du fichier vocab.yaml
  2. Présence d'au moins un fichier capabilities-*.yaml dans bcm/
  3. Unicité des identifiants de capacités (tous fichiers confondus)
  4. Validité des champs level et zoning par rapport à vocab.yaml
  5. Règles parent :
     - un L1 ne doit PAS avoir de champ parent
     - un L2+ DOIT avoir un parent
     - le parent référencé DOIT exister dans l'ensemble des capacités chargées
     - le parent d'un L2 doit être un L1 ; le parent d'un L3 doit être un L2
  6. Contrôles heatmap optionnels
      7. Règles cross-assets (evts/) :
         - un événement métier doit être émis par une capacité de niveau L2 ou L3
         - un événement métier doit référencer un objet métier
         - un événement ressource doit référencer une ressource et un seul événement métier (`business_event`)
            - l'événement métier référencé et la ressource portée d'un événement ressource doivent pointer vers le même objet métier
         - une ressource doit référencer un objet métier
                 - une abonnement métier doit référencer un événement métier existant avec la bonne version
             - une abonnement ressource doit référencer un événement ressource existant et cohérent
             - une abonnement ressource doit référencer une abonnement métier existante et cohérente
             - toute abonnement métier doit être référencée par au moins une abonnement ressource
  8. Couverture des propriétés d'objets métier :
     - toute propriété définie dans un objet métier doit être référencée
       via business_object_property dans au moins une ressource
    9. Cohérence L2/L3 des objets métier :
         - si une capacité L2 possède des capacités L3, tout objet métier référant cette L2
             doit déclarer emitting_capability_L3 (liste non vide)
         - chaque capacité listée dans emitting_capability_L3 doit être une L3 existante
             dont le parent est la L2 référencée

Usage :
    python tools/validate_repo.py
    python tools/validate_repo.py --business-object OBJ.COEUR.005.DECLARATION_SINISTRE
"""

from __future__ import annotations

import argparse
import sys
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BCM_DIR = ROOT / "bcm"
VOCAB_FILE = BCM_DIR / "vocab.yaml"
ASSETS_DIR = BCM_DIR
TEMPLATES_DIR = ROOT / "templates"
EXTERNALS_DIR = ROOT / "externals"
PROCESSUS_METIER_DIR = EXTERNALS_DIR / "processus-metier"
PROCESSUS_RESSOURCE_DIR = EXTERNALS_DIR / "processus-ressource"

LEVEL_HIERARCHY = {
    "L2": "L1",
    "L3": "L2",
}

errors: list[str] = []
warnings: list[str] = []


def error(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def promote_warnings_to_errors_if_needed(strict: bool) -> None:
    if not strict or not warnings:
        return
    for warning_msg in warnings:
        error(f"[strict] {warning_msg}")


def validate_templates() -> None:
    expected_templates = [
        TEMPLATES_DIR / "capability-template.yaml",
        TEMPLATES_DIR / "business-event" / "template-business-event.yaml",
        TEMPLATES_DIR / "business-event" / "template-business-subscription.yaml",
        TEMPLATES_DIR / "resource-event" / "template-resource-event.yaml",
        TEMPLATES_DIR / "resource-event" / "template-resource-subscription.yaml",
        TEMPLATES_DIR / "business-object" / "template-business-object.yaml",
        TEMPLATES_DIR / "resource" / "template-resource.yaml",
    ]

    semver_pattern = re.compile(r"^\d+\.\d+\.\d+$")

    for template_path in expected_templates:
        if not template_path.exists():
            error(f"[templates] fichier template introuvable: {template_path.relative_to(ROOT)}")
            continue

        try:
            data = yaml.safe_load(template_path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            error(f"[templates] impossible de parser {template_path.relative_to(ROOT)}: {exc}")
            continue

        meta = data.get("meta")
        if not isinstance(meta, dict):
            error(f"[templates] {template_path.name}: champ 'meta' manquant ou invalide")
            continue

        template_version = meta.get("template_version")
        if not isinstance(template_version, str) or not template_version.strip():
            error(
                f"[templates] {template_path.name}: champ 'meta.template_version' obligatoire "
                f"(format attendu: x.y.z)"
            )
            continue

        if not semver_pattern.match(template_version.strip()):
            error(
                f"[templates] {template_path.name}: meta.template_version '{template_version}' "
                f"invalide (format attendu: x.y.z)"
            )


# ──────────────────────────────────────────────────────────────
# Chargement
# ──────────────────────────────────────────────────────────────


def load_vocab() -> dict:
    if not VOCAB_FILE.exists():
        print(f"[FATAL] Fichier introuvable : {VOCAB_FILE}")
        sys.exit(1)
    return yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))


def load_all_capabilities() -> tuple[list[dict], list[Path]]:
    """Charge toutes les capacités depuis bcm/capabilities-*.yaml."""
    caps: list[dict] = []
    files: list[Path] = []
    for f in sorted(BCM_DIR.glob("capabilities-*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        file_caps = data.get("capabilities", [])
        # Ajoute un champ _source pour le reporting
        for c in file_caps:
            c["_source"] = f.name
        caps.extend(file_caps)
        files.append(f)
    return caps, files


def load_assets(pattern: str, key: str) -> tuple[list[dict], list[Path]]:
    """Charge des assets YAML depuis bcm/ (sous-répertoires inclus)."""
    items: list[dict] = []
    files: list[Path] = []

    if not ASSETS_DIR.exists():
        return items, files

    for f in sorted(ASSETS_DIR.rglob(pattern)):
        if f.name.startswith("template-"):
            continue

        rel_source = str(f.relative_to(ASSETS_DIR))

        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        file_items = data.get(key, []) or []
        if not isinstance(file_items, list):
            error(f"[{rel_source}] Champ '{key}' invalide (liste attendue)")
            files.append(f)
            continue

        for item in file_items:
            if isinstance(item, dict):
                item["_source"] = rel_source
                items.append(item)
            else:
                error(f"[{rel_source}] Entrée invalide dans '{key}' (mapping attendu)")

        files.append(f)

    return items, files


def load_external_processes(process_dir: Path, root_key: str) -> tuple[list[dict], list[Path]]:
    """Charge des processus externes (métier ou ressource)."""
    items: list[dict] = []
    files: list[Path] = []

    if not process_dir.exists():
        return items, files

    for f in sorted(process_dir.rglob("*.yaml")):
        rel_source = str(f.relative_to(ROOT))
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            error(f"[{rel_source}] impossible de parser le fichier: {exc}")
            files.append(f)
            continue

        if not isinstance(data, dict):
            error(f"[{rel_source}] contenu YAML invalide (mapping racine attendu)")
            files.append(f)
            continue

        process_item = data.get(root_key)
        if not isinstance(process_item, dict):
            error(f"[{rel_source}] champ racine '{root_key}' manquant ou invalide")
            files.append(f)
            continue

        process_item["_source"] = rel_source
        items.append(process_item)
        files.append(f)

    return items, files


# ──────────────────────────────────────────────────────────────
# Validations
# ──────────────────────────────────────────────────────────────


def validate(caps: list[dict], vocab: dict) -> None:
    levels = set(vocab.get("levels", []))
    zonings = set(vocab.get("zoning", []))

    ids: set[str] = set()
    by_id: dict[str, dict] = {}

    # ── Passe 1 : champs individuels ────────────────────────
    for c in caps:
        src = c.get("_source", "?")
        cid = c.get("id")

        if not cid:
            error(f"[{src}] Capacité sans champ 'id'")
            continue

        if cid in ids:
            error(f"[{src}] Identifiant dupliqué : {cid}")
        ids.add(cid)
        by_id[cid] = c

        lvl = c.get("level")
        if lvl not in levels:
            error(f"[{src}] {cid}: level '{lvl}' invalide (attendu : {sorted(levels)})")

        zon = c.get("zoning")
        if zon not in zonings:
            error(f"[{src}] {cid}: zoning '{zon}' invalide (attendu : {sorted(zonings)})")

        # Règles parent selon le level
        if lvl == "L1":
            if "parent" in c:
                error(f"[{src}] {cid}: un L1 ne doit pas avoir de champ 'parent'")
        else:
            parent = c.get("parent")
            if not parent:
                error(f"[{src}] {cid}: level {lvl} doit avoir un champ 'parent'")

        # Heatmap optionnel
        hm = c.get("heatmap", {})
        if hm and "maturity" in hm:
            allowed = set(vocab.get("heatmap_scales", {}).get("maturity", []))
            if allowed and hm["maturity"] not in allowed:
                error(
                    f"[{src}] {cid}: maturity '{hm['maturity']}' "
                    f"invalide (attendu : {sorted(allowed)})"
                )

    # ── Passe 2 : existence et cohérence des parents ────────
    for c in caps:
        cid = c.get("id")
        if not cid:
            continue
        lvl = c.get("level")
        if lvl == "L1":
            continue

        parent_id = c.get("parent")
        if not parent_id:
            continue  # déjà signalé en passe 1

        src = c.get("_source", "?")

        if parent_id not in by_id:
            error(
                f"[{src}] {cid}: parent '{parent_id}' introuvable "
                f"dans l'ensemble des capacités chargées"
            )
            continue

        # Vérifier que le level du parent est cohérent
        expected_parent_level = LEVEL_HIERARCHY.get(lvl)
        if expected_parent_level:
            actual_parent_level = by_id[parent_id].get("level")
            if actual_parent_level != expected_parent_level:
                error(
                    f"[{src}] {cid} (level {lvl}): le parent '{parent_id}' "
                    f"est de level '{actual_parent_level}', "
                    f"attendu '{expected_parent_level}'"
                )


def index_by_id(items: list[dict], kind: str) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for item in items:
        src = item.get("_source", "?")
        iid = item.get("id")
        if not iid:
            error(f"[{src}] {kind} sans champ 'id'")
            continue
        if iid in indexed:
            error(f"[{src}] Identifiant dupliqué ({kind}) : {iid}")
            continue
        indexed[iid] = item
    return indexed


def collect_relation_ids(
    item: dict,
    plural_key: str,
    singular_key: str,
    src: str,
    item_id: str,
    label: str,
) -> list[str]:
    """Lit une relation 1-n (nouveau format) avec fallback sur l'ancien format 1-1."""
    relation_ids: list[str] = []

    if plural_key in item:
        raw_value = item.get(plural_key)
        if not isinstance(raw_value, list):
            error(f"[{src}] {item_id}: champ '{plural_key}' invalide (liste attendue)")
            return []
        if not raw_value:
            error(f"[{src}] {item_id}: champ '{plural_key}' obligatoire (liste non vide attendue)")
            return []

        for idx, rel_id in enumerate(raw_value):
            if not isinstance(rel_id, str) or not rel_id.strip():
                error(
                    f"[{src}] {item_id}: {plural_key}[{idx}] invalide "
                    f"(chaîne non vide attendue)"
                )
                continue
            relation_ids.append(rel_id.strip())

        return relation_ids

    legacy_value = item.get(singular_key)
    if legacy_value:
        if not isinstance(legacy_value, str) or not legacy_value.strip():
            error(f"[{src}] {item_id}: champ '{singular_key}' invalide (chaîne non vide attendue)")
            return []
        warn(
            f"[{src}] {item_id}: champ '{singular_key}' legacy détecté; "
            f"préférer '{plural_key}' (liste)"
        )
        return [legacy_value.strip()]

    error(
        f"[{src}] {item_id}: champ '{plural_key}' obligatoire "
        f"(ou '{singular_key}' en legacy) pour {label}"
    )
    return []


def collect_single_relation_id(
    item: dict,
    singular_key: str,
    plural_key: str,
    src: str,
    item_id: str,
    label: str,
) -> str | None:
    if plural_key in item:
        error(
            f"[{src}] {item_id}: champ '{plural_key}' interdit "
            f"(cardinalité 1 attendue, utiliser '{singular_key}')"
        )

    value = item.get(singular_key)
    if not isinstance(value, str) or not value.strip():
        error(
            f"[{src}] {item_id}: champ '{singular_key}' obligatoire "
            f"(chaîne non vide attendue) pour {label}"
        )
        return None

    return value.strip()


def validate_cross_assets(
    caps: list[dict],
    business_events: list[dict],
    business_objects: list[dict],
    resource_events: list[dict],
    resources: list[dict],
) -> None:
    cap_by_id = {c.get("id"): c for c in caps if c.get("id")}
    l3_children_by_l2: dict[str, set[str]] = {}
    for cap in caps:
        cid = cap.get("id")
        if not isinstance(cid, str):
            continue
        if cap.get("level") != "L3":
            continue
        parent_id = cap.get("parent")
        if isinstance(parent_id, str) and parent_id:
            l3_children_by_l2.setdefault(parent_id, set()).add(cid)

    be_by_id = index_by_id(business_events, "événement métier")
    bo_by_id = index_by_id(business_objects, "objet métier")
    re_by_id = index_by_id(resource_events, "événement ressource")
    rs_by_id = index_by_id(resources, "ressource")

    # 1) Événement métier : capacité L2/L3 + objet métier
    for event in business_events:
        src = event.get("_source", "?")
        eid = event.get("id", "<sans-id>")

        version = event.get("version")
        if not version:
            error(f"[{src}] {eid}: champ 'version' obligatoire")

        emitting_capability = event.get("emitting_capability")
        if not emitting_capability:
            error(f"[{src}] {eid}: champ 'emitting_capability' obligatoire")
        elif emitting_capability not in cap_by_id:
            error(f"[{src}] {eid}: emitting_capability '{emitting_capability}' introuvable")
        else:
            cap_level = cap_by_id[emitting_capability].get("level")
            if cap_level not in {"L2", "L3"}:
                error(
                    f"[{src}] {eid}: emitting_capability '{emitting_capability}' "
                    f"doit être de level L2 ou L3 (actuel: {cap_level})"
                )

        carried_business_object = event.get("carried_business_object")
        if not carried_business_object:
            error(f"[{src}] {eid}: champ 'carried_business_object' obligatoire")
        elif carried_business_object not in bo_by_id:
            error(
                f"[{src}] {eid}: objet métier '{carried_business_object}' introuvable "
                f"dans business-object-*.yaml"
            )

    # 1 bis) Objet métier : ne doit pas référencer d'événement métier
    for obj in business_objects:
        src = obj.get("_source", "?")
        oid = obj.get("id", "<sans-id>")

        emitting_capability = obj.get("emitting_capability")
        if isinstance(emitting_capability, str) and emitting_capability in cap_by_id:
            children_l3 = l3_children_by_l2.get(emitting_capability, set())
            has_l3_field = "emitting_capability_L3" in obj

            if children_l3:
                if not has_l3_field:
                    error(
                        f"[{src}] {oid}: champ 'emitting_capability_L3' obligatoire car "
                        f"la capacité L2 '{emitting_capability}' possède des capacités L3"
                    )
                else:
                    raw_l3_list = obj.get("emitting_capability_L3")
                    if not isinstance(raw_l3_list, list):
                        error(
                            f"[{src}] {oid}: champ 'emitting_capability_L3' invalide "
                            f"(liste attendue)"
                        )
                    elif not raw_l3_list:
                        error(
                            f"[{src}] {oid}: champ 'emitting_capability_L3' obligatoire "
                            f"(liste non vide attendue)"
                        )
                    else:
                        seen_l3: set[str] = set()
                        for idx, l3_id in enumerate(raw_l3_list):
                            if not isinstance(l3_id, str) or not l3_id.strip():
                                error(
                                    f"[{src}] {oid}: emitting_capability_L3[{idx}] invalide "
                                    f"(chaîne non vide attendue)"
                                )
                                continue

                            l3_id = l3_id.strip()
                            if l3_id in seen_l3:
                                error(
                                    f"[{src}] {oid}: emitting_capability_L3 contient un "
                                    f"doublon ('{l3_id}')"
                                )
                                continue
                            seen_l3.add(l3_id)

                            referenced_cap = cap_by_id.get(l3_id)
                            if not referenced_cap:
                                error(
                                    f"[{src}] {oid}: emitting_capability_L3 '{l3_id}' introuvable"
                                )
                                continue

                            if referenced_cap.get("level") != "L3":
                                error(
                                    f"[{src}] {oid}: emitting_capability_L3 '{l3_id}' doit "
                                    f"référencer une capacité de niveau L3"
                                )
                                continue

                            l3_parent = referenced_cap.get("parent")
                            if l3_parent != emitting_capability:
                                error(
                                    f"[{src}] {oid}: emitting_capability_L3 '{l3_id}' référence "
                                    f"la L2 '{l3_parent}', attendu '{emitting_capability}'"
                                )
            elif has_l3_field:
                error(
                    f"[{src}] {oid}: champ 'emitting_capability_L3' interdit car la "
                    f"capacité L2 '{emitting_capability}' ne possède aucune capacité L3"
                )

        if "emitting_business_event" in obj:
            error(
                f"[{src}] {oid}: champ 'emitting_business_event' interdit. "
                f"La relation doit être portée par l'événement métier via 'carried_business_object'."
            )

        if "emitting_business_events" in obj:
            error(
                f"[{src}] {oid}: champ 'emitting_business_events' interdit. "
                f"La relation doit être portée par l'événement métier via 'carried_business_object'."
            )

    # 2) Événement ressource : référence ressource + un seul événement métier
    for event in resource_events:
        src = event.get("_source", "?")
        eid = event.get("id", "<sans-id>")

        carried_resource = event.get("carried_resource")
        data = event.get("data")
        if carried_resource and data:
            error(f"[{src}] {eid}: les champs 'carried_resource' et 'data' sont mutuellement exclusifs")
        elif not carried_resource and not data:
            error(f"[{src}] {eid}: un des champs 'carried_resource' ou 'data' doit être renseigné")
        elif carried_resource and carried_resource not in rs_by_id:
            error(
                f"[{src}] {eid}: ressource '{carried_resource}' introuvable "
                f"dans resource-*.yaml"
            )

        business_event = collect_single_relation_id(
            event,
            "business_event",
            "business_events",
            src,
            eid,
            "l'événement métier lié à l'événement ressource",
        )
        if business_event and business_event not in be_by_id:
            error(
                f"[{src}] {eid}: événement métier '{business_event}' introuvable "
                f"dans business-event-*.yaml"
            )

        # Cohérence métier : la ressource portée et l'événement métier lié
        # doivent converger vers le même objet métier.
        if (
            isinstance(carried_resource, str)
            and carried_resource in rs_by_id
            and isinstance(business_event, str)
            and business_event in be_by_id
        ):
            resource_business_object = rs_by_id[carried_resource].get("business_object")
            event_business_object = be_by_id[business_event].get("carried_business_object")
            if resource_business_object != event_business_object:
                error(
                    f"[{src}] {eid}: incohérence de rattachement objet métier entre "
                    f"carried_resource '{carried_resource}' (business_object='{resource_business_object}') "
                    f"et business_event '{business_event}' (carried_business_object='{event_business_object}')"
                )

    # 3) Ressource : référence objet métier
    for resource in resources:
        src = resource.get("_source", "?")
        rid = resource.get("id", "<sans-id>")

        business_object = resource.get("business_object")
        if not business_object:
            error(f"[{src}] {rid}: champ 'business_object' obligatoire")
        elif business_object not in bo_by_id:
            error(
                f"[{src}] {rid}: objet métier '{business_object}' introuvable "
                f"dans business-object-*.yaml"
            )


def validate_business_subscriptions(
    caps: list[dict],
    business_events: list[dict],
    business_subscriptions: list[dict],
) -> None:
    cap_by_id = {c.get("id"): c for c in caps if c.get("id")}
    be_by_id = index_by_id(business_events, "événement métier")

    for sub in business_subscriptions:
        src = sub.get("_source", "?")
        sid = sub.get("id", "<sans-id>")

        consumer_capability = sub.get("consumer_capability")
        if not consumer_capability:
            error(f"[{src}] {sid}: champ 'consumer_capability' obligatoire")
        elif consumer_capability not in cap_by_id:
            error(f"[{src}] {sid}: consumer_capability '{consumer_capability}' introuvable")
        else:
            cap_level = cap_by_id[consumer_capability].get("level")
            if cap_level not in {"L2", "L3"}:
                error(
                    f"[{src}] {sid}: consumer_capability '{consumer_capability}' "
                    f"doit être de level L2 ou L3 (actuel: {cap_level})"
                )

        subscribed_event = sub.get("subscribed_event")
        if not isinstance(subscribed_event, dict):
            error(f"[{src}] {sid}: champ 'subscribed_event' obligatoire (mapping attendu)")
            continue

        event_id = subscribed_event.get("id")
        if not event_id:
            error(f"[{src}] {sid}: subscribed_event.id obligatoire")
            continue

        if event_id not in be_by_id:
            error(
                f"[{src}] {sid}: subscribed_event.id '{event_id}' introuvable "
                f"dans business-event-*.yaml"
            )
            continue

        expected_event = be_by_id[event_id]

        subscribed_version = subscribed_event.get("version")
        if not subscribed_version:
            error(f"[{src}] {sid}: subscribed_event.version obligatoire")
        else:
            expected_version = expected_event.get("version")
            if subscribed_version != expected_version:
                error(
                    f"[{src}] {sid}: subscribed_event.version '{subscribed_version}' "
                    f"différente de la version de l'événement métier '{expected_version}'"
                )

        emitting_capability = subscribed_event.get("emitting_capability")
        if not emitting_capability:
            error(f"[{src}] {sid}: subscribed_event.emitting_capability obligatoire")
        else:
            expected_emitter = expected_event.get("emitting_capability")
            if emitting_capability != expected_emitter:
                error(
                    f"[{src}] {sid}: subscribed_event.emitting_capability '{emitting_capability}' "
                    f"différent de l'émetteur de l'événement métier '{expected_emitter}'"
                )


def validate_resource_subscriptions(
    caps: list[dict],
    business_subscriptions: list[dict],
    resource_events: list[dict],
    resource_subscriptions: list[dict],
) -> None:
    cap_by_id = {c.get("id"): c for c in caps if c.get("id")}
    re_by_id = index_by_id(resource_events, "événement ressource")
    bs_by_id = index_by_id(business_subscriptions, "abonnement métier")
    referenced_business_subscriptions: set[str] = set()

    for sub in resource_subscriptions:
        src = sub.get("_source", "?")
        sid = sub.get("id", "<sans-id>")

        consumer_capability = sub.get("consumer_capability")
        if not consumer_capability:
            error(f"[{src}] {sid}: champ 'consumer_capability' obligatoire")
        elif consumer_capability not in cap_by_id:
            error(f"[{src}] {sid}: consumer_capability '{consumer_capability}' introuvable")
        else:
            cap_level = cap_by_id[consumer_capability].get("level")
            if cap_level not in {"L2", "L3"}:
                error(
                    f"[{src}] {sid}: consumer_capability '{consumer_capability}' "
                    f"doit être de level L2 ou L3 (actuel: {cap_level})"
                )

        linked_business_subscription = sub.get("linked_business_subscription")
        if not linked_business_subscription:
            error(f"[{src}] {sid}: champ 'linked_business_subscription' obligatoire")
            linked_business = None
        elif linked_business_subscription not in bs_by_id:
            error(
                f"[{src}] {sid}: linked_business_subscription '{linked_business_subscription}' introuvable "
                f"dans business-subscription-*.yaml"
            )
            linked_business = None
        else:
            referenced_business_subscriptions.add(linked_business_subscription)
            linked_business = bs_by_id[linked_business_subscription]

            expected_consumer = linked_business.get("consumer_capability")
            if consumer_capability and consumer_capability != expected_consumer:
                error(
                    f"[{src}] {sid}: consumer_capability '{consumer_capability}' "
                    f"différente de celle de la abonnement métier liée '{expected_consumer}'"
                )

        subscribed_resource_event = sub.get("subscribed_resource_event")
        if not isinstance(subscribed_resource_event, dict):
            error(f"[{src}] {sid}: champ 'subscribed_resource_event' obligatoire (mapping attendu)")
            continue

        event_id = subscribed_resource_event.get("id")
        if not event_id:
            error(f"[{src}] {sid}: subscribed_resource_event.id obligatoire")
            continue

        if event_id not in re_by_id:
            error(
                f"[{src}] {sid}: subscribed_resource_event.id '{event_id}' introuvable "
                f"dans resource-event-*.yaml"
            )
            continue

        expected_event = re_by_id[event_id]

        emitting_capability = subscribed_resource_event.get("emitting_capability")
        if not emitting_capability:
            error(f"[{src}] {sid}: subscribed_resource_event.emitting_capability obligatoire")
        else:
            expected_emitter = expected_event.get("emitting_capability")
            if emitting_capability != expected_emitter:
                error(
                    f"[{src}] {sid}: subscribed_resource_event.emitting_capability '{emitting_capability}' "
                    f"différent de l'émetteur de l'événement ressource '{expected_emitter}'"
                )

        linked_business_event = subscribed_resource_event.get("linked_business_event")
        if not linked_business_event:
            error(f"[{src}] {sid}: subscribed_resource_event.linked_business_event obligatoire")
        else:
            expected_business_event = collect_single_relation_id(
                expected_event,
                "business_event",
                "business_events",
                expected_event.get("_source", "?"),
                expected_event.get("id", "<sans-id>"),
                "l'événement métier lié",
            )
            if expected_business_event and linked_business_event != expected_business_event:
                error(
                    f"[{src}] {sid}: subscribed_resource_event.linked_business_event '{linked_business_event}' "
                    f"différent du business_event de l'événement ressource '{expected_event.get('id', '<sans-id>')}'"
                )

            if linked_business:
                business_subscribed_event = (linked_business.get("subscribed_event") or {}).get("id")
                if business_subscribed_event and linked_business_event != business_subscribed_event:
                    error(
                        f"[{src}] {sid}: linked_business_event '{linked_business_event}' "
                        f"différent de l'événement de la abonnement métier liée '{business_subscribed_event}'"
                    )

        if linked_business:
            business_emitter = (linked_business.get("subscribed_event") or {}).get("emitting_capability")
            resource_emitter = subscribed_resource_event.get("emitting_capability")
            if business_emitter and resource_emitter and business_emitter != resource_emitter:
                error(
                    f"[{src}] {sid}: emitting_capability '{resource_emitter}' "
                    f"différente de l'émetteur de la abonnement métier liée '{business_emitter}'"
                )

    for business_subscription_id in bs_by_id:
        if business_subscription_id not in referenced_business_subscriptions:
            error(
                f"[cross-subscriptions] abonnement métier '{business_subscription_id}' non référencée "
                f"par une abonnement ressource"
            )


def validate_business_object_properties_coverage(
    business_objects: list[dict],
    resources: list[dict],
) -> None:
    """Vérifie que toute propriété définie dans un objet métier est référencée au moins une fois dans une ressource.
    
    Règle : chaque propriété (champ data.name) d'un objet métier doit être référencée
    via business_object_property dans au moins une ressource qui pointe vers cet objet métier.
    """
    bo_by_id = index_by_id(business_objects, "objet métier")

    # Collecter toutes les propriétés référencées par les ressources
    # Structure: { business_object_id: { property_name1, property_name2, ... } }
    referenced_properties: dict[str, set[str]] = {}

    for resource in resources:
        business_object_id = resource.get("business_object")
        if not business_object_id:
            continue

        data = resource.get("data", []) or []
        for field in data:
            if not isinstance(field, dict):
                continue
            bo_prop = field.get("business_object_property")
            if bo_prop:
                if business_object_id not in referenced_properties:
                    referenced_properties[business_object_id] = set()
                referenced_properties[business_object_id].add(bo_prop)

    # Vérifier que chaque propriété de chaque objet métier est référencée
    for bo in business_objects:
        src = bo.get("_source", "?")
        bo_id = bo.get("id")
        if not bo_id:
            continue

        data = bo.get("data", []) or []
        bo_referenced_props = referenced_properties.get(bo_id, set())

        for field in data:
            if not isinstance(field, dict):
                continue
            field_name = field.get("name")
            if not field_name:
                continue

            if field_name not in bo_referenced_props:
                error(
                    f"[{src}] {bo_id}: propriété '{field_name}' non référencée "
                    f"par aucune ressource (via business_object_property)"
                )


def _extract_list_of_ids(value: object, src: str, pid: str, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        error(f"[{src}] {pid}: champ '{field_name}' invalide (liste attendue)")
        return []

    ids: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            error(
                f"[{src}] {pid}: {field_name}[{idx}] invalide "
                f"(chaîne non vide attendue)"
            )
            continue
        ids.append(item.strip())
    return ids


def _validate_capability_refs(
    processes: list[dict],
    cap_by_id: dict[str, dict],
    process_kind: str,
) -> None:
    for process in processes:
        src = process.get("_source", "?")
        pid = process.get("id", "<sans-id>")

        cap_refs: list[str] = []

        parent_capability = process.get("parent_capability")
        if isinstance(parent_capability, str) and parent_capability.strip():
            cap_refs.append(parent_capability.strip())

        decision_point = process.get("decision_point")
        if isinstance(decision_point, str) and decision_point.strip():
            cap_refs.append(decision_point.strip())

        cap_refs.extend(
            _extract_list_of_ids(
                process.get("internal_capabilities"),
                src,
                pid,
                "internal_capabilities",
            )
        )

        for chain_key in ["event_capability_chain"]:
            chain = process.get(chain_key)
            if chain is None:
                continue
            if not isinstance(chain, list):
                error(f"[{src}] {pid}: champ '{chain_key}' invalide (liste attendue)")
                continue
            for idx, step in enumerate(chain):
                if not isinstance(step, dict):
                    error(
                        f"[{src}] {pid}: {chain_key}[{idx}] invalide "
                        f"(mapping attendu)"
                    )
                    continue
                step_cap = step.get("capability")
                if isinstance(step_cap, str) and step_cap.strip():
                    cap_refs.append(step_cap.strip())

        for cap_id in cap_refs:
            if cap_id not in cap_by_id:
                error(
                    f"[{src}] {pid}: capacité '{cap_id}' introuvable "
                    f"(processus {process_kind})"
                )


def _collect_event_refs_from_chain(
    process: dict,
    src: str,
    pid: str,
    chain_key: str,
    single_in_key: str,
    single_out_key: str,
    multi_in_key: str,
    multi_out_key: str,
) -> list[str]:
    event_refs: list[str] = []

    chain = process.get(chain_key)
    if chain is None:
        return event_refs

    if not isinstance(chain, list):
        error(f"[{src}] {pid}: champ '{chain_key}' invalide (liste attendue)")
        return event_refs

    for idx, step in enumerate(chain):
        if not isinstance(step, dict):
            error(f"[{src}] {pid}: {chain_key}[{idx}] invalide (mapping attendu)")
            continue

        for key in [single_in_key, single_out_key]:
            value = step.get(key)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                error(
                    f"[{src}] {pid}: {chain_key}[{idx}].{key} invalide "
                    f"(chaîne non vide attendue)"
                )
                continue
            event_refs.append(value.strip())

        for key in [multi_in_key, multi_out_key]:
            values = step.get(key)
            if values is None:
                continue
            event_refs.extend(
                _extract_list_of_ids(values, src, pid, f"{chain_key}[{idx}].{key}")
            )

    return event_refs


def _validate_process_documentation(process: dict, process_kind: str) -> None:
    """Valide la complétude de la section documentation d'un processus externe."""
    src = process.get("_source", "?")
    pid = process.get("id", "<sans-id>")

    documentation = process.get("documentation")
    if not isinstance(documentation, dict):
        error(f"[{src}] {pid}: champ 'documentation' obligatoire (mapping attendu)")
        return

    common_required_fields = [
        "objectif",
        "portee",
        "parties_prenantes",
        "preconditions",
        "postconditions",
        "scenarios",
        "indicateurs_suivi",
    ]

    kind_specific_field = "valeur_metier" if process_kind == "métier" else "valeur_operationnelle"
    required_fields = [*common_required_fields, kind_specific_field]

    for field in required_fields:
        value = documentation.get(field)
        if value is None:
            error(f"[{src}] {pid}: documentation.{field} obligatoire")
            continue

        if isinstance(value, str):
            if not value.strip():
                error(f"[{src}] {pid}: documentation.{field} invalide (chaîne non vide attendue)")
        elif isinstance(value, list):
            if not value:
                error(f"[{src}] {pid}: documentation.{field} invalide (liste non vide attendue)")
            else:
                for idx, item in enumerate(value):
                    if not isinstance(item, str) or not item.strip():
                        error(
                            f"[{src}] {pid}: documentation.{field}[{idx}] invalide "
                            f"(chaîne non vide attendue)"
                        )
        elif isinstance(value, dict):
            # contrôles détaillés plus bas sur portee / scenarios
            pass
        else:
            error(
                f"[{src}] {pid}: documentation.{field} invalide "
                f"(chaîne, liste ou mapping attendu)"
            )

    portee = documentation.get("portee")
    if isinstance(portee, dict):
        for subfield in ["inclut", "exclut"]:
            subvalue = portee.get(subfield)
            if not isinstance(subvalue, list) or not subvalue:
                error(
                    f"[{src}] {pid}: documentation.portee.{subfield} invalide "
                    f"(liste non vide attendue)"
                )
                continue
            for idx, item in enumerate(subvalue):
                if not isinstance(item, str) or not item.strip():
                    error(
                        f"[{src}] {pid}: documentation.portee.{subfield}[{idx}] invalide "
                        f"(chaîne non vide attendue)"
                    )
    elif portee is not None:
        error(f"[{src}] {pid}: documentation.portee invalide (mapping attendu)")

    scenarios = documentation.get("scenarios")
    if isinstance(scenarios, dict):
        for subfield in ["nominal", "alternatif"]:
            subvalue = scenarios.get(subfield)
            if not isinstance(subvalue, str) or not subvalue.strip():
                error(
                    f"[{src}] {pid}: documentation.scenarios.{subfield} invalide "
                    f"(chaîne non vide attendue)"
                )
    elif scenarios is not None:
        error(f"[{src}] {pid}: documentation.scenarios invalide (mapping attendu)")


def validate_external_processes(
    caps: list[dict],
    business_events: list[dict],
    resource_events: list[dict],
    business_subscriptions: list[dict],
    resource_subscriptions: list[dict],
    business_processes: list[dict],
    resource_processes: list[dict],
) -> None:
    cap_by_id = {c.get("id"): c for c in caps if isinstance(c.get("id"), str)}
    be_by_id = {e.get("id"): e for e in business_events if isinstance(e.get("id"), str)}
    re_by_id = {e.get("id"): e for e in resource_events if isinstance(e.get("id"), str)}
    bs_by_id = {s.get("id"): s for s in business_subscriptions if isinstance(s.get("id"), str)}
    rs_by_id = {s.get("id"): s for s in resource_subscriptions if isinstance(s.get("id"), str)}

    _validate_capability_refs(business_processes, cap_by_id, "métier")
    _validate_capability_refs(resource_processes, cap_by_id, "ressource")

    for process in business_processes:
        _validate_process_documentation(process, "métier")

    for process in resource_processes:
        _validate_process_documentation(process, "ressource")

    # Processus métier -> événements métier
    for process in business_processes:
        src = process.get("_source", "?")
        pid = process.get("id", "<sans-id>")
        event_refs: list[str] = []
        subscription_refs: list[str] = []

        for field in ["entry_event", "triggering_business_event", "derived_business_event"]:
            value = process.get(field)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                error(f"[{src}] {pid}: champ '{field}' invalide (chaîne non vide attendue)")
                continue
            event_refs.append(value.strip())

        start = process.get("start")
        if isinstance(start, dict) and start.get("type") == "event":
            start_event = start.get("event")
            if isinstance(start_event, str) and start_event.strip():
                event_refs.append(start_event.strip())
            elif start_event is not None:
                error(f"[{src}] {pid}: start.event invalide (chaîne non vide attendue)")

        business_assets = process.get("business_assets")
        if isinstance(business_assets, dict):
            event_refs.extend(
                _extract_list_of_ids(
                    business_assets.get("evenements_metier"),
                    src,
                    pid,
                    "business_assets.evenements_metier",
                )
            )
            subscription_refs.extend(
                _extract_list_of_ids(
                    business_assets.get("abonnements_metier"),
                    src,
                    pid,
                    "business_assets.abonnements_metier",
                )
            )

        context_filters = process.get("context_filters")
        if isinstance(context_filters, dict):
            tbe = context_filters.get("triggering_business_event")
            if isinstance(tbe, str) and tbe.strip():
                event_refs.append(tbe.strip())

        event_refs.extend(
            _collect_event_refs_from_chain(
                process,
                src,
                pid,
                "event_subscription_chain",
                "consumes_business_event",
                "emits_business_event",
                "consumes_business_events",
                "emits_business_events",
            )
        )

        event_subscription_chain = process.get("event_subscription_chain")
        if isinstance(event_subscription_chain, list):
            for idx, step in enumerate(event_subscription_chain):
                if not isinstance(step, dict):
                    continue
                via_subscription = step.get("via_subscription")
                if via_subscription is None:
                    continue
                if not isinstance(via_subscription, str) or not via_subscription.strip():
                    error(
                        f"[{src}] {pid}: event_subscription_chain[{idx}].via_subscription "
                        f"invalide (chaîne non vide attendue)"
                    )
                    continue
                subscription_refs.append(via_subscription.strip())
        event_refs.extend(
            _collect_event_refs_from_chain(
                process,
                src,
                pid,
                "event_capability_chain",
                "consumes_event",
                "emits_event",
                "consumes_events",
                "emits_events",
            )
        )

        exits_metier = process.get("exits_metier")
        if isinstance(exits_metier, list):
            for idx, exit_item in enumerate(exits_metier):
                if not isinstance(exit_item, dict):
                    error(f"[{src}] {pid}: exits_metier[{idx}] invalide (mapping attendu)")
                    continue
                to_event = exit_item.get("to_business_event")
                if isinstance(to_event, str) and to_event.strip():
                    event_refs.append(to_event.strip())

        for event_id in event_refs:
            if event_id not in be_by_id:
                error(
                    f"[{src}] {pid}: événement métier '{event_id}' introuvable "
                    f"(processus métier)"
                )

        for subscription_id in subscription_refs:
            if subscription_id not in bs_by_id:
                error(
                    f"[{src}] {pid}: abonnement métier '{subscription_id}' introuvable "
                    f"(processus métier)"
                )

    # Processus ressource -> événements ressource
    for process in resource_processes:
        src = process.get("_source", "?")
        pid = process.get("id", "<sans-id>")
        event_refs: list[str] = []
        subscription_refs: list[str] = []

        for field in ["entry_event", "triggering_resource_event", "derived_resource_event"]:
            value = process.get(field)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                error(f"[{src}] {pid}: champ '{field}' invalide (chaîne non vide attendue)")
                continue
            event_refs.append(value.strip())

        start = process.get("start")
        if isinstance(start, dict) and start.get("type") == "event":
            start_event = start.get("event")
            if isinstance(start_event, str) and start_event.strip():
                event_refs.append(start_event.strip())
            elif start_event is not None:
                error(f"[{src}] {pid}: start.event invalide (chaîne non vide attendue)")

        resource_assets = process.get("resource_assets")
        if isinstance(resource_assets, dict):
            event_refs.extend(
                _extract_list_of_ids(
                    resource_assets.get("evenements_ressource"),
                    src,
                    pid,
                    "resource_assets.evenements_ressource",
                )
            )
            subscription_refs.extend(
                _extract_list_of_ids(
                    resource_assets.get("abonnements_ressource"),
                    src,
                    pid,
                    "resource_assets.abonnements_ressource",
                )
            )

        context_filters = process.get("context_filters")
        if isinstance(context_filters, dict):
            tre = context_filters.get("triggering_resource_event")
            dre = context_filters.get("derived_resource_event")
            if isinstance(tre, str) and tre.strip():
                event_refs.append(tre.strip())
            if isinstance(dre, str) and dre.strip():
                event_refs.append(dre.strip())

        event_refs.extend(
            _collect_event_refs_from_chain(
                process,
                src,
                pid,
                "event_subscription_chain",
                "consumes_resource_event",
                "emits_resource_event",
                "consumes_resource_events",
                "emits_resource_events",
            )
        )

        event_subscription_chain = process.get("event_subscription_chain")
        if isinstance(event_subscription_chain, list):
            for idx, step in enumerate(event_subscription_chain):
                if not isinstance(step, dict):
                    continue
                via_subscription = step.get("via_subscription")
                if via_subscription is None:
                    continue
                if not isinstance(via_subscription, str) or not via_subscription.strip():
                    error(
                        f"[{src}] {pid}: event_subscription_chain[{idx}].via_subscription "
                        f"invalide (chaîne non vide attendue)"
                    )
                    continue
                subscription_refs.append(via_subscription.strip())
        event_refs.extend(
            _collect_event_refs_from_chain(
                process,
                src,
                pid,
                "event_capability_chain",
                "consumes_event",
                "emits_event",
                "consumes_events",
                "emits_events",
            )
        )

        exits_ressource = process.get("exits_ressource")
        if isinstance(exits_ressource, list):
            for idx, exit_item in enumerate(exits_ressource):
                if not isinstance(exit_item, dict):
                    error(f"[{src}] {pid}: exits_ressource[{idx}] invalide (mapping attendu)")
                    continue
                to_event = exit_item.get("to_resource_event")
                if isinstance(to_event, str) and to_event.strip():
                    event_refs.append(to_event.strip())

        for event_id in event_refs:
            if event_id not in re_by_id:
                error(
                    f"[{src}] {pid}: événement ressource '{event_id}' introuvable "
                    f"(processus ressource)"
                )

        for subscription_id in subscription_refs:
            if subscription_id not in rs_by_id:
                error(
                    f"[{src}] {pid}: abonnement ressource '{subscription_id}' introuvable "
                    f"(processus ressource)"
                )


# ──────────────────────────────────────────────────────────────
# Validation ciblée d'un objet métier
# ──────────────────────────────────────────────────────────────


def validate_single_business_object(
    bo_id: str,
    business_objects: list[dict],
    business_events: list[dict],
    resources: list[dict],
    caps: list[dict],
) -> None:
    """Valide un objet métier spécifique et affiche un rapport détaillé."""
    bo_by_id = {o.get("id"): o for o in business_objects if o.get("id")}
    be_by_id = {e.get("id"): e for e in business_events if e.get("id")}
    cap_by_id = {c.get("id"): c for c in caps if c.get("id")}

    if bo_id not in bo_by_id:
        print(f"[FATAL] Objet métier '{bo_id}' introuvable.")
        print(f"\nObjets métier disponibles :")
        for oid in sorted(bo_by_id.keys()):
            print(f"  • {oid}")
        sys.exit(1)

    bo = bo_by_id[bo_id]
    src = bo.get("_source", "?")

    print(f"\n{'='*70}")
    print(f"VALIDATION OBJET MÉTIER : {bo_id}")
    print(f"{'='*70}")

    # Informations générales
    print(f"\n## Informations générales")
    print(f"  Nom           : {bo.get('name', '?')}")
    print(f"  Source        : {src}")
    print(f"  Definition    : {bo.get('definition', '?')[:80]}..." if len(bo.get('definition', '')) > 80 else f"  Definition    : {bo.get('definition', '?')}")

    # Capability émettrice
    emitting_cap = bo.get("emitting_capability")
    print(f"\n## Capability émettrice")
    if emitting_cap:
        if emitting_cap in cap_by_id:
            cap = cap_by_id[emitting_cap]
            print(f"  [✓] {emitting_cap} ({cap.get('name', '?')}) - Level {cap.get('level', '?')}")
        else:
            print(f"  [✗] {emitting_cap} - INTROUVABLE")
            error(f"[{src}] {bo_id}: emitting_capability '{emitting_cap}' introuvable")
    else:
        print(f"  [✗] Non définie")
        error(f"[{src}] {bo_id}: champ 'emitting_capability' obligatoire")

    # Propriétés de l'objet métier
    data = bo.get("data", []) or []
    print(f"\n## Propriétés ({len(data)})")

    # Collecter les références depuis les ressources
    referencing_resources: dict[str, list[str]] = {}  # property_name -> [resource_ids]
    for resource in resources:
        if resource.get("business_object") != bo_id:
            continue
        res_id = resource.get("id", "?")
        res_data = resource.get("data", []) or []
        for field in res_data:
            if not isinstance(field, dict):
                continue
            bo_prop = field.get("business_object_property")
            if bo_prop:
                if bo_prop not in referencing_resources:
                    referencing_resources[bo_prop] = []
                referencing_resources[bo_prop].append(res_id)

    for field in data:
        if not isinstance(field, dict):
            continue
        field_name = field.get("name", "?")
        field_type = field.get("type", "?")
        field_required = "•" if field.get("required") else "◦"
        refs = referencing_resources.get(field_name, [])
        if refs:
            print(f"  {field_required} {field_name} ({field_type}) [✓ {len(refs)} ref(s)]")
        else:
            print(f"  {field_required} {field_name} ({field_type}) [⚠ non référencée]")
            warn(f"[{src}] {bo_id}: propriété '{field_name}' non référencée")

    # Ressources qui implémentent cet objet métier
    implementing_resources = [r for r in resources if r.get("business_object") == bo_id]
    print(f"\n## Ressources implémentant cet objet métier ({len(implementing_resources)})")
    for res in implementing_resources:
        res_id = res.get("id", "?")
        res_name = res.get("name", "?")
        res_data = res.get("data", []) or []
        mapped_props = sum(1 for f in res_data if isinstance(f, dict) and f.get("business_object_property"))
        print(f"  • {res_id}")
        print(f"    Nom : {res_name}")
        print(f"    Propriétés mappées : {mapped_props}/{len(data)}")

    if not implementing_resources:
        print(f"  [⚠] Aucune ressource n'implémente cet objet métier")
        warn(f"[{src}] {bo_id}: aucune ressource ne référence cet objet métier")

    # Résumé
    print(f"\n{'='*70}")
    print(f"RÉSUMÉ")
    print(f"{'='*70}")

    props_covered = sum(1 for p in data if isinstance(p, dict) and p.get("name") in referencing_resources)
    total_props = len([p for p in data if isinstance(p, dict) and p.get("name")])
    coverage = (props_covered / total_props * 100) if total_props > 0 else 0

    print(f"  Propriétés          : {total_props}")
    print(f"  Propriétés couvertes: {props_covered} ({coverage:.0f}%)")
    print(f"  Ressources         : {len(implementing_resources)}")
    print(f"  Warnings           : {len(warnings)}")
    print(f"  Erreurs            : {len(errors)}")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validation structurelle du référentiel BCM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--business-object", "-o",
        metavar="ID",
        help="Valider un objet métier spécifique (ex: OBJ.COEUR.005.DECLARATION_SINISTRE)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Mode strict: tout warning est traité comme une erreur bloquante",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vocab = load_vocab()

    caps, files = load_all_capabilities()
    if not files:
        print(f"[FATAL] Aucun fichier capabilities-*.yaml dans {BCM_DIR}")
        sys.exit(1)

    business_events, business_event_files = load_assets("business-event-*.yaml", "business_events")
    business_objects, business_object_files = load_assets("business-object-*.yaml", "resources")
    resource_events, resource_event_files = load_assets("resource-event-*.yaml", "resource_events")
    resources, resource_files = load_assets("resource-*.yaml", "resources")
    business_subscriptions, business_subscription_files = load_assets(
        "business-subscription-*.yaml",
        "business_subscriptions",
    )
    resource_subscriptions, resource_subscription_files = load_assets(
        "resource-subscription-*.yaml",
        "resource_subscriptions",
    )
    business_processes, business_process_files = load_external_processes(
        PROCESSUS_METIER_DIR,
        "processus_metier",
    )
    resource_processes, resource_process_files = load_external_processes(
        PROCESSUS_RESSOURCE_DIR,
        "processus_ressource",
    )

    # Mode validation d'un objet métier spécifique
    if args.business_object:
        validate_single_business_object(
            args.business_object,
            business_objects,
            business_events,
            resources,
            caps,
        )
        promote_warnings_to_errors_if_needed(args.strict)
        # Afficher les erreurs/warnings
        if warnings:
            print(f"\n")
            for w in warnings:
                print(f"[WARN] {w}")
        if errors:
            print(f"\n[FAIL] {len(errors)} erreur(s) détectée(s) :\n")
            for e in errors:
                print(f"  ✗ {e}")
            sys.exit(1)
        else:
            print(f"\n[OK] Validation de l'objet métier '{args.business_object}' réussie.")
        return

    # Mode validation complète
    print(f"[INFO] Fichiers chargés :")
    for f in files:
        n = sum(1 for c in caps if c.get("_source") == f.name)
        print(f"  • {f.name}: {n} capacité(s)")

    loaded_evts_files = (
        business_event_files
        + business_object_files
        + resource_event_files
        + resource_files
        + business_subscription_files
        + resource_subscription_files
    )
    if loaded_evts_files:
        print(f"[INFO] Assets evts chargés :")
        for f in loaded_evts_files:
            rel_source = str(f.relative_to(ASSETS_DIR))
            if f in business_event_files:
                n = sum(1 for e in business_events if e.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} événement(s) métier")
            elif f in business_object_files:
                n = sum(1 for o in business_objects if o.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} objet(s) métier")
            elif f in resource_event_files:
                n = sum(1 for e in resource_events if e.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} événement(s) ressource")
            elif f in business_subscription_files:
                n = sum(1 for s in business_subscriptions if s.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} abonnement(s) métier")
            elif f in resource_subscription_files:
                n = sum(1 for s in resource_subscriptions if s.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} abonnement(s) ressource")
            else:
                n = sum(1 for r in resources if r.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} ressource(s)")
    else:
        warn("Aucun fichier evts non-template chargé (contrôles cross-assets ignorés)")

    loaded_process_files = business_process_files + resource_process_files
    if loaded_process_files:
        print(f"[INFO] Processus externes chargés :")
        for f in loaded_process_files:
            rel_source = str(f.relative_to(ROOT))
            if f in business_process_files:
                n = sum(1 for p in business_processes if p.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} processus métier")
            else:
                n = sum(1 for p in resource_processes if p.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} processus ressource")

    validate_templates()

    validate(caps, vocab)
    validate_cross_assets(caps, business_events, business_objects, resource_events, resources)
    validate_business_subscriptions(caps, business_events, business_subscriptions)
    validate_resource_subscriptions(caps, business_subscriptions, resource_events, resource_subscriptions)
    validate_business_object_properties_coverage(business_objects, resources)
    validate_external_processes(
        caps,
        business_events,
        resource_events,
        business_subscriptions,
        resource_subscriptions,
        business_processes,
        resource_processes,
    )

    promote_warnings_to_errors_if_needed(args.strict)

    # ── Rapport ─────────────────────────────────────────────
    if warnings:
        for w in warnings:
            print(f"[WARN] {w}")

    if errors:
        print(f"\n[FAIL] {len(errors)} erreur(s) détectée(s) :\n")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)

    total_l1 = sum(1 for c in caps if c.get("level") == "L1")
    total_l2 = sum(1 for c in caps if c.get("level") == "L2")
    total_l3 = sum(1 for c in caps if c.get("level") == "L3")

    parts = [f"{total_l1} L1"]
    if total_l2:
        parts.append(f"{total_l2} L2")
    if total_l3:
        parts.append(f"{total_l3} L3")

    print(
        f"\n[OK] Validation réussie — {len(caps)} capacités "
        f"({', '.join(parts)}) dans {len(files)} fichier(s)"
    )


if __name__ == "__main__":
    main()
