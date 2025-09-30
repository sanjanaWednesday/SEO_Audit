"""
DataForSEO API Client Package
Organized API clients for different SEO analysis categories
"""

from .base_client import BaseDataForSEOClient
from .domain_apis import DomainAPIs
from .keyword_apis import KeywordAPIs
from .backlink_apis import BacklinkAPIs
from .serp_apis import SERPAPIs

class DataForSEOClient:
    """
    Main DataForSEO client that combines all API categories
    
    Usage:
        client = DataForSEOClient()
        
        # Domain analysis
        metrics = await client.domain.get_domain_metrics("example.com")
        competitors = await client.domain.get_competitors("example.com")
        
        # Keyword research
        keywords = await client.keyword.get_ranked_keywords("example.com")
        volume = await client.keyword.get_search_volume(["keyword1", "keyword2"])
        
        # Backlink analysis
        backlinks = await client.backlink.get_backlinks_summary("example.com")
        
        # SERP analysis
        serp = await client.serp.get_serp_analysis("target keyword")
        content = await client.serp.get_content_analysis("https://example.com")
    """
    
    def __init__(self):
        self.domain = DomainAPIs()
        self.keyword = KeywordAPIs()
        self.backlink = BacklinkAPIs()
        self.serp = SERPAPIs()
    
    # Convenience methods for backward compatibility
    async def get_domain_metrics(self, target: str, location_code: int = 2840, language_code: str = "en") -> dict:
        """Convenience method for domain metrics"""
        return await self.domain.get_domain_metrics(target, location_code, language_code)
    
    async def get_ranked_keywords(self, target: str, location_code: int = 2840, language_code: str = "en", limit: int = 100) -> dict:
        """Convenience method for ranked keywords"""
        return await self.keyword.get_ranked_keywords(target, location_code, language_code, limit)
    
    async def get_backlinks_summary(self, target: str, internal_list_limit: int = 10, backlinks_status_type: str = "live") -> dict:
        """Convenience method for backlinks summary"""
        return await self.backlink.get_backlinks_summary(target, internal_list_limit, backlinks_status_type)
    
    async def get_competitors(self, target: str, location_code: int = 2840, language_code: str = "en", limit: int = 10) -> dict:
        """Convenience method for competitors"""
        return await self.domain.get_competitors(target, location_code, language_code, limit)
    
    async def get_domain_intersection(self, targets: dict, location_code: int = 2840, language_code: str = "en", intersections: str = "2", limit: int = 100) -> dict:
        """Convenience method for domain intersection"""
        return await self.domain.get_domain_intersection(targets, location_code, language_code, intersections, limit)
    
    async def get_keywords_from_site(self, target: str, location_code: int = 2840, language_code: str = "en", include_serp_info: bool = True, limit: int = 100) -> dict:
        """Convenience method for keywords from site"""
        return await self.keyword.get_keywords_from_site(target, location_code, language_code, include_serp_info, limit)
    
    async def get_search_volume(self, keywords: list, location_code: int = 2840, language_code: str = "en") -> dict:
        """Convenience method for search volume"""
        return await self.keyword.get_search_volume(keywords, location_code, language_code)
    
    async def get_keyword_suggestions(self, keyword: str, location_code: int = 2840, language_code: str = "en", include_seed_keyword: bool = True, include_serp_info: bool = True, limit: int = 100) -> dict:
        """Convenience method for keyword suggestions"""
        return await self.keyword.get_keyword_suggestions(keyword, location_code, language_code, include_seed_keyword, include_serp_info, limit)
    
    async def get_serp_analysis(self, keyword: str, location_code: int = 2840, language_code: str = "en", device: str = "desktop", depth: int = 100) -> dict:
        """Convenience method for SERP analysis"""
        return await self.serp.get_serp_analysis(keyword, location_code, language_code, device, depth)
    
    async def get_content_analysis(self, url: str, enable_javascript: bool = True, support_javascript: bool = True) -> dict:
        """Convenience method for content analysis"""
        return await self.serp.get_content_analysis(url, enable_javascript, support_javascript)
    
    async def get_backlinks_list(self, target: str, limit: int = 100) -> dict:
        """Convenience method for backlinks list"""
        return await self.backlink.get_backlinks_list(target, limit)

__all__ = ['DataForSEOClient', 'DomainAPIs', 'KeywordAPIs', 'BacklinkAPIs', 'SERPAPIs', 'BaseDataForSEOClient']
