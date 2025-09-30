"""
Domain Analysis APIs
Handles domain metrics, competitors, and domain intersection analysis
"""
from typing import Dict, List, Optional
from .base_client import BaseDataForSEOClient

class DomainAPIs(BaseDataForSEOClient):
    """APIs for domain analysis and competitor research"""
    
    async def get_domain_metrics(self, target: str, location_code: int = 2840, language_code: str = "en") -> Dict:
        """
        Get domain metrics for a website
        
        Args:
            target: Domain to analyze (e.g., "example.com")
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            
        Returns:
            Dict containing domain metrics data
        """
        endpoint = "/dataforseo_labs/google/domain_metrics/task_post"
        data = [{
            "target": target,
            "location_code": location_code,
            "language_code": language_code
        }]
        
        task_id = await self.create_task(endpoint, data)
        if not task_id:
            return {"error": "Failed to create domain metrics task"}
        
        return await self.get_task_result("/dataforseo_labs/google/domain_metrics/task_get", task_id)

    async def get_competitors(self, target: str, location_code: int = 2840, language_code: str = "en", limit: int = 10) -> Dict:
        """
        Get competitors for a website based on keyword overlap
        
        Args:
            target: Domain to find competitors for
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            limit: Maximum number of competitors to return
            
        Returns:
            Dict containing competitor domains and overlap data
        """
        endpoint = "/dataforseo_labs/google/competitors_domain/live"
        data = [{
            "target": target,
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit
        }]
        
        return await self.make_live_request(endpoint, data)

    async def get_domain_intersection(self, targets: Dict[str, str], location_code: int = 2840, language_code: str = "en", intersections: str = "2", limit: int = 100) -> Dict:
        """
        Get domain intersection for content gap analysis
        
        Args:
            targets: Dict mapping target IDs to domains (e.g., {"1": "mysite.com", "2": "competitor.com"})
            location_code: Location code (2840 = United States)
            language_code: Language code ("en" = English)
            intersections: Which domains to include ("1", "2", "1,2", "1,2,3")
            limit: Maximum number of keywords to return
            
        Returns:
            Dict containing intersection analysis data
        """
        endpoint = "/dataforseo_labs/google/domain_intersection/live"
        data = [{
            "targets": targets,
            "location_code": location_code,
            "language_code": language_code,
            "intersections": intersections,
            "limit": limit
        }]
        
        task_id = await self.create_task(endpoint, data)
        if not task_id:
            return {"error": "Failed to create domain intersection task"}
        
        return await self.make_live_request(endpoint, data)
