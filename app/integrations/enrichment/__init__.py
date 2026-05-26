"""Lead enrichment package.

Same shape as the CRM and email packages: a ``base.py`` defining the
``EnrichmentProvider`` Protocol + a ``LeadFacts`` dataclass, concrete
providers next to it, and a ``factory.py`` that picks one based on
settings + tenant config.
"""
from app.integrations.enrichment.base import (
    EnrichmentError,
    EnrichmentProvider,
    LeadFacts,
)
from app.integrations.enrichment.factory import get_enrichment_provider

__all__ = [
    "EnrichmentError",
    "EnrichmentProvider",
    "LeadFacts",
    "get_enrichment_provider",
]
