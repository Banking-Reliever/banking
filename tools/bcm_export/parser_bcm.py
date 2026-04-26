"""
Parsers for BCM YAML files.

This module contains the parsers that read BCM YAML files
and build the intermediate Python data model.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

try:
    from .domain_model import (
        BCMModel, CapabilityL1, CapabilityL2, BusinessEvent, BusinessObject,
        BusinessSubscription, BusinessConcept, DataField, EventScope, BCMType, SourceTraceability
    )
except ImportError:
    from domain_model import (
        BCMModel, CapabilityL1, CapabilityL2, BusinessEvent, BusinessObject,
        BusinessSubscription, BusinessConcept, DataField, EventScope, BCMType, SourceTraceability
    )

logger = logging.getLogger(__name__)


def _normalize_scope_value(scope_value: str) -> str:
    """Normalizes FR/EN scope variants to EventScope values."""
    value = (scope_value or "public").strip().lower()
    aliases = {
        "public": "public",
        "publique": "public",
        "internal": "internal",
        "interne": "internal",
        "private": "private",
        "prive": "private",
        "privé": "private"
    }
    return aliases.get(value, value)


class BCMParseError(Exception):
    """Error raised when parsing BCM files."""
    pass


class YAMLParser:
    """Generic YAML parser with error handling."""

    @staticmethod
    def load_yaml_file(file_path: Path) -> Dict[str, Any]:
        """Loads a YAML file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data is None:
                    raise BCMParseError(f"Empty YAML file: {file_path}")
                return data
        except FileNotFoundError:
            raise BCMParseError(f"YAML file not found: {file_path}")
        except yaml.YAMLError as e:
            raise BCMParseError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise BCMParseError(f"Error loading {file_path}: {e}")
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str], context: str) -> None:
        """Validates that all required fields are present."""
        missing = [field for field in required_fields if field not in data or not data[field]]
        if missing:
            raise BCMParseError(f"Missing required fields in {context}: {missing}")


class CapabilityL1Parser:
    """Parser for L1 capabilities."""

    def __init__(self, yaml_parser: YAMLParser, strict: bool = False):
        self.yaml_parser = yaml_parser
        self.strict = strict

    def parse_file(self, file_path: Path) -> List[CapabilityL1]:
        """Parses an L1 capabilities file."""
        logger.info(f"Parsing L1 capabilities from {file_path}")
        
        data = self.yaml_parser.load_yaml_file(file_path)
        
        # Validate overall structure
        if 'capabilities' not in data:
            raise BCMParseError(f"No 'capabilities' section in {file_path}")

        capabilities = []
        for i, cap_data in enumerate(data['capabilities']):
            try:
                capability = self._parse_capability_l1(cap_data, file_path, i)
                capabilities.append(capability)
            except BCMParseError as e:
                raise BCMParseError(f"Invalid L1 capability at index {i} in {file_path}: {e}")
            except Exception as e:
                if self.strict:
                    raise BCMParseError(
                        f"Unexpected error while parsing L1 capability at index {i} in {file_path}: {e}"
                    ) from e
                logger.warning(f"Skipping invalid L1 capability at index {i} in {file_path}: {e}")
        
        logger.info(f"Parsed {len(capabilities)} L1 capabilities from {file_path}")
        return capabilities
    
    def _parse_capability_l1(self, data: Dict[str, Any], file_path: Path, index: int) -> CapabilityL1:
        """Parses an individual L1 capability."""
        required_fields = ['id', 'name', 'level', 'description', 'owner']
        context = f"L1 capability #{index} in {file_path}"
        self.yaml_parser.validate_required_fields(data, required_fields, context)

        # Validate L1 level
        if data['level'] != 'L1':
            raise BCMParseError(f"Expected level 'L1', got '{data['level']}' in {context}")

        # Validate ID prefix
        if not data['id'].startswith('CAP.'):
            raise BCMParseError(f"L1 ID must start with 'CAP.', got '{data['id']}' in {context}")

        source = SourceTraceability(
            source_id=data['id'],
            source_file=str(file_path),
            bcm_type=BCMType.CAPABILITY_L1,
            source_line=None  # YAML parser does not provide line numbers
        )
        
        return CapabilityL1(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            owner=data['owner'],
            zoning=data.get('zoning', ''),
            adrs=data.get('adrs', []),
            source=source
        )


class CapabilityL2Parser:
    """Parser for L2 capabilities."""

    def __init__(self, yaml_parser: YAMLParser, strict: bool = False):
        self.yaml_parser = yaml_parser
        self.strict = strict

    def parse_file(self, file_path: Path, l2_to_l1_map: Optional[Dict[str, str]] = None) -> List[CapabilityL2]:
        """Parses an L2 capabilities file."""
        logger.info(f"Parsing L2 capabilities from {file_path}")
        
        data = self.yaml_parser.load_yaml_file(file_path)
        
        # Validate overall structure
        if 'capabilities' not in data:
            raise BCMParseError(f"No 'capabilities' section in {file_path}")

        capabilities = []
        for i, cap_data in enumerate(data['capabilities']):
            try:
                capability = self._parse_capability_l2(cap_data, file_path, i, l2_to_l1_map or {})
                capabilities.append(capability)
            except BCMParseError as e:
                raise BCMParseError(f"Invalid L2/L3 capability at index {i} in {file_path}: {e}")
            except Exception as e:
                if self.strict:
                    raise BCMParseError(
                        f"Unexpected error while parsing L2/L3 capability at index {i} in {file_path}: {e}"
                    ) from e
                logger.warning(f"Skipping invalid L2 capability at index {i} in {file_path}: {e}")
        
        logger.info(f"Parsed {len(capabilities)} L2 capabilities from {file_path}")
        return capabilities
    
    def _parse_capability_l2(
        self,
        data: Dict[str, Any],
        file_path: Path,
        index: int,
        l2_to_l1_map: Dict[str, str]
    ) -> CapabilityL2:
        """Parses an individual service capability (L2 or L3)."""
        required_fields = ['id', 'name', 'level', 'parent', 'description', 'owner']
        context = f"L2 capability #{index} in {file_path}"
        self.yaml_parser.validate_required_fields(data, required_fields, context)

        level = data.get('level')
        if level not in {'L2', 'L3'}:
            raise BCMParseError(f"Expected level 'L2' or 'L3', got '{level}' in {context}")

        # Validate ID prefix
        if not data['id'].startswith('CAP.'):
            raise BCMParseError(f"L2 ID must start with 'CAP.', got '{data['id']}' in {context}")

        # Validate parent ID
        if not data['parent'].startswith('CAP.'):
            raise BCMParseError(f"Capability parent must start with 'CAP.', got '{data['parent']}' in {context}")

        parent_l1_id = data['parent']
        parent_l2_id = None
        bcm_type = BCMType.CAPABILITY_L2

        if level == 'L3':
            parent_l2_id = data['parent']
            parent_l1_id = l2_to_l1_map.get(parent_l2_id)
            if not parent_l1_id:
                raise BCMParseError(
                    f"Cannot resolve L1 parent from L3 parent '{parent_l2_id}' in {context}"
                )
            bcm_type = BCMType.CAPABILITY_L3
        
        source = SourceTraceability(
            source_id=data['id'],
            source_file=str(file_path),
            bcm_type=bcm_type
        )
        
        return CapabilityL2(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            owner=data['owner'],
            parent_l1_id=parent_l1_id,
            level=level,
            parent_l2_id=parent_l2_id,
            zoning=data.get('zoning', ''),
            adrs=data.get('adrs', []),
            source=source
        )


class BusinessEventParser:
    """Parser for business events."""

    def __init__(self, yaml_parser: YAMLParser, strict: bool = False):
        self.yaml_parser = yaml_parser
        self.strict = strict

    def parse_file(self, file_path: Path) -> List[BusinessEvent]:
        """Parses a business events file."""
        logger.info(f"Parsing business events from {file_path}")
        
        data = self.yaml_parser.load_yaml_file(file_path)
        
        # Validate overall structure
        if 'business_events' not in data:
            raise BCMParseError(f"No 'business_events' section in {file_path}")

        events = []
        for i, event_data in enumerate(data['business_events']):
            try:
                event = self._parse_business_event(event_data, file_path, i)
                events.append(event)
            except BCMParseError as e:
                raise BCMParseError(f"Invalid business event at index {i} in {file_path}: {e}")
            except Exception as e:
                if self.strict:
                    raise BCMParseError(
                        f"Unexpected error while parsing business event at index {i} in {file_path}: {e}"
                    ) from e
                logger.warning(f"Skipping invalid business event at index {i} in {file_path}: {e}")
        
        logger.info(f"Parsed {len(events)} business events from {file_path}")
        return events
    
    def _parse_business_event(self, data: Dict[str, Any], file_path: Path, index: int) -> BusinessEvent:
        """Parses an individual business event."""
        required_fields = ['id', 'name', 'version', 'definition', 'emitting_capability', 'carried_business_object']
        context = f"Business event #{index} in {file_path}"
        self.yaml_parser.validate_required_fields(data, required_fields, context)

        # Validate ID prefixes
        if not data['id'].startswith('EVT.'):
            raise BCMParseError(f"Event ID must start with 'EVT.', got '{data['id']}' in {context}")
        
        if not data['emitting_capability'].startswith('CAP.'):
            raise BCMParseError(f"Emitting capability must start with 'CAP.', got '{data['emitting_capability']}' in {context}")
        
        if not data['carried_business_object'].startswith('OBJ.'):
            raise BCMParseError(f"Business object must start with 'OBJ.', got '{data['carried_business_object']}' in {context}")
        
        # Parse scope with fallback
        scope_str = _normalize_scope_value(data.get('scope', 'public'))
        try:
            scope = EventScope(scope_str)
        except ValueError:
            if self.strict:
                raise BCMParseError(f"Unknown scope '{scope_str}' for event {data['id']}")
            logger.warning(f"Unknown scope '{scope_str}' for event {data['id']}, defaulting to PUBLIC")
            scope = EventScope.PUBLIC
        
        source = SourceTraceability(
            source_id=data['id'],
            source_file=str(file_path),
            bcm_type=BCMType.BUSINESS_EVENT
        )
        
        return BusinessEvent(
            id=data['id'],
            name=data['name'],
            version=data['version'],
            definition=data['definition'],
            emitting_capability_l2_id=data['emitting_capability'],
            business_object_id=data['carried_business_object'],
            scope=scope,
            adrs=data.get('adrs', []),
            tags=data.get('tags', []),
            source=source
        )


class BusinessObjectParser:
    """Parser for business objects."""

    def __init__(self, yaml_parser: YAMLParser, strict: bool = False):
        self.yaml_parser = yaml_parser
        self.strict = strict

    def parse_file(self, file_path: Path) -> List[BusinessObject]:
        """Parses a business objects file."""
        logger.info(f"Parsing business objects from {file_path}")
        
        data = self.yaml_parser.load_yaml_file(file_path)
        
        # Validate overall structure (field is called 'resources' for historical reasons)
        if 'resources' not in data:
            raise BCMParseError(f"No 'resources' section in {file_path}")
        
        objects = []
        for i, obj_data in enumerate(data['resources']):
            try:
                obj = self._parse_business_object(obj_data, file_path, i)
                objects.append(obj)
            except BCMParseError as e:
                raise BCMParseError(f"Invalid business object at index {i} in {file_path}: {e}")
            except Exception as e:
                if self.strict:
                    raise BCMParseError(
                        f"Unexpected error while parsing business object at index {i} in {file_path}: {e}"
                    ) from e
                logger.warning(f"Skipping invalid business object at index {i} in {file_path}: {e}")
        
        logger.info(f"Parsed {len(objects)} business objects from {file_path}")
        return objects
    
    def _parse_business_object(self, data: Dict[str, Any], file_path: Path, index: int) -> BusinessObject:
        """Parses an individual business object."""
        required_fields = ['id', 'name', 'definition', 'emitting_capability']
        context = f"Business object #{index} in {file_path}"
        self.yaml_parser.validate_required_fields(data, required_fields, context)

        if 'emitting_business_event' in data or 'emitting_business_events' in data:
            raise BCMParseError(
                f"Forbidden relation in {context}: business objects must not reference events. "
                f"Use event->object relation via 'carried_business_object' on business events."
            )
        
        # Validate ID prefixes
        if not data['id'].startswith('OBJ.'):
            raise BCMParseError(f"Object ID must start with 'OBJ.', got '{data['id']}' in {context}")

        if not data['emitting_capability'].startswith('CAP.'):
            raise BCMParseError(f"Emitting capability must start with 'CAP.', got '{data['emitting_capability']}' in {context}")

        # Parse data fields if present
        data_fields = []
        if 'data' in data and data['data']:
            for j, field_data in enumerate(data['data']):
                try:
                    field = self._parse_data_field(field_data, data['id'], j)
                    data_fields.append(field)
                except BCMParseError as e:
                    raise BCMParseError(f"Invalid data field #{j} for object {data['id']}: {e}")
                except Exception as e:
                    if self.strict:
                        raise BCMParseError(
                            f"Unexpected error while parsing data field #{j} for object {data['id']}: {e}"
                        ) from e
                    logger.warning(f"Skipping invalid data field #{j} for object {data['id']}: {e}")
        
        source = SourceTraceability(
            source_id=data['id'],
            source_file=str(file_path),
            bcm_type=BCMType.BUSINESS_OBJECT
        )
        
        return BusinessObject(
            id=data['id'],
            name=data['name'],
            definition=data['definition'],
            emitting_capability_l2_id=data['emitting_capability'],
            emitting_capability_l3_ids=data.get('emitting_capability_L3', []) or [],
            data_fields=data_fields,
            adrs=data.get('adrs', []),
            tags=data.get('tags', []),
            source=source
        )
    
    def _parse_data_field(self, data: Dict[str, Any], object_id: str, index: int) -> DataField:
        """Parses a data field of a business object."""
        required_fields = ['name', 'type', 'description']
        context = f"Data field #{index} of object {object_id}"
        self.yaml_parser.validate_required_fields(data, required_fields, context)

        # Validate boolean type for required
        required_val = data.get('required', False)
        if not isinstance(required_val, bool):
            raise BCMParseError(f"Field 'required' must be boolean, got {type(required_val)} in {context}")
        
        return DataField(
            name=data['name'],
            type=data['type'],
            description=data['description'],
            required=required_val
        )


class BusinessSubscriptionParser:
    """Parser for business event subscriptions."""

    def __init__(self, yaml_parser: YAMLParser, strict: bool = False):
        self.yaml_parser = yaml_parser
        self.strict = strict

    def parse_file(self, file_path: Path) -> List[BusinessSubscription]:
        """Parses a business subscriptions file."""
        logger.info(f"Parsing business subscriptions from {file_path}")

        data = self.yaml_parser.load_yaml_file(file_path)

        if 'business_subscriptions' not in data:
            raise BCMParseError(f"No 'business_subscriptions' section in {file_path}")

        subscriptions = []
        for i, sub_data in enumerate(data['business_subscriptions']):
            try:
                sub = self._parse_business_subscription(sub_data, file_path, i)
                subscriptions.append(sub)
            except BCMParseError as e:
                raise BCMParseError(f"Invalid business subscription at index {i} in {file_path}: {e}")
            except Exception as e:
                if self.strict:
                    raise BCMParseError(
                        f"Unexpected error while parsing business subscription at index {i} in {file_path}: {e}"
                    ) from e
                logger.warning(f"Skipping invalid business subscription at index {i} in {file_path}: {e}")

        logger.info(f"Parsed {len(subscriptions)} business subscriptions from {file_path}")
        return subscriptions

    def _parse_business_subscription(self, data: Dict[str, Any], file_path: Path, index: int) -> BusinessSubscription:
        """Parses an individual business subscription."""
        required_fields = ['id', 'consumer_capability', 'subscribed_event']
        context = f"Business subscription #{index} in {file_path}"
        self.yaml_parser.validate_required_fields(data, required_fields, context)

        if not data['id'].startswith('SUB.'):
            raise BCMParseError(f"Subscription ID must start with 'SUB.', got '{data['id']}' in {context}")

        if not data['consumer_capability'].startswith('CAP.'):
            raise BCMParseError(
                f"Consumer capability must start with 'CAP.', got '{data['consumer_capability']}' in {context}"
            )

        subscribed_event = data.get('subscribed_event', {}) or {}
        subscribed_required = ['id', 'version', 'emitting_capability']
        self.yaml_parser.validate_required_fields(
            subscribed_event,
            subscribed_required,
            f"subscribed_event of {data['id']}"
        )

        if not subscribed_event['id'].startswith('EVT.'):
            raise BCMParseError(
                f"Subscribed event ID must start with 'EVT.', got '{subscribed_event['id']}' in {context}"
            )

        if not subscribed_event['emitting_capability'].startswith('CAP.'):
            raise BCMParseError(
                f"Subscribed event emitting capability must start with 'CAP.', got '{subscribed_event['emitting_capability']}' in {context}"
            )

        scope_str = _normalize_scope_value(data.get('scope', 'public'))
        try:
            scope = EventScope(scope_str)
        except ValueError:
            if self.strict:
                raise BCMParseError(f"Unknown scope '{scope_str}' for subscription {data['id']}")
            logger.warning(f"Unknown scope '{scope_str}' for subscription {data['id']}, defaulting to PUBLIC")
            scope = EventScope.PUBLIC

        source = SourceTraceability(
            source_id=data['id'],
            source_file=str(file_path),
            bcm_type=BCMType.BUSINESS_SUBSCRIPTION
        )

        return BusinessSubscription(
            id=data['id'],
            consumer_capability_l2_id=data['consumer_capability'],
            subscribed_event_id=subscribed_event['id'],
            subscribed_event_version=subscribed_event['version'],
            emitting_capability_l2_id=subscribed_event['emitting_capability'],
            scope=scope,
            rationale=data.get('rationale', ''),
            adrs=data.get('adrs', []),
            tags=data.get('tags', []),
            source=source
        )


class BusinessConceptParser:
    """Parser for canonical business concepts."""

    def __init__(self, yaml_parser: YAMLParser, strict: bool = False):
        self.yaml_parser = yaml_parser
        self.strict = strict

    def parse_file(self, file_path: Path) -> List[BusinessConcept]:
        """Parses a business concepts file."""
        logger.info(f"Parsing business concepts from {file_path}")

        data = self.yaml_parser.load_yaml_file(file_path)

        if 'concepts' not in data:
            raise BCMParseError(f"No 'concepts' section in {file_path}")

        concepts = []
        for i, concept_data in enumerate(data['concepts']):
            try:
                concept = self._parse_business_concept(concept_data, file_path, i)
                concepts.append(concept)
            except BCMParseError as e:
                raise BCMParseError(f"Invalid business concept at index {i} in {file_path}: {e}")
            except Exception as e:
                if self.strict:
                    raise BCMParseError(
                        f"Unexpected error while parsing business concept at index {i} in {file_path}: {e}"
                    ) from e
                logger.warning(f"Skipping invalid business concept at index {i} in {file_path}: {e}")

        logger.info(f"Parsed {len(concepts)} business concepts from {file_path}")
        return concepts

    def _parse_business_concept(self, data: Dict[str, Any], file_path: Path, index: int) -> BusinessConcept:
        """Parses an individual business concept."""
        required_fields = ['id', 'name', 'definition']
        context = f"Business concept #{index} in {file_path}"
        self.yaml_parser.validate_required_fields(data, required_fields, context)

        if not data['id'].startswith('CPT.'):
            raise BCMParseError(f"Concept ID must start with 'CPT.', got '{data['id']}' in {context}")

        properties = []
        if 'properties' in data and data['properties']:
            for j, field_data in enumerate(data['properties']):
                try:
                    field = self._parse_concept_property(field_data, data['id'], j)
                    properties.append(field)
                except BCMParseError as e:
                    raise BCMParseError(
                        f"Invalid concept property #{j} for concept {data['id']}: {e}"
                    )
                except Exception as e:
                    if self.strict:
                        raise BCMParseError(
                            f"Unexpected error while parsing concept property #{j} for concept {data['id']}: {e}"
                        ) from e
                    logger.warning(
                        f"Skipping invalid concept property #{j} for concept {data['id']}: {e}"
                    )

        source = SourceTraceability(
            source_id=data['id'],
            source_file=str(file_path),
            bcm_type=BCMType.BUSINESS_CONCEPT
        )

        return BusinessConcept(
            id=data['id'],
            name=data['name'],
            definition=data['definition'],
            scope=data.get('scope', []),
            properties=properties,
            business_rules=data.get('business_rules', []),
            tags=data.get('tags', []),
            source=source
        )

    def _parse_concept_property(self, data: Dict[str, Any], concept_id: str, index: int) -> DataField:
        """Parses a business concept property."""
        required_fields = ['name', 'type', 'description']
        context = f"Concept property #{index} of concept {concept_id}"
        self.yaml_parser.validate_required_fields(data, required_fields, context)

        required_val = data.get('required', False)
        if not isinstance(required_val, bool):
            raise BCMParseError(f"Field 'required' must be boolean, got {type(required_val)} in {context}")

        return DataField(
            name=data['name'],
            type=data['type'],
            description=data['description'],
            required=required_val
        )


class BCMParser:
    """Main parser that orchestrates parsing of all BCM files."""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.yaml_parser = YAMLParser()
        self.capability_l1_parser = CapabilityL1Parser(self.yaml_parser, strict=self.strict)
        self.capability_l2_parser = CapabilityL2Parser(self.yaml_parser, strict=self.strict)
        self.business_event_parser = BusinessEventParser(self.yaml_parser, strict=self.strict)
        self.business_object_parser = BusinessObjectParser(self.yaml_parser, strict=self.strict)
        self.business_subscription_parser = BusinessSubscriptionParser(self.yaml_parser, strict=self.strict)
        self.business_concept_parser = BusinessConceptParser(self.yaml_parser, strict=self.strict)

    def parse_bcm_directory(self, bcm_dir: Path) -> BCMModel:
        """Parses all BCM files in a directory and builds the complete model."""
        logger.info(f"Parsing BCM directory: {bcm_dir}")
        
        if not bcm_dir.exists() or not bcm_dir.is_dir():
            raise BCMParseError(f"BCM directory not found or not a directory: {bcm_dir}")
        
        model = BCMModel()

        # Parse L1 capabilities
        l1_file = bcm_dir / "capabilities-L1.yaml"
        if l1_file.exists():
            model.capabilities_l1.extend(self.capability_l1_parser.parse_file(l1_file))
        else:
            if self.strict:
                raise BCMParseError(f"L1 capabilities file not found: {l1_file}")
            logger.warning(f"L1 capabilities file not found: {l1_file}")
        
        # Parse L2 capabilities (pattern capabilities-*-L2.yaml)
        l2_files = list(bcm_dir.glob("capabilities-*-L2.yaml"))
        for l2_file in l2_files:
            model.capabilities_l2.extend(self.capability_l2_parser.parse_file(l2_file))
        
        if not l2_files:
            if self.strict:
                raise BCMParseError(f"No L2 capabilities files found in {bcm_dir}")
            logger.warning(f"No L2 capabilities files found in {bcm_dir}")

        # Parse L3 capabilities (pattern capabilities-*-L3.yaml)
        l2_to_l1_map = {cap.id: cap.parent_l1_id for cap in model.capabilities_l2 if cap.level == "L2"}
        l3_files = list(bcm_dir.glob("capabilities-*-L3.yaml"))
        for l3_file in l3_files:
            model.capabilities_l2.extend(
                self.capability_l2_parser.parse_file(l3_file, l2_to_l1_map=l2_to_l1_map)
            )
        
        # Parse business events
        event_dir = bcm_dir / "business-event"
        if event_dir.exists():
            event_files = list(event_dir.glob("business-event-*.yaml"))
            for event_file in event_files:
                model.business_events.extend(self.business_event_parser.parse_file(event_file))

            subscription_files = list(event_dir.glob("business-subscription-*.yaml"))
            for subscription_file in subscription_files:
                model.business_subscriptions.extend(
                    self.business_subscription_parser.parse_file(subscription_file)
                )
        else:
            if self.strict:
                raise BCMParseError(f"Business events directory not found: {event_dir}")
            logger.warning(f"Business events directory not found: {event_dir}")
        
        # Parse business objects
        object_dir = bcm_dir / "business-object"
        if object_dir.exists():
            object_files = list(object_dir.glob("business-object-*.yaml"))
            for object_file in object_files:
                model.business_objects.extend(self.business_object_parser.parse_file(object_file))
        else:
            if self.strict:
                raise BCMParseError(f"Business objects directory not found: {object_dir}")
            logger.warning(f"Business objects directory not found: {object_dir}")

        # Parse business concepts
        concept_dir = bcm_dir / "business-concept"
        if concept_dir.exists():
            concept_files = list(concept_dir.glob("business-concept-*.yaml"))
            for concept_file in concept_files:
                model.business_concepts.extend(self.business_concept_parser.parse_file(concept_file))
        else:
            if self.strict:
                raise BCMParseError(f"Business concepts directory not found: {concept_dir}")
            logger.warning(f"Business concepts directory not found: {concept_dir}")
        
        logger.info(f"BCM parsing complete. Summary: {model.get_summary()}")
        return model
    
    def parse_specific_files(self,
                           l1_file: Optional[Path] = None,
                           l2_files: Optional[List[Path]] = None,
                           event_files: Optional[List[Path]] = None,
                           object_files: Optional[List[Path]] = None,
                           subscription_files: Optional[List[Path]] = None,
                           concept_files: Optional[List[Path]] = None) -> BCMModel:
        """Parses specific BCM files (for tests or custom usage)."""
        model = BCMModel()
        
        if l1_file:
            model.capabilities_l1.extend(self.capability_l1_parser.parse_file(l1_file))
        
        if l2_files:
            for l2_file in l2_files:
                model.capabilities_l2.extend(self.capability_l2_parser.parse_file(l2_file))
        
        if event_files:
            for event_file in event_files:
                model.business_events.extend(self.business_event_parser.parse_file(event_file))
        
        if object_files:
            for object_file in object_files:
                model.business_objects.extend(self.business_object_parser.parse_file(object_file))

        if subscription_files:
            for subscription_file in subscription_files:
                model.business_subscriptions.extend(
                    self.business_subscription_parser.parse_file(subscription_file)
                )

        if concept_files:
            for concept_file in concept_files:
                model.business_concepts.extend(
                    self.business_concept_parser.parse_file(concept_file)
                )
        
        return model