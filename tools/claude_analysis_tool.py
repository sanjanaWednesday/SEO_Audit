"""
ClaudeAnalysisTool - AI-powered code fix generation using Claude
"""
from crewai.tools import BaseTool
from typing import Type, Dict, List
from pydantic import BaseModel, Field
import sys
import os

# Add parent directory to path to import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.claude_service import ClaudeService
from services.onpage_code_fixer import OnPageCodeFixer
import json
import asyncio


class ClaudeAnalysisInput(BaseModel):
    """Input schema for ClaudeAnalysisTool"""
    onpage_data: str = Field(..., description="JSON string of on-page crawl data")
    domain: str = Field(..., description="Domain being analyzed")


class ClaudeAnalysisTool(BaseTool):
    name: str = "Claude AI Analysis Tool"
    description: str = """
    Uses Claude AI to analyze technical SEO issues and generate platform-specific code fixes.
    Takes on-page crawl data and returns AI-generated fixes for each issue.
    Detects platform (WordPress, Shopify, etc.) and generates appropriate solutions.
    """
    args_schema: Type[BaseModel] = ClaudeAnalysisInput
    
    def _run(self, onpage_data: str, domain: str) -> Dict:
        """
        Analyze technical issues with Claude AI (synchronous wrapper)
        
        Args:
            onpage_data: JSON string of on-page data
            domain: Domain being analyzed
            
        Returns:
            Analysis results with AI-generated fixes
        """
        # Check if there's already a running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in a loop, run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._async_run(onpage_data, domain)
                )
                return future.result()
        except RuntimeError:
            # No event loop running
            return asyncio.run(self._async_run(onpage_data, domain))
    
    async def _async_run(self, onpage_data: str, domain: str) -> Dict:
        """Async implementation of Claude analysis"""
        
        try:
            # Parse on-page data
            if isinstance(onpage_data, str):
                data = json.loads(onpage_data)
            else:
                data = onpage_data
            
            # Initialize Claude service and code fixer
            claude_service = ClaudeService()
            code_fixer = OnPageCodeFixer(claude_service)
            
            # Process data - extract issues from pages
            pages_data = self._extract_pages_data(data)
            
            if not pages_data:
                return {
                    "success": False,
                    "error": "No pages data found in on-page results"
                }
            
            # Build issues structure that OnPageCodeFixer expects
            code_fixer.json_results = {"onpage_data": {"pages": pages_data}}
            code_fixer.issues_by_url = {}
            code_fixer.csv_issues = []
            
            # Extract issues from pages
            items = pages_data.get('tasks', [{}])[0].get('result', [{}])[0].get('items', [])
            
            for item in items:
                if item.get('resource_type') != 'html':
                    continue
                
                url = item.get('url', '')
                checks = item.get('checks', {})
                
                # Extract issues for this URL
                url_issues = []
                
                issue_checks = [
                    ('is_broken', 'Broken Page', 'Critical'),
                    ('is_4xx_code', '4XX Error', 'Critical'),
                    ('is_5xx_code', '5XX Error', 'Critical'),
                    ('no_h1_tag', 'Missing H1', 'Critical'),
                    ('no_title', 'Missing Title', 'Critical'),
                    ('no_description', 'Missing Meta Description', 'High'),
                    ('duplicate_title', 'Duplicate Title', 'High'),
                    ('duplicate_description', 'Duplicate Description', 'High'),
                    ('broken_links', 'Broken Links', 'High'),
                    ('high_loading_time', 'Slow Page Load', 'High'),
                    ('is_orphan_page', 'Orphan Page', 'High'),
                    ('large_page_size', 'Large Page Size', 'Medium'),
                    ('low_content_rate', 'Low Content Rate', 'Medium'),
                ]
                
                for check_key, issue_name, severity in issue_checks:
                    if checks.get(check_key, False):
                        issue = {
                            'Issue Type': issue_name,
                            'Severity': severity,
                            'Page URL': url,
                            'Status Code': item.get('status_code', ''),
                        }
                        url_issues.append(issue)
                        code_fixer.csv_issues.append(issue)
                
                if url_issues:
                    code_fixer.issues_by_url[url] = {
                        'page_data': item,
                        'issues': url_issues
                    }
            
            # Detect platform
            platform = code_fixer.detect_platform()
            
            # Check if there are issues
            if not code_fixer.issues_by_url:
                return {
                    "success": True,
                    "message": "No technical issues found",
                    "platform": platform,
                    "urls_analyzed": 0,
                    "total_issues": 0,
                    "fixes": []
                }
            
            # Analyze with Claude
            analysis_results = await code_fixer.analyze_all_urls()
            
            return {
                "success": True,
                "platform": platform,
                "domain": domain,
                "urls_analyzed": len(code_fixer.issues_by_url),
                "total_issues": len(code_fixer.csv_issues),
                "analysis": analysis_results,
                "message": f"Analyzed {len(code_fixer.issues_by_url)} URLs with {len(code_fixer.csv_issues)} issues"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Claude analysis failed: {str(e)}"
            }
    
    def _extract_pages_data(self, data: Dict) -> Dict:
        """Extract pages data from on-page results"""
        
        # Check different possible structures
        if 'pages' in data:
            return data['pages']
        
        if 'onpage_data' in data and 'pages' in data['onpage_data']:
            return data['onpage_data']['pages']
        
        # If data itself is the pages structure
        if 'tasks' in data:
            return data
        
        return {}

