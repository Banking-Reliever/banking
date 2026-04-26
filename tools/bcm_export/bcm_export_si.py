#!/usr/bin/env python3
"""
BCM SI (resources) export script to EventCatalog.

Usage:
    python bcm_export_si.py --input /path/to/bcm --output /path/to/views/FOODAROO-SI
    python bcm_export_si.py --input /path/to/bcm --output /path/to/views/FOODAROO-SI --dry-run
    python bcm_export_si.py --input /path/to/bcm --validate-only
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

try:
    from .eventcatalog_generator import EventCatalogGenerator
except ImportError:
    from eventcatalog_generator import EventCatalogGenerator


logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO

    class ColoredFormatter(logging.Formatter):
        COLORS = {
            "DEBUG": "\033[36m",
            "INFO": "\033[32m",
            "WARNING": "\033[33m",
            "ERROR": "\033[31m",
            "CRITICAL": "\033[35m",
        }
        RESET = "\033[0m"

        def format(self, record):
            color = self.COLORS.get(record.levelname, "")
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            return super().format(record)

    handler = logging.StreamHandler()
    if sys.stdout.isatty():
        formatter = ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s")
    else:
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[handler])


def load_yaml(file_path: Path) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"Empty YAML: {file_path}")
    return data


def slug_from_id(bcm_id: str) -> str:
    parts = bcm_id.split(".")
    if len(parts) >= 3 and parts[-1].isdigit():
        slug_parts = parts[-2:]
    elif len(parts) >= 4:
        slug_parts = [parts[-1]]
    else:
        slug_parts = [p for p in parts if p not in ["CAP", "EVT", "OBJ", "RES", "SUB"]]

    cleaned = []
    for part in slug_parts:
        value = part.lower().replace("_", "-")
        value = re.sub(r"[^a-z0-9-]", "", value)
        value = re.sub(r"-+", "-", value).strip("-")
        if value:
            cleaned.append(value)

    if not cleaned:
        raise ValueError(f"Invalid slug for ID: {bcm_id}")
    return "-".join(cleaned)


def process_slug_from_id(process_id: str) -> str:
    """Generates a flow slug from a resource process identifier."""
    parts = process_id.split(".")
    if len(parts) >= 5 and parts[0] == "PRC":
        base = "-".join(parts[2:])
    else:
        base = process_id

    value = base.lower().replace("_", "-").replace(".", "-")
    value = re.sub(r"[^a-z0-9-]", "", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown-process"


def owner_slug(owner: str) -> str:
    if not owner:
        return "unknown"
    value = owner.lower().replace(" & ", " et ").replace("&", "et")
    value = value.replace("/", "-").replace(" ", "-")
    value = re.sub(r"[^a-z0-9-]", "", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


def normalize_scope(scope: str) -> str:
    raw = (scope or "public").strip().lower()
    aliases = {
        "public": "public",
        "publique": "public",
        "internal": "internal",
        "interne": "internal",
        "private": "private",
        "prive": "private",
        "privé": "private",
    }
    return aliases.get(raw, "public")


def first_relation_id(item: Dict[str, Any], plural_key: str, singular_key: str) -> str:
    """Returns the first ID of a relation (list format or legacy)."""
    plural_value = item.get(plural_key)
    if isinstance(plural_value, list):
        for relation_id in plural_value:
            if isinstance(relation_id, str) and relation_id.strip():
                return relation_id.strip()

    singular_value = item.get(singular_key)
    if isinstance(singular_value, str) and singular_value.strip():
        return singular_value.strip()

    return ""


def parse_capabilities(bcm_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    l1_file = bcm_dir / "capabilities-L1.yaml"
    if not l1_file.exists():
        raise ValueError(f"Missing file: {l1_file}")

    l1_data = []
    for capability in load_yaml(l1_file).get("capabilities", []):
        if isinstance(capability, dict):
            item = capability.copy()
            item["__source_file"] = str(l1_file)
            l1_data.append(item)
    l2_data: List[Dict[str, Any]] = []

    l2_files = list(bcm_dir.glob("capabilities-*-L2.yaml"))
    if not l2_files:
        raise ValueError(f"No capabilities-*-L2.yaml file found in {bcm_dir}")

    for file_path in l2_files:
        for capability in load_yaml(file_path).get("capabilities", []):
            if isinstance(capability, dict):
                item = capability.copy()
                item["__source_file"] = str(file_path)
                l2_data.append(item)

    l3_data: List[Dict[str, Any]] = []
    l3_files = list(bcm_dir.glob("capabilities-*-L3.yaml"))
    for file_path in l3_files:
        for capability in load_yaml(file_path).get("capabilities", []):
            if isinstance(capability, dict):
                item = capability.copy()
                item["__source_file"] = str(file_path)
                l3_data.append(item)

    l1 = [c for c in l1_data if c.get("level") == "L1"]
    l2 = [c for c in l2_data if c.get("level") == "L2"]
    l3 = [c for c in l3_data if c.get("level") == "L3"]

    l2_parent_l1_by_id = {cap.get("id"): cap.get("parent") for cap in l2}
    for cap in l3:
        parent_l2_id = cap.get("parent")
        cap["parent_l2_id"] = parent_l2_id
        cap["parent_l1_id"] = l2_parent_l1_by_id.get(parent_l2_id)

    return l1, l2 + l3


def parse_resources(bcm_dir: Path) -> List[Dict[str, Any]]:
    res_dir = bcm_dir / "resource"
    if not res_dir.exists():
        raise ValueError(f"Missing directory: {res_dir}")

    resources: List[Dict[str, Any]] = []
    for file_path in res_dir.glob("resource-*.yaml"):
        for resource in load_yaml(file_path).get("resources", []):
            if isinstance(resource, dict):
                item = resource.copy()
                item["__source_file"] = str(file_path)
                resources.append(item)
    return resources


def parse_resource_events(bcm_dir: Path) -> List[Dict[str, Any]]:
    event_dir = bcm_dir / "resource-event"
    if not event_dir.exists():
        raise ValueError(f"Missing directory: {event_dir}")

    events: List[Dict[str, Any]] = []
    for file_path in event_dir.glob("resource-event-*.yaml"):
        for event in load_yaml(file_path).get("resource_events", []):
            if isinstance(event, dict):
                item = event.copy()
                item["__source_file"] = str(file_path)
                events.append(item)
    return events


def parse_resource_subscriptions(bcm_dir: Path) -> List[Dict[str, Any]]:
    event_dir = bcm_dir / "resource-event"
    if not event_dir.exists():
        raise ValueError(f"Missing directory: {event_dir}")

    subscriptions: List[Dict[str, Any]] = []
    for file_path in event_dir.glob("resource-subscription-*.yaml"):
        for subscription in load_yaml(file_path).get("resource_subscriptions", []):
            if isinstance(subscription, dict):
                item = subscription.copy()
                item["__source_file"] = str(file_path)
                subscriptions.append(item)
    return subscriptions


def build_resource_flow_steps(
    process: Dict[str, Any],
    event_versions_by_id: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Builds EventCatalog steps from the resource event_subscription_chain."""
    steps: List[Dict[str, Any]] = []
    edges: Dict[str, List[str]] = {}

    def _add_edge(source_id: str, target_id: str) -> None:
        if not source_id or not target_id:
            return
        edges.setdefault(source_id, [])
        if target_id not in edges[source_id]:
            edges[source_id].append(target_id)

    start = process.get("start") or {}
    if start.get("type") == "interaction":
        interaction_text = start.get("interaction") or "Operational interaction"
        steps.append(
            {
                "id": "START",
                "type": "actor",
                "title": "Process trigger",
                "summary": interaction_text,
                "actor": {
                    "name": "Operational actor",
                    "summary": interaction_text,
                },
            }
        )

    step_id_to_step: Dict[str, Dict[str, Any]] = {}
    emitted_event_to_steps: Dict[str, List[str]] = {}
    consumed_event_by_step: Dict[str, str] = {}
    trigger_steps: List[str] = []

    chain = process.get("event_subscription_chain") or []
    for idx, step in enumerate(chain, start=1):
        step_id = step.get("step_id") or f"STEP.{idx:03d}"
        emitted_event_id = step.get("emits_resource_event")
        consumed_event_id = step.get("consumes_resource_event")
        consumes_trigger = step.get("consumes_trigger")

        flow_step: Dict[str, Any] = {
            "id": step_id,
            "type": "message",
            "title": step_id,
            "summary": step.get("note") or "Resource process step",
        }

        if emitted_event_id:
            flow_step["message"] = {
                "id": slug_from_id(emitted_event_id),
                "version": event_versions_by_id.get(emitted_event_id, "1.0.0"),
            }
        else:
            flow_step["type"] = "node"

        steps.append(flow_step)
        step_id_to_step[step_id] = flow_step

        if emitted_event_id:
            emitted_event_to_steps.setdefault(emitted_event_id, []).append(step_id)

        if isinstance(consumed_event_id, str) and consumed_event_id.strip():
            consumed_event_by_step[step_id] = consumed_event_id.strip()

        if consumes_trigger is not None:
            trigger_steps.append(step_id)

    if "START" in step_id_to_step or any(s.get("id") == "START" for s in steps):
        for target_id in trigger_steps:
            _add_edge("START", target_id)

    for target_step_id, consumed_event in consumed_event_by_step.items():
        producer_steps = emitted_event_to_steps.get(consumed_event, [])
        for producer_step_id in producer_steps:
            _add_edge(producer_step_id, target_step_id)

    for step in steps:
        sid = step.get("id")
        successors = edges.get(sid, [])
        if not successors:
            continue
        if len(successors) == 1:
            step["next_step"] = successors[0]
        else:
            step["next_steps"] = successors

    return steps


def load_processus_ressource_as_flows(
    bcm_input_dir: Path,
    resource_events: List[Dict[str, Any]],
    strict: bool = False,
) -> List[Dict[str, Any]]:
    """Loads external resource processes and transforms them into EventCatalog flows."""
    repo_root = bcm_input_dir.parent
    process_dir = repo_root / "externals" / "processus-ressource"

    if not process_dir.exists():
        logger.info(f"No processus-ressource directory found at {process_dir}, skipping flow export")
        return []

    process_files = sorted(process_dir.glob("processus-ressource-*.yaml"))
    if not process_files:
        logger.info(f"No processus-ressource files found in {process_dir}")
        return []

    event_versions_by_id = {
        event.get("id"): str(event.get("version") or "1.0.0")
        for event in resource_events
        if isinstance(event.get("id"), str)
    }

    flows: List[Dict[str, Any]] = []
    for file_path in process_files:
        try:
            data = load_yaml(file_path) or {}
            process = data.get("processus_ressource") or {}
            if not isinstance(process, dict) or not process:
                if strict:
                    raise ValueError(f"No 'processus_ressource' section in {file_path}")
                logger.warning(f"No 'processus_ressource' section in {file_path}, skipping")
                continue

            process_type = process.get("process_type")
            if process_type and process_type != "ressource":
                logger.debug(f"Skipping non-ressource process in {file_path}: {process_type}")
                continue

            process_id = process.get("id") or file_path.stem
            process_name = process.get("name") or process_id
            meta = data.get("meta") or {}

            flow_steps = build_resource_flow_steps(process, event_versions_by_id)
            if not flow_steps:
                if strict:
                    raise ValueError(f"Process {process_id} has no steps")
                logger.warning(f"Process {process_id} has no steps, skipping")
                continue

            owners_raw = meta.get("owners") or []
            owners = [owner_slug(owner) for owner in owners_raw if owner]
            if not owners:
                owners = ["unknown"]

            flows.append(
                {
                    "id": process_slug_from_id(process_id),
                    "name": process_name,
                    "version": str(meta.get("version") or "1.0.0"),
                    "summary": f"Automatic export of resource process `{process_id}` to an EventCatalog flow.",
                    "owners": owners,
                    "steps": flow_steps,
                    "documentation": process.get("documentation") or {},
                    "metadata": {
                        "bcm": {
                            "source_id": process_id,
                            "source_file": str(file_path),
                            "bcm_type": "processus_ressource",
                            "exported_at": datetime.now().isoformat(),
                        }
                    },
                }
            )

        except Exception as exc:
            if strict:
                raise
            logger.warning(f"Failed to load processus ressource file {file_path}: {exc}")

    return flows


def validate_relations(
    l1: List[Dict[str, Any]],
    services: List[Dict[str, Any]],
    resources: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    subscriptions: List[Dict[str, Any]],
) -> List[str]:
    errors: List[str] = []

    l1_ids = {c.get("id") for c in l1}
    service_ids = {c.get("id") for c in services}
    res_ids = {r.get("id") for r in resources}
    evt_ids = {e.get("id") for e in events}

    l2_ids = {c.get("id") for c in services if c.get("level") == "L2"}

    for cap in services:
        if cap.get("level") == "L2":
            parent = cap.get("parent")
            if parent not in l1_ids:
                errors.append(f"L2 {cap.get('id')} parent L1 not found: {parent}")
        elif cap.get("level") == "L3":
            parent_l2 = cap.get("parent")
            if parent_l2 not in l2_ids:
                errors.append(f"L3 {cap.get('id')} parent L2 not found: {parent_l2}")

    for resource in resources:
        effective_resource_capability = resource.get("emitting_capability")
        preferred_l3 = resource.get("emitting_capability_L3") or []
        if preferred_l3:
            effective_resource_capability = preferred_l3[0]

        if effective_resource_capability not in service_ids:
            errors.append(
                f"Resource {resource.get('id')} emitting capability not found: {effective_resource_capability}"
            )

    for event in events:
        if event.get("emitting_capability") not in service_ids:
            errors.append(
                f"Resource event {event.get('id')} emitting capability not found: {event.get('emitting_capability')}"
            )
        # carried_resource is optional if data is provided (mutually exclusive)
        carried_resource = event.get("carried_resource")
        if carried_resource and carried_resource not in res_ids:
            errors.append(
                f"Resource event {event.get('id')} carried resource not found: {carried_resource}"
            )

    for sub in subscriptions:
        if sub.get("consumer_capability") not in service_ids:
            errors.append(
                f"Resource subscription {sub.get('id')} consumer_capability not found: {sub.get('consumer_capability')}"
            )
        sub_evt = (sub.get("subscribed_resource_event") or {}).get("id")
        if sub_evt not in evt_ids:
            errors.append(
                f"Resource subscription {sub.get('id')} subscribed event not found: {sub_evt}"
            )

    return errors


def normalize_to_eventcatalog(
    l1: List[Dict[str, Any]],
    services_data: List[Dict[str, Any]],
    resources: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    subscriptions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    l1_by_id = {c["id"]: c for c in l1}
    services_by_id = {c["id"]: c for c in services_data}
    resources_by_id = {resource.get("id"): resource for resource in resources}
    l3_children_by_l2_id: Dict[str, List[str]] = {}

    for cap in services_data:
        if cap.get("level") == "L3" and cap.get("parent"):
            l3_children_by_l2_id.setdefault(cap.get("parent"), []).append(cap.get("id"))

    def resolve_service_id(capability_id: str, preferred_l3_ids: List[str] = None) -> str:
        cap = services_by_id.get(capability_id)
        if not cap:
            return capability_id

        if cap.get("level") == "L3":
            return capability_id

        preferred = preferred_l3_ids or []
        l3_children = l3_children_by_l2_id.get(capability_id, [])
        preferred_match = [cap_id for cap_id in preferred if cap_id in l3_children]
        if preferred_match:
            return preferred_match[0]

        return capability_id

    def domain_from_service_id(capability_id: str) -> str:
        cap = services_by_id.get(capability_id)
        if not cap:
            return "unknown-domain"

        parent = cap.get("parent_l1_id")
        if not parent:
            if cap.get("level") == "L2":
                parent = cap.get("parent")
            elif cap.get("level") == "L3":
                parent_l2 = services_by_id.get(cap.get("parent"), {})
                parent = parent_l2.get("parent")

        if not parent or parent not in l1_by_id:
            return "unknown-domain"
        return slug_from_id(parent)

    domains = []
    for cap in l1:
        domains.append(
            {
                "id": slug_from_id(cap["id"]),
                "name": cap.get("name", cap["id"]),
                "summary": cap.get("description", ""),
                "owners": [owner_slug(cap.get("owner", "unknown"))],
                "metadata": {
                    "bcm": {
                        "source_id": cap.get("id"),
                        "source_file": cap.get("__source_file"),
                        "bcm_type": "capability_l1",
                        "zoning": cap.get("zoning", ""),
                        "exported_at": datetime.now().isoformat(),
                    }
                },
            }
        )

    services = []
    for cap in services_data:
        services.append(
            {
                "id": slug_from_id(cap["id"]),
                "name": cap.get("name", cap["id"]),
                "summary": cap.get("description", ""),
                "owners": [owner_slug(cap.get("owner", "unknown"))],
                "_domain": domain_from_service_id(cap.get("id", "")),
                "metadata": {
                    "bcm": {
                        "source_id": cap.get("id"),
                        "source_file": cap.get("__source_file"),
                        "bcm_type": "capability_l3" if cap.get("level") == "L3" else "capability_l2",
                        "level": cap.get("level", "L2"),
                        "parent_l1_id": cap.get("parent_l1_id") if cap.get("level") == "L3" else cap.get("parent"),
                        "parent_l2_id": cap.get("parent") if cap.get("level") == "L3" else None,
                        "zoning": cap.get("zoning", ""),
                        "exported_at": datetime.now().isoformat(),
                    }
                },
            }
        )

    entities = []
    for resource in resources:
        effective_resource_capability = resolve_service_id(
            resource.get("emitting_capability", ""),
            preferred_l3_ids=resource.get("emitting_capability_L3") or [],
        )
        emitting_resource_event_id = first_relation_id(
            resource,
            "emitting_resource_events",
            "emitting_resource_event",
        )
        properties = []
        for field in resource.get("data", []) or []:
            if not field.get("name") or not field.get("type"):
                continue
            properties.append(
                {
                    "name": field.get("name"),
                    "type": field.get("type"),
                    "required": bool(field.get("required", False)),
                    "description": field.get("description", ""),
                }
            )

        entities.append(
            {
                "id": slug_from_id(resource["id"]),
                "name": resource.get("name", resource["id"]),
                "summary": resource.get("definition", ""),
                "owners": [owner_slug("unknown")],
                "properties": properties,
                "_domain": domain_from_service_id(effective_resource_capability),
                "metadata": {
                    "bcm": {
                        "source_id": resource.get("id"),
                        "source_file": resource.get("__source_file"),
                        "bcm_type": "resource",
                        "emitting_capability_id": effective_resource_capability,
                        "emitting_capability_l2_id": resource.get("emitting_capability"),
                        "emitting_capability_l3_ids": resource.get("emitting_capability_L3", []),
                        # Canonical SI key
                        "emitting_resource_event_id": emitting_resource_event_id,
                        # Compatibility alias (used by current generator display)
                        "emitting_business_event_id": emitting_resource_event_id,
                        # Canonical SI key
                        "resource_id": resource.get("id"),
                        # Cross-reference SI -> Business
                        "linked_business_object_id": resource.get("business_object"),
                        # Compatibility alias (field used by current display)
                        "business_object_id": resource.get("business_object"),
                        "exported_at": datetime.now().isoformat(),
                    }
                },
            }
        )

    normalized_events = []
    for event in events:
        effective_event_capability = resolve_service_id(event.get("emitting_capability", ""))
        ressource_id = event.get("carried_resource")
        linked_resource = resources_by_id.get(ressource_id)
        effective_resource_capability = resolve_service_id(
            linked_resource.get("emitting_capability", "") if isinstance(linked_resource, dict) else "",
            preferred_l3_ids=(linked_resource.get("emitting_capability_L3") or []) if isinstance(linked_resource, dict) else [],
        )
        linked_business_object_id = (
            linked_resource.get("business_object")
            if isinstance(linked_resource, dict)
            else None
        )
        entity_slug = slug_from_id(ressource_id) if isinstance(ressource_id, str) and ressource_id else None
        entity_domain = (
            domain_from_service_id(effective_resource_capability)
            if linked_resource
            else domain_from_service_id(effective_event_capability)
        )
        normalized_events.append(
            {
                "id": slug_from_id(event["id"]),
                "name": event.get("name", event["id"]),
                "version": "1.0.0",
                "summary": event.get("definition", ""),
                "owners": [owner_slug("unknown")],
                "_service": slug_from_id(effective_event_capability or "unknown-service"),
                "_domain": domain_from_service_id(effective_event_capability),
                "_entity_slug": entity_slug,
                "_entity_domain": entity_domain,
                "_entity_version": "1.0.0",
                "metadata": {
                    "bcm": {
                        "source_id": event.get("id"),
                        "source_file": event.get("__source_file"),
                        "bcm_type": "resource_event",
                        "emitting_capability_id": effective_event_capability,
                        "emitting_capability_l2_id": event.get("emitting_capability"),
                        # Canonical SI key
                        "resource_id": ressource_id,
                        # Cross-reference SI -> Business
                        "linked_business_object_id": linked_business_object_id,
                        # used by the current generator for the "Associated entity" section
                        "business_object_id": ressource_id,
                        "linked_business_event_id": first_relation_id(
                            event,
                            "business_events",
                            "business_event",
                        ),
                        "scope": normalize_scope(event.get("scope", "public")),
                        "tags": event.get("tags", []),
                        "exported_at": datetime.now().isoformat(),
                    }
                },
            }
        )

    normalized_subscriptions = []
    for sub in subscriptions:
        subscribed_event = sub.get("subscribed_resource_event") or {}
        effective_consumer_capability = resolve_service_id(sub.get("consumer_capability", ""))
        effective_producer_capability = resolve_service_id(subscribed_event.get("emitting_capability", ""))
        normalized_subscriptions.append(
            {
                "id": sub.get("id"),
                "consumer_service": slug_from_id(effective_consumer_capability or "unknown-service"),
                "consumer_domain": domain_from_service_id(effective_consumer_capability),
                "event": {
                    "id": slug_from_id(subscribed_event.get("id", "unknown-event")),
                    "version": "1.0.0",
                },
                "producer_service": slug_from_id(effective_producer_capability or "unknown-service"),
                "scope": normalize_scope(sub.get("scope", "public")),
                "rationale": sub.get("rationale", ""),
                "tags": sub.get("tags", []),
                "metadata": {
                    "bcm": {
                        "source_id": sub.get("id"),
                        "source_file": sub.get("__source_file"),
                        "bcm_type": "resource_subscription",
                        "consumer_capability_id": sub.get("consumer_capability"),
                        "subscribed_event_id": subscribed_event.get("id"),
                        "emitting_capability_id": subscribed_event.get("emitting_capability"),
                        "linked_business_subscription_id": sub.get("linked_business_subscription"),
                        # Compatibility alias
                        "linked_business_subscription": sub.get("linked_business_subscription"),
                        "exported_at": datetime.now().isoformat(),
                    }
                },
            }
        )

    return {
        "domains": domains,
        "services": services,
        "events": normalized_events,
        "entities": entities,
        "subscriptions": normalized_subscriptions,
        "metadata": {
            "normalized_at": datetime.now().isoformat(),
            "normalized_counts": {
                "domains": len(domains),
                "services": len(services),
                "events": len(normalized_events),
                "entities": len(entities),
                "subscriptions": len(normalized_subscriptions),
            },
            "source_counts": {
                "capabilities_l1": len(l1),
                "capabilities_l2": len([cap for cap in services_data if cap.get("level") == "L2"]),
                "capabilities_l3": len([cap for cap in services_data if cap.get("level") == "L3"]),
                "resources": len(resources),
                "resource_events": len(events),
                "resource_subscriptions": len(subscriptions),
            },
            "warnings": [],
            "missing_relations": {},
        },
    }


def print_summary(normalized_data: Dict[str, Any], generation_report: Dict[str, Any] = None) -> None:
    counts = normalized_data["metadata"]["normalized_counts"]
    src = normalized_data["metadata"]["source_counts"]

    print("\n" + "=" * 80)
    print("BCM SI (Resources) -> EventCatalog EXPORT SUMMARY")
    print("=" * 80)

    print("\n[OK] Status: SUCCESS")

    print("\nBCM sources analysed:")
    print(f"   * L1 capabilities: {src['capabilities_l1']}")
    print(f"   * L2 capabilities: {src['capabilities_l2']}")
    if "capabilities_l3" in src:
        print(f"   * L3 capabilities: {src['capabilities_l3']}")
    print(f"   * Resources: {src['resources']}")
    print(f"   * Resource events: {src['resource_events']}")
    print(f"   * Resource subscriptions: {src['resource_subscriptions']}")
    if "resource_processes" in src:
        print(f"   * Resource processes: {src['resource_processes']}")

    print("\nEventCatalog artefacts generated:")
    print(f"   * Domains: {counts['domains']}")
    print(f"   * Services: {counts['services']}")
    print(f"   * Events: {counts['events']}")
    print(f"   * Entities: {counts['entities']}")
    print(f"   * Subscriptions: {counts['subscriptions']}")
    if "flows" in counts:
        print(f"   * Flows: {counts['flows']}")

    if generation_report:
        print(f"\nFiles created: {len(generation_report.get('files_generated', []))}")
        print(f"Generation time: {generation_report.get('duration_seconds', 0):.2f}s")

    print("\n" + "=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export BCM SI (resources) to EventCatalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input ./bcm --output ./views/FOODAROO-SI
  %(prog)s --input ./bcm --output ./views/FOODAROO-SI --dry-run
  %(prog)s --input ./bcm --validate-only --verbose
        """,
    )

    parser.add_argument("--input", "-i", dest="input_dir", required=True)
    parser.add_argument("--output", "-o", dest="output_dir")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: every warning is treated as a blocking error",
    )
    parser.add_argument("--report-json", metavar="FILE")

    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        input_dir = Path(args.input_dir)
        if not input_dir.exists() or not input_dir.is_dir():
            raise ValueError(f"Invalid input directory: {input_dir}")

        if not args.validate_only and not args.output_dir:
            raise ValueError("--output is required unless --validate-only is set")

        logger.info("Parsing BCM SI (resources)...")
        l1, l2 = parse_capabilities(input_dir)
        resources = parse_resources(input_dir)
        events = parse_resource_events(input_dir)
        subscriptions = parse_resource_subscriptions(input_dir)

        relation_errors = validate_relations(l1, l2, resources, events, subscriptions)
        if relation_errors:
            logger.error("Consistency errors detected:")
            for err in relation_errors:
                logger.error(f"  - {err}")
            return 1

        logger.info("Normalizing SI data...")
        normalized_data = normalize_to_eventcatalog(l1, l2, resources, events, subscriptions)

        logger.info("Loading external resource processes for flow export...")
        flow_data = load_processus_ressource_as_flows(input_dir, events, strict=args.strict)
        normalized_data["flows"] = flow_data
        normalized_data["metadata"]["normalized_counts"]["flows"] = len(flow_data)
        normalized_data["metadata"]["source_counts"]["resource_processes"] = len(flow_data)

        if args.validate_only:
            print_summary(normalized_data)
            return 0

        generation_report = None
        if not args.dry_run:
            logger.info("Generating EventCatalog FOODAROO-SI...")
            generator = EventCatalogGenerator(Path(args.output_dir))
            generation_report = generator.generate_catalog(normalized_data)
            if generation_report.get("errors"):
                for err in generation_report["errors"]:
                    logger.error(err)
                return 1
            if args.strict and generation_report.get("warnings"):
                for warning in generation_report.get("warnings", []):
                    logger.error(f"[strict] {warning}")
                return 1
        else:
            logger.info("Dry-run enabled: no files written")

        if args.strict and normalized_data.get("metadata", {}).get("warnings"):
            for warning in normalized_data["metadata"].get("warnings", []):
                logger.error(f"[strict] {warning}")
            return 1

        if args.report_json:
            report = {
                "normalized": normalized_data["metadata"],
                "generation": generation_report,
            }
            with open(args.report_json, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON report saved: {args.report_json}")

        print_summary(normalized_data, generation_report)
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.verbose:
            import traceback

            logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
