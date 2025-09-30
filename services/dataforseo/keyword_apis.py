"""
Keyword Research APIs
Handles keyword analysis, search volume, and keyword suggestions
"""
from typing import Dict, List, Optional
from .base_client import BaseDataForSEOClient

class KeywordAPIs(BaseDataForSEOClient):
    """APIs for keyword research and analysis"""
    
    async def get_ranked_keywords(self, target: str, location_code: int = 2840, language_code: str = "en", limit: int = 100) -> Dict:
        """
        Get ranked keywords for a website
        
        Args:
            target: Domain to analyze (e.g., "example.com")
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            limit: Maximum number of keywords to return
            
        Returns:
            Dict containing ranked keywords data
        """
        endpoint = "/dataforseo_labs/google/ranked_keywords/task_post"
        data = [{
            "target": target,
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit
        }]
        
        task_id = await self.create_task(endpoint, data)
        if not task_id:
            return {"error": "Failed to create ranked keywords task"}
        
        return await self.get_task_result("/dataforseo_labs/google/ranked_keywords/task_get", task_id)

    async def get_keywords_from_site(self, target: str, location_code: int = 2840, language_code: str = "en", include_serp_info: bool = True, limit: int = 100) -> Dict:
        """
        Get keywords from a website
        
        Args:
            target: Domain to analyze (e.g., "competitor.com")
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            include_serp_info: Include SERP information
            limit: Maximum number of keywords to return
            
        Returns:
            Dict containing keywords found on the site
        """
        endpoint = "/keywords_data/google_ads/keywords_for_site/task_post"
        data = [{
            "target": target,
            "location_code": location_code,
            "language_code": language_code,
            "include_serp_info": include_serp_info,
            "limit": limit
        }]
        
        task_id = await self.create_task(endpoint, data)
        if not task_id:
            return {"error": "Failed to create keywords from site task"}
        
        return await self.get_task_result("/keywords_data/google_ads/keywords_for_site/task_get", task_id)

    async def get_search_volume(self, keywords: List[str], location_code: int = 2840, language_code: str = "en") -> Dict:
        """
        Get search volume for keywords
        
        Args:
            keywords: List of keywords to analyze
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            
        Returns:
            Dict containing search volume data for each keyword
        """
        endpoint = "/keywords_data/google_ads/search_volume/task_post"
        data = [{
            "keywords": keywords,
            "location_code": location_code,
            "language_code": language_code
        }]
        
        task_id = await self.create_task(endpoint, data)
        if not task_id:
            return {"error": "Failed to create search volume task"}
        
        return await self.get_task_result("/keywords_data/google_ads/search_volume/task_get", task_id)

    async def get_keyword_suggestions(self, keyword: str, location_code: int = 2840, language_code: str = "en", include_seed_keyword: bool = True, include_serp_info: bool = True, limit: int = 100) -> Dict:
        """
        Get keyword suggestions for a main topic
        
        Args:
            keyword: Seed keyword to get suggestions for
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            include_seed_keyword: Include the seed keyword in results
            include_serp_info: Include SERP information
            limit: Maximum number of keywords to return
            
        Returns:
            Dict containing keyword suggestions
        """
        endpoint = "/keywords_data/google_ads/keywords_for_keywords/task_post"
        data = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "include_seed_keyword": include_seed_keyword,
            "include_serp_info": include_serp_info,
            "limit": limit
        }]
        
        task_id = await self.create_task(endpoint, data)
        if not task_id:
            return {"error": "Failed to create keyword suggestions task"}
        
        return await self.get_task_result("/keywords_data/google_ads/keywords_for_keywords/task_get", task_id)
