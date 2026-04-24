"""
Normalisation des données BCM pour l'export EventCatalog.

Ce module transforme les données BCM brutes en données propres, homogènes 
et compatibles avec EventCatalog.
"""

import re
from typing import List, Dict, Any, Set
from datetime import datetime
import logging

try:
    from .domain_model import BCMModel, CapabilityL1, CapabilityL2, BusinessEvent, BusinessObject, BusinessSubscription, BusinessConcept
except ImportError:
    from domain_model import BCMModel, CapabilityL1, CapabilityL2, BusinessEvent, BusinessObject, BusinessSubscription, BusinessConcept

logger = logging.getLogger(__name__)


class NormalizationError(Exception):
    """Erreur de normalisation des données."""
    pass


class SlugGenerator:
    """Générateur de slugs EventCatalog à partir d'identifiants BCM."""
    
    @staticmethod
    def from_bcm_id(bcm_id: str) -> str:
        """
        Génère un slug EventCatalog à partir d'un ID BCM.
        
        Exemples:
        - CAP.COEUR.005 -> coeur-005
        - CAP.COEUR.005.DSP -> dsp
        - EVT.COEUR.005.DECLARATION_SINISTRE_RECUE -> declaration-sinistre-recue
        """
        if not bcm_id:
            raise NormalizationError("BCM ID cannot be empty")
        
        parts = bcm_id.split('.')
        
        # Pour les L1: prendre les 2 derniers segments (COEUR.005)
        if len(parts) >= 3 and parts[-1].isdigit():
            slug_parts = parts[-2:]
        # Pour les L2, événements, objets: prendre le dernier segment
        elif len(parts) >= 4:
            slug_parts = [parts[-1]]
        else:
            # Fallback: tout l'ID sans préfixes
            slug_parts = [p for p in parts if p not in ['CAP', 'EVT', 'OBJ', 'RES']]
        
        # Normaliser chaque partie
        normalized_parts = []
        for part in slug_parts:
            # Lowercase et remplacement underscore par tirets
            normalized = part.lower().replace('_', '-')
            # Suppression caractères spéciaux (garde lettres, chiffres, tirets)
            normalized = re.sub(r'[^a-z0-9-]', '', normalized)
            # Suppression tirets multiples
            normalized = re.sub(r'-+', '-', normalized)
            # Suppression tirets en début/fin
            normalized = normalized.strip('-')
            if normalized:
                normalized_parts.append(normalized)
        
        if not normalized_parts:
            raise NormalizationError(f"Cannot generate valid slug from BCM ID: {bcm_id}")
        
        return '-'.join(normalized_parts)
    
    @staticmethod
    def validate_slug(slug: str) -> bool:
        """Valide qu'un slug respecte les conventions EventCatalog."""
        if not slug:
            return False
        # Slug doit être uniquement lettres minuscules, chiffres et tirets
        # Pas de tiret en début/fin, pas de tirets multiples
        pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
        return bool(re.match(pattern, slug))


class TitleGenerator:
    """Générateur de titres lisibles pour EventCatalog."""
    
    @staticmethod
    def from_name_or_id(name: str, bcm_id: str) -> str:
        """
        Génère un titre lisible à partir du name BCM ou de l'ID en fallback.
        
        Règles:
        - Utilise le name si présent et non vide
        - Sinon, humanise l'ID
        - Préserve les accents et caractères spéciaux métier
        """
        if name and name.strip():
            return name.strip()
        
        return TitleGenerator.humanize_id(bcm_id)
    
    @staticmethod
    def humanize_id(bcm_id: str) -> str:
        """
        Humanise un ID BCM en titre lisible.
        
        Exemple: EVT.COEUR.005.DECLARATION_SINISTRE_RECUE -> "Déclaration Sinistre Reçue"
        """
        if not bcm_id:
            return "Unnamed"
        
        # Prendre la dernière partie de l'ID
        parts = bcm_id.split('.')
        last_part = parts[-1] if parts else bcm_id
        
        # Remplacer underscores par espaces
        humanized = last_part.replace('_', ' ')
        
        # Capitaliser chaque mot
        words = humanized.split()
        capitalized_words = []
        for word in words:
            # Capitaliser première lettre, garder le reste tel quel (pour les accents)
            if word:
                capitalized = word[0].upper() + word[1:].lower()
                capitalized_words.append(capitalized)
        
        return ' '.join(capitalized_words)


class OwnerNormalizer:
    """Normaliseur d'owners pour EventCatalog."""
    
    @staticmethod
    def normalize_owner(raw_owner: str) -> str:
        """
        Normalise un owner BCM en format EventCatalog.
        
        Règles:
        - Lowercase
        - Espaces -> tirets
        - Caractères spéciaux supprimés
        - Ampersands & -> et
        """
        if not raw_owner:
            return "unknown-owner"
        
        # Normalisation de base
        normalized = raw_owner.lower()
        
        # Remplacements spécifiques
        normalized = normalized.replace(' & ', ' et ')
        normalized = normalized.replace('&', 'et')
        normalized = normalized.replace('/', '-')
        normalized = normalized.replace(' ', '-')
        
        # Suppression caractères spéciaux (garde lettres, chiffres, tirets)
        normalized = re.sub(r'[^a-z0-9-]', '', normalized)
        
        # Nettoyage tirets multiples/début/fin
        normalized = re.sub(r'-+', '-', normalized)
        normalized = normalized.strip('-')
        
        return normalized if normalized else "unknown-owner"
    
    @staticmethod
    def normalize_owners_list(raw_owners: List[str]) -> List[str]:
        """Normalise une liste d'owners."""
        normalized = []
        for owner in raw_owners:
            norm_owner = OwnerNormalizer.normalize_owner(owner)
            if norm_owner not in normalized:  # Évite les doublons
                normalized.append(norm_owner)
        return normalized


class RelationshipResolver:
    """Résolveur de relations entre éléments BCM."""
    
    def __init__(self, model: BCMModel):
        self.model = model
        
        # Index pour accès rapide
        self.l1_by_id = {cap.id: cap for cap in model.capabilities_l1}
        self.l2_by_id = {cap.id: cap for cap in model.capabilities_l2}
        self.l3_children_by_l2_id = {}
        for cap in model.capabilities_l2:
            if getattr(cap, "level", "L2") == "L3" and getattr(cap, "parent_l2_id", None):
                self.l3_children_by_l2_id.setdefault(cap.parent_l2_id, []).append(cap.id)
        self.events_by_id = {evt.id: evt for evt in model.business_events}
        self.objects_by_id = {obj.id: obj for obj in model.business_objects}
        self.subscriptions_by_id = {sub.id: sub for sub in model.business_subscriptions}
        self.concepts_by_id = {concept.id: concept for concept in model.business_concepts}

    def resolve_emitting_capability(self, capability_id: str, preferred_l3_ids: List[str] = None) -> str:
        """Résout la capacité à utiliser pour l'export (priorité L3 si explicitée)."""
        if not capability_id:
            return capability_id

        cap = self.l2_by_id.get(capability_id)
        if cap and getattr(cap, "level", "L2") == "L3":
            return capability_id

        l3_children = self.l3_children_by_l2_id.get(capability_id, [])
        if not l3_children:
            return capability_id

        preferred = preferred_l3_ids or []
        preferred_matches = [cap_id for cap_id in preferred if cap_id in l3_children]
        if preferred_matches:
            return preferred_matches[0]

        return capability_id

    def should_export_as_service(self, capability: CapabilityL2) -> bool:
        """Indique si une capacité doit être exportée comme service EventCatalog.

        Règle métier: une capacité L2 qui possède des capacités enfants L3
        ne doit pas être exportée en tant que service.
        """
        if capability.level != "L2":
            return True

        return len(self.l3_children_by_l2_id.get(capability.id, [])) == 0
    
    def resolve_l2_to_l1_domain(self, l2_capability: CapabilityL2) -> str:
        """Résout le domain slug d'une capacité L2."""
        parent_l1 = self.l1_by_id.get(l2_capability.parent_l1_id)
        if parent_l1:
            return SlugGenerator.from_bcm_id(parent_l1.id)
        
        logger.warning(f"Cannot resolve L1 parent for L2 {l2_capability.id}")
        return "unknown-domain"
    
    def resolve_event_to_service(self, event: BusinessEvent) -> str:
        """Résout le service slug d'un événement."""
        effective_capability_id = self.resolve_emitting_capability(event.emitting_capability_l2_id)
        l2_capability = self.l2_by_id.get(effective_capability_id)
        if l2_capability:
            return SlugGenerator.from_bcm_id(l2_capability.id)
        
        logger.warning(f"Cannot resolve L2 capability for event {event.id}")
        return "unknown-service"
    
    def resolve_event_to_domain(self, event: BusinessEvent) -> str:
        """Résout le domain slug d'un événement (via sa capacité L2)."""
        effective_capability_id = self.resolve_emitting_capability(event.emitting_capability_l2_id)
        l2_capability = self.l2_by_id.get(effective_capability_id)
        if l2_capability:
            return self.resolve_l2_to_l1_domain(l2_capability)
        
        logger.warning(f"Cannot resolve domain for event {event.id}")
        return "unknown-domain"
    
    def resolve_object_to_domain(self, obj: BusinessObject) -> str:
        """Résout le domain slug d'un objet métier (via sa capacité L2)."""
        effective_capability_id = self.resolve_emitting_capability(
            obj.emitting_capability_l2_id,
            preferred_l3_ids=obj.emitting_capability_l3_ids,
        )
        l2_capability = self.l2_by_id.get(effective_capability_id)
        if l2_capability:
            return self.resolve_l2_to_l1_domain(l2_capability)
        
        logger.warning(f"Cannot resolve domain for object {obj.id}")
        return "unknown-domain"

    def resolve_concept_to_domain(self, concept: BusinessConcept) -> str:
        """Résout le domain slug d'un concept métier depuis son ID CPT.<ZONE>.<L1>.*."""
        parts = (concept.id or "").split('.')
        if len(parts) >= 3:
            domain_id = f"CAP.{parts[1]}.{parts[2]}"
            try:
                return SlugGenerator.from_bcm_id(domain_id)
            except Exception:
                pass

        logger.warning(f"Cannot resolve domain for concept {concept.id}")
        return "unknown-domain"

    @staticmethod
    def _tokenize_for_matching(*texts: str) -> Set[str]:
        """Tokenisation simple pour rapprochement heuristique objet/concept."""
        tokens = set()
        for text in texts:
            if not text:
                continue
            for token in re.findall(r"[a-zA-Z0-9]+", text.lower()):
                if len(token) >= 3:
                    tokens.add(token)
        return tokens

    def find_best_concept_for_object(self, obj: BusinessObject) -> Dict[str, Any]:
        """Trouve le concept métier le plus pertinent pour un objet via heuristique."""
        obj_domain = self.resolve_object_to_domain(obj)
        candidates = [
            concept for concept in self.model.business_concepts
            if self.resolve_concept_to_domain(concept) == obj_domain
        ]

        if not candidates:
            return {}

        object_tokens = self._tokenize_for_matching(obj.id, obj.name, obj.definition)
        object_fields_map = {
            field.name.lower(): field.name
            for field in obj.data_fields
            if field.name
        }
        object_fields = set(object_fields_map.keys())

        best = None
        best_score = 0
        best_overlap_fields = []

        for concept in candidates:
            concept_tokens = self._tokenize_for_matching(concept.id, concept.name, concept.definition)
            token_overlap = object_tokens.intersection(concept_tokens)

            concept_fields = {prop.name.lower() for prop in concept.properties if prop.name}
            field_overlap = object_fields.intersection(concept_fields)

            # Pondération: recouvrement des champs > recouvrement lexical général
            score = (2 * len(field_overlap)) + len(token_overlap)

            if score > best_score:
                best_score = score
                best = concept
                best_overlap_fields = sorted(object_fields_map.get(field, field) for field in field_overlap)

        if not best or best_score == 0:
            return {}

        return {
            "id": best.id,
            "name": best.name,
            "definition": best.definition,
            "scope": best.scope,
            "tags": best.tags,
            "matching": {
                "score": best_score,
                "overlap_fields": best_overlap_fields,
                "overlap_fields_count": len(best_overlap_fields),
                "object_fields_count": len(object_fields),
                "concept_fields_count": len({prop.name.lower() for prop in best.properties if prop.name})
            }
        }
    
    def get_missing_relations(self) -> Dict[str, List[str]]:
        """Identifie les relations manquantes dans le modèle."""
        missing = {
            "l2_without_l1": [],
            "events_without_l2": [],
            "events_without_object": [],
            "objects_without_l2": [],
            "subscriptions_without_consumer_l2": [],
            "subscriptions_without_event": [],
            "subscriptions_without_emitter_l2": []
        }
        
        # L2 sans L1 parent
        for l2 in self.model.capabilities_l2:
            if l2.parent_l1_id not in self.l1_by_id:
                missing["l2_without_l1"].append(l2.id)
        
        # Events sans L2 émettrice
        for event in self.model.business_events:
            if event.emitting_capability_l2_id not in self.l2_by_id:
                missing["events_without_l2"].append(event.id)
        
        # Events sans objet métier
        for event in self.model.business_events:
            if event.business_object_id not in self.objects_by_id:
                missing["events_without_object"].append(event.id)
        
        # Objects sans L2 émettrice
        for obj in self.model.business_objects:
            if obj.emitting_capability_l2_id not in self.l2_by_id:
                missing["objects_without_l2"].append(obj.id)

        for sub in self.model.business_subscriptions:
            if sub.consumer_capability_l2_id not in self.l2_by_id:
                missing["subscriptions_without_consumer_l2"].append(sub.id)

            if sub.subscribed_event_id not in self.events_by_id:
                missing["subscriptions_without_event"].append(sub.id)

            if sub.emitting_capability_l2_id not in self.l2_by_id:
                missing["subscriptions_without_emitter_l2"].append(sub.id)
        
        return {k: v for k, v in missing.items() if v}


class BCMNormalizer:
    """Normaliseur principal pour les données BCM."""
    
    def __init__(self):
        self.slug_generator = SlugGenerator()
        self.title_generator = TitleGenerator()
        self.owner_normalizer = OwnerNormalizer()
    
    def normalize_model(self, model: BCMModel) -> Dict[str, Any]:
        """
        Normalise un modèle BCM complet.
        
        Retourne un dictionnaire avec les données normalisées et des métadonnées
        de normalisation (warnings, statistiques, etc.).
        """
        logger.info("Starting BCM model normalization")
        
        start_time = datetime.now()
        
        # Résolveur de relations
        relation_resolver = RelationshipResolver(model)
        
        # Collecte des warnings
        warnings = []
        
        # Normalisation par type
        normalized_l1 = []
        for cap in model.capabilities_l1:
            try:
                normalized = self._normalize_capability_l1(cap)
                normalized_l1.append(normalized)
            except Exception as e:
                warnings.append(f"Failed to normalize L1 {cap.id}: {e}")
        
        normalized_l2 = []
        excluded_services_due_to_l3 = []
        for cap in model.capabilities_l2:
            try:
                if not relation_resolver.should_export_as_service(cap):
                    excluded_services_due_to_l3.append(cap.id)
                    continue
                normalized = self._normalize_capability_l2(cap, relation_resolver)
                normalized_l2.append(normalized)
            except Exception as e:
                warnings.append(f"Failed to normalize L2 {cap.id}: {e}")

        if excluded_services_due_to_l3:
            logger.info(
                "Skipped L2 service export because child L3 exist: %s",
                ", ".join(sorted(excluded_services_due_to_l3)),
            )
        
        normalized_events = []
        for event in model.business_events:
            try:
                normalized = self._normalize_business_event(event, relation_resolver)
                normalized_events.append(normalized)
            except Exception as e:
                warnings.append(f"Failed to normalize event {event.id}: {e}")

        normalized_concepts = []
        for concept in model.business_concepts:
            try:
                normalized = self._normalize_business_concept(concept, relation_resolver)
                normalized_concepts.append(normalized)
            except Exception as e:
                warnings.append(f"Failed to normalize concept {concept.id}: {e}")
        
        normalized_objects = []
        for obj in model.business_objects:
            try:
                normalized = self._normalize_business_object(obj, relation_resolver)
                normalized_objects.append(normalized)
            except Exception as e:
                warnings.append(f"Failed to normalize object {obj.id}: {e}")

        normalized_subscriptions = []
        for sub in model.business_subscriptions:
            try:
                normalized = self._normalize_business_subscription(sub, relation_resolver)
                normalized_subscriptions.append(normalized)
            except Exception as e:
                warnings.append(f"Failed to normalize subscription {sub.id}: {e}")
        
        # Validation unicité des slugs
        slug_conflicts = self._check_slug_uniqueness(
            normalized_l1, normalized_l2, normalized_events, normalized_objects
        )
        warnings.extend(slug_conflicts)
        
        # Relations manquantes
        missing_relations = relation_resolver.get_missing_relations()
        if missing_relations:
            warnings.append(f"Missing relations detected: {missing_relations}")
        
        end_time = datetime.now()
        
        result = {
            "domains": normalized_l1,
            "services": normalized_l2,
            "events": normalized_events,
            "entities": normalized_objects,
            "subscriptions": normalized_subscriptions,
            "concepts": normalized_concepts,
            "metadata": {
                "normalized_at": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds(),
                "source_counts": model.get_summary(),
                "normalized_counts": {
                    "domains": len(normalized_l1),
                    "services": len(normalized_l2),
                    "events": len(normalized_events),
                    "entities": len(normalized_objects),
                    "subscriptions": len(normalized_subscriptions),
                    "concepts": len(normalized_concepts)
                },
                "warnings": warnings,
                "missing_relations": missing_relations,
                "excluded_services_due_to_l3": sorted(excluded_services_due_to_l3)
            }
        }
        
        logger.info(f"BCM normalization complete in {result['metadata']['duration_seconds']:.2f}s")
        if warnings:
            logger.warning(f"Normalization completed with {len(warnings)} warnings")
        
        return result
    
    def _normalize_capability_l1(self, cap: CapabilityL1) -> Dict[str, Any]:
        """Normalise une capacité L1 vers un domain EventCatalog."""
        slug = self.slug_generator.from_bcm_id(cap.id)
        title = self.title_generator.from_name_or_id(cap.name, cap.id)
        
        return {
            "id": slug,
            "name": title,
            "summary": cap.description[:200] + "..." if len(cap.description) > 200 else cap.description,
            "owners": [self.owner_normalizer.normalize_owner(cap.owner)],
            "ubiquitous_language": {
                "concepts": [],
                "terms": []
            },
            "metadata": {
                "bcm": {
                    "source_id": cap.id,
                    "source_file": cap.source.source_file if cap.source else None,
                    "bcm_type": "capability_l1",
                    "zoning": cap.zoning,
                    "exported_at": datetime.now().isoformat()
                }
            }
        }
    
    def _normalize_capability_l2(self, cap: CapabilityL2, resolver: RelationshipResolver) -> Dict[str, Any]:
        """Normalise une capacité L2 vers un service EventCatalog."""
        slug = self.slug_generator.from_bcm_id(cap.id)
        title = self.title_generator.from_name_or_id(cap.name, cap.id)
        domain_slug = resolver.resolve_l2_to_l1_domain(cap)
        
        return {
            "id": slug,
            "name": title,
            "summary": cap.description[:200] + "..." if len(cap.description) > 200 else cap.description,
            # Suppression du champ domain du frontmatter - utilisé pour placement fichier seulement
            "_domain": domain_slug,  # Utilisé pour le chemin de fichier
            "owners": [self.owner_normalizer.normalize_owner(cap.owner)],
            "metadata": {
                "bcm": {
                    "source_id": cap.id,
                    "source_file": cap.source.source_file if cap.source else None,
                    "bcm_type": "capability_l3" if cap.level == "L3" else "capability_l2",
                    "level": cap.level,
                    "parent_l1_id": cap.parent_l1_id,
                    "parent_l2_id": cap.parent_l2_id,
                    "zoning": cap.zoning,
                    "exported_at": datetime.now().isoformat()
                }
            }
        }
    
    def _normalize_business_event(self, event: BusinessEvent, resolver: RelationshipResolver) -> Dict[str, Any]:
        """Normalise un événement métier vers un event EventCatalog."""
        slug = self.slug_generator.from_bcm_id(event.id)
        title = self.title_generator.from_name_or_id(event.name, event.id)
        service_slug = resolver.resolve_event_to_service(event)
        domain_slug = resolver.resolve_event_to_domain(event)
        entity_slug = self.slug_generator.from_bcm_id(event.business_object_id)
        entity_obj = resolver.objects_by_id.get(event.business_object_id)
        entity_domain_slug = resolver.resolve_object_to_domain(entity_obj) if entity_obj else domain_slug
        
        return {
            "id": slug,
            "name": title,
            "version": event.version,
            "summary": event.definition[:200] + "..." if len(event.definition) > 200 else event.definition,
            # Suppression des champs service et domain du frontmatter - utilisés pour placement fichier seulement
            "_service": service_slug,  # Utilisé pour le chemin de fichier
            "_domain": domain_slug,   # Utilisé pour le chemin de fichier
            # Suppression entities du frontmatter - référence dans le contenu markdown à la place
            "_entity_slug": entity_slug,  # Utilisé pour le contenu markdown
            "_entity_domain": entity_domain_slug,  # Utilisé pour générer le lien markdown vers l'entity
            "_entity_version": "1.0.0",  # Version EventCatalog de l'entity cible
            "owners": [self.owner_normalizer.normalize_owner("unknown")],  # Pas d'owner pour les events
            "metadata": {
                "bcm": {
                    "source_id": event.id,
                    "source_file": event.source.source_file if event.source else None,
                    "bcm_type": "business_event",
                    "emitting_capability_id": event.emitting_capability_l2_id,
                    "business_object_id": event.business_object_id,
                    "scope": event.scope.value,
                    "tags": event.tags,
                    "exported_at": datetime.now().isoformat()
                }
            }
        }
    
    def _normalize_business_object(self, obj: BusinessObject, resolver: RelationshipResolver) -> Dict[str, Any]:
        """Normalise un objet métier vers une entity EventCatalog."""
        slug = self.slug_generator.from_bcm_id(obj.id)
        title = self.title_generator.from_name_or_id(obj.name, obj.id)
        effective_emitting_capability_id = resolver.resolve_emitting_capability(
            obj.emitting_capability_l2_id,
            preferred_l3_ids=obj.emitting_capability_l3_ids,
        )
        domain_slug = resolver.resolve_object_to_domain(obj)
        
        # Propriétés EventCatalog depuis les data fields
        properties = []
        for field in obj.data_fields:
            properties.append(field.to_eventcatalog_property())

        concept_context = resolver.find_best_concept_for_object(obj)
        
        return {
            "id": slug,
            "name": title,
            "summary": obj.definition[:200] + "..." if len(obj.definition) > 200 else obj.definition,
            # Suppression du champ domain du frontmatter - utilisé pour placement fichier seulement
            "_domain": domain_slug,  # Utilisé pour le chemin de fichier
            "properties": properties,
            "concept_context": concept_context,
            "owners": [self.owner_normalizer.normalize_owner("unknown")],  # Pas d'owner pour les entities
            "metadata": {
                "bcm": {
                    "source_id": obj.id,
                    "source_file": obj.source.source_file if obj.source else None,
                    "bcm_type": "business_object",
                    "emitting_capability_id": effective_emitting_capability_id,
                    "emitting_capability_l2_id": obj.emitting_capability_l2_id,
                    "emitting_capability_l3_ids": obj.emitting_capability_l3_ids,
                    "exported_at": datetime.now().isoformat()
                }
            }
        }

    def _normalize_business_concept(self, concept: BusinessConcept, resolver: RelationshipResolver) -> Dict[str, Any]:
        """Normalise un concept métier pour enrichissements documentaires."""
        slug = self.slug_generator.from_bcm_id(concept.id)
        domain_slug = resolver.resolve_concept_to_domain(concept)

        properties = [prop.to_eventcatalog_property() for prop in concept.properties]

        return {
            "id": slug,
            "name": concept.name,
            "summary": concept.definition[:200] + "..." if len(concept.definition) > 200 else concept.definition,
            "definition": concept.definition,
            "scope": concept.scope,
            "tags": concept.tags,
            "business_rules": concept.business_rules,
            "properties": properties,
            "_domain": domain_slug,
            "metadata": {
                "bcm": {
                    "source_id": concept.id,
                    "source_file": concept.source.source_file if concept.source else None,
                    "bcm_type": "business_concept",
                    "exported_at": datetime.now().isoformat()
                }
            }
        }

    def _normalize_business_subscription(self, sub: BusinessSubscription, resolver: RelationshipResolver) -> Dict[str, Any]:
        """Normalise une abonnement métier pour usage EventCatalog (receives)."""
        effective_consumer_capability_id = resolver.resolve_emitting_capability(sub.consumer_capability_l2_id)
        effective_emitter_capability_id = resolver.resolve_emitting_capability(sub.emitting_capability_l2_id)

        consumer_service_slug = self.slug_generator.from_bcm_id(effective_consumer_capability_id)
        emitter_service_slug = self.slug_generator.from_bcm_id(effective_emitter_capability_id)
        event_slug = self.slug_generator.from_bcm_id(sub.subscribed_event_id)

        consumer_l2 = resolver.l2_by_id.get(effective_consumer_capability_id)
        consumer_domain_slug = (
            resolver.resolve_l2_to_l1_domain(consumer_l2)
            if consumer_l2
            else "unknown-domain"
        )

        return {
            "id": sub.id,
            "consumer_service": consumer_service_slug,
            "consumer_domain": consumer_domain_slug,
            "event": {
                "id": event_slug,
                "version": sub.subscribed_event_version
            },
            "producer_service": emitter_service_slug,
            "scope": sub.scope.value,
            "rationale": sub.rationale,
            "tags": sub.tags,
            "metadata": {
                "bcm": {
                    "source_id": sub.id,
                    "source_file": sub.source.source_file if sub.source else None,
                    "bcm_type": "business_subscription",
                    "consumer_capability_id": effective_consumer_capability_id,
                    "consumer_capability_l2_id": sub.consumer_capability_l2_id,
                    "subscribed_event_id": sub.subscribed_event_id,
                    "emitting_capability_id": effective_emitter_capability_id,
                    "emitting_capability_l2_id": sub.emitting_capability_l2_id,
                    "exported_at": datetime.now().isoformat()
                }
            }
        }
    
    def _check_slug_uniqueness(self, domains: List[Dict], services: List[Dict], 
                              events: List[Dict], entities: List[Dict]) -> List[str]:
        """Vérifie l'unicité des slugs générés."""
        conflicts = []
        
        # Slugs par scope
        domain_slugs = {d["id"] for d in domains}
        service_slugs_by_domain = {}
        event_slugs_by_service = {}
        entity_slugs_by_domain = {}
        
        # Group par domain/service
        for service in services:
            domain = service.get("_domain", "unknown-domain")
            if domain not in service_slugs_by_domain:
                service_slugs_by_domain[domain] = set()
            
            if service["id"] in service_slugs_by_domain[domain]:
                conflicts.append(f"Duplicate service slug '{service['id']}' in domain '{domain}'")
            service_slugs_by_domain[domain].add(service["id"])
        
        # Vérifier unicité dans chaque scope
        if len(domain_slugs) != len(domains):
            conflicts.append("Duplicate domain slugs detected")
        
        return conflicts