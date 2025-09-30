"""
Backlink Analysis APIs
Handles backlink summary and detailed backlink analysis
"""
from typing import Dict, List, Optional
from .base_client import BaseDataForSEOClient

class BacklinkAPIs(BaseDataForSEOClient):
    """APIs for backlink analysis and research"""
    
    async def get_backlinks_summary(self, target: str, internal_list_limit: int = 10, backlinks_status_type: str = "live") -> Dict:
        """
        Get backlinks summary for a website
        
        Args:
            target: Domain to analyze (e.g., "example.com")
            internal_list_limit: Limit for internal links analysis
            backlinks_status_type: Type of backlinks to analyze ("live", "lost", "all")
            
        Returns:
            Dict containing backlinks summary data
        """
        endpoint = "/backlinks/summary/live"
        data = [{
            "target": target,
            "internal_list_limit": internal_list_limit,
            "backlinks_status_type": backlinks_status_type
        }]
        
        return await self.make_live_request(endpoint, data)

    async def get_backlinks_list(self, target: str, limit: int = 100) -> Dict:
        """
        Get detailed backlinks list for a website
        
        Args:
            target: Domain to analyze (e.g., "competitor.com")
            limit: Maximum number of backlinks to return
            
        Returns:
            Dict containing detailed backlinks data
        """
        endpoint = "/backlinks/backlinks/live"
        data = [{
            "target": target,
            "mode": "as_is",
            "filters": ["dofollow", "=", True],
            "order_by": ["rank", "desc"],
            "limit": limit
        }]
        
        return await self.make_live_request(endpoint, data)
