"""
Intermediate data model for BCM export to EventCatalog.

This module defines the Python classes that represent BCM elements
in a normalised form, independent of both the YAML source format and
the EventCatalog target format.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class BCMType(Enum):
    """Types of BCM elements."""
    CAPABILITY_L1 = "capability_l1"
    CAPABILITY_L2 = "capability_l2"
    CAPABILITY_L3 = "capability_l3"
    BUSINESS_EVENT = "business_event"
    BUSINESS_OBJECT = "business_object"
    BUSINESS_SUBSCRIPTION = "business_subscription"
    BUSINESS_CONCEPT = "business_concept"


class EventScope(Enum):
    """Visibility scope of business events."""
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"


@dataclass
class SourceTraceability:
    """Traceability metadata pointing back to the BCM sources."""
    source_id: str
    source_file: str
    bcm_type: BCMType
    exported_at: Optional[datetime] = None
    source_line: Optional[int] = None
    
    def __post_init__(self):
        if self.exported_at is None:
            self.exported_at = datetime.now()


@dataclass
class DataField:
    """Data field of a business object."""
    name: str
    type: str
    description: str
    required: bool = False

    def to_eventcatalog_property(self) -> Dict[str, Any]:
        """Converts to EventCatalog property format."""
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description
        }


@dataclass
class BusinessConcept:
    """Canonical business concept (ubiquitous language source)."""
    id: str
    name: str
    definition: str
    scope: List[str] = field(default_factory=list)
    properties: List[DataField] = field(default_factory=list)
    business_rules: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source: Optional[SourceTraceability] = None

    def validate(self) -> List[str]:
        """Validates the consistency of the business concept."""
        errors = []
        if not self.id.startswith('CPT.'):
            errors.append(f"Concept ID must start with 'CPT.': {self.id}")
        if not self.name:
            errors.append(f"Concept must have a name: {self.id}")
        if not self.definition:
            errors.append(f"Concept must have a definition: {self.id}")
        return errors


@dataclass
class CapabilityL1:
    """L1 business capability (EventCatalog Domain)."""
    id: str
    name: str
    description: str
    owner: str
    zoning: str
    adrs: List[str] = field(default_factory=list)
    source: Optional[SourceTraceability] = None
    
    def get_slug(self) -> str:
        """Generates the EventCatalog slug from the BCM ID."""
        # CAP.COEUR.005 -> coeur-005
        parts = self.id.split('.')
        if len(parts) >= 3:
            return f"{parts[1].lower()}-{parts[2].lower()}"
        return self.id.lower().replace('.', '-')

    def get_eventcatalog_id(self) -> str:
        """EventCatalog ID (identical to slug for domains)."""
        return self.get_slug()

    def validate(self) -> List[str]:
        """Validates the consistency of the L1 capability."""
        errors = []
        if not self.id.startswith('CAP.'):
            errors.append(f"L1 ID must start with 'CAP.': {self.id}")
        if not self.name:
            errors.append(f"L1 must have a name: {self.id}")
        if not self.owner:
            errors.append(f"L1 must have an owner: {self.id}")
        return errors


@dataclass
class CapabilityL2:
    """L2 business capability (EventCatalog Service)."""
    id: str
    name: str
    description: str
    owner: str
    parent_l1_id: str
    zoning: str
    level: str = "L2"
    parent_l2_id: Optional[str] = None
    adrs: List[str] = field(default_factory=list)
    source: Optional[SourceTraceability] = None
    
    def get_slug(self) -> str:
        """Generates the EventCatalog slug from the BCM ID."""
        # CAP.COEUR.005.DSP -> dsp
        parts = self.id.split('.')
        if len(parts) >= 4:
            return parts[-1].lower().replace('_', '-')
        return self.id.lower().replace('.', '-').replace('_', '-')

    def get_eventcatalog_id(self) -> str:
        """EventCatalog ID (identical to slug for services)."""
        return self.get_slug()

    def get_parent_domain_slug(self) -> str:
        """Parent domain slug for EventCatalog."""
        # CAP.COEUR.005 -> coeur-005
        parts = self.parent_l1_id.split('.')
        if len(parts) >= 3:
            return f"{parts[1].lower()}-{parts[2].lower()}"
        return self.parent_l1_id.lower().replace('.', '-')

    def validate(self) -> List[str]:
        """Validates the consistency of the L2 capability."""
        errors = []
        if not self.id.startswith('CAP.'):
            errors.append(f"L2 ID must start with 'CAP.': {self.id}")
        if self.level not in {"L2", "L3"}:
            errors.append(f"Capability level must be L2 or L3: {self.id} ({self.level})")
        if not self.parent_l1_id:
            errors.append(f"Capability must have a parent L1: {self.id}")
        if not self.parent_l1_id.startswith('CAP.'):
            errors.append(f"Capability parent L1 must be a valid ID: {self.parent_l1_id}")
        if self.level == "L3" and (not self.parent_l2_id or not self.parent_l2_id.startswith('CAP.')):
            errors.append(f"L3 capability must have a valid L2 parent: {self.id}")
        return errors


@dataclass
class BusinessEvent:
    """Business event (EventCatalog Event)."""
    id: str
    name: str
    version: str
    definition: str
    emitting_capability_l2_id: str
    business_object_id: str
    scope: EventScope
    adrs: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source: Optional[SourceTraceability] = None
    
    def get_slug(self) -> str:
        """Generates the EventCatalog slug from the BCM ID."""
        # EVT.COEUR.005.DECLARATION_SINISTRE_RECUE -> declaration-sinistre-recue
        parts = self.id.split('.')
        if len(parts) >= 4:
            return parts[-1].lower().replace('_', '-')
        return self.id.lower().replace('.', '-').replace('_', '-')

    def get_eventcatalog_id(self) -> str:
        """EventCatalog ID (identical to slug for events)."""
        return self.get_slug()

    def get_service_slug(self) -> str:
        """Slug of the emitting service for EventCatalog."""
        # CAP.COEUR.005.DSP -> dsp
        parts = self.emitting_capability_l2_id.split('.')
        if len(parts) >= 4:
            return parts[-1].lower().replace('_', '-')
        return self.emitting_capability_l2_id.lower().replace('.', '-').replace('_', '-')

    def get_domain_slug(self) -> str:
        """Domain slug for EventCatalog (via the emitting capability)."""
        # CAP.COEUR.005.DSP -> coeur-005
        parts = self.emitting_capability_l2_id.split('.')
        if len(parts) >= 3:
            return f"{parts[1].lower()}-{parts[2].lower()}"
        return "unknown-domain"

    def get_business_object_slug(self) -> str:
        """Slug of the associated business object."""
        # OBJ.COEUR.005.DECLARATION_SINISTRE_RECUE -> declaration-sinistre-recue
        parts = self.business_object_id.split('.')
        if len(parts) >= 4:
            return parts[-1].lower().replace('_', '-')
        return self.business_object_id.lower().replace('.', '-').replace('_', '-')

    def validate(self) -> List[str]:
        """Validates the consistency of the event."""
        errors = []
        if not self.id.startswith('EVT.'):
            errors.append(f"Event ID must start with 'EVT.': {self.id}")
        if not self.emitting_capability_l2_id.startswith('CAP.'):
            errors.append(f"Emitting capability must be a valid L2 ID: {self.emitting_capability_l2_id}")
        if not self.business_object_id.startswith('OBJ.'):
            errors.append(f"Business object must be a valid object ID: {self.business_object_id}")
        if not self.version:
            errors.append(f"Event must have a version: {self.id}")
        return errors


@dataclass
class BusinessObject:
    """Business object (EventCatalog Entity)."""
    id: str
    name: str
    definition: str
    emitting_capability_l2_id: str
    emitting_capability_l3_ids: List[str] = field(default_factory=list)
    data_fields: List[DataField] = field(default_factory=list)
    adrs: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source: Optional[SourceTraceability] = None
    
    def get_slug(self) -> str:
        """Generates the EventCatalog slug from the BCM ID."""
        # OBJ.COEUR.005.DECLARATION_SINISTRE_RECUE -> declaration-sinistre-recue
        parts = self.id.split('.')
        if len(parts) >= 4:
            return parts[-1].lower().replace('_', '-')
        return self.id.lower().replace('.', '-').replace('_', '-')

    def get_eventcatalog_id(self) -> str:
        """EventCatalog ID (identical to slug for entities)."""
        return self.get_slug()

    def get_domain_slug(self) -> str:
        """Domain slug for EventCatalog (via the emitting capability)."""
        # CAP.COEUR.005.DSP -> coeur-005
        parts = self.emitting_capability_l2_id.split('.')
        if len(parts) >= 3:
            return f"{parts[1].lower()}-{parts[2].lower()}"
        return "unknown-domain"

    def validate(self) -> List[str]:
        """Validates the consistency of the business object."""
        errors = []
        if not self.id.startswith('OBJ.'):
            errors.append(f"Object ID must start with 'OBJ.': {self.id}")
        if not self.emitting_capability_l2_id.startswith('CAP.'):
            errors.append(f"Emitting capability must be a valid L2 ID: {self.emitting_capability_l2_id}")
        return errors


@dataclass
class BusinessSubscription:
    """Business subscription (consumption of an event by an L2 capability)."""
    id: str
    consumer_capability_l2_id: str
    subscribed_event_id: str
    subscribed_event_version: str
    emitting_capability_l2_id: str
    scope: EventScope
    rationale: str = ""
    adrs: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source: Optional[SourceTraceability] = None

    def validate(self) -> List[str]:
        """Validates the consistency of the subscription."""
        errors = []
        if not self.id.startswith('SUB.'):
            errors.append(f"Subscription ID must start with 'SUB.': {self.id}")
        if not self.consumer_capability_l2_id.startswith('CAP.'):
            errors.append(
                f"Consumer capability must be a valid L2 ID: {self.consumer_capability_l2_id}"
            )
        if not self.subscribed_event_id.startswith('EVT.'):
            errors.append(f"Subscribed event must be a valid event ID: {self.subscribed_event_id}")
        if not self.emitting_capability_l2_id.startswith('CAP.'):
            errors.append(
                f"Emitting capability must be a valid L2 ID: {self.emitting_capability_l2_id}"
            )
        if not self.subscribed_event_version:
            errors.append(f"Subscribed event version is required: {self.id}")
        return errors


@dataclass
class BCMModel:
    """Complete BCM model loaded in memory."""
    capabilities_l1: List[CapabilityL1] = field(default_factory=list)
    capabilities_l2: List[CapabilityL2] = field(default_factory=list)
    business_events: List[BusinessEvent] = field(default_factory=list)
    business_objects: List[BusinessObject] = field(default_factory=list)
    business_subscriptions: List[BusinessSubscription] = field(default_factory=list)
    business_concepts: List[BusinessConcept] = field(default_factory=list)
    
    def get_capability_l1_by_id(self, capability_id: str) -> Optional[CapabilityL1]:
        """Finds an L1 capability by its ID."""
        return next((cap for cap in self.capabilities_l1 if cap.id == capability_id), None)

    def get_capability_l2_by_id(self, capability_id: str) -> Optional[CapabilityL2]:
        """Finds an L2 capability by its ID."""
        return next((cap for cap in self.capabilities_l2 if cap.id == capability_id), None)

    def get_business_event_by_id(self, event_id: str) -> Optional[BusinessEvent]:
        """Finds a business event by its ID."""
        return next((evt for evt in self.business_events if evt.id == event_id), None)

    def get_business_object_by_id(self, object_id: str) -> Optional[BusinessObject]:
        """Finds a business object by its ID."""
        return next((obj for obj in self.business_objects if obj.id == object_id), None)

    def get_business_subscription_by_id(self, subscription_id: str) -> Optional[BusinessSubscription]:
        """Finds a business subscription by its ID."""
        return next((sub for sub in self.business_subscriptions if sub.id == subscription_id), None)

    def get_business_concept_by_id(self, concept_id: str) -> Optional[BusinessConcept]:
        """Finds a business concept by its ID."""
        return next((concept for concept in self.business_concepts if concept.id == concept_id), None)

    def validate_all(self) -> Dict[str, List[str]]:
        """Validates the overall consistency of the model."""
        all_errors = {
            "capabilities_l1": [],
            "capabilities_l2": [],
            "business_events": [],
            "business_objects": [],
            "business_subscriptions": [],
            "business_concepts": [],
            "relations": []
        }
        
        # Validate individual elements
        for cap_l1 in self.capabilities_l1:
            all_errors["capabilities_l1"].extend(cap_l1.validate())

        for cap_l2 in self.capabilities_l2:
            all_errors["capabilities_l2"].extend(cap_l2.validate())
            # Validate L2 -> L1 relation
            if not self.get_capability_l1_by_id(cap_l2.parent_l1_id):
                all_errors["relations"].append(f"L2 {cap_l2.id} references non-existent L1 {cap_l2.parent_l1_id}")
        
        for event in self.business_events:
            all_errors["business_events"].extend(event.validate())
            # Validate Event -> L2 relation
            if not self.get_capability_l2_by_id(event.emitting_capability_l2_id):
                all_errors["relations"].append(f"Event {event.id} references non-existent L2 {event.emitting_capability_l2_id}")
            # Validate Event -> Object relation
            if not self.get_business_object_by_id(event.business_object_id):
                all_errors["relations"].append(f"Event {event.id} references non-existent object {event.business_object_id}")
        
        for obj in self.business_objects:
            all_errors["business_objects"].extend(obj.validate())
            # Validate Object -> L2 relation
            if not self.get_capability_l2_by_id(obj.emitting_capability_l2_id):
                all_errors["relations"].append(f"Object {obj.id} references non-existent L2 {obj.emitting_capability_l2_id}")

        for sub in self.business_subscriptions:
            all_errors["business_subscriptions"].extend(sub.validate())

            if not self.get_capability_l2_by_id(sub.consumer_capability_l2_id):
                all_errors["relations"].append(
                    f"Subscription {sub.id} references non-existent consumer L2 {sub.consumer_capability_l2_id}"
                )

            if not self.get_business_event_by_id(sub.subscribed_event_id):
                all_errors["relations"].append(
                    f"Subscription {sub.id} references non-existent event {sub.subscribed_event_id}"
                )

            if not self.get_capability_l2_by_id(sub.emitting_capability_l2_id):
                all_errors["relations"].append(
                    f"Subscription {sub.id} references non-existent emitting L2 {sub.emitting_capability_l2_id}"
                )

        for concept in self.business_concepts:
            all_errors["business_concepts"].extend(concept.validate())
        
        # Filter out empty error lists
        return {k: v for k, v in all_errors.items() if v}

    def get_summary(self) -> Dict[str, int]:
        """Statistical summary of the model."""
        return {
            "capabilities_l1": len(self.capabilities_l1),
            "capabilities_l2": len(self.capabilities_l2),  
            "business_events": len(self.business_events),
            "business_objects": len(self.business_objects),
            "business_subscriptions": len(self.business_subscriptions),
            "business_concepts": len(self.business_concepts)
        }