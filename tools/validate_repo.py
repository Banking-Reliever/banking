#!/usr/bin/env python3
"""
validate_repo.py — Structural validation of the BCM repository.

Checks:
  1. Presence of vocab.yaml file
  2. Presence of at least one capabilities-*.yaml file in bcm/
  3. Uniqueness of capability identifiers (across all files)
  4. Validity of level and zoning fields against vocab.yaml
  5. Parent rules:
     - an L1 must NOT have a parent field
     - an L2+ MUST have a parent
     - the referenced parent MUST exist in the set of loaded capabilities
     - the parent of an L2 must be an L1; the parent of an L3 must be an L2
  6. Optional heatmap checks
      7. Cross-asset rules (evts/):
         - a business event must be emitted by a capability of level L2 or L3
         - a business event must reference a business object
         - a resource event must reference a resource and exactly one business event (`business_event`)
            - the referenced business event and the carried resource of a resource event must point to the same business object
         - a resource must reference a business object
                 - a business subscription must reference an existing business event with the correct version
             - a resource subscription must reference an existing and coherent resource event
             - a resource subscription must reference an existing and coherent business subscription
             - every business subscription must be referenced by at least one resource subscription
  8. Business object property coverage:
     - every property defined in a business object must be referenced
       via business_object_property in at least one resource
    9. L2/L3 coherence of business objects:
         - if an L2 capability has L3 capabilities, every business object referencing this L2
             must declare emitting_capability_L3 (non-empty list)
         - each capability listed in emitting_capability_L3 must be an existing L3
             whose parent is the referenced L2

Usage:
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
            error(f"[templates] template file not found: {template_path.relative_to(ROOT)}")
            continue

        try:
            data = yaml.safe_load(template_path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            error(f"[templates] unable to parse {template_path.relative_to(ROOT)}: {exc}")
            continue

        meta = data.get("meta")
        if not isinstance(meta, dict):
            error(f"[templates] {template_path.name}: 'meta' field missing or invalid")
            continue

        template_version = meta.get("template_version")
        if not isinstance(template_version, str) or not template_version.strip():
            error(
                f"[templates] {template_path.name}: 'meta.template_version' field required "
                f"(expected format: x.y.z)"
            )
            continue

        if not semver_pattern.match(template_version.strip()):
            error(
                f"[templates] {template_path.name}: meta.template_version '{template_version}' "
                f"invalid (expected format: x.y.z)"
            )


# ──────────────────────────────────────────────────────────────
# Chargement
# ──────────────────────────────────────────────────────────────


def load_vocab() -> dict:
    if not VOCAB_FILE.exists():
        print(f"[FATAL] File not found: {VOCAB_FILE}")
        sys.exit(1)
    return yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))


def load_all_capabilities() -> tuple[list[dict], list[Path]]:
    """Loads all capabilities from bcm/capabilities-*.yaml."""
    caps: list[dict] = []
    files: list[Path] = []
    for f in sorted(BCM_DIR.glob("capabilities-*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        file_caps = data.get("capabilities", [])
        # Add a _source field for reporting
        for c in file_caps:
            c["_source"] = f.name
        caps.extend(file_caps)
        files.append(f)
    return caps, files


def load_assets(pattern: str, key: str) -> tuple[list[dict], list[Path]]:
    """Loads YAML assets from bcm/ (including subdirectories)."""
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
            error(f"[{rel_source}] Field '{key}' invalid (list expected)")
            files.append(f)
            continue

        for item in file_items:
            if isinstance(item, dict):
                item["_source"] = rel_source
                items.append(item)
            else:
                error(f"[{rel_source}] Invalid entry in '{key}' (mapping expected)")

        files.append(f)

    return items, files


def load_external_processes(process_dir: Path, root_key: str) -> tuple[list[dict], list[Path]]:
    """Loads external processes (business or resource)."""
    items: list[dict] = []
    files: list[Path] = []

    if not process_dir.exists():
        return items, files

    for f in sorted(process_dir.rglob("*.yaml")):
        rel_source = str(f.relative_to(ROOT))
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            error(f"[{rel_source}] unable to parse file: {exc}")
            files.append(f)
            continue

        if not isinstance(data, dict):
            error(f"[{rel_source}] invalid YAML content (root mapping expected)")
            files.append(f)
            continue

        process_item = data.get(root_key)
        if not isinstance(process_item, dict):
            error(f"[{rel_source}] root field '{root_key}' missing or invalid")
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

    # ── Pass 1: individual fields ────────────────────────
    for c in caps:
        src = c.get("_source", "?")
        cid = c.get("id")

        if not cid:
            error(f"[{src}] Capability without 'id' field")
            continue

        if cid in ids:
            error(f"[{src}] Duplicate identifier: {cid}")
        ids.add(cid)
        by_id[cid] = c

        lvl = c.get("level")
        if lvl not in levels:
            error(f"[{src}] {cid}: level '{lvl}' invalid (expected: {sorted(levels)})")

        zon = c.get("zoning")
        if zon not in zonings:
            error(f"[{src}] {cid}: zoning '{zon}' invalid (expected: {sorted(zonings)})")

        # Parent rules by level
        if lvl == "L1":
            if "parent" in c:
                error(f"[{src}] {cid}: an L1 must not have a 'parent' field")
        else:
            parent = c.get("parent")
            if not parent:
                error(f"[{src}] {cid}: level {lvl} must have a 'parent' field")

        # Optional heatmap
        hm = c.get("heatmap", {})
        if hm and "maturity" in hm:
            allowed = set(vocab.get("heatmap_scales", {}).get("maturity", []))
            if allowed and hm["maturity"] not in allowed:
                error(
                    f"[{src}] {cid}: maturity '{hm['maturity']}' "
                    f"invalid (expected: {sorted(allowed)})"
                )

    # ── Pass 2: parent existence and coherence ────────
    for c in caps:
        cid = c.get("id")
        if not cid:
            continue
        lvl = c.get("level")
        if lvl == "L1":
            continue

        parent_id = c.get("parent")
        if not parent_id:
            continue  # already reported in pass 1

        src = c.get("_source", "?")

        if parent_id not in by_id:
            error(
                f"[{src}] {cid}: parent '{parent_id}' not found "
                f"in the set of loaded capabilities"
            )
            continue

        # Verify that the parent level is coherent
        expected_parent_level = LEVEL_HIERARCHY.get(lvl)
        if expected_parent_level:
            actual_parent_level = by_id[parent_id].get("level")
            if actual_parent_level != expected_parent_level:
                error(
                    f"[{src}] {cid} (level {lvl}): parent '{parent_id}' "
                    f"has level '{actual_parent_level}', "
                    f"expected '{expected_parent_level}'"
                )


def index_by_id(items: list[dict], kind: str) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for item in items:
        src = item.get("_source", "?")
        iid = item.get("id")
        if not iid:
            error(f"[{src}] {kind} without 'id' field")
            continue
        if iid in indexed:
            error(f"[{src}] Duplicate identifier ({kind}): {iid}")
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
    """Reads a 1-n relation (new format) with fallback to the old 1-1 format."""
    relation_ids: list[str] = []

    if plural_key in item:
        raw_value = item.get(plural_key)
        if not isinstance(raw_value, list):
            error(f"[{src}] {item_id}: field '{plural_key}' invalid (list expected)")
            return []
        if not raw_value:
            error(f"[{src}] {item_id}: field '{plural_key}' required (non-empty list expected)")
            return []

        for idx, rel_id in enumerate(raw_value):
            if not isinstance(rel_id, str) or not rel_id.strip():
                error(
                    f"[{src}] {item_id}: {plural_key}[{idx}] invalid "
                    f"(non-empty string expected)"
                )
                continue
            relation_ids.append(rel_id.strip())

        return relation_ids

    legacy_value = item.get(singular_key)
    if legacy_value:
        if not isinstance(legacy_value, str) or not legacy_value.strip():
            error(f"[{src}] {item_id}: field '{singular_key}' invalid (non-empty string expected)")
            return []
        warn(
            f"[{src}] {item_id}: legacy field '{singular_key}' detected; "
            f"prefer '{plural_key}' (list)"
        )
        return [legacy_value.strip()]

    error(
        f"[{src}] {item_id}: field '{plural_key}' required "
        f"(or '{singular_key}' in legacy) for {label}"
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
            f"[{src}] {item_id}: field '{plural_key}' forbidden "
            f"(cardinality 1 expected, use '{singular_key}')"
        )

    value = item.get(singular_key)
    if not isinstance(value, str) or not value.strip():
        error(
            f"[{src}] {item_id}: field '{singular_key}' required "
            f"(non-empty string expected) for {label}"
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

    be_by_id = index_by_id(business_events, "business event")
    bo_by_id = index_by_id(business_objects, "business object")
    re_by_id = index_by_id(resource_events, "resource event")
    rs_by_id = index_by_id(resources, "resource")

    # 1) Business event: L2/L3 capability + business object
    for event in business_events:
        src = event.get("_source", "?")
        eid = event.get("id", "<no-id>")

        version = event.get("version")
        if not version:
            error(f"[{src}] {eid}: 'version' field required")

        emitting_capability = event.get("emitting_capability")
        if not emitting_capability:
            error(f"[{src}] {eid}: 'emitting_capability' field required")
        elif emitting_capability not in cap_by_id:
            error(f"[{src}] {eid}: emitting_capability '{emitting_capability}' not found")
        else:
            cap_level = cap_by_id[emitting_capability].get("level")
            if cap_level not in {"L2", "L3"}:
                error(
                    f"[{src}] {eid}: emitting_capability '{emitting_capability}' "
                    f"must be level L2 or L3 (current: {cap_level})"
                )

        carried_business_object = event.get("carried_business_object")
        if not carried_business_object:
            error(f"[{src}] {eid}: 'carried_business_object' field required")
        elif carried_business_object not in bo_by_id:
            error(
                f"[{src}] {eid}: business object '{carried_business_object}' not found "
                f"in business-object-*.yaml"
            )

    # 1 bis) Business object: must not reference a business event
    for obj in business_objects:
        src = obj.get("_source", "?")
        oid = obj.get("id", "<no-id>")

        emitting_capability = obj.get("emitting_capability")
        if isinstance(emitting_capability, str) and emitting_capability in cap_by_id:
            children_l3 = l3_children_by_l2.get(emitting_capability, set())
            has_l3_field = "emitting_capability_L3" in obj

            if children_l3:
                if not has_l3_field:
                    error(
                        f"[{src}] {oid}: 'emitting_capability_L3' field required because "
                        f"L2 capability '{emitting_capability}' has L3 capabilities"
                    )
                else:
                    raw_l3_list = obj.get("emitting_capability_L3")
                    if not isinstance(raw_l3_list, list):
                        error(
                            f"[{src}] {oid}: 'emitting_capability_L3' field invalid "
                            f"(list expected)"
                        )
                    elif not raw_l3_list:
                        error(
                            f"[{src}] {oid}: 'emitting_capability_L3' field required "
                            f"(non-empty list expected)"
                        )
                    else:
                        seen_l3: set[str] = set()
                        for idx, l3_id in enumerate(raw_l3_list):
                            if not isinstance(l3_id, str) or not l3_id.strip():
                                error(
                                    f"[{src}] {oid}: emitting_capability_L3[{idx}] invalid "
                                    f"(non-empty string expected)"
                                )
                                continue

                            l3_id = l3_id.strip()
                            if l3_id in seen_l3:
                                error(
                                    f"[{src}] {oid}: emitting_capability_L3 contains a "
                                    f"duplicate ('{l3_id}')"
                                )
                                continue
                            seen_l3.add(l3_id)

                            referenced_cap = cap_by_id.get(l3_id)
                            if not referenced_cap:
                                error(
                                    f"[{src}] {oid}: emitting_capability_L3 '{l3_id}' not found"
                                )
                                continue

                            if referenced_cap.get("level") != "L3":
                                error(
                                    f"[{src}] {oid}: emitting_capability_L3 '{l3_id}' must "
                                    f"reference a level L3 capability"
                                )
                                continue

                            l3_parent = referenced_cap.get("parent")
                            if l3_parent != emitting_capability:
                                error(
                                    f"[{src}] {oid}: emitting_capability_L3 '{l3_id}' references "
                                    f"L2 '{l3_parent}', expected '{emitting_capability}'"
                                )
            elif has_l3_field:
                error(
                    f"[{src}] {oid}: 'emitting_capability_L3' field forbidden because "
                    f"L2 capability '{emitting_capability}' has no L3 capabilities"
                )

        if "emitting_business_event" in obj:
            error(
                f"[{src}] {oid}: 'emitting_business_event' field forbidden. "
                f"The relation must be carried by the business event via 'carried_business_object'."
            )

        if "emitting_business_events" in obj:
            error(
                f"[{src}] {oid}: 'emitting_business_events' field forbidden. "
                f"The relation must be carried by the business event via 'carried_business_object'."
            )

    # 2) Resource event: resource reference + exactly one business event
    for event in resource_events:
        src = event.get("_source", "?")
        eid = event.get("id", "<no-id>")

        carried_resource = event.get("carried_resource")
        data = event.get("data")
        if carried_resource and data:
            error(f"[{src}] {eid}: 'carried_resource' and 'data' fields are mutually exclusive")
        elif not carried_resource and not data:
            error(f"[{src}] {eid}: one of 'carried_resource' or 'data' fields must be provided")
        elif carried_resource and carried_resource not in rs_by_id:
            error(
                f"[{src}] {eid}: resource '{carried_resource}' not found "
                f"in resource-*.yaml"
            )

        business_event = collect_single_relation_id(
            event,
            "business_event",
            "business_events",
            src,
            eid,
            "the business event linked to the resource event",
        )
        if business_event and business_event not in be_by_id:
            error(
                f"[{src}] {eid}: business event '{business_event}' not found "
                f"in business-event-*.yaml"
            )

        # Business coherence: the carried resource and the linked business event
        # must converge toward the same business object.
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
                    f"[{src}] {eid}: business object mismatch between "
                    f"carried_resource '{carried_resource}' (business_object='{resource_business_object}') "
                    f"and business_event '{business_event}' (carried_business_object='{event_business_object}')"
                )

    # 3) Resource: business object reference
    for resource in resources:
        src = resource.get("_source", "?")
        rid = resource.get("id", "<no-id>")

        business_object = resource.get("business_object")
        if not business_object:
            error(f"[{src}] {rid}: 'business_object' field required")
        elif business_object not in bo_by_id:
            error(
                f"[{src}] {rid}: business object '{business_object}' not found "
                f"in business-object-*.yaml"
            )


def validate_business_subscriptions(
    caps: list[dict],
    business_events: list[dict],
    business_subscriptions: list[dict],
) -> None:
    cap_by_id = {c.get("id"): c for c in caps if c.get("id")}
    be_by_id = index_by_id(business_events, "business event")

    for sub in business_subscriptions:
        src = sub.get("_source", "?")
        sid = sub.get("id", "<sans-id>")

        consumer_capability = sub.get("consumer_capability")
        if not consumer_capability:
            error(f"[{src}] {sid}: field 'consumer_capability' required")
        elif consumer_capability not in cap_by_id:
            error(f"[{src}] {sid}: consumer_capability '{consumer_capability}' not found")
        else:
            cap_level = cap_by_id[consumer_capability].get("level")
            if cap_level not in {"L2", "L3"}:
                error(
                    f"[{src}] {sid}: consumer_capability '{consumer_capability}' "
                    f"must be level L2 or L3 (current: {cap_level})"
                )

        subscribed_event = sub.get("subscribed_event")
        if not isinstance(subscribed_event, dict):
            error(f"[{src}] {sid}: field 'subscribed_event' required (mapping expected)")
            continue

        event_id = subscribed_event.get("id")
        if not event_id:
            error(f"[{src}] {sid}: subscribed_event.id required")
            continue

        if event_id not in be_by_id:
            error(
                f"[{src}] {sid}: subscribed_event.id '{event_id}' not found "
                f"in business-event-*.yaml"
            )
            continue

        expected_event = be_by_id[event_id]

        subscribed_version = subscribed_event.get("version")
        if not subscribed_version:
            error(f"[{src}] {sid}: subscribed_event.version required")
        else:
            expected_version = expected_event.get("version")
            if subscribed_version != expected_version:
                error(
                    f"[{src}] {sid}: subscribed_event.version '{subscribed_version}' "
                    f"differs from the business event version '{expected_version}'"
                )

        emitting_capability = subscribed_event.get("emitting_capability")
        if not emitting_capability:
            error(f"[{src}] {sid}: subscribed_event.emitting_capability required")
        else:
            expected_emitter = expected_event.get("emitting_capability")
            if emitting_capability != expected_emitter:
                error(
                    f"[{src}] {sid}: subscribed_event.emitting_capability '{emitting_capability}' "
                    f"differs from the business event emitter '{expected_emitter}'"
                )


def validate_resource_subscriptions(
    caps: list[dict],
    business_subscriptions: list[dict],
    resource_events: list[dict],
    resource_subscriptions: list[dict],
) -> None:
    cap_by_id = {c.get("id"): c for c in caps if c.get("id")}
    re_by_id = index_by_id(resource_events, "resource event")
    bs_by_id = index_by_id(business_subscriptions, "business subscription")
    referenced_business_subscriptions: set[str] = set()

    for sub in resource_subscriptions:
        src = sub.get("_source", "?")
        sid = sub.get("id", "<sans-id>")

        consumer_capability = sub.get("consumer_capability")
        if not consumer_capability:
            error(f"[{src}] {sid}: field 'consumer_capability' required")
        elif consumer_capability not in cap_by_id:
            error(f"[{src}] {sid}: consumer_capability '{consumer_capability}' not found")
        else:
            cap_level = cap_by_id[consumer_capability].get("level")
            if cap_level not in {"L2", "L3"}:
                error(
                    f"[{src}] {sid}: consumer_capability '{consumer_capability}' "
                    f"must be level L2 or L3 (current: {cap_level})"
                )

        linked_business_subscription = sub.get("linked_business_subscription")
        if not linked_business_subscription:
            error(f"[{src}] {sid}: field 'linked_business_subscription' required")
            linked_business = None
        elif linked_business_subscription not in bs_by_id:
            error(
                f"[{src}] {sid}: linked_business_subscription '{linked_business_subscription}' not found "
                f"in business-subscription-*.yaml"
            )
            linked_business = None
        else:
            referenced_business_subscriptions.add(linked_business_subscription)
            linked_business = bs_by_id[linked_business_subscription]

            expected_consumer = linked_business.get("consumer_capability")
            if consumer_capability and consumer_capability != expected_consumer:
                error(
                    f"[{src}] {sid}: consumer_capability '{consumer_capability}' "
                    f"differs from the linked business subscription's consumer_capability '{expected_consumer}'"
                )

        subscribed_resource_event = sub.get("subscribed_resource_event")
        if not isinstance(subscribed_resource_event, dict):
            error(f"[{src}] {sid}: field 'subscribed_resource_event' required (mapping expected)")
            continue

        event_id = subscribed_resource_event.get("id")
        if not event_id:
            error(f"[{src}] {sid}: subscribed_resource_event.id required")
            continue

        if event_id not in re_by_id:
            error(
                f"[{src}] {sid}: subscribed_resource_event.id '{event_id}' not found "
                f"in resource-event-*.yaml"
            )
            continue

        expected_event = re_by_id[event_id]

        emitting_capability = subscribed_resource_event.get("emitting_capability")
        if not emitting_capability:
            error(f"[{src}] {sid}: subscribed_resource_event.emitting_capability required")
        else:
            expected_emitter = expected_event.get("emitting_capability")
            if emitting_capability != expected_emitter:
                error(
                    f"[{src}] {sid}: subscribed_resource_event.emitting_capability '{emitting_capability}' "
                    f"differs from the resource event emitter '{expected_emitter}'"
                )

        linked_business_event = subscribed_resource_event.get("linked_business_event")
        if not linked_business_event:
            error(f"[{src}] {sid}: subscribed_resource_event.linked_business_event required")
        else:
            expected_business_event = collect_single_relation_id(
                expected_event,
                "business_event",
                "business_events",
                expected_event.get("_source", "?"),
                expected_event.get("id", "<sans-id>"),
                "the linked business event",
            )
            if expected_business_event and linked_business_event != expected_business_event:
                error(
                    f"[{src}] {sid}: subscribed_resource_event.linked_business_event '{linked_business_event}' "
                    f"differs from the business_event of resource event '{expected_event.get('id', '<sans-id>')}'"
                )

            if linked_business:
                business_subscribed_event = (linked_business.get("subscribed_event") or {}).get("id")
                if business_subscribed_event and linked_business_event != business_subscribed_event:
                    error(
                        f"[{src}] {sid}: linked_business_event '{linked_business_event}' "
                        f"differs from the event of the linked business subscription '{business_subscribed_event}'"
                    )

        if linked_business:
            business_emitter = (linked_business.get("subscribed_event") or {}).get("emitting_capability")
            resource_emitter = subscribed_resource_event.get("emitting_capability")
            if business_emitter and resource_emitter and business_emitter != resource_emitter:
                error(
                    f"[{src}] {sid}: emitting_capability '{resource_emitter}' "
                    f"differs from the linked business subscription's emitter '{business_emitter}'"
                )

    for business_subscription_id in bs_by_id:
        if business_subscription_id not in referenced_business_subscriptions:
            error(
                f"[cross-subscriptions] business subscription '{business_subscription_id}' not referenced "
                f"by any resource subscription"
            )


def validate_business_object_properties_coverage(
    business_objects: list[dict],
    resources: list[dict],
) -> None:
    """Checks that every property defined in a business object is referenced at least once in a resource.

    Rule: each property (data.name field) of a business object must be referenced
    via business_object_property in at least one resource that points to that business object.
    """
    bo_by_id = index_by_id(business_objects, "business object")

    # Collect all properties referenced by resources
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

    # Check that every property of each business object is referenced
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
                    f"[{src}] {bo_id}: property '{field_name}' not referenced "
                    f"by any resource (via business_object_property)"
                )


def _extract_list_of_ids(value: object, src: str, pid: str, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        error(f"[{src}] {pid}: field '{field_name}' invalid (list expected)")
        return []

    ids: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            error(
                f"[{src}] {pid}: {field_name}[{idx}] invalid "
                f"(non-empty string expected)"
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
                error(f"[{src}] {pid}: field '{chain_key}' invalid (list expected)")
                continue
            for idx, step in enumerate(chain):
                if not isinstance(step, dict):
                    error(
                        f"[{src}] {pid}: {chain_key}[{idx}] invalid "
                        f"(mapping expected)"
                    )
                    continue
                step_cap = step.get("capability")
                if isinstance(step_cap, str) and step_cap.strip():
                    cap_refs.append(step_cap.strip())

        for cap_id in cap_refs:
            if cap_id not in cap_by_id:
                error(
                    f"[{src}] {pid}: capability '{cap_id}' not found "
                    f"({process_kind} process)"
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
        error(f"[{src}] {pid}: field '{chain_key}' invalid (list expected)")
        return event_refs

    for idx, step in enumerate(chain):
        if not isinstance(step, dict):
            error(f"[{src}] {pid}: {chain_key}[{idx}] invalid (mapping expected)")
            continue

        for key in [single_in_key, single_out_key]:
            value = step.get(key)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                error(
                    f"[{src}] {pid}: {chain_key}[{idx}].{key} invalid "
                    f"(non-empty string expected)"
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
    """Validates the completeness of the documentation section of an external process."""
    src = process.get("_source", "?")
    pid = process.get("id", "<sans-id>")

    documentation = process.get("documentation")
    if not isinstance(documentation, dict):
        error(f"[{src}] {pid}: field 'documentation' required (mapping expected)")
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

    kind_specific_field = "valeur_metier" if process_kind == "business" else "valeur_operationnelle"
    required_fields = [*common_required_fields, kind_specific_field]

    for field in required_fields:
        value = documentation.get(field)
        if value is None:
            error(f"[{src}] {pid}: documentation.{field} required")
            continue

        if isinstance(value, str):
            if not value.strip():
                error(f"[{src}] {pid}: documentation.{field} invalid (non-empty string expected)")
        elif isinstance(value, list):
            if not value:
                error(f"[{src}] {pid}: documentation.{field} invalid (non-empty list expected)")
            else:
                for idx, item in enumerate(value):
                    if not isinstance(item, str) or not item.strip():
                        error(
                            f"[{src}] {pid}: documentation.{field}[{idx}] invalid "
                            f"(non-empty string expected)"
                        )
        elif isinstance(value, dict):
            # detailed checks below for portee / scenarios
            pass
        else:
            error(
                f"[{src}] {pid}: documentation.{field} invalid "
                f"(string, list, or mapping expected)"
            )

    portee = documentation.get("portee")
    if isinstance(portee, dict):
        for subfield in ["inclut", "exclut"]:
            subvalue = portee.get(subfield)
            if not isinstance(subvalue, list) or not subvalue:
                error(
                    f"[{src}] {pid}: documentation.portee.{subfield} invalid "
                    f"(non-empty list expected)"
                )
                continue
            for idx, item in enumerate(subvalue):
                if not isinstance(item, str) or not item.strip():
                    error(
                        f"[{src}] {pid}: documentation.portee.{subfield}[{idx}] invalid "
                        f"(non-empty string expected)"
                    )
    elif portee is not None:
        error(f"[{src}] {pid}: documentation.portee invalid (mapping expected)")

    scenarios = documentation.get("scenarios")
    if isinstance(scenarios, dict):
        for subfield in ["nominal", "alternatif"]:
            subvalue = scenarios.get(subfield)
            if not isinstance(subvalue, str) or not subvalue.strip():
                error(
                    f"[{src}] {pid}: documentation.scenarios.{subfield} invalid "
                    f"(non-empty string expected)"
                )
    elif scenarios is not None:
        error(f"[{src}] {pid}: documentation.scenarios invalid (mapping expected)")


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

    _validate_capability_refs(business_processes, cap_by_id, "business")
    _validate_capability_refs(resource_processes, cap_by_id, "resource")

    for process in business_processes:
        _validate_process_documentation(process, "business")

    for process in resource_processes:
        _validate_process_documentation(process, "resource")

    # Business processes -> business events
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
                error(f"[{src}] {pid}: field '{field}' invalid (non-empty string expected)")
                continue
            event_refs.append(value.strip())

        start = process.get("start")
        if isinstance(start, dict) and start.get("type") == "event":
            start_event = start.get("event")
            if isinstance(start_event, str) and start_event.strip():
                event_refs.append(start_event.strip())
            elif start_event is not None:
                error(f"[{src}] {pid}: start.event invalid (non-empty string expected)")

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
                        f"invalid (non-empty string expected)"
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
                    error(f"[{src}] {pid}: exits_metier[{idx}] invalid (mapping expected)")
                    continue
                to_event = exit_item.get("to_business_event")
                if isinstance(to_event, str) and to_event.strip():
                    event_refs.append(to_event.strip())

        for event_id in event_refs:
            if event_id not in be_by_id:
                error(
                    f"[{src}] {pid}: business event '{event_id}' not found "
                    f"(business process)"
                )

        for subscription_id in subscription_refs:
            if subscription_id not in bs_by_id:
                error(
                    f"[{src}] {pid}: business subscription '{subscription_id}' not found "
                    f"(business process)"
                )

    # Resource processes -> resource events
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
                error(f"[{src}] {pid}: field '{field}' invalid (non-empty string expected)")
                continue
            event_refs.append(value.strip())

        start = process.get("start")
        if isinstance(start, dict) and start.get("type") == "event":
            start_event = start.get("event")
            if isinstance(start_event, str) and start_event.strip():
                event_refs.append(start_event.strip())
            elif start_event is not None:
                error(f"[{src}] {pid}: start.event invalid (non-empty string expected)")

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
                        f"invalid (non-empty string expected)"
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
                    error(f"[{src}] {pid}: exits_ressource[{idx}] invalid (mapping expected)")
                    continue
                to_event = exit_item.get("to_resource_event")
                if isinstance(to_event, str) and to_event.strip():
                    event_refs.append(to_event.strip())

        for event_id in event_refs:
            if event_id not in re_by_id:
                error(
                    f"[{src}] {pid}: resource event '{event_id}' not found "
                    f"(resource process)"
                )

        for subscription_id in subscription_refs:
            if subscription_id not in rs_by_id:
                error(
                    f"[{src}] {pid}: resource subscription '{subscription_id}' not found "
                    f"(resource process)"
                )


# ──────────────────────────────────────────────────────────────
# Targeted validation of a business object
# ──────────────────────────────────────────────────────────────


def validate_single_business_object(
    bo_id: str,
    business_objects: list[dict],
    business_events: list[dict],
    resources: list[dict],
    caps: list[dict],
) -> None:
    """Validates a specific business object and prints a detailed report."""
    bo_by_id = {o.get("id"): o for o in business_objects if o.get("id")}
    be_by_id = {e.get("id"): e for e in business_events if e.get("id")}
    cap_by_id = {c.get("id"): c for c in caps if c.get("id")}

    if bo_id not in bo_by_id:
        print(f"[FATAL] Business object '{bo_id}' not found.")
        print(f"\nAvailable business objects:")
        for oid in sorted(bo_by_id.keys()):
            print(f"  • {oid}")
        sys.exit(1)

    bo = bo_by_id[bo_id]
    src = bo.get("_source", "?")

    print(f"\n{'='*70}")
    print(f"BUSINESS OBJECT VALIDATION: {bo_id}")
    print(f"{'='*70}")

    # General information
    print(f"\n## General information")
    print(f"  Name          : {bo.get('name', '?')}")
    print(f"  Source        : {src}")
    print(f"  Definition    : {bo.get('definition', '?')[:80]}..." if len(bo.get('definition', '')) > 80 else f"  Definition    : {bo.get('definition', '?')}")

    # Emitting capability
    emitting_cap = bo.get("emitting_capability")
    print(f"\n## Emitting capability")
    if emitting_cap:
        if emitting_cap in cap_by_id:
            cap = cap_by_id[emitting_cap]
            print(f"  [✓] {emitting_cap} ({cap.get('name', '?')}) - Level {cap.get('level', '?')}")
        else:
            print(f"  [✗] {emitting_cap} - NOT FOUND")
            error(f"[{src}] {bo_id}: emitting_capability '{emitting_cap}' not found")
    else:
        print(f"  [✗] Not defined")
        error(f"[{src}] {bo_id}: field 'emitting_capability' required")

    # Business object properties
    data = bo.get("data", []) or []
    print(f"\n## Properties ({len(data)})")

    # Collect references from resources
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
            print(f"  {field_required} {field_name} ({field_type}) [⚠ not referenced]")
            warn(f"[{src}] {bo_id}: property '{field_name}' not referenced")

    # Resources implementing this business object
    implementing_resources = [r for r in resources if r.get("business_object") == bo_id]
    print(f"\n## Resources implementing this business object ({len(implementing_resources)})")
    for res in implementing_resources:
        res_id = res.get("id", "?")
        res_name = res.get("name", "?")
        res_data = res.get("data", []) or []
        mapped_props = sum(1 for f in res_data if isinstance(f, dict) and f.get("business_object_property"))
        print(f"  • {res_id}")
        print(f"    Name: {res_name}")
        print(f"    Mapped properties: {mapped_props}/{len(data)}")

    if not implementing_resources:
        print(f"  [⚠] No resource implements this business object")
        warn(f"[{src}] {bo_id}: no resource references this business object")

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")

    props_covered = sum(1 for p in data if isinstance(p, dict) and p.get("name") in referencing_resources)
    total_props = len([p for p in data if isinstance(p, dict) and p.get("name")])
    coverage = (props_covered / total_props * 100) if total_props > 0 else 0

    print(f"  Properties          : {total_props}")
    print(f"  Covered properties  : {props_covered} ({coverage:.0f}%)")
    print(f"  Resources           : {len(implementing_resources)}")
    print(f"  Warnings            : {len(warnings)}")
    print(f"  Errors              : {len(errors)}")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Structural validation of the BCM repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--business-object", "-o",
        metavar="ID",
        help="Validate a specific business object (e.g.: OBJ.COEUR.005.DECLARATION_SINISTRE)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: every warning is treated as a blocking error",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vocab = load_vocab()

    caps, files = load_all_capabilities()
    if not files:
        print(f"[FATAL] No capabilities-*.yaml file found in {BCM_DIR}")
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

    # Validate a specific business object
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
            print(f"\n[FAIL] {len(errors)} error(s) detected:\n")
            for e in errors:
                print(f"  ✗ {e}")
            sys.exit(1)
        else:
            print(f"\n[OK] Business object '{args.business_object}' validation passed.")
        return

    # Full validation mode
    print(f"[INFO] Loaded files:")
    for f in files:
        n = sum(1 for c in caps if c.get("_source") == f.name)
        print(f"  • {f.name}: {n} capability(ies)")

    loaded_evts_files = (
        business_event_files
        + business_object_files
        + resource_event_files
        + resource_files
        + business_subscription_files
        + resource_subscription_files
    )
    if loaded_evts_files:
        print(f"[INFO] Event assets loaded:")
        for f in loaded_evts_files:
            rel_source = str(f.relative_to(ASSETS_DIR))
            if f in business_event_files:
                n = sum(1 for e in business_events if e.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} business event(s)")
            elif f in business_object_files:
                n = sum(1 for o in business_objects if o.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} business object(s)")
            elif f in resource_event_files:
                n = sum(1 for e in resource_events if e.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} resource event(s)")
            elif f in business_subscription_files:
                n = sum(1 for s in business_subscriptions if s.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} business subscription(s)")
            elif f in resource_subscription_files:
                n = sum(1 for s in resource_subscriptions if s.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} resource subscription(s)")
            else:
                n = sum(1 for r in resources if r.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} resource(s)")
    else:
        warn("No non-template event files loaded (cross-asset checks skipped)")

    loaded_process_files = business_process_files + resource_process_files
    if loaded_process_files:
        print(f"[INFO] External processes loaded:")
        for f in loaded_process_files:
            rel_source = str(f.relative_to(ROOT))
            if f in business_process_files:
                n = sum(1 for p in business_processes if p.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} business process(es)")
            else:
                n = sum(1 for p in resource_processes if p.get("_source") == rel_source)
                print(f"  • {rel_source}: {n} resource process(es)")

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
        print(f"\n[FAIL] {len(errors)} error(s) detected:\n")
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
        f"\n[OK] Validation passed — {len(caps)} capabilities "
        f"({', '.join(parts)}) in {len(files)} file(s)"
    )


if __name__ == "__main__":
    main()
