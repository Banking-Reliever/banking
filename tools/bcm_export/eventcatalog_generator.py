"""
EventCatalog file generator from normalised BCM data.

This module generates the EventCatalog directory tree and MDX files
from the normalised BCM model.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class EventCatalogGenerator:
    """Main generator for the EventCatalog directory tree."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.domains_dir = self.output_dir / "domains"
        self.flows_dir = self.output_dir / "flows"

    def generate_catalog(self, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates the complete EventCatalog.

        Args:
            normalized_data: Normalised data from BCMNormalizer

        Returns:
            Generation report with statistics and errors
        """
        logger.info(f"Generating EventCatalog in {self.output_dir}")

        start_time = datetime.now()
        report = {
            "generated_at": start_time.isoformat(),
            "output_directory": str(self.output_dir),
            "files_generated": [],
            "errors": [],
            "warnings": []
        }

        try:
            self._create_base_structure()
            self._clean_generated_tree()

            domains_to_generate = normalized_data.get("domains", [])
            services_to_generate = normalized_data.get("services", [])
            entities_to_generate = normalized_data.get("entities", [])
            events_to_generate = normalized_data.get("events", [])
            flows_to_generate = normalized_data.get("flows", [])

            domains_report = self._generate_domains(domains_to_generate, normalized_data)
            report["files_generated"].extend(domains_report["files"])
            report["errors"].extend(domains_report["errors"])
            report["warnings"].extend(domains_report["warnings"])

            services_report = self._generate_services(services_to_generate, normalized_data)
            report["files_generated"].extend(services_report["files"])
            report["errors"].extend(services_report["errors"])
            report["warnings"].extend(services_report["warnings"])

            entities_report = self._generate_entities(entities_to_generate, normalized_data)
            report["files_generated"].extend(entities_report["files"])
            report["errors"].extend(entities_report["errors"])
            report["warnings"].extend(entities_report["warnings"])

            events_report = self._generate_events(events_to_generate, normalized_data)
            report["files_generated"].extend(events_report["files"])
            report["errors"].extend(events_report["errors"])
            report["warnings"].extend(events_report["warnings"])

            flows_report = self._generate_flows(flows_to_generate, normalized_data)
            report["files_generated"].extend(flows_report["files"])
            report["errors"].extend(flows_report["errors"])
            report["warnings"].extend(flows_report["warnings"])

            end_time = datetime.now()
            report["duration_seconds"] = (end_time - start_time).total_seconds()
            report["success"] = len(report["errors"]) == 0

            logger.info(f"EventCatalog generation completed in {report['duration_seconds']:.2f}s")
            if report["errors"]:
                logger.error(f"Generation completed with {len(report['errors'])} errors")

        except Exception as e:
            logger.error(f"Fatal error during EventCatalog generation: {e}")
            report["errors"].append(f"Fatal error: {e}")
            report["success"] = False

        return report

    def _create_base_structure(self):
        """Creates the base directory structure."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.domains_dir.mkdir(exist_ok=True)
        self.flows_dir.mkdir(exist_ok=True)

        gitignore_path = self.output_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = """# Generated files
*.tmp
.DS_Store
"""
            gitignore_path.write_text(gitignore_content, encoding='utf-8')

    def _clean_generated_tree(self):
        """Removes the generated tree to avoid stale artefacts."""
        if self.domains_dir.exists():
            shutil.rmtree(self.domains_dir)
        self.domains_dir.mkdir(parents=True, exist_ok=True)

        if self.flows_dir.exists():
            shutil.rmtree(self.flows_dir)
        self.flows_dir.mkdir(parents=True, exist_ok=True)

    def _generate_domains(self, domains: List[Dict], normalized_data: Dict) -> Dict[str, Any]:
        """Generates domain files."""
        report = {"files": [], "errors": [], "warnings": []}

        for domain in domains:
            try:
                enriched_domain = self._enrich_domain_with_relations(domain, normalized_data)

                domain_dir = self.domains_dir / domain["id"]
                domain_dir.mkdir(exist_ok=True)

                domain_file = domain_dir / "index.mdx"
                content = self._generate_domain_mdx(enriched_domain)
                domain_file.write_text(content, encoding='utf-8')

                report["files"].append(str(domain_file))

                ubiquitous_language_file = domain_dir / "ubiquitous-language.mdx"
                ubiquitous_language_content = self._generate_domain_ubiquitous_language_mdx(enriched_domain)
                ubiquitous_language_file.write_text(ubiquitous_language_content, encoding='utf-8')

                report["files"].append(str(ubiquitous_language_file))
                logger.debug(f"Generated domain: {domain['id']}")

            except Exception as e:
                error_msg = f"Failed to generate domain {domain.get('id', 'unknown')}: {e}"
                report["errors"].append(error_msg)
                logger.error(error_msg)

        return report

    def _generate_services(self, services: List[Dict], normalized_data: Dict) -> Dict[str, Any]:
        """Generates service files."""
        report = {"files": [], "errors": [], "warnings": []}

        for service in services:
            try:
                enriched_service = self._enrich_service_with_events(service, normalized_data)

                domain_slug = service.get("_domain", "unknown-domain")
                domain_dir = self.domains_dir / domain_slug
                services_dir = domain_dir / "services" / service["id"]
                services_dir.mkdir(parents=True, exist_ok=True)

                service_file = services_dir / "index.mdx"
                content = self._generate_service_mdx(enriched_service)
                service_file.write_text(content, encoding='utf-8')

                report["files"].append(str(service_file))
                logger.debug(f"Generated service: {domain_slug}/{service['id']}")

            except Exception as e:
                error_msg = f"Failed to generate service {service.get('id', 'unknown')}: {e}"
                report["errors"].append(error_msg)
                logger.error(error_msg)

        return report

    def _generate_entities(self, entities: List[Dict], normalized_data: Dict) -> Dict[str, Any]:
        """Generates entity files."""
        report = {"files": [], "errors": [], "warnings": []}

        for entity in entities:
            try:
                domain_slug = entity.get("_domain", "unknown-domain")
                domain_dir = self.domains_dir / domain_slug
                entities_dir = domain_dir / "entities" / entity["id"]
                entities_dir.mkdir(parents=True, exist_ok=True)

                entity_file = entities_dir / "index.mdx"
                content = self._generate_entity_mdx(entity)
                entity_file.write_text(content, encoding='utf-8')

                report["files"].append(str(entity_file))
                logger.debug(f"Generated entity: {domain_slug}/{entity['id']}")

            except Exception as e:
                error_msg = f"Failed to generate entity {entity.get('id', 'unknown')}: {e}"
                report["errors"].append(error_msg)
                logger.error(error_msg)

        return report

    def _generate_events(self, events: List[Dict], normalized_data: Dict) -> Dict[str, Any]:
        """Generates event files."""
        report = {"files": [], "errors": [], "warnings": []}

        for event in events:
            try:
                domain_slug = event.get("_domain", "unknown-domain")
                service_slug = event.get("_service", "unknown-service")

                domain_dir = self.domains_dir / domain_slug
                events_dir = domain_dir / "services" / service_slug / "events" / event["id"]
                events_dir.mkdir(parents=True, exist_ok=True)

                event_file = events_dir / "index.mdx"
                content = self._generate_event_mdx(event)
                event_file.write_text(content, encoding='utf-8')

                report["files"].append(str(event_file))
                logger.debug(f"Generated event: {domain_slug}/{service_slug}/{event['id']}")

            except Exception as e:
                error_msg = f"Failed to generate event {event.get('id', 'unknown')}: {e}"
                report["errors"].append(error_msg)
                logger.error(error_msg)

        return report

    def _generate_flows(self, flows: List[Dict], normalized_data: Dict) -> Dict[str, Any]:
        """Generates flow files."""
        report = {"files": [], "errors": [], "warnings": []}

        for flow in flows:
            try:
                flow_dir = self.flows_dir / flow["id"]
                flow_dir.mkdir(parents=True, exist_ok=True)

                flow_file = flow_dir / "index.mdx"
                content = self._generate_flow_mdx(flow)
                flow_file.write_text(content, encoding='utf-8')

                report["files"].append(str(flow_file))
                logger.debug(f"Generated flow: {flow['id']}")

            except Exception as e:
                error_msg = f"Failed to generate flow {flow.get('id', 'unknown')}: {e}"
                report["errors"].append(error_msg)
                logger.error(error_msg)

        return report

    def _enrich_domain_with_relations(self, domain: Dict, normalized_data: Dict) -> Dict:
        """Enriches a domain with its services, entities and ubiquitous language."""
        enriched = domain.copy()

        domain_services = [
            {"id": svc["id"]}
            for svc in normalized_data["services"]
            if svc.get("_domain") == domain["id"]
        ]
        enriched["services"] = domain_services

        domain_entities = [
            {"id": ent["id"]}
            for ent in normalized_data["entities"]
            if ent.get("_domain") == domain["id"]
        ]
        enriched["entities"] = domain_entities

        domain_concepts = [
            concept
            for concept in normalized_data.get("concepts", [])
            if concept.get("_domain") == domain["id"]
        ]
        enriched["ubiquitous_language"] = self._build_domain_ubiquitous_language(
            domain_id=domain["id"],
            concepts=domain_concepts,
            entities=normalized_data.get("entities", [])
        )

        return enriched

    def _build_domain_ubiquitous_language(self, domain_id: str, concepts: List[Dict], entities: List[Dict]) -> Dict[str, Any]:
        """Builds a ubiquitous language view from the domain's business concepts and objects."""
        domain_entities = [entity for entity in entities if entity.get("_domain") == domain_id]

        glossary_by_name = {}
        for entity in domain_entities:
            for prop in entity.get("properties", []):
                name = (prop.get("name") or "").strip()
                if not name:
                    continue
                if name not in glossary_by_name:
                    glossary_by_name[name] = {
                        "name": name,
                        "type": prop.get("type", "N/A"),
                        "description": prop.get("description", ""),
                        "sources": [entity.get("id")]
                    }
                elif entity.get("id") not in glossary_by_name[name]["sources"]:
                    glossary_by_name[name]["sources"].append(entity.get("id"))

        normalized_concepts = []
        for concept in concepts:
            normalized_concepts.append({
                "id": concept.get("id"),
                "source_id": concept.get("metadata", {}).get("bcm", {}).get("source_id"),
                "name": concept.get("name"),
                "summary": concept.get("summary"),
                "scope": concept.get("scope", []),
                "tags": concept.get("tags", []),
                "properties": [
                    {
                        "name": prop.get("name"),
                        "type": prop.get("type"),
                        "description": prop.get("description", "")
                    }
                    for prop in concept.get("properties", [])
                ]
            })

        terms = sorted(glossary_by_name.values(), key=lambda t: t["name"].lower())

        return {
            "concepts": normalized_concepts,
            "terms": terms
        }

    def _enrich_service_with_events(self, service: Dict, normalized_data: Dict) -> Dict:
        """Enriches a service with its emitted/received events."""
        enriched = service.copy()
        service_domain = service.get("_domain", "unknown-domain")

        service_events = [
            {"id": evt["id"], "version": evt["version"]}
            for evt in normalized_data["events"]
            if evt.get("_service") == service["id"] and evt.get("_domain") == service_domain
        ]
        enriched["sends"] = service_events

        service_subscriptions = [
            sub for sub in normalized_data.get("subscriptions", [])
            if sub.get("consumer_service") == service["id"] and sub.get("consumer_domain") == service_domain
        ]

        receives_events = []
        for sub in service_subscriptions:
            event_ref = sub.get("event", {})
            event_id = event_ref.get("id")
            event_version = event_ref.get("version")
            if event_id and event_version:
                receives_events.append({
                    "id": event_id,
                    "version": event_version
                })

        seen = set()
        deduped_receives = []
        for event in receives_events:
            key = (event["id"], event["version"])
            if key not in seen:
                seen.add(key)
                deduped_receives.append(event)

        enriched["receives"] = deduped_receives
        return enriched

    def _generate_domain_mdx(self, domain: Dict) -> str:
        """Generates the MDX content for a domain."""
        frontmatter = {
            "id": domain["id"],
            "name": domain["name"],
            "summary": domain["summary"],
            "version": domain.get("version", "1.0.0"),
            "owners": domain["owners"]
        }

        if domain.get("services"):
            frontmatter["services"] = domain["services"]

        if domain.get("entities"):
            frontmatter["entities"] = domain["entities"]

        badges = []
        if domain.get("metadata", {}).get("bcm", {}).get("zoning"):
            badges.append({
                "content": f"Zone: {domain['metadata']['bcm']['zoning']}",
                "backgroundColor": "blue",
                "textColor": "white"
            })

        if badges:
            frontmatter["badges"] = badges

        yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

        content = f"""---
{yaml_content}---

# {domain['name']}

{domain['summary']}

## Services

This domain contains the following business services:

{self._format_services_list(domain.get('services', []))}

## Entities

Business entities managed by this domain:

{self._format_entities_list(domain.get('entities', []))}

## Ubiquitous Language

{self._format_ubiquitous_language(domain.get('ubiquitous_language', {}))}

## BCM Metadata

- **BCM Source ID**: {domain.get('metadata', {}).get('bcm', {}).get('source_id', 'N/A')}
- **Type**: {domain.get('metadata', {}).get('bcm', {}).get('bcm_type', 'N/A')}
- **Urbanization zone**: {domain.get('metadata', {}).get('bcm', {}).get('zoning', 'N/A')}
"""

        return content

    def _generate_service_mdx(self, service: Dict) -> str:
        """Generates the MDX content for a service."""
        frontmatter = {
            "id": service["id"],
            "name": service["name"],
            "summary": service["summary"],
            "version": service.get("version", "1.0.0"),
            "owners": service["owners"]
        }

        if service.get("receives"):
            frontmatter["receives"] = service["receives"]

        if service.get("sends"):
            frontmatter["sends"] = [
                {"id": event["id"], "version": event["version"]}
                for event in service["sends"]
            ]

        yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

        content = f"""---
{yaml_content}---

# {service['name']}

{service['summary']}

## Emitted Events

This service emits the following business events:

{self._format_events_list(service.get('sends', []))}

## Subscribed Events

This service subscribes to the following business events:

{self._format_events_list(service.get('receives', []))}

## BCM Metadata

- **BCM Source ID**: {service.get('metadata', {}).get('bcm', {}).get('source_id', 'N/A')}
- **L1 Parent**: {service.get('metadata', {}).get('bcm', {}).get('parent_l1_id', 'N/A')}
- **Type**: {service.get('metadata', {}).get('bcm', {}).get('bcm_type', 'N/A')}
"""

        return content

    def _generate_entity_mdx(self, entity: Dict) -> str:
        """Generates the MDX content for an entity."""
        frontmatter = {
            "id": entity["id"],
            "name": entity["name"],
            "version": entity.get("version", "1.0.0"),
            "summary": entity["summary"],
            "owners": entity["owners"]
        }

        if entity.get("properties"):
            for prop in entity["properties"]:
                if prop.get("required"):
                    frontmatter["identifier"] = prop["name"]
                    break

        if entity.get("properties"):
            frontmatter["properties"] = entity["properties"]

        yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

        content = f"""---
{yaml_content}---

# {entity['name']}

{entity['summary']}

## Properties

{self._format_properties_table(entity.get('properties', []))}

## Conceptual Positioning

{self._format_entity_concept_context(entity.get('concept_context', {}))}

## BCM Metadata

- **BCM Source ID**: {entity.get('metadata', {}).get('bcm', {}).get('source_id', 'N/A')}
- **Emitting capability**: {entity.get('metadata', {}).get('bcm', {}).get('emitting_capability_id', 'N/A')}
- **Type**: {entity.get('metadata', {}).get('bcm', {}).get('bcm_type', 'N/A')}
"""

        return content

    def _generate_event_mdx(self, event: Dict) -> str:
        """Generates the MDX content for an event."""
        frontmatter = {
            "id": event["id"],
            "name": event["name"],
            "version": event["version"],
            "summary": event["summary"],
            "owners": event["owners"]
        }

        badges = []
        bcm_tags = event.get("metadata", {}).get("bcm", {}).get("tags", [])
        for tag in bcm_tags:
            badges.append({
                "content": f"Tag: {tag}",
                "backgroundColor": "blue",
                "textColor": "white"
            })

        bcm_scope = event.get("metadata", {}).get("bcm", {}).get("scope")
        if bcm_scope and bcm_scope != "public":
            badges.append({
                "content": f"Scope: {bcm_scope}",
                "backgroundColor": "orange",
                "textColor": "white"
            })

        if badges:
            frontmatter["badges"] = badges

        yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

        entity_slug = event.get("_entity_slug")
        entity_version = event.get("_entity_version", "1.0.0")

        if entity_slug:
            entity_link = f"/docs/entities/{entity_slug}/{entity_version}"
            entity_reference_line = (
                f"This event carries the business entity "
                f"**[{entity_slug}]({entity_link})** "
                f"(BCM reference: `{event.get('metadata', {}).get('bcm', {}).get('business_object_id', 'N/A')}`)."
            )
        else:
            entity_reference_line = (
                "This event carries an unresolved business entity "
                f"(BCM reference: `{event.get('metadata', {}).get('bcm', {}).get('business_object_id', 'N/A')}`)."
            )

        content = f"""---
{yaml_content}---

# {event['name']}

{event['summary']}

## Associated Entity

{entity_reference_line}

## BCM Metadata

- **BCM Source ID**: {event.get('metadata', {}).get('bcm', {}).get('source_id', 'N/A')}
- **Emitting capability**: {event.get('metadata', {}).get('bcm', {}).get('emitting_capability_id', 'N/A')}
- **Carried business object**: {event.get('metadata', {}).get('bcm', {}).get('business_object_id', 'N/A')}
- **Scope**: {event.get('metadata', {}).get('bcm', {}).get('scope', 'N/A')}
- **Type**: {event.get('metadata', {}).get('bcm', {}).get('bcm_type', 'N/A')}
"""

        return content

    def _generate_flow_mdx(self, flow: Dict) -> str:
        """Generates the MDX content for a flow."""
        metadata = flow.get("metadata", {}).get("bcm", {})
        bcm_type = metadata.get("bcm_type", "processus_metier")

        if bcm_type == "processus_ressource":
            source_badge = "Source: BCM Resource Process"
            source_description = (
                "This flow is automatically generated from an **external resource process** "
                "in the BCM repository."
            )
        else:
            source_badge = "Source: BCM Business Process"
            source_description = (
                "This flow is automatically generated from an **external business process** "
                "in the BCM repository."
            )

        frontmatter = {
            "id": flow["id"],
            "name": flow["name"],
            "version": flow.get("version", "1.0.0"),
            "summary": flow.get("summary", ""),
            "owners": flow.get("owners", ["unknown-owner"]),
            "steps": flow.get("steps", [])
        }

        normalized_frontmatter_doc = self._build_flow_frontmatter_documentation(
            flow.get("documentation") or {},
            bcm_type,
        )
        if normalized_frontmatter_doc:
            frontmatter["documentation"] = normalized_frontmatter_doc

        badges = [
            {
                "content": source_badge,
                "backgroundColor": "purple",
                "textColor": "white"
            }
        ]
        frontmatter["badges"] = badges

        yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)

        source_id = metadata.get("source_id", "N/A")
        source_file = metadata.get("source_file", "N/A")
        documentation_block = self._format_process_documentation(
            flow.get("documentation") or {},
            bcm_type,
        )

        content = f"""---
{yaml_content}---

# {flow.get('name', flow.get('id', 'Flow'))}

{flow.get('summary', '')}

## Description

{source_description}

## Process Documentation

{documentation_block}

## BCM Traceability

- **BCM source ID**: `{source_id}`
- **Source file**: `{source_file}`
"""

        return content

    def _build_flow_frontmatter_documentation(self, documentation: Dict[str, Any], bcm_type: str) -> Dict[str, Any]:
        """Prepares a compact documentation block for the frontmatter."""
        if not isinstance(documentation, dict) or not documentation:
            return {}

        def _clean_text(value: Any) -> str:
            if isinstance(value, str) and value.strip():
                return value.strip()
            return ""

        def _clean_list(value: Any) -> List[str]:
            if not isinstance(value, list):
                return []
            cleaned = []
            for item in value:
                if isinstance(item, str) and item.strip():
                    cleaned.append(item.strip())
            return cleaned

        value_key = "valeur_metier" if bcm_type == "processus_metier" else "valeur_operationnelle"

        portee = documentation.get("portee") if isinstance(documentation.get("portee"), dict) else {}
        scenarios = documentation.get("scenarios") if isinstance(documentation.get("scenarios"), dict) else {}

        payload = {
            "objectif": _clean_text(documentation.get("objectif")),
            value_key: _clean_text(documentation.get(value_key)),
            "portee": {
                "inclut": _clean_list(portee.get("inclut")) if isinstance(portee, dict) else [],
                "exclut": _clean_list(portee.get("exclut")) if isinstance(portee, dict) else [],
            },
            "parties_prenantes": _clean_list(documentation.get("parties_prenantes")),
            "preconditions": _clean_list(documentation.get("preconditions")),
            "postconditions": _clean_list(documentation.get("postconditions")),
            "scenarios": {
                "nominal": _clean_text(scenarios.get("nominal")) if isinstance(scenarios, dict) else "",
                "alternatif": _clean_text(scenarios.get("alternatif")) if isinstance(scenarios, dict) else "",
            },
            "indicateurs_suivi": _clean_list(documentation.get("indicateurs_suivi")),
        }

        has_content = False
        for key, value in payload.items():
            if isinstance(value, str) and value:
                has_content = True
                break
            if isinstance(value, list) and value:
                has_content = True
                break
            if isinstance(value, dict):
                if any((isinstance(v, str) and v) or (isinstance(v, list) and v) for v in value.values()):
                    has_content = True
                    break

        return payload if has_content else {}

    def _format_process_documentation(self, documentation: Dict[str, Any], bcm_type: str) -> str:
        """Formats process documentation for markdown rendering."""
        if not documentation:
            return "_No detailed documentation was provided in the source process file._"

        def _as_list(value: Any) -> List[str]:
            if not isinstance(value, list):
                return []
            items = []
            for item in value:
                if isinstance(item, str) and item.strip():
                    items.append(item.strip())
            return items

        def _as_text(value: Any, default: str = "N/A") -> str:
            if isinstance(value, str) and value.strip():
                return value.strip()
            return default

        value_field_label = "Business value" if bcm_type == "processus_metier" else "Operational value"
        value_field_key = "valeur_metier" if bcm_type == "processus_metier" else "valeur_operationnelle"

        objectif = _as_text(documentation.get("objectif"))
        value_text = _as_text(documentation.get(value_field_key))

        portee = documentation.get("portee") if isinstance(documentation.get("portee"), dict) else {}
        inclut = _as_list(portee.get("inclut")) if isinstance(portee, dict) else []
        exclut = _as_list(portee.get("exclut")) if isinstance(portee, dict) else []

        parties_prenantes = _as_list(documentation.get("parties_prenantes"))
        preconditions = _as_list(documentation.get("preconditions"))
        postconditions = _as_list(documentation.get("postconditions"))
        indicateurs = _as_list(documentation.get("indicateurs_suivi"))

        scenarios = documentation.get("scenarios") if isinstance(documentation.get("scenarios"), dict) else {}
        scenario_nominal = _as_text(scenarios.get("nominal")) if isinstance(scenarios, dict) else "N/A"
        scenario_alternatif = _as_text(scenarios.get("alternatif")) if isinstance(scenarios, dict) else "N/A"

        def _bullets(items: List[str], empty_text: str = "N/A") -> str:
            if not items:
                return f"- {empty_text}"
            return "\n".join(f"- {item}" for item in items)

        return f"""### Objective

{objectif}

### {value_field_label}

{value_text}

### Scope

**Includes:**
{_bullets(inclut)}

**Excludes:**
{_bullets(exclut)}

### Stakeholders

{_bullets(parties_prenantes)}

### Preconditions

{_bullets(preconditions)}

### Postconditions

{_bullets(postconditions)}

### Scenarios

- **Nominal:** {scenario_nominal}
- **Alternative:** {scenario_alternatif}

### Tracking indicators

{_bullets(indicateurs)}
"""

    def _format_services_list(self, services: List[Dict]) -> str:
        """Formats a list of services as markdown."""
        if not services:
            return "_No service defined._"

        return "\n".join(f"- **{service['id']}**" for service in services)

    def _format_entities_list(self, entities: List[Dict]) -> str:
        """Formats a list of entities as markdown."""
        if not entities:
            return "_No entity defined._"

        return "\n".join(f"- **{entity['id']}**" for entity in entities)

    def _format_events_list(self, events: List[Dict]) -> str:
        """Formats a list of events as markdown."""
        if not events:
            return "_No event defined._"

        lines = []
        for event in events:
            version = event.get("version", "N/A")
            lines.append(f"- **{event['id']}** (v{version})")

        return "\n".join(lines)

    def _format_properties_table(self, properties: List[Dict]) -> str:
        """Formats entity properties as a markdown table."""
        if not properties:
            return "_No property defined._"

        lines = [
            "| Name | Type | Required | Description |",
            "|-----|------|-------------|-------------|"
        ]

        for prop in properties:
            required = "✅" if prop.get("required") else "❌"
            lines.append(
                f"| {prop['name']} | {prop['type']} | {required} | {prop.get('description', '')} |"
            )

        return "\n".join(lines)

    def _format_entity_concept_context(self, context: Dict[str, Any]) -> str:
        """Formats the conceptual positioning block of a business object within its concept."""
        if not context:
            return "_No business concept was automatically matched to this object._"

        matching = context.get("matching", {})
        overlap_fields = matching.get("overlap_fields", [])
        overlap_fields_text = ", ".join(overlap_fields) if overlap_fields else "no common field identified"

        scope = context.get("scope", [])
        scope_text = ", ".join(scope) if scope else "N/A"

        return (
            f"- **Linked business concept**: `{context.get('id', 'N/A')}` — **{context.get('name', 'N/A')}**\n"
            f"- **Concept definition**: {context.get('definition', 'N/A')}\n"
            f"- **Scope**: {scope_text}\n"
            f"- **Automatic matching**: score `{matching.get('score', 0)}` ; common fields: {overlap_fields_text}"
        )

    def _format_ubiquitous_language(self, ubiquitous_language: Dict[str, Any]) -> str:
        """Formats the ubiquitous language section of a domain."""
        def _escape_table_cell(value: Any) -> str:
            text = "" if value is None else str(value)
            # Avoid MDX/HTML errors in table cells
            text = text.replace("&", "&amp;")
            text = text.replace("<", "&lt;").replace(">", "&gt;")
            text = text.replace("|", "\\|")
            text = text.replace("\n", "<br/>")
            return text

        concepts = ubiquitous_language.get("concepts", [])
        terms = ubiquitous_language.get("terms", [])

        concept_lines = ["### Canonical business concepts", ""]
        if concepts:
            for concept in concepts:
                scope = ", ".join(concept.get("scope", [])) if concept.get("scope") else "N/A"
                concept_reference = concept.get("source_id") or concept.get("id", "N/A")
                concept_lines.append(
                    f"- **{concept.get('name', 'N/A')}** (`{concept_reference}`) — {concept.get('summary', '')}"
                )
                concept_lines.append(f"  - Scope: {scope}")
        else:
            concept_lines.append("_No canonical business concept documented for this domain._")

        terms_lines = ["", "### Business glossary (objects & properties)", ""]
        if terms:
            terms_lines.append("| Term | Type | Description | Source objects |")
            terms_lines.append("|---|---|---|---|")
            for term in terms:
                sources = ", ".join(f"`{source}`" for source in term.get("sources", [])) or "N/A"
                terms_lines.append(
                    f"| {_escape_table_cell(term.get('name', 'N/A'))} | {_escape_table_cell(term.get('type', 'N/A'))} | {_escape_table_cell(term.get('description', ''))} | {_escape_table_cell(sources)} |"
                )
        else:
            terms_lines.append("_No business term was extracted from the domain objects._")

        return "\n".join(concept_lines + terms_lines)

    def _generate_domain_ubiquitous_language_mdx(self, domain: Dict[str, Any]) -> str:
        """Generates the `ubiquitous-language.mdx` file expected by EventCatalog."""
        ubiquitous_language = domain.get("ubiquitous_language", {})
        concepts = ubiquitous_language.get("concepts", [])
        terms = ubiquitous_language.get("terms", [])

        dictionary = []

        for concept in concepts:
            concept_ref = concept.get("source_id") or concept.get("id") or "N/A"
            concept_scope = ", ".join(concept.get("scope", [])) if concept.get("scope") else "N/A"
            concept_summary = concept.get("summary") or "Canonical business concept"
            concept_definition = concept.get("summary") or "No description provided."

            dictionary.append({
                "id": concept_ref,
                "name": concept.get("name") or concept_ref,
                "summary": concept_summary,
                "description": (
                    f"BCM concept: `{concept_ref}`\n\n"
                    f"{concept_definition}\n\n"
                    f"Scope: {concept_scope}"
                ),
                "icon": "BookOpen"
            })

        for term in terms:
            term_name = term.get("name") or "N/A"
            term_type = term.get("type") or "N/A"
            term_description = term.get("description") or "No description provided."
            sources = term.get("sources", [])
            sources_text = ", ".join(f"`{source}`" for source in sources) if sources else "N/A"

            dictionary.append({
                "id": term_name,
                "name": term_name,
                "summary": term_description,
                "description": (
                    f"Type: `{term_type}`\n\n"
                    f"{term_description}\n\n"
                    f"Source objects: {sources_text}"
                ),
                "icon": "List"
            })

        frontmatter = {
            "dictionary": dictionary
        }

        yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)

        domain_name = domain.get("name", "domain")
        return f"""---
{yaml_content}---
This page is automatically generated from the business concepts and objects of domain **{domain_name}**.
"""
