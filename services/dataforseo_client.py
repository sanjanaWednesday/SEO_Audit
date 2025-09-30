"""
DataForSEO API Client (Legacy Wrapper)
This file maintains backward compatibility while using the new organized structure.

For new code, consider using the organized modules directly:
- from services.dataforseo import DataForSEOClient
- from services.dataforseo.domain_apis import DomainAPIs
- from services.dataforseo.keyword_apis import KeywordAPIs
- etc.
"""

from .dataforseo import DataForSEOClient

# This maintains backward compatibility for existing code
__all__ = ['DataForSEOClient']
