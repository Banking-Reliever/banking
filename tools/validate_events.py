#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROCESSUS_METIER_DIR = ROOT / "externals" / "processus-metier"
PROCESSUS_RESSOURCE_DIR = ROOT / "externals" / "processus-ressource"


ASSET_CONFIG: dict[str, tuple[str, str]] = {
    "business_events": ("business-event-*.yaml", "business_events"),
    "business_objects": ("business-object-*.yaml", "resources"),
    "resource_events": ("resource-event-*.yaml", "resource_events"),
    "resources": ("resource-*.yaml", "resources"),
    "business_subscriptions": ("business-subscription-*.yaml", "business_subscriptions"),
    "resource_subscriptions": ("resource-subscription-*.yaml", "resource_subscriptions"),
}


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"[FATAL] Fichier introuvable: {path}")
    except Exception as exc:
        raise SystemExit(f"[FATAL] Impossible de lire/parse {path}: {exc}")


def load_capabilities_from_file(bcm_file: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    data = load_yaml(bcm_file) or {}
    caps = data.get("capabilities", [])
    if not isinstance(caps, list):
        errors.append(f"[{bcm_file.name}] champ 'capabilities' invalide (liste attendue)")
        return [], errors

    result: list[dict[str, Any]] = []
    for cap in caps:
        if not isinstance(cap, dict):
            errors.append(f"[{bcm_file.name}] entrée invalide dans 'capabilities' (mapping attendu)")
            continue
        cap["_source"] = bcm_file.name
        result.append(cap)
    return result, errors


def load_capabilities_from_dir(bcm_dir: Path) -> tuple[list[dict[str, Any]], list[Path], list[str]]:
    errors: list[str] = []
    files = sorted(bcm_dir.glob("capabilities-*.yaml"))
    if not files:
        errors.append(f"Aucun fichier capabilities-*.yaml trouvé dans {bcm_dir}")
        return [], [], errors

    caps: list[dict[str, Any]] = []
    for file_path in files:
        file_caps, file_errors = load_capabilities_from_file(file_path)
        caps.extend(file_caps)
        errors.extend(file_errors)
    return caps, files, errors


def load_assets(events_dir: Path, pattern: str, key: str) -> tuple[list[dict[str, Any]], list[Path], list[str]]:
    errors: list[str] = []
    items: list[dict[str, Any]] = []
    files: list[Path] = []

    for file_path in sorted(events_dir.rglob(pattern)):
        if file_path.name.startswith("template-"):
            continue

        rel_source = str(file_path.relative_to(events_dir))

        data = load_yaml(file_path) or {}
        file_items = data.get(key, [])
        if not isinstance(file_items, list):
            errors.append(f"[{rel_source}] champ '{key}' invalide (liste attendue)")
            files.append(file_path)
            continue

        for item in file_items:
            if not isinstance(item, dict):
                errors.append(f"[{rel_source}] entrée invalide dans '{key}' (mapping attendu)")
                continue
            item["_source"] = rel_source
            items.append(item)

        files.append(file_path)

    return items, files, errors


def load_external_processes(process_dir: Path, root_key: str) -> tuple[list[dict[str, Any]], list[Path], list[str]]:
    errors: list[str] = []
    items: list[dict[str, Any]] = []
    files: list[Path] = []

    if not process_dir.exists():
        return items, files, errors

    for file_path in sorted(process_dir.rglob("*.yaml")):
        rel_source = str(file_path.relative_to(ROOT))
        data = load_yaml(file_path) or {}
        if not isinstance(data, dict):
            errors.append(f"[{rel_source}] contenu YAML invalide (mapping racine attendu)")
            files.append(file_path)
            continue

        process_item = data.get(root_key)
        if not isinstance(process_item, dict):
            errors.append(f"[{rel_source}] champ racine '{root_key}' manquant ou invalide")
            files.append(file_path)
            continue

        process_item["_source"] = rel_source
        items.append(process_item)
        files.append(file_path)

    return items, files, errors


def index_by_id(items: list[dict[str, Any]], kind: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        src = item.get("_source", "?")
        item_id = item.get("id")
        if not item_id:
            errors.append(f"[{src}] {kind} sans champ 'id'")
            continue
        if item_id in indexed:
            errors.append(f"[{src}] Identifiant dupliqué ({kind}) : {item_id}")
            continue
        indexed[item_id] = item
    return indexed, errors


def validate_capability_refs(cap_by_id: dict[str, dict[str, Any]], cap_id: str, where: str) -> list[str]:
    errors: list[str] = []
    if not cap_id:
        return errors
    if cap_id not in cap_by_id:
        errors.append(f"{where}: capacité '{cap_id}' introuvable")
        return errors

    level = cap_by_id[cap_id].get("level")
    if level not in {"L2", "L3"}:
        errors.append(f"{where}: capacité '{cap_id}' doit être L2 ou L3 (actuel: {level})")
    return errors


def collect_relation_ids(
    item: dict[str, Any],
    plural_key: str,
    singular_key: str,
    prefix: str,
    label: str,
) -> tuple[list[str], list[str]]:
    """Lit une relation 1-n (format courant) avec fallback sur l'ancien format 1-1."""
    errors: list[str] = []
    relation_ids: list[str] = []

    if plural_key in item:
        raw_value = item.get(plural_key)
        if not isinstance(raw_value, list):
            return [], [f"{prefix}: champ '{plural_key}' invalide (liste attendue)"]
        if not raw_value:
            return [], [f"{prefix}: champ '{plural_key}' obligatoire (liste non vide attendue)"]

        for idx, rel_id in enumerate(raw_value):
            if not isinstance(rel_id, str) or not rel_id.strip():
                errors.append(
                    f"{prefix}: {plural_key}[{idx}] invalide (chaîne non vide attendue)"
                )
                continue
            relation_ids.append(rel_id.strip())
        return relation_ids, errors

    legacy_value = item.get(singular_key)
    if legacy_value:
        if not isinstance(legacy_value, str) or not legacy_value.strip():
            return [], [f"{prefix}: champ '{singular_key}' invalide (chaîne non vide attendue)"]
        return [legacy_value.strip()], []

    return [], [
        f"{prefix}: champ '{plural_key}' obligatoire (ou '{singular_key}' en legacy) pour {label}"
    ]


def collect_single_relation_id(
    item: dict[str, Any],
    singular_key: str,
    plural_key: str,
    prefix: str,
    label: str,
) -> tuple[str | None, list[str]]:
    errors: list[str] = []

    if plural_key in item:
        errors.append(
            f"{prefix}: champ '{plural_key}' interdit (cardinalité 1 attendue, utiliser '{singular_key}')"
        )

    value = item.get(singular_key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{prefix}: champ '{singular_key}' obligatoire (chaîne non vide attendue) pour {label}")
        return None, errors

    return value.strip(), errors


def _extract_list_of_ids(
    value: Any,
    prefix: str,
    field_name: str,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    if value is None:
        return [], errors

    if not isinstance(value, list):
        return [], [f"{prefix}: champ '{field_name}' invalide (liste attendue)"]

    refs: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(
                f"{prefix}: {field_name}[{idx}] invalide (chaîne non vide attendue)"
            )
            continue
        refs.append(item.strip())
    return refs, errors


def _collect_event_refs_from_chain(
    process: dict[str, Any],
    prefix: str,
    chain_key: str,
    single_in_key: str,
    single_out_key: str,
    multi_in_key: str,
    multi_out_key: str,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    refs: list[str] = []

    chain = process.get(chain_key)
    if chain is None:
        return refs, errors
    if not isinstance(chain, list):
        return refs, [f"{prefix}: champ '{chain_key}' invalide (liste attendue)"]

    for idx, step in enumerate(chain):
        if not isinstance(step, dict):
            errors.append(f"{prefix}: {chain_key}[{idx}] invalide (mapping attendu)")
            continue

        for key in [single_in_key, single_out_key]:
            value = step.get(key)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"{prefix}: {chain_key}[{idx}].{key} invalide (chaîne non vide attendue)"
                )
                continue
            refs.append(value.strip())

        for key in [multi_in_key, multi_out_key]:
            more_refs, more_errors = _extract_list_of_ids(
                step.get(key),
                prefix,
                f"{chain_key}[{idx}].{key}",
            )
            refs.extend(more_refs)
            errors.extend(more_errors)

    return refs, errors


def validate_external_process_relations(
    capabilities: list[dict[str, Any]],
    business_events: list[dict[str, Any]],
    resource_events: list[dict[str, Any]],
    business_subscriptions: list[dict[str, Any]],
    resource_subscriptions: list[dict[str, Any]],
    business_processes: list[dict[str, Any]],
    resource_processes: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []

    cap_by_id = {c.get("id"): c for c in capabilities if isinstance(c.get("id"), str)}
    be_by_id = {e.get("id"): e for e in business_events if isinstance(e.get("id"), str)}
    re_by_id = {e.get("id"): e for e in resource_events if isinstance(e.get("id"), str)}
    bs_by_id = {s.get("id"): s for s in business_subscriptions if isinstance(s.get("id"), str)}
    rs_by_id = {s.get("id"): s for s in resource_subscriptions if isinstance(s.get("id"), str)}

    def collect_capability_refs(process: dict[str, Any], prefix: str) -> tuple[list[str], list[str]]:
        local_errors: list[str] = []
        refs: list[str] = []

        for field in ["parent_capability", "decision_point"]:
            value = process.get(field)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                local_errors.append(f"{prefix}: champ '{field}' invalide (chaîne non vide attendue)")
                continue
            refs.append(value.strip())

        internal_refs, internal_errors = _extract_list_of_ids(
            process.get("internal_capabilities"),
            prefix,
            "internal_capabilities",
        )
        refs.extend(internal_refs)
        local_errors.extend(internal_errors)

        chain = process.get("event_capability_chain")
        if chain is not None:
            if not isinstance(chain, list):
                local_errors.append(f"{prefix}: champ 'event_capability_chain' invalide (liste attendue)")
            else:
                for idx, step in enumerate(chain):
                    if not isinstance(step, dict):
                        local_errors.append(
                            f"{prefix}: event_capability_chain[{idx}] invalide (mapping attendu)"
                        )
                        continue
                    capability = step.get("capability")
                    if capability is None:
                        continue
                    if not isinstance(capability, str) or not capability.strip():
                        local_errors.append(
                            f"{prefix}: event_capability_chain[{idx}].capability invalide "
                            f"(chaîne non vide attendue)"
                        )
                        continue
                    refs.append(capability.strip())

        return refs, local_errors

    for process in business_processes:
        src = process.get("_source", "?")
        pid = process.get("id", "<sans-id>")
        prefix = f"[{src}] {pid}"

        cap_refs, cap_errors = collect_capability_refs(process, prefix)
        errors.extend(cap_errors)
        for cap_id in cap_refs:
            if cap_id not in cap_by_id:
                errors.append(f"{prefix}: capacité '{cap_id}' introuvable (processus métier)")

        event_refs: list[str] = []
        subscription_refs: list[str] = []
        for field in ["entry_event", "triggering_business_event", "derived_business_event"]:
            value = process.get(field)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}: champ '{field}' invalide (chaîne non vide attendue)")
                continue
            event_refs.append(value.strip())

        start = process.get("start")
        if isinstance(start, dict) and start.get("type") == "event":
            start_event = start.get("event")
            if isinstance(start_event, str) and start_event.strip():
                event_refs.append(start_event.strip())
            elif start_event is not None:
                errors.append(f"{prefix}: start.event invalide (chaîne non vide attendue)")

        business_assets = process.get("business_assets")
        if isinstance(business_assets, dict):
            refs, list_errors = _extract_list_of_ids(
                business_assets.get("evenements_metier"),
                prefix,
                "business_assets.evenements_metier",
            )
            event_refs.extend(refs)
            errors.extend(list_errors)

            refs, list_errors = _extract_list_of_ids(
                business_assets.get("abonnements_metier"),
                prefix,
                "business_assets.abonnements_metier",
            )
            subscription_refs.extend(refs)
            errors.extend(list_errors)

        context_filters = process.get("context_filters")
        if isinstance(context_filters, dict):
            tbe = context_filters.get("triggering_business_event")
            if isinstance(tbe, str) and tbe.strip():
                event_refs.append(tbe.strip())

        refs, chain_errors = _collect_event_refs_from_chain(
            process,
            prefix,
            "event_subscription_chain",
            "consumes_business_event",
            "emits_business_event",
            "consumes_business_events",
            "emits_business_events",
        )
        event_refs.extend(refs)
        errors.extend(chain_errors)

        event_subscription_chain = process.get("event_subscription_chain")
        if isinstance(event_subscription_chain, list):
            for idx, step in enumerate(event_subscription_chain):
                if not isinstance(step, dict):
                    continue
                via_subscription = step.get("via_subscription")
                if via_subscription is None:
                    continue
                if not isinstance(via_subscription, str) or not via_subscription.strip():
                    errors.append(
                        f"{prefix}: event_subscription_chain[{idx}].via_subscription invalide "
                        f"(chaîne non vide attendue)"
                    )
                    continue
                subscription_refs.append(via_subscription.strip())

        refs, chain_errors = _collect_event_refs_from_chain(
            process,
            prefix,
            "event_capability_chain",
            "consumes_event",
            "emits_event",
            "consumes_events",
            "emits_events",
        )
        event_refs.extend(refs)
        errors.extend(chain_errors)

        exits_metier = process.get("exits_metier")
        if isinstance(exits_metier, list):
            for idx, exit_item in enumerate(exits_metier):
                if not isinstance(exit_item, dict):
                    errors.append(f"{prefix}: exits_metier[{idx}] invalide (mapping attendu)")
                    continue
                to_event = exit_item.get("to_business_event")
                if isinstance(to_event, str) and to_event.strip():
                    event_refs.append(to_event.strip())

        for event_id in event_refs:
            if event_id not in be_by_id:
                errors.append(f"{prefix}: événement métier '{event_id}' introuvable")

        for subscription_id in subscription_refs:
            if subscription_id not in bs_by_id:
                errors.append(f"{prefix}: abonnement métier '{subscription_id}' introuvable")

    for process in resource_processes:
        src = process.get("_source", "?")
        pid = process.get("id", "<sans-id>")
        prefix = f"[{src}] {pid}"

        cap_refs, cap_errors = collect_capability_refs(process, prefix)
        errors.extend(cap_errors)
        for cap_id in cap_refs:
            if cap_id not in cap_by_id:
                errors.append(f"{prefix}: capacité '{cap_id}' introuvable (processus ressource)")

        event_refs: list[str] = []
        subscription_refs: list[str] = []
        for field in ["entry_event", "triggering_resource_event", "derived_resource_event"]:
            value = process.get(field)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}: champ '{field}' invalide (chaîne non vide attendue)")
                continue
            event_refs.append(value.strip())

        start = process.get("start")
        if isinstance(start, dict) and start.get("type") == "event":
            start_event = start.get("event")
            if isinstance(start_event, str) and start_event.strip():
                event_refs.append(start_event.strip())
            elif start_event is not None:
                errors.append(f"{prefix}: start.event invalide (chaîne non vide attendue)")

        resource_assets = process.get("resource_assets")
        if isinstance(resource_assets, dict):
            refs, list_errors = _extract_list_of_ids(
                resource_assets.get("evenements_ressource"),
                prefix,
                "resource_assets.evenements_ressource",
            )
            event_refs.extend(refs)
            errors.extend(list_errors)

            refs, list_errors = _extract_list_of_ids(
                resource_assets.get("abonnements_ressource"),
                prefix,
                "resource_assets.abonnements_ressource",
            )
            subscription_refs.extend(refs)
            errors.extend(list_errors)

        context_filters = process.get("context_filters")
        if isinstance(context_filters, dict):
            tre = context_filters.get("triggering_resource_event")
            dre = context_filters.get("derived_resource_event")
            if isinstance(tre, str) and tre.strip():
                event_refs.append(tre.strip())
            if isinstance(dre, str) and dre.strip():
                event_refs.append(dre.strip())

        refs, chain_errors = _collect_event_refs_from_chain(
            process,
            prefix,
            "event_subscription_chain",
            "consumes_resource_event",
            "emits_resource_event",
            "consumes_resource_events",
            "emits_resource_events",
        )
        event_refs.extend(refs)
        errors.extend(chain_errors)

        event_subscription_chain = process.get("event_subscription_chain")
        if isinstance(event_subscription_chain, list):
            for idx, step in enumerate(event_subscription_chain):
                if not isinstance(step, dict):
                    continue
                via_subscription = step.get("via_subscription")
                if via_subscription is None:
                    continue
                if not isinstance(via_subscription, str) or not via_subscription.strip():
                    errors.append(
                        f"{prefix}: event_subscription_chain[{idx}].via_subscription invalide "
                        f"(chaîne non vide attendue)"
                    )
                    continue
                subscription_refs.append(via_subscription.strip())

        refs, chain_errors = _collect_event_refs_from_chain(
            process,
            prefix,
            "event_capability_chain",
            "consumes_event",
            "emits_event",
            "consumes_events",
            "emits_events",
        )
        event_refs.extend(refs)
        errors.extend(chain_errors)

        exits_ressource = process.get("exits_ressource")
        if isinstance(exits_ressource, list):
            for idx, exit_item in enumerate(exits_ressource):
                if not isinstance(exit_item, dict):
                    errors.append(f"{prefix}: exits_ressource[{idx}] invalide (mapping attendu)")
                    continue
                to_event = exit_item.get("to_resource_event")
                if isinstance(to_event, str) and to_event.strip():
                    event_refs.append(to_event.strip())

        for event_id in event_refs:
            if event_id not in re_by_id:
                errors.append(f"{prefix}: événement ressource '{event_id}' introuvable")

        for subscription_id in subscription_refs:
            if subscription_id not in rs_by_id:
                errors.append(f"{prefix}: abonnement ressource '{subscription_id}' introuvable")

    return errors


def validate_cross_relations(
    capabilities: list[dict[str, Any]],
    business_events: list[dict[str, Any]],
    business_objects: list[dict[str, Any]],
    resource_events: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    business_subscriptions: list[dict[str, Any]],
    resource_subscriptions: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []

    cap_by_id, cap_index_errors = index_by_id(capabilities, "capacité")
    be_by_id, be_index_errors = index_by_id(business_events, "événement métier")
    bo_by_id, bo_index_errors = index_by_id(business_objects, "objet métier")
    re_by_id, re_index_errors = index_by_id(resource_events, "événement ressource")
    rs_by_id, rs_index_errors = index_by_id(resources, "ressource")
    bs_by_id, bs_index_errors = index_by_id(business_subscriptions, "abonnement métier")
    rsub_by_id, rsub_index_errors = index_by_id(resource_subscriptions, "abonnement ressource")

    errors.extend(cap_index_errors)
    errors.extend(be_index_errors)
    errors.extend(bo_index_errors)
    errors.extend(re_index_errors)
    errors.extend(rs_index_errors)
    errors.extend(bs_index_errors)
    errors.extend(rsub_index_errors)

    l3_children_by_l2: dict[str, set[str]] = {}
    for capability in capabilities:
        capability_id = capability.get("id")
        if not isinstance(capability_id, str):
            continue
        if capability.get("level") != "L3":
            continue
        parent_id = capability.get("parent")
        if isinstance(parent_id, str) and parent_id:
            l3_children_by_l2.setdefault(parent_id, set()).add(capability_id)

    for event in business_events:
        src = event.get("_source", "?")
        event_id = event.get("id", "<sans-id>")
        prefix = f"[{src}] {event_id}"

        if not event.get("version"):
            errors.append(f"{prefix}: champ 'version' obligatoire")

        emitting_capability = event.get("emitting_capability")
        if not emitting_capability:
            errors.append(f"{prefix}: champ 'emitting_capability' obligatoire")
        else:
            errors.extend(validate_capability_refs(cap_by_id, emitting_capability, f"{prefix}.emitting_capability"))

        carried_business_object = event.get("carried_business_object")
        if not carried_business_object:
            errors.append(f"{prefix}: champ 'carried_business_object' obligatoire")
        elif carried_business_object not in bo_by_id:
            errors.append(f"{prefix}: objet métier '{carried_business_object}' introuvable")

    for business_object in business_objects:
        src = business_object.get("_source", "?")
        object_id = business_object.get("id", "<sans-id>")
        prefix = f"[{src}] {object_id}"

        emitting_capability = business_object.get("emitting_capability")
        if not emitting_capability:
            errors.append(f"{prefix}: champ 'emitting_capability' obligatoire")
        else:
            errors.extend(validate_capability_refs(cap_by_id, emitting_capability, f"{prefix}.emitting_capability"))

        if isinstance(emitting_capability, str) and emitting_capability in cap_by_id:
            children_l3 = l3_children_by_l2.get(emitting_capability, set())
            has_l3_field = "emitting_capability_L3" in business_object

            if children_l3:
                if not has_l3_field:
                    errors.append(
                        f"{prefix}: champ 'emitting_capability_L3' obligatoire car la capacité L2 "
                        f"'{emitting_capability}' possède des capacités L3"
                    )
                else:
                    raw_l3_list = business_object.get("emitting_capability_L3")
                    if not isinstance(raw_l3_list, list):
                        errors.append(f"{prefix}: champ 'emitting_capability_L3' invalide (liste attendue)")
                    elif not raw_l3_list:
                        errors.append(
                            f"{prefix}: champ 'emitting_capability_L3' obligatoire "
                            f"(liste non vide attendue)"
                        )
                    else:
                        seen_l3: set[str] = set()
                        for idx, l3_id in enumerate(raw_l3_list):
                            if not isinstance(l3_id, str) or not l3_id.strip():
                                errors.append(
                                    f"{prefix}: emitting_capability_L3[{idx}] invalide "
                                    f"(chaîne non vide attendue)"
                                )
                                continue

                            l3_id = l3_id.strip()
                            if l3_id in seen_l3:
                                errors.append(
                                    f"{prefix}: emitting_capability_L3 contient un doublon ('{l3_id}')"
                                )
                                continue
                            seen_l3.add(l3_id)

                            referenced_cap = cap_by_id.get(l3_id)
                            if not referenced_cap:
                                errors.append(f"{prefix}: emitting_capability_L3 '{l3_id}' introuvable")
                                continue

                            if referenced_cap.get("level") != "L3":
                                errors.append(
                                    f"{prefix}: emitting_capability_L3 '{l3_id}' doit référencer "
                                    "une capacité de niveau L3"
                                )
                                continue

                            l3_parent = referenced_cap.get("parent")
                            if l3_parent != emitting_capability:
                                errors.append(
                                    f"{prefix}: emitting_capability_L3 '{l3_id}' référence la L2 "
                                    f"'{l3_parent}', attendu '{emitting_capability}'"
                                )
            elif has_l3_field:
                errors.append(
                    f"{prefix}: champ 'emitting_capability_L3' interdit car la capacité L2 "
                    f"'{emitting_capability}' ne possède aucune capacité L3"
                )

        if "emitting_business_event" in business_object:
            errors.append(
                f"{prefix}: champ 'emitting_business_event' interdit. "
                f"La relation doit être portée par l'événement métier via 'carried_business_object'."
            )

        if "emitting_business_events" in business_object:
            errors.append(
                f"{prefix}: champ 'emitting_business_events' interdit. "
                f"La relation doit être portée par l'événement métier via 'carried_business_object'."
            )

    for resource_event in resource_events:
        src = resource_event.get("_source", "?")
        event_id = resource_event.get("id", "<sans-id>")
        prefix = f"[{src}] {event_id}"

        emitting_capability = resource_event.get("emitting_capability")
        if not emitting_capability:
            errors.append(f"{prefix}: champ 'emitting_capability' obligatoire")
        else:
            errors.extend(validate_capability_refs(cap_by_id, emitting_capability, f"{prefix}.emitting_capability"))

        carried_resource = resource_event.get("carried_resource")
        data = resource_event.get("data")
        if carried_resource and data:
            errors.append(f"{prefix}: les champs 'carried_resource' et 'data' sont mutuellement exclusifs")
        elif not carried_resource and not data:
            errors.append(f"{prefix}: un des champs 'carried_resource' ou 'data' doit être renseigné")
        elif carried_resource and carried_resource not in rs_by_id:
            errors.append(f"{prefix}: ressource '{carried_resource}' introuvable")

        business_event, relation_errors = collect_single_relation_id(
            resource_event,
            "business_event",
            "business_events",
            prefix,
            "l'événement métier lié à l'événement ressource",
        )
        errors.extend(relation_errors)
        if business_event and business_event not in be_by_id:
            errors.append(f"{prefix}: événement métier '{business_event}' introuvable")

        # Cohérence de rattachement : un événement ressource doit relier une
        # ressource et un événement métier pointant vers le même objet métier.
        if (
            isinstance(carried_resource, str)
            and carried_resource in rs_by_id
            and isinstance(business_event, str)
            and business_event in be_by_id
        ):
            resource_business_object = rs_by_id[carried_resource].get("business_object")
            event_business_object = be_by_id[business_event].get("carried_business_object")
            if resource_business_object != event_business_object:
                errors.append(
                    f"{prefix}: incohérence de rattachement objet métier entre "
                    f"carried_resource '{carried_resource}' (business_object='{resource_business_object}') "
                    f"et business_event '{business_event}' (carried_business_object='{event_business_object}')"
                )

    referenced_business_events: set[str] = set()
    for resource_event in resource_events:
        src = resource_event.get("_source", "?")
        event_id = resource_event.get("id", "<sans-id>")
        prefix = f"[{src}] {event_id}"
        business_event, relation_errors = collect_single_relation_id(
            resource_event,
            "business_event",
            "business_events",
            prefix,
            "l'événement métier lié à l'événement ressource",
        )
        errors.extend(relation_errors)
        if business_event and business_event in be_by_id:
            referenced_business_events.add(business_event)

    for business_event_id in be_by_id:
        if business_event_id not in referenced_business_events:
            errors.append(
                f"[cross-events] événement métier '{business_event_id}' non référencé par un événement ressource"
            )

    for resource in resources:
        src = resource.get("_source", "?")
        resource_id = resource.get("id", "<sans-id>")
        prefix = f"[{src}] {resource_id}"

        emitting_capability = resource.get("emitting_capability")
        if not emitting_capability:
            errors.append(f"{prefix}: champ 'emitting_capability' obligatoire")
        else:
            errors.extend(validate_capability_refs(cap_by_id, emitting_capability, f"{prefix}.emitting_capability"))

        business_object = resource.get("business_object")
        if not business_object:
            errors.append(f"{prefix}: champ 'business_object' obligatoire")
        elif business_object not in bo_by_id:
            errors.append(f"{prefix}: objet métier '{business_object}' introuvable")
        else:
            bo_data = bo_by_id[business_object].get("data", []) or []
            bo_properties = {
                field.get("name")
                for field in bo_data
                if isinstance(field, dict) and field.get("name")
            }

            resource_data = resource.get("data", []) or []
            mapped_properties = {
                field.get("business_object_property")
                for field in resource_data
                if isinstance(field, dict) and field.get("business_object_property")
            }

            missing_properties = sorted(bo_properties - mapped_properties)
            if missing_properties:
                errors.append(
                    f"{prefix}: propriétés de l'objet métier '{business_object}' non référencées "
                    f"dans la ressource: {', '.join(missing_properties)}"
                )

            unknown_mapped_properties = sorted(mapped_properties - bo_properties)
            if unknown_mapped_properties:
                errors.append(
                    f"{prefix}: business_object_property inconnue(s) pour '{business_object}': "
                    f"{', '.join(unknown_mapped_properties)}"
                )

    for subscription in business_subscriptions:
        src = subscription.get("_source", "?")
        subscription_id = subscription.get("id", "<sans-id>")
        prefix = f"[{src}] {subscription_id}"

        consumer_capability = subscription.get("consumer_capability")
        if not consumer_capability:
            errors.append(f"{prefix}: champ 'consumer_capability' obligatoire")
        else:
            errors.extend(validate_capability_refs(cap_by_id, consumer_capability, f"{prefix}.consumer_capability"))

        subscribed_event = subscription.get("subscribed_event")
        if not isinstance(subscribed_event, dict):
            errors.append(f"{prefix}: champ 'subscribed_event' obligatoire (mapping attendu)")
            continue

        event_id = subscribed_event.get("id")
        if not event_id:
            errors.append(f"{prefix}: subscribed_event.id obligatoire")
            continue
        if event_id not in be_by_id:
            errors.append(f"{prefix}: subscribed_event.id '{event_id}' introuvable")
            continue

        expected_event = be_by_id[event_id]

        version = subscribed_event.get("version")
        expected_version = expected_event.get("version")
        if not version:
            errors.append(f"{prefix}: subscribed_event.version obligatoire")
        elif version != expected_version:
            errors.append(
                f"{prefix}: subscribed_event.version '{version}' différente de '{expected_version}'"
            )

        emitter = subscribed_event.get("emitting_capability")
        expected_emitter = expected_event.get("emitting_capability")
        if not emitter:
            errors.append(f"{prefix}: subscribed_event.emitting_capability obligatoire")
        elif emitter != expected_emitter:
            errors.append(
                f"{prefix}: subscribed_event.emitting_capability '{emitter}' différent de '{expected_emitter}'"
            )

    referenced_business_subscriptions: set[str] = set()
    for subscription in resource_subscriptions:
        src = subscription.get("_source", "?")
        subscription_id = subscription.get("id", "<sans-id>")
        prefix = f"[{src}] {subscription_id}"

        consumer_capability = subscription.get("consumer_capability")
        if not consumer_capability:
            errors.append(f"{prefix}: champ 'consumer_capability' obligatoire")
        else:
            errors.extend(validate_capability_refs(cap_by_id, consumer_capability, f"{prefix}.consumer_capability"))

        linked_business_subscription = subscription.get("linked_business_subscription")
        linked_business = None
        if not linked_business_subscription:
            errors.append(f"{prefix}: champ 'linked_business_subscription' obligatoire")
        elif linked_business_subscription not in bs_by_id:
            errors.append(
                f"{prefix}: linked_business_subscription '{linked_business_subscription}' introuvable"
            )
        else:
            linked_business = bs_by_id[linked_business_subscription]
            referenced_business_subscriptions.add(linked_business_subscription)
            expected_consumer = linked_business.get("consumer_capability")
            if consumer_capability and expected_consumer and consumer_capability != expected_consumer:
                errors.append(
                    f"{prefix}: consumer_capability '{consumer_capability}' différente de '{expected_consumer}'"
                )

        subscribed_resource_event = subscription.get("subscribed_resource_event")
        if not isinstance(subscribed_resource_event, dict):
            errors.append(f"{prefix}: champ 'subscribed_resource_event' obligatoire (mapping attendu)")
            continue

        event_id = subscribed_resource_event.get("id")
        if not event_id:
            errors.append(f"{prefix}: subscribed_resource_event.id obligatoire")
            continue
        if event_id not in re_by_id:
            errors.append(f"{prefix}: subscribed_resource_event.id '{event_id}' introuvable")
            continue

        expected_resource_event = re_by_id[event_id]

        resource_emitter = subscribed_resource_event.get("emitting_capability")
        expected_resource_emitter = expected_resource_event.get("emitting_capability")
        if not resource_emitter:
            errors.append(f"{prefix}: subscribed_resource_event.emitting_capability obligatoire")
        elif resource_emitter != expected_resource_emitter:
            errors.append(
                f"{prefix}: subscribed_resource_event.emitting_capability '{resource_emitter}' différent de '{expected_resource_emitter}'"
            )

        linked_business_event = subscribed_resource_event.get("linked_business_event")
        expected_business_event, relation_errors = collect_single_relation_id(
            expected_resource_event,
            "business_event",
            "business_events",
            f"[{expected_resource_event.get('_source', '?')}] {expected_resource_event.get('id', '<sans-id>')}",
            "l'événement métier lié à l'événement ressource",
        )
        errors.extend(relation_errors)
        if not linked_business_event:
            errors.append(f"{prefix}: subscribed_resource_event.linked_business_event obligatoire")
        elif expected_business_event and linked_business_event != expected_business_event:
            errors.append(
                f"{prefix}: subscribed_resource_event.linked_business_event '{linked_business_event}' différent du business_event de l'événement ressource ('{expected_business_event}')"
            )

        if linked_business:
            business_subscribed_event = (linked_business.get("subscribed_event") or {}).get("id")
            if linked_business_event and business_subscribed_event and linked_business_event != business_subscribed_event:
                errors.append(
                    f"{prefix}: linked_business_event '{linked_business_event}' différent de la abonnement métier '{business_subscribed_event}'"
                )

            business_emitter = (linked_business.get("subscribed_event") or {}).get("emitting_capability")
            if business_emitter and resource_emitter and business_emitter != resource_emitter:
                errors.append(
                    f"{prefix}: emitting_capability '{resource_emitter}' différente de la abonnement métier liée '{business_emitter}'"
                )

    for business_subscription_id in bs_by_id:
        if business_subscription_id not in referenced_business_subscriptions:
            errors.append(
                f"[cross-subscriptions] abonnement métier '{business_subscription_id}' non référencée par une abonnement ressource"
            )

    # Couverture globale des propriétés d'objets métier par les ressources :
    # toute propriété d'un objet métier doit être référencée au moins une fois
    # via business_object_property dans une ressource pointant vers cet objet.
    referenced_properties_by_object: dict[str, set[str]] = {}
    for resource in resources:
        business_object_id = resource.get("business_object")
        if not isinstance(business_object_id, str) or not business_object_id:
            continue

        for field in resource.get("data", []) or []:
            if not isinstance(field, dict):
                continue
            property_name = field.get("business_object_property")
            if isinstance(property_name, str) and property_name.strip():
                referenced_properties_by_object.setdefault(business_object_id, set()).add(
                    property_name.strip()
                )

    for business_object in business_objects:
        src = business_object.get("_source", "?")
        object_id = business_object.get("id")
        if not isinstance(object_id, str) or not object_id:
            continue

        covered_properties = referenced_properties_by_object.get(object_id, set())
        for field in business_object.get("data", []) or []:
            if not isinstance(field, dict):
                continue
            field_name = field.get("name")
            if not isinstance(field_name, str) or not field_name.strip():
                continue

            if field_name.strip() not in covered_properties:
                errors.append(
                    f"[{src}] {object_id}: propriété '{field_name}' non référencée "
                    f"par aucune ressource (via business_object_property)"
                )

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validation en masse des assets d'événements BCM (répertoire bcm/, sous-répertoires inclus) "
            "contre les capacités BCM (capabilities-*.yaml)."
        )
    )
    parser.add_argument("--bcm-dir", default="bcm", help="Répertoire des capacités (défaut: bcm)")
    parser.add_argument("--events-dir", default="bcm", help="Répertoire des assets événements (défaut: bcm)")
    parser.add_argument("--bcm", help="Mode legacy: fichier unique des capacités")
    parser.add_argument("--events", help="Mode legacy: fichier unique d'événements métier")
    return parser.parse_args()


def run_single_file_mode(bcm_file: Path, events_file: Path) -> int:
    capabilities, cap_errors = load_capabilities_from_file(bcm_file)
    business_events, _, be_errors = load_assets(events_file.parent, events_file.name, "evenements_metier")
    if not business_events:
        data = load_yaml(events_file) or {}
        file_items = data.get("evenements_metier", [])
        if isinstance(file_items, list):
            for item in file_items:
                if isinstance(item, dict):
                    item["_source"] = events_file.name
                    business_events.append(item)

    errors = cap_errors + be_errors
    errors.extend(
        validate_cross_relations(
            capabilities=capabilities,
            business_events=business_events,
            business_objects=[],
            resource_events=[],
            resources=[],
            business_subscriptions=[],
            resource_subscriptions=[],
        )
    )

    if errors:
        print(f"[FAIL] {len(errors)} erreur(s) détectée(s):")
        for msg in errors:
            print(f"  ✗ {msg}")
        return 1

    print("[OK] Validation réussie (mode fichier unique).")
    return 0


def run_batch_mode(bcm_dir: Path, events_dir: Path) -> int:
    if not bcm_dir.exists():
        print(f"[FATAL] Répertoire introuvable: {bcm_dir}")
        return 2
    if not events_dir.exists():
        print(f"[FATAL] Répertoire introuvable: {events_dir}")
        return 2

    capabilities, capability_files, errors = load_capabilities_from_dir(bcm_dir)

    loaded: dict[str, list[dict[str, Any]]] = {}
    loaded_files: dict[str, list[Path]] = {}
    for key, (pattern, root_key) in ASSET_CONFIG.items():
        items, files, asset_errors = load_assets(events_dir, pattern, root_key)
        loaded[key] = items
        loaded_files[key] = files
        errors.extend(asset_errors)

    business_processes, business_process_files, process_errors = load_external_processes(
        PROCESSUS_METIER_DIR,
        "processus_metier",
    )
    resource_processes, resource_process_files, process_errors_2 = load_external_processes(
        PROCESSUS_RESSOURCE_DIR,
        "processus_ressource",
    )
    errors.extend(process_errors)
    errors.extend(process_errors_2)

    errors.extend(
        validate_cross_relations(
            capabilities=capabilities,
            business_events=loaded["business_events"],
            business_objects=loaded["business_objects"],
            resource_events=loaded["resource_events"],
            resources=loaded["resources"],
            business_subscriptions=loaded["business_subscriptions"],
            resource_subscriptions=loaded["resource_subscriptions"],
        )
    )
    errors.extend(
        validate_external_process_relations(
            capabilities=capabilities,
            business_events=loaded["business_events"],
            resource_events=loaded["resource_events"],
            business_subscriptions=loaded["business_subscriptions"],
            resource_subscriptions=loaded["resource_subscriptions"],
            business_processes=business_processes,
            resource_processes=resource_processes,
        )
    )

    print("[INFO] Capacités chargées:")
    for file_path in capability_files:
        count = sum(1 for cap in capabilities if cap.get("_source") == file_path.name)
        print(f"  • {file_path.name}: {count} capacité(s)")

    print("[INFO] Assets evts chargés (hors templates):")
    for key, files in loaded_files.items():
        for file_path in files:
            rel_source = str(file_path.relative_to(events_dir))
            count = sum(1 for item in loaded[key] if item.get("_source") == rel_source)
            print(f"  • {rel_source}: {count} entrée(s)")

    loaded_process_files = business_process_files + resource_process_files
    if loaded_process_files:
        print("[INFO] Processus externes chargés:")
        for file_path in loaded_process_files:
            rel_source = str(file_path.relative_to(ROOT))
            if file_path in business_process_files:
                count = sum(1 for item in business_processes if item.get("_source") == rel_source)
                print(f"  • {rel_source}: {count} processus métier")
            else:
                count = sum(1 for item in resource_processes if item.get("_source") == rel_source)
                print(f"  • {rel_source}: {count} processus ressource")

    if errors:
        print(f"\n[FAIL] {len(errors)} erreur(s) détectée(s):")
        for msg in errors:
            print(f"  ✗ {msg}")
        return 1

    total_assets = sum(len(items) for items in loaded.values())
    print(
        f"\n[OK] Validation réussie — {len(capabilities)} capacité(s), "
        f"{total_assets} asset(s) evts, {sum(len(v) for v in loaded_files.values())} fichier(s) evts"
    )
    return 0


def main() -> int:
    args = parse_args()

    if bool(args.bcm) ^ bool(args.events):
        print("[FATAL] Utiliser --bcm et --events ensemble, ou aucun des deux pour le mode batch.")
        return 2

    if args.bcm and args.events:
        return run_single_file_mode(Path(args.bcm), Path(args.events))

    return run_batch_mode(Path(args.bcm_dir), Path(args.events_dir))


if __name__ == "__main__":
    raise SystemExit(main())
