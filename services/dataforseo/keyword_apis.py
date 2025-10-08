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
        Get ranked keywords for a website (LIVE)
        
        Args:
            target: Domain to analyze (e.g., "example.com")
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            limit: Maximum number of keywords to return
            
        Returns:
            Dict containing ranked keywords data
        """
        endpoint = "/dataforseo_labs/google/ranked_keywords/live"
        data = [{
            "target": target,
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit
        }]
        
        return await self.make_live_request(endpoint, data)

    async def get_keywords_from_site(self, target: str, location_code: int = 2840, language_code: str = "en", include_serp_info: bool = True, limit: int = 100) -> Dict:
        """
        Get keywords from a website (LIVE)
        
        Args:
            target: Domain to analyze (e.g., "competitor.com")
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            include_serp_info: Include SERP information
            limit: Maximum number of keywords to return
            
        Returns:
            Dict containing keywords found on the site
        """
        endpoint = "/dataforseo_labs/google/keywords_for_site/live"
        data = [{
            "target": target,
            "location_code": location_code,
            "language_code": language_code,
            "include_serp_info": include_serp_info,
            "limit": limit
        }]
        
        return await self.make_live_request(endpoint, data)

    async def get_search_volume(self, keywords: List[str], location_code: int = 2840, language_code: str = "en") -> Dict:
        """
        Get search volume for keywords (LIVE)
        Args:
            keywords: List of keywords to analyze
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            
        Returns:
            Dict containing search volume data for each keyword
        """
        endpoint = "/keywords_data/google_ads/search_volume/live"
        data = [{
            "keywords": keywords,
            "location_code": location_code,
            "language_code": language_code
        }]
        
        return await self.make_live_request(endpoint, data)

    async def get_keyword_suggestions(self, keyword: str, location_code: int = 2840, language_code: str = "en", include_seed_keyword: bool = True, include_serp_info: bool = True, limit: int = 100) -> Dict:
        """
        Get keyword suggestions for a main topic (LIVE)

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
        endpoint = "/dataforseo_labs/google/keyword_suggestions/live"
        data = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "include_seed_keyword": include_seed_keyword,
            "include_serp_info": include_serp_info,
            "limit": limit
        }]
        
        return await self.make_live_request(endpoint, data)
