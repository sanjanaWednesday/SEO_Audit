"""
DataForSEOTool - Wrapper for all DataForSEO API calls (no backlinks)
"""
from crewai.tools import BaseTool
from typing import Type, Dict, List, Optional
from pydantic import BaseModel, Field
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


class DataForSEOInput(BaseModel):
    """Input schema for DataForSEOTool"""
    action: str = Field(..., description="Action to perform: domain_metrics, ranked_keywords, competitors, domain_intersection, keywords_from_site, search_volume, keyword_suggestions, serp_analysis, content_analysis")
    target: str = Field(None, description="Target domain or keyword")
    target2: str = Field(None, description="Second target for domain_intersection")
    keywords: List[str] = Field(None, description="List of keywords for search_volume")
    limit: int = Field(15, description="Result limit")
    intersections: bool = Field(False, description="For domain_intersection")


class DataForSEOTool(BaseTool):
    name: str = "DataForSEO API Tool"
    description: str = """
    Comprehensive tool for DataForSEO API calls. Supports:
    - domain_metrics: Get domain ranking metrics
    - ranked_keywords: Get keywords the domain ranks for
    - competitors: Find competitor domains
    - domain_intersection: Find keyword gaps between domains
    - keywords_from_site: Get keywords for a site
    - search_volume: Get search volume for keywords
    - keyword_suggestions: Get keyword suggestions
    - serp_analysis: Analyze SERP for a keyword
    - content_analysis: Analyze page content
    
    NO BACKLINK APIS - We don't use backlink data.
    """
    args_schema: Type[BaseModel] = DataForSEOInput
    
    def _run(self, action: str, target: str = None, target2: str = None, 
             keywords: List[str] = None, limit: int = 15, intersections: bool = False) -> Dict:
        """
        Execute DataForSEO API call (synchronous wrapper)
        
        Args:
            action: API action to perform
            target: Target domain or keyword
            target2: Second target for comparisons
            keywords: List of keywords
            limit: Result limit
            intersections: For domain intersection
            
        Returns:
            API response dictionary
        """
        # Check if there's already a running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in a loop, we need to run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._async_run(action, target, target2, keywords, limit, intersections)
                )
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(self._async_run(action, target, target2, keywords, limit, intersections))
    
    async def _async_run(self, action: str, target: str = None, target2: str = None,
                         keywords: List[str] = None, limit: int = 15, intersections: bool = False) -> Dict:
        """Async implementation of API calls"""
        
        action_map = {
            'domain_metrics': self._domain_metrics,
            'ranked_keywords': self._ranked_keywords,
            'competitors': self._competitors,
            'domain_intersection': self._domain_intersection,
            'keywords_from_site': self._keywords_from_site,
            'search_volume': self._search_volume,
            'keyword_suggestions': self._keyword_suggestions,
            'serp_analysis': self._serp_analysis,
            'content_analysis': self._content_analysis
        }
        
        if action not in action_map:
            return {"error": f"Unknown action: {action}", "success": False}
        
        result = await action_map[action](target, target2, keywords, limit, intersections)
        return result
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[List[Dict]] = None) -> Dict:
        """Make authenticated request to DataForSEO API"""
        base_url = os.getenv('DATAFORSEO_BASE_URL', 'https://api.dataforseo.com/v3')
        username = os.getenv('DATAFORSEO_USERNAME')
        password = os.getenv('DATAFORSEO_PASSWORD')
        auth = aiohttp.BasicAuth(username, password) if username and password else None
        
        url = f"{base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        async with aiohttp.ClientSession(auth=auth) as session:
            try:
                if method.upper() == 'POST':
                    async with session.post(url, json=data, headers=headers) as response:
                        result = await response.json()
                        if response.status != 200:
                            return {"error": f"HTTP {response.status}", "endpoint": endpoint, "success": False}
                        
                        if result.get('tasks') and result['tasks'][0].get('status_code') not in [20000, 20100]:
                            status_code = result['tasks'][0].get('status_code')
                            status_message = result['tasks'][0].get('status_message', 'Unknown error')
                            return {"error": f"DataForSEO {status_code}: {status_message}", "success": False}
                        
                        result['success'] = True
                        return result
                else:
                    async with session.get(url, headers=headers) as response:
                        result = await response.json()
                        if response.status != 200:
                            return {"error": f"HTTP {response.status}", "endpoint": endpoint, "success": False}
                        
                        if result.get('tasks') and result['tasks'][0].get('status_code') not in [20000, 20100]:
                            status_code = result['tasks'][0].get('status_code')
                            status_message = result['tasks'][0].get('status_message', 'Unknown error')
                            return {"error": f"DataForSEO {status_code}: {status_message}", "success": False}
                        
                        result['success'] = True
                        return result
            except Exception as e:
                return {"error": str(e), "endpoint": endpoint, "success": False}
    
    async def _domain_metrics(self, target: str, *args) -> Dict:
        """Get domain ranking metrics"""
        endpoint = "/dataforseo_labs/google/domain_rank_overview/live"
        data = [{"target": target, "location_code": 2840, "language_code": "en"}]
        return await self._make_request('POST', endpoint, data)
    
    async def _ranked_keywords(self, target: str, *args, limit: int = 15, **kwargs) -> Dict:
        """Get keywords the domain ranks for"""
        endpoint = "/dataforseo_labs/google/ranked_keywords/live"
        data = [{"target": target, "location_code": 2840, "language_code": "en", "limit": limit}]
        return await self._make_request('POST', endpoint, data)
    
    async def _competitors(self, target: str, *args, limit: int = 15, **kwargs) -> Dict:
        """Find competitor domains"""
        endpoint = "/dataforseo_labs/google/competitors_domain/live"
        data = [{"target": target, "location_code": 2840, "language_code": "en", "limit": limit}]
        return await self._make_request('POST', endpoint, data)
    
    async def _domain_intersection(self, target: str, target2: str, *args, 
                                   intersections: bool = False, limit: int = 15, **kwargs) -> Dict:
        """Find keyword gaps between two domains"""
        endpoint = "/dataforseo_labs/google/domain_intersection/live"
        data = [{
            "target1": target,
            "target2": target2,
            "location_code": 2840,
            "language_code": "en",
            "intersections": intersections,
            "limit": limit
        }]
        return await self._make_request('POST', endpoint, data)
    
    async def _keywords_from_site(self, target: str, *args, limit: int = 15, **kwargs) -> Dict:
        """Get keywords for a site"""
        endpoint = "/dataforseo_labs/google/keywords_for_site/live"
        data = [{"target": target, "location_code": 2840, "language_code": "en", "limit": limit}]
        return await self._make_request('POST', endpoint, data)
    
    async def _search_volume(self, target: str, target2: str, keywords: List[str], *args, **kwargs) -> Dict:
        """Get search volume for keywords"""
        endpoint = "/keywords_data/google_ads/search_volume/live"
        if keywords:
            data = [{"keywords": keywords, "location_code": 2840, "language_code": "en"}]
            return await self._make_request('POST', endpoint, data)
        return {"error": "Keywords list required", "success": False}
    
    async def _keyword_suggestions(self, target: str, *args, limit: int = 15, **kwargs) -> Dict:
        """Get keyword suggestions"""
        endpoint = "/dataforseo_labs/google/keyword_suggestions/live"
        data = [{"keyword": target, "location_code": 2840, "language_code": "en", "limit": limit}]
        return await self._make_request('POST', endpoint, data)
    
    async def _serp_analysis(self, target: str, *args, **kwargs) -> Dict:
        """Analyze SERP for a keyword"""
        endpoint = "/serp/google/organic/live/regular"
        data = [{
            "keyword": target,
            "location_code": 2840,
            "language_code": "en",
            "device": "desktop",
            "depth": 100
        }]
        return await self._make_request('POST', endpoint, data)
    
    async def _content_analysis(self, target: str, *args, **kwargs) -> Dict:
        """Analyze page content"""
        # Target should be a URL for this
        if not target.startswith('http'):
            target = f"https://{target}"
        
        endpoint = "/on_page/instant_pages"
        data = [{
            "url": target,
            "enable_javascript": False,
            "check_spell": True,
            "calculate_keyword_density": True
        }]
        return await self._make_request('POST', endpoint, data)

