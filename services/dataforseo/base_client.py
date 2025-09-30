"""
Base DataForSEO API Client
Handles authentication, task creation, and result retrieval
"""
import asyncio
import aiohttp
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseDataForSEOClient:
    """Base client for DataForSEO API operations"""
    
    def __init__(self):
        self.base_url = os.getenv('DATAFORSEO_BASE_URL', 'https://api.dataforseo.com/v3')
        self.username = os.getenv('DATAFORSEO_USERNAME')
        self.password = os.getenv('DATAFORSEO_PASSWORD')
        self.auth = aiohttp.BasicAuth(self.username, self.password) if self.username and self.password else None
        
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to DataForSEO API"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        async with aiohttp.ClientSession(auth=self.auth) as session:
            try:
                if method.upper() == 'POST':
                    async with session.post(url, json=data, headers=headers) as response:
                        result = await response.json()
                        if response.status != 200:
                            logger.error(f"API Error {response.status}: {result}")
                        return result
                else:
                    async with session.get(url, headers=headers) as response:
                        result = await response.json()
                        if response.status != 200:
                            logger.error(f"API Error {response.status}: {result}")
                        return result
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return {"error": str(e)}
    
    async def create_task(self, endpoint: str, data: List[Dict]) -> Optional[str]:
        """Create a task and return task ID"""
        result = await self._make_request('POST', endpoint, data)
        if result.get('tasks') and result['tasks'][0].get('id'):
            return result['tasks'][0]['id']
        logger.error(f"Failed to create task: {result}")
        return None
    
    async def get_task_result(self, endpoint: str, task_id: str, max_attempts: int = 10, delay: int = 30) -> Dict:
        """Get task result with retry logic"""
        for attempt in range(max_attempts):
            result = await self._make_request('GET', f"{endpoint}/{task_id}")
            
            if result.get('tasks') and result['tasks'][0].get('status_code') == 20000:
                return result
            
            if attempt < max_attempts - 1:
                logger.info(f"Task {task_id} not ready, waiting {delay}s (attempt {attempt + 1}/{max_attempts})")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Task {task_id} failed after {max_attempts} attempts")
                return result
        
        return result
    
    async def make_live_request(self, endpoint: str, data: List[Dict]) -> Dict:
        """Make a live API request (immediate response, no task creation)"""
        return await self._make_request('POST', endpoint, data)