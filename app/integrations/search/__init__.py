"""Web search integration package.

Same shape as CRM / email / enrichment: a ``base.py`` defining the
``SearchProvider`` Protocol + ``SearchResult`` dataclass, concrete
providers next to it, and a ``factory.py`` that picks one based on
settings + tenant config.
"""
from app.integrations.search.base import (
    SearchError,
    SearchProvider,
    SearchResult,
)
from app.integrations.search.factory import get_search_provider

__all__ = [
    "SearchError",
    "SearchProvider",
    "SearchResult",
    "get_search_provider",
]
