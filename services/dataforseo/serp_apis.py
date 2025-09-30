"""
SERP Analysis APIs
Handles SERP analysis and content quality checks
"""
from typing import Dict, List, Optional
from .base_client import BaseDataForSEOClient

class SERPAPIs(BaseDataForSEOClient):
    """APIs for SERP analysis and content quality checks"""
    
    async def get_serp_analysis(self, keyword: str, location_code: int = 2840, language_code: str = "en", device: str = "desktop", depth: int = 100) -> Dict:
        """
        Get SERP analysis for a keyword
        
        Args:
            keyword: Keyword to analyze SERP for
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            device: Device type ("desktop", "mobile", "tablet")
            depth: Number of results to analyze
            
        Returns:
            Dict containing SERP analysis data
        """
        endpoint = "/serp/google/organic/task_post"
        data = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "device": device,
            "depth": depth
        }]
        
        task_id = await self.create_task(endpoint, data)
        if not task_id:
            return {"error": "Failed to create SERP analysis task"}
        
        return await self.get_task_result("/serp/google/organic/task_get", task_id)

    async def get_content_analysis(self, url: str, enable_javascript: bool = True, support_javascript: bool = True) -> Dict:
        """
        Get instant content analysis for a URL
        
        Args:
            url: URL to analyze (e.g., "https://example.com/page")
            enable_javascript: Enable JavaScript rendering
            support_javascript: Support JavaScript features
            
        Returns:
            Dict containing content analysis data
        """
        endpoint = "/on_page/instant_pages"
        data = [{
            "url": url,
            "enable_javascript": enable_javascript,
            "support_javascript": support_javascript
        }]
        
        return await self._make_request('POST', endpoint, data)
