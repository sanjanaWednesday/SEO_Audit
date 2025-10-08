"""
OnPageCrawlerTool - Handles on-page crawling with DataForSEO
"""
from crewai.tools import BaseTool
from typing import Type, Dict, Optional
from pydantic import BaseModel, Field
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


class OnPageCrawlerInput(BaseModel):
    """Input schema for OnPageCrawlerTool"""
    action: str = Field(..., description="Action: start_crawl, check_status, get_results, get_summary")
    domain: str = Field(None, description="Domain to crawl")
    task_id: str = Field(None, description="Task ID for checking status/getting results")
    max_pages: int = Field(10, description="Maximum pages to crawl")


class OnPageCrawlerTool(BaseTool):
    name: str = "OnPage Crawler Tool"
    description: str = """
    Manages on-page technical SEO crawling. Actions:
    - start_crawl: Start crawling a domain
    - check_status: Check if crawl is complete
    - get_results: Get crawl results (pages data)
    - get_summary: Get crawl summary
    Returns task_id when starting, status when checking, full data when getting results.
    """
    args_schema: Type[BaseModel] = OnPageCrawlerInput
    
    def _run(self, action: str, domain: str = None, task_id: str = None, max_pages: int = 10) -> Dict:
        """
        Execute on-page crawl action (synchronous wrapper)
        
        Args:
            action: Action to perform
            domain: Domain to crawl
            task_id: Task ID for status/results
            max_pages: Max pages to crawl
            
        Returns:
            Action result dictionary
        """
        # Check if there's already a running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in a loop, run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._async_run(action, domain, task_id, max_pages)
                )
                return future.result()
        except RuntimeError:
            # No event loop running
            return asyncio.run(self._async_run(action, domain, task_id, max_pages))
    
    async def _async_run(self, action: str, domain: str = None, 
                        task_id: str = None, max_pages: int = 10) -> Dict:
        """Async implementation"""
        
        action_map = {
            'start_crawl': self._start_crawl,
            'check_status': self._check_status,
            'get_results': self._get_results,
            'get_summary': self._get_summary
        }
        
        if action not in action_map:
            return {"error": f"Unknown action: {action}", "success": False}
        
        if action == 'start_crawl':
            return await self._start_crawl(domain, max_pages)
        else:
            return await action_map[action](task_id)
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[list] = None) -> Dict:
        """Make authenticated request"""
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
                            return {"error": f"HTTP {response.status}", "success": False}
                        
                        if result.get('tasks') and result['tasks'][0].get('status_code') not in [20000, 20100]:
                            status_code = result['tasks'][0].get('status_code')
                            status_message = result['tasks'][0].get('status_message', 'Unknown error')
                            return {"error": f"DataForSEO {status_code}: {status_message}", "success": False}
                        
                        result['success'] = True
                        return result
                else:  # GET
                    async with session.get(url, headers=headers) as response:
                        result = await response.json()
                        if response.status != 200:
                            return {"error": f"HTTP {response.status}", "success": False}
                        
                        if result.get('tasks') and result['tasks'][0].get('status_code') not in [20000, 20100]:
                            status_code = result['tasks'][0].get('status_code')
                            status_message = result['tasks'][0].get('status_message', 'Unknown error')
                            return {"error": f"DataForSEO {status_code}: {status_message}", "success": False}
                        
                        result['success'] = True
                        return result
            except Exception as e:
                return {"error": str(e), "success": False}
    
    async def _start_crawl(self, domain: str, max_pages: int = 10) -> Dict:
        """Start on-page crawl task"""
        endpoint = "/on_page/task_post"
        data = [{
            "target": domain,
            "max_crawl_pages": max_pages,
            "load_resources": True,
            "enable_javascript": True,
        }]
        
        result = await self._make_request('POST', endpoint, data)
        
        if result.get('success') and result.get('tasks'):
            task_id = result['tasks'][0].get('id')
            return {
                "success": True,
                "task_id": task_id,
                "domain": domain,
                "max_pages": max_pages,
                "message": f"Crawl started for {domain}"
            }
        
        return result
    
    async def _check_status(self, task_id: str) -> Dict:
        """Check crawl status"""
        if not task_id:
            return {"error": "task_id required", "success": False}
        
        summary = await self._get_summary(task_id)
        
        if not summary.get('success'):
            return summary
        
        tasks = summary.get('tasks', [])
        if tasks and tasks[0].get('result'):
            result = tasks[0]['result'][0]
            crawl_status = result.get('crawl_progress', '').lower()
            crawl_status_obj = result.get('crawl_status', {})
            pages_crawled = crawl_status_obj.get('pages_crawled', 0) if crawl_status_obj else 0
            
            is_complete = crawl_status in ['finished', 'completed']
            is_failed = 'error' in crawl_status or 'failed' in crawl_status
            
            return {
                "success": True,
                "task_id": task_id,
                "status": crawl_status,
                "pages_crawled": pages_crawled,
                "is_complete": is_complete,
                "is_failed": is_failed,
                "is_running": not is_complete and not is_failed
            }
        
        return {"error": "No status data", "success": False}
    
    async def _get_summary(self, task_id: str) -> Dict:
        """Get crawl summary"""
        if not task_id:
            return {"error": "task_id required", "success": False}
        
        endpoint = f"/on_page/summary/{task_id}"
        return await self._make_request('GET', endpoint)
    
    async def _get_results(self, task_id: str, limit: int = 50) -> Dict:
        """Get crawl results (pages data)"""
        if not task_id:
            return {"error": "task_id required", "success": False}
        
        endpoint = "/on_page/pages"
        data = [{
            "id": task_id,
            "limit": limit,
            "offset": 0
        }]
        
        result = await self._make_request('POST', endpoint, data)
        
        if result.get('success'):
            result['task_id'] = task_id
        
        return result

