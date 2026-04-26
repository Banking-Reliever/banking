"""
BCM Export - Exports BCM to EventCatalog.

This package contains all the tools needed to export
a Business Capability Map (BCM) to an EventCatalog.

Main usage:
    from bcm_export import BCMParser, BCMNormalizer, EventCatalogGenerator

    # Or use the CLI script:
    python bcm_export_metier.py --input ./bcm --output ./eventcatalog
"""

__version__ = "1.0.0"
__author__ = "FOODAROO - Architecture Team"

# Main imports for use as a module
from .domain_model import (
    BCMModel, CapabilityL1, CapabilityL2, BusinessEvent, BusinessObject,
    DataField, EventScope, BCMType, SourceTraceability
)

from .parser_bcm import BCMParser, BCMParseError
from .normalizer import BCMNormalizer, NormalizationError
from .eventcatalog_generator import EventCatalogGenerator

__all__ = [
    # Model classes
    "BCMModel",
    "CapabilityL1",
    "CapabilityL2",
    "BusinessEvent",
    "BusinessObject",
    "DataField",
    "EventScope",
    "BCMType",
    "SourceTraceability",

    # Parsers and generators
    "BCMParser",
    "BCMNormalizer",
    "EventCatalogGenerator",

    # Exceptions
    "BCMParseError",
    "NormalizationError"
]