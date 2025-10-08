"""
DataForSEO API Client Package
Organized API clients for different SEO analysis categories
"""

from .base_client import BaseDataForSEOClient
from .domain_apis import DomainAPIs
from .keyword_apis import KeywordAPIs
from .backlink_apis import BacklinkAPIs
from .serp_apis import SERPAPIs
from .onpage_apis import OnPageAPIs

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
        self.onpage = OnPageAPIs()
    
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
class OnPageAPIs:
    def __init__(self, client=None):
        self.client = client  # BaseDataForSEOClient instance

    async def start_crawling_task(self, target, start_url=None, max_crawl_pages=10,
                                  force_sitewide_checks=True, max_crawl_depth=2,
                                   store_raw_html=True,
                                  enable_javascript=True, support_javascript=True):
        """Create a new crawl task"""
        body = {
            "target": target,
            "start_url": start_url or f"https://{target}",
            "max_crawl_pages": max_crawl_pages,
            "force_sitewide_checks": force_sitewide_checks,
            "max_crawl_depth": max_crawl_depth,
            "store_raw_html": store_raw_html,
            "enable_javascript": enable_javascript,
            "support_javascript": support_javascript
        }
        response = await self.client.post("/v3/on_page/task_post", body)
        task_id = response.get("tasks", [{}])[0].get("id")
        return task_id

    async def get_task_result(self, task_id):
        """Get crawl results for a task_id"""
        response = await self.client.get(f"/v3/on_page/task_get/{task_id}")
        return response

    async def get_crawled_pages(self, crawl_id, limit=10, filters=None, order_by=None, offset=0):
        """Fetch pages data using crawl_id"""
        body = {
            "crawl_id": crawl_id,
            "limit": limit,
            "offset": offset,
            "filters": filters or [],
            "order_by": order_by or []
        }
        response = await self.client.post("/v3/on_page/pages", body)
        return response


__all__ = ['DataForSEOClient', 'DomainAPIs', 'KeywordAPIs', 'BacklinkAPIs', 'SERPAPIs', 'OnPageAPIs', 'BaseDataForSEOClient']
