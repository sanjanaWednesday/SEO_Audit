# services/dataforseo/onpage_apis.py
from typing import Dict, List, Any, Optional
from .base_client import BaseDataForSEOClient
import asyncio
import logging

logger = logging.getLogger(__name__)

class OnPageAPIs(BaseDataForSEOClient):
    """On-Page API wrapper for DataForSEO"""

    def __init__(self):
        super().__init__()

    async def start_crawling_task(self, target: str,max_crawl_pages=10,
                                  enable_javascript=True) -> str:
        """Create a new crawl task and return task ID"""
        body = [{
            "target": target,
            "max_crawl_pages": max_crawl_pages,
            "load_resources": True,
            "enable_javascript": enable_javascript,
        }]
        
        logger.info(f"Creating crawl task for target: {target}")
        response = await self._make_request('POST', "/on_page/task_post", body)
        
        # Extract task ID
        tasks = response.get("tasks", [])
        if not tasks or not tasks[0].get("id"):
            raise ValueError(f"Failed to create task: {response}")
        
        task_id = tasks[0]["id"]
        status_code = tasks[0].get("status_code")
        
        if status_code != 20100: 
            raise ValueError(f"Task creation failed with status {status_code}: {tasks[0].get('status_message')}")
        
        logger.info(f"Task created successfully: {task_id}")
        return task_id

    async def wait_for_task_completion(self, task_id: str, wait_time: int = 600, 
                                       check_interval: int = 30) -> bool:
        """
        Wait for task to complete with periodic status checks
        
        Args:
            task_id: The task ID to monitor
            wait_time: Total time to wait in seconds (default: 600 = 10 minutes)
            check_interval: How often to check status in seconds (default: 30)
        
        Returns:
            bool: True if task completed, False if timeout
        """
        logger.info(f"Waiting up to {wait_time}s for task {task_id} to complete (minimum 5-10 minutes for task creation)...")
        
        elapsed = 0
        checks = 0
        
        while elapsed < wait_time:
            await asyncio.sleep(check_interval)
            elapsed += check_interval
            checks += 1
            
            try:
                summary = await self.get_page_summary(task_id)
                
                # Check if we got valid data
                tasks = summary.get("tasks", [])
                if tasks and tasks[0].get("result"):
                    result = tasks[0]["result"][0]
                    crawl_status = result.get("crawl_progress", "")
                    crawl_status_lower = crawl_status.lower() if crawl_status else ""
                    
                    crawl_status_obj = result.get("crawl_status", {})
                    pages_crawled = crawl_status_obj.get("pages_crawled", 0) if crawl_status_obj else 0
                    
                    logger.info(f"Check {checks}: Status={crawl_status}, Pages={pages_crawled}")
                    
                    if crawl_status_lower == "finished" or crawl_status_lower == "completed":
                        logger.info(f"Task completed after {elapsed}s with {pages_crawled} pages")
                        return True
                    
                    if "error" in crawl_status_lower or "failed" in crawl_status_lower:
                        logger.error(f"Task failed with status: {crawl_status}")
                        return False
                        
            except Exception as e:
                logger.warning(f"Check {checks} error (continuing): {str(e)}")
        
        logger.warning(f"Task did not complete within {wait_time}s")
        return False

    async def get_page_summary(self, task_id: str) -> Dict:
        """Get summary of crawl results"""
        response = await self._make_request('GET', f"/on_page/summary/{task_id}")
        return response

    async def get_crawled_pages(self, task_id: str, limit=100, filters=None, 
                                order_by=None, offset=0) -> Dict:
        """
        Fetch pages data for a completed task
        
        Args:
            task_id: The completed task ID
            limit: Number of pages to return (default: 100)
            filters: Optional filters array
            order_by: Optional ordering array
            offset: Pagination offset
        """
        body = [{
            "id": task_id,
            "limit": limit,
            "offset": offset
        }]
        
        if filters:
            body[0]["filters"] = filters
        if order_by:
            body[0]["order_by"] = order_by
        
        logger.info(f"Fetching pages for task {task_id} (limit={limit}, offset={offset})")
        response = await self._make_request('POST', "/on_page/pages", body)
        
        return response

    async def get_technical_issues(self, task_id: str, limit: int = 100, offset: int = 0) -> Dict:
        """
        Get technical SEO issues (extracted from pages data).
        Note: DataForSEO doesn't have a separate /technical_issues endpoint.
        Technical issues are in the 'checks' field of each page in /on_page/pages response.
        """
        # Just return the pages data - technical issues are in the 'checks' field
        return await self.get_crawled_pages(task_id, limit=limit, offset=offset)

    async def run_full_diagnostic(self, target: str, max_crawl_pages: int = 10,
                                  wait_time: int = 600) -> Dict[str, Any]:
        """
        Complete workflow: Create task → Wait → Get summary → Get pages
        
        Args:
            target: Website domain (e.g., "example.com")
            max_crawl_pages: Maximum pages to crawl
            wait_time: Time to wait for completion in seconds (default: 600 = 10 minutes)
        
        Returns:
            Dict containing task_id, summary, pages, and status
        """
        result = {
            "task_id": None,
            "summary": None,
            "pages": None,
            "technical_issues": None,
            "status": "failed",
            "error": None
        }
        
        try:
            # Step 1: Create task
            logger.info(f"Step 1/4: Creating crawl task for {target}")
            task_id = await self.start_crawling_task(
                target=target,
                max_crawl_pages=max_crawl_pages
            )
            result["task_id"] = task_id
            
            # Step 2: Wait for completion
            logger.info(f"Step 2/4: Waiting for task completion ({wait_time}s)")
            completed = await self.wait_for_task_completion(task_id, wait_time)
            
            if not completed:
                result["error"] = "Task did not complete in time"
                return result
            
            # Step 3: Get summary
            logger.info("Step 3/4: Fetching summary")
            summary = await self.get_page_summary(task_id)
            result["summary"] = summary
            
            # Step 4: Get pages
            logger.info("Step 4/4: Fetching crawled pages")
            pages = await self.get_crawled_pages(task_id, limit=100)
            result["pages"] = pages
            
            # Optional: Get technical issues
            try:
                technical_issues = await self.get_technical_issues(task_id, limit=100)
                result["technical_issues"] = technical_issues
            except Exception as e:
                logger.warning(f"Could not fetch technical issues: {e}")
            
            result["status"] = "success"
            logger.info(f"✓ Full diagnostic completed for {target}")
            
        except Exception as e:
            logger.error(f"Diagnostic failed: {str(e)}")
            result["error"] = str(e)
        
        return result

    async def get_instant_page_analysis(self, url: str, enable_javascript: bool = True,
                                        support_javascript: bool = True, 
                                        custom_user_agent: str = None) -> Dict:
        """Get instant on-page analysis for a URL (no waiting required)"""
        body = [{
            "url": url,
            "enable_javascript": enable_javascript,
            "support_javascript": support_javascript
        }]
        
        if custom_user_agent:
            body[0]["custom_user_agent"] = custom_user_agent
        
        return await self._make_request('POST', "/on_page/instant_pages", body)


# Example usage:
"""
from services.dataforseo.onpage_apis import OnPageAPIs

async def main():
    api = OnPageAPIs()
    
    # Run full diagnostic (create → wait → get results)
    results = await api.run_full_diagnostic(
        target="example.com",
        max_crawl_pages=10,
        wait_time=300  # 5 minutes
    )
    
    if results["status"] == "success":
        print(f"Task ID: {results['task_id']}")
        print(f"Pages crawled: {len(results['pages'].get('tasks', [{}])[0].get('result', []))}")
        # Process results for Google Sheets
    else:
        print(f"Error: {results['error']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
"""