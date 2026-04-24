"""
Générateur de fichiers EventCatalog à partir des données BCM normalisées.

Ce module génère l'arborescence et les fichiers MDX EventCatalog
à partir du modèle BCM normalisé.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class EventCatalogGenerator:
    """Générateur principal pour l'arborescence EventCatalog."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.domains_dir = self.output_dir / "domains"
        self.flows_dir = self.output_dir / "flows"

    def generate_catalog(self, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère l'ensemble du catalogue EventCatalog.

        Args:
            normalized_data: Données normalisées du BCMNormalizer

        Returns:
            Rapport de génération avec statistiques et erreurs
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
        """Crée la structure de répertoires de base."""
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
        """Supprime l'arborescence générée pour éviter les artefacts obsolètes."""
        if self.domains_dir.exists():
            shutil.rmtree(self.domains_dir)
        self.domains_dir.mkdir(parents=True, exist_ok=True)

        if self.flows_dir.exists():
            shutil.rmtree(self.flows_dir)
        self.flows_dir.mkdir(parents=True, exist_ok=True)

    def _generate_domains(self, domains: List[Dict], normalized_data: Dict) -> Dict[str, Any]:
        """Génère les fichiers de domains."""
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
        """Génère les fichiers de services."""
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
        """Génère les fichiers d'entités."""
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
        """Génère les fichiers d'événements."""
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
        """Génère les fichiers de flows."""
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
        """Enrichit un domain avec ses services, entités et langage ubiquitaire."""
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
        """Construit une vue de langage ubiquitaire à partir des concepts et objets métier du domaine."""
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
        """Enrichit un service avec ses événements émis/reçus."""
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
        """Génère le contenu MDX d'un domain."""
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

Ce domaine contient les services métier suivants :

{self._format_services_list(domain.get('services', []))}

## Entités

Les entités métier gérées par ce domaine :

{self._format_entities_list(domain.get('entities', []))}

## Ubiquitous Language

{self._format_ubiquitous_language(domain.get('ubiquitous_language', {}))}

## Métadonnées BCM

- **ID Source BCM**: {domain.get('metadata', {}).get('bcm', {}).get('source_id', 'N/A')}
- **Type**: {domain.get('metadata', {}).get('bcm', {}).get('bcm_type', 'N/A')}
- **Zone d'urbanisation**: {domain.get('metadata', {}).get('bcm', {}).get('zoning', 'N/A')}
"""

        return content

    def _generate_service_mdx(self, service: Dict) -> str:
        """Génère le contenu MDX d'un service."""
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

## Événements émis

Ce service émet les événements métier suivants :

{self._format_events_list(service.get('sends', []))}

## Événements souscrits

Ce service souscrit aux événements métier suivants :

{self._format_events_list(service.get('receives', []))}

## Métadonnées BCM

- **ID Source BCM**: {service.get('metadata', {}).get('bcm', {}).get('source_id', 'N/A')}
- **Parent L1**: {service.get('metadata', {}).get('bcm', {}).get('parent_l1_id', 'N/A')}
- **Type**: {service.get('metadata', {}).get('bcm', {}).get('bcm_type', 'N/A')}
"""

        return content

    def _generate_entity_mdx(self, entity: Dict) -> str:
        """Génère le contenu MDX d'une entité."""
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

## Propriétés

{self._format_properties_table(entity.get('properties', []))}

## Positionnement conceptuel

{self._format_entity_concept_context(entity.get('concept_context', {}))}

## Métadonnées BCM

- **ID Source BCM**: {entity.get('metadata', {}).get('bcm', {}).get('source_id', 'N/A')}
- **Capacité émettrice**: {entity.get('metadata', {}).get('bcm', {}).get('emitting_capability_id', 'N/A')}
- **Type**: {entity.get('metadata', {}).get('bcm', {}).get('bcm_type', 'N/A')}
"""

        return content

    def _generate_event_mdx(self, event: Dict) -> str:
        """Génère le contenu MDX d'un événement."""
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
                f"Cet événement porte l'entité métier "
                f"**[{entity_slug}]({entity_link})** "
                f"(référence BCM: `{event.get('metadata', {}).get('bcm', {}).get('business_object_id', 'N/A')}`)."
            )
        else:
            entity_reference_line = (
                "Cet événement porte une entité métier non résolue "
                f"(référence BCM: `{event.get('metadata', {}).get('bcm', {}).get('business_object_id', 'N/A')}`)."
            )

        content = f"""---
{yaml_content}---

# {event['name']}

{event['summary']}

## Entité associée

{entity_reference_line}

## Métadonnées BCM

- **ID Source BCM**: {event.get('metadata', {}).get('bcm', {}).get('source_id', 'N/A')}
- **Capacité émettrice**: {event.get('metadata', {}).get('bcm', {}).get('emitting_capability_id', 'N/A')}
- **Objet métier porté**: {event.get('metadata', {}).get('bcm', {}).get('business_object_id', 'N/A')}
- **Portée**: {event.get('metadata', {}).get('bcm', {}).get('scope', 'N/A')}
- **Type**: {event.get('metadata', {}).get('bcm', {}).get('bcm_type', 'N/A')}
"""

        return content

    def _generate_flow_mdx(self, flow: Dict) -> str:
        """Génère le contenu MDX d'un flow."""
        metadata = flow.get("metadata", {}).get("bcm", {})
        bcm_type = metadata.get("bcm_type", "processus_metier")

        if bcm_type == "processus_ressource":
            source_badge = "Source: Processus Ressource BCM"
            source_description = (
                "Ce flow est généré automatiquement depuis un **processus ressource externe** "
                "du référentiel BCM."
            )
        else:
            source_badge = "Source: Processus Métier BCM"
            source_description = (
                "Ce flow est généré automatiquement depuis un **processus métier externe** "
                "du référentiel BCM."
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

## Documentation du processus

{documentation_block}

## Traçabilité BCM

- **ID source BCM**: `{source_id}`
- **Fichier source**: `{source_file}`
"""

        return content

    def _build_flow_frontmatter_documentation(self, documentation: Dict[str, Any], bcm_type: str) -> Dict[str, Any]:
        """Prépare un bloc documentation compact pour le frontmatter."""
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
        """Formate la documentation des processus pour rendu markdown."""
        if not documentation:
            return "_Aucune documentation détaillée n'a été fournie dans le fichier processus source._"

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

        value_field_label = "Valeur métier" if bcm_type == "processus_metier" else "Valeur opérationnelle"
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

        return f"""### Objectif

{objectif}

### {value_field_label}

{value_text}

### Portée

**Inclut :**
{_bullets(inclut)}

**Exclut :**
{_bullets(exclut)}

### Parties prenantes

{_bullets(parties_prenantes)}

### Préconditions

{_bullets(preconditions)}

### Postconditions

{_bullets(postconditions)}

### Scénarios

- **Nominal :** {scenario_nominal}
- **Alternatif :** {scenario_alternatif}

### Indicateurs de suivi

{_bullets(indicateurs)}
"""

    def _format_services_list(self, services: List[Dict]) -> str:
        """Formate une liste de services en markdown."""
        if not services:
            return "_Aucun service défini._"

        return "\n".join(f"- **{service['id']}**" for service in services)

    def _format_entities_list(self, entities: List[Dict]) -> str:
        """Formate une liste d'entités en markdown."""
        if not entities:
            return "_Aucune entité définie._"

        return "\n".join(f"- **{entity['id']}**" for entity in entities)

    def _format_events_list(self, events: List[Dict]) -> str:
        """Formate une liste d'événements en markdown."""
        if not events:
            return "_Aucun événement défini._"

        lines = []
        for event in events:
            version = event.get("version", "N/A")
            lines.append(f"- **{event['id']}** (v{version})")

        return "\n".join(lines)

    def _format_properties_table(self, properties: List[Dict]) -> str:
        """Formate les propriétés d'une entité en tableau markdown."""
        if not properties:
            return "_Aucune propriété définie._"

        lines = [
            "| Nom | Type | Obligatoire | Description |",
            "|-----|------|-------------|-------------|"
        ]

        for prop in properties:
            required = "✅" if prop.get("required") else "❌"
            lines.append(
                f"| {prop['name']} | {prop['type']} | {required} | {prop.get('description', '')} |"
            )

        return "\n".join(lines)

    def _format_entity_concept_context(self, context: Dict[str, Any]) -> str:
        """Formate le bloc de positionnement d'un objet métier dans son concept."""
        if not context:
            return "_Aucun concept métier rapproché automatiquement pour cet objet._"

        matching = context.get("matching", {})
        overlap_fields = matching.get("overlap_fields", [])
        overlap_fields_text = ", ".join(overlap_fields) if overlap_fields else "aucun champ commun identifié"

        scope = context.get("scope", [])
        scope_text = ", ".join(scope) if scope else "N/A"

        return (
            f"- **Concept métier rattaché**: `{context.get('id', 'N/A')}` — **{context.get('name', 'N/A')}**\n"
            f"- **Définition du concept**: {context.get('definition', 'N/A')}\n"
            f"- **Périmètre (scope)**: {scope_text}\n"
            f"- **Rapprochement automatique**: score `{matching.get('score', 0)}` ; champs communs: {overlap_fields_text}"
        )

    def _format_ubiquitous_language(self, ubiquitous_language: Dict[str, Any]) -> str:
        """Formate la section de langage ubiquitaire d'un domaine."""
        def _escape_table_cell(value: Any) -> str:
            text = "" if value is None else str(value)
            # Éviter les erreurs MDX/HTML dans les cellules de tableau
            text = text.replace("&", "&amp;")
            text = text.replace("<", "&lt;").replace(">", "&gt;")
            text = text.replace("|", "\\|")
            text = text.replace("\n", "<br/>")
            return text

        concepts = ubiquitous_language.get("concepts", [])
        terms = ubiquitous_language.get("terms", [])

        concept_lines = ["### Concepts métier canoniques", ""]
        if concepts:
            for concept in concepts:
                scope = ", ".join(concept.get("scope", [])) if concept.get("scope") else "N/A"
                concept_reference = concept.get("source_id") or concept.get("id", "N/A")
                concept_lines.append(
                    f"- **{concept.get('name', 'N/A')}** (`{concept_reference}`) — {concept.get('summary', '')}"
                )
                concept_lines.append(f"  - Scope: {scope}")
        else:
            concept_lines.append("_Aucun concept métier canonique documenté pour ce domaine._")

        terms_lines = ["", "### Glossaire métier (objets & propriétés)", ""]
        if terms:
            terms_lines.append("| Terme | Type | Description | Objets sources |")
            terms_lines.append("|---|---|---|---|")
            for term in terms:
                sources = ", ".join(f"`{source}`" for source in term.get("sources", [])) or "N/A"
                terms_lines.append(
                    f"| {_escape_table_cell(term.get('name', 'N/A'))} | {_escape_table_cell(term.get('type', 'N/A'))} | {_escape_table_cell(term.get('description', ''))} | {_escape_table_cell(sources)} |"
                )
        else:
            terms_lines.append("_Aucun terme métier n'a été extrait des objets du domaine._")

        return "\n".join(concept_lines + terms_lines)

    def _generate_domain_ubiquitous_language_mdx(self, domain: Dict[str, Any]) -> str:
        """Génère le fichier `ubiquitous-language.mdx` attendu par EventCatalog."""
        ubiquitous_language = domain.get("ubiquitous_language", {})
        concepts = ubiquitous_language.get("concepts", [])
        terms = ubiquitous_language.get("terms", [])

        dictionary = []

        for concept in concepts:
            concept_ref = concept.get("source_id") or concept.get("id") or "N/A"
            concept_scope = ", ".join(concept.get("scope", [])) if concept.get("scope") else "N/A"
            concept_summary = concept.get("summary") or "Concept métier canonique"
            concept_definition = concept.get("summary") or "Aucune description fournie."

            dictionary.append({
                "id": concept_ref,
                "name": concept.get("name") or concept_ref,
                "summary": concept_summary,
                "description": (
                    f"Concept BCM: `{concept_ref}`\n\n"
                    f"{concept_definition}\n\n"
                    f"Scope: {concept_scope}"
                ),
                "icon": "BookOpen"
            })

        for term in terms:
            term_name = term.get("name") or "N/A"
            term_type = term.get("type") or "N/A"
            term_description = term.get("description") or "Aucune description fournie."
            sources = term.get("sources", [])
            sources_text = ", ".join(f"`{source}`" for source in sources) if sources else "N/A"

            dictionary.append({
                "id": term_name,
                "name": term_name,
                "summary": term_description,
                "description": (
                    f"Type: `{term_type}`\n\n"
                    f"{term_description}\n\n"
                    f"Objets sources: {sources_text}"
                ),
                "icon": "List"
            })

        frontmatter = {
            "dictionary": dictionary
        }

        yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)

        domain_name = domain.get("name", "domaine")
        return f"""---
{yaml_content}---
Cette page est générée automatiquement à partir des concepts et objets métier du domaine **{domain_name}**.
"""
