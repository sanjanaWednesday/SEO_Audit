# services/dataforseo/base_client.py
import aiohttp
import os
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class BaseDataForSEOClient:
    """Base client for DataForSEO API operations"""

    def __init__(self):
        self.base_url = os.getenv('DATAFORSEO_BASE_URL', 'https://api.dataforseo.com/v3')
        self.username = os.getenv('DATAFORSEO_USERNAME')
        self.password = os.getenv('DATAFORSEO_PASSWORD')
        self.auth = aiohttp.BasicAuth(self.username, self.password) if self.username and self.password else None

    async def _make_request(self, method: str, endpoint: str, data: Optional[Any] = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

        if not self.username or not self.password:
            logger.error("DataForSEO credentials missing in environment variables.")
            return {"error": "Authentication credentials not found"}

        async with aiohttp.ClientSession(auth=self.auth) as session:
            try:
                if method.upper() == "POST":
                    async with session.post(url, json=data, headers=headers) as resp:
                        if 'application/json' in resp.headers.get('content-type', ''):
                            result = await resp.json()
                        else:
                            text = await resp.text()
                            return {"error": f"Non-JSON response: {text}"}
                        if resp.status != 200:
                            logger.error(f"API Error {resp.status}: {result}")
                        return result
                else:
                    async with session.get(url, headers=headers) as resp:
                        if 'application/json' in resp.headers.get('content-type', ''):
                            result = await resp.json()
                        else:
                            text = await resp.text()
                            return {"error": f"Non-JSON response: {text}"}
                        if resp.status != 200:
                            logger.error(f"API Error {resp.status}: {result}")
                        return result
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return {"error": str(e)}

    async def make_live_request(self, endpoint: str, data: List[Dict]) -> Dict:
        """For instant analysis without task creation"""
        return await self._make_request('POST', endpoint, data)
