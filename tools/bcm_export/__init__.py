"""
BCM Export - Export BCM vers EventCatalog.

Ce package contient tous les outils nécessaires pour exporter
un Business Capability Map (BCM) vers un EventCatalog.

Usage principal:
    from bcm_export import BCMParser, BCMNormalizer, EventCatalogGenerator
    
    # Ou utiliser le script CLI:
    python bcm_export_metier.py --input ./bcm --output ./eventcatalog
"""

__version__ = "1.0.0"
__author__ = "FOODAROO - Équipe Architecture"

# Imports principaux pour usage en tant que module
from .domain_model import (
    BCMModel, CapabilityL1, CapabilityL2, BusinessEvent, BusinessObject,
    DataField, EventScope, BCMType, SourceTraceability
)

from .parser_bcm import BCMParser, BCMParseError
from .normalizer import BCMNormalizer, NormalizationError
from .eventcatalog_generator import EventCatalogGenerator

__all__ = [
    # Classes de modèle
    "BCMModel", 
    "CapabilityL1", 
    "CapabilityL2", 
    "BusinessEvent", 
    "BusinessObject",
    "DataField",
    "EventScope",
    "BCMType", 
    "SourceTraceability",
    
    # Parseurs et générateurs  
    "BCMParser",
    "BCMNormalizer", 
    "EventCatalogGenerator",
    
    # Exceptions
    "BCMParseError",
    "NormalizationError"
]