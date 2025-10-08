"""
SEO Audit Orchestrator
Unified service that handles the complete SEO audit workflow
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from .dataforseo_client import DataForSEOClient
from .mongo_service import MongoService
from models.execution_logs import LogStatus

logger = logging.getLogger(__name__)

class SEOAuditOrchestrator:
    def __init__(self, mongo_service: MongoService = None, execution_id: str = None):
        self.dataforseo = DataForSEOClient()
        self.mongo_service = mongo_service
        self.execution_id = execution_id
        self.results = {}
        
    async def run_complete_audit(self, target_domain: str, main_topic: str = None) -> Dict:
        """
        Run the complete SEO audit workflow as defined in day4.txt
        
        Args:
            target_domain: The website to audit (e.g., "example.com")
            main_topic: Main topic keyword for suggestions (optional)
        
        Returns:
            Dict containing all audit results
        """
        logger.info(f"Starting SEO audit for {target_domain}")
        
        try:
            # Phase 1: Establish Baseline (YOUR SITE)
            logger.info("Phase 1: Establishing baseline for your site")
            baseline_results = await self._establish_baseline(target_domain)
            self.results['baseline'] = baseline_results
            
            # Phase 2: Discover Competition
            logger.info("Phase 2: Discovering competitors")
            competitors = await self._discover_competitors(target_domain)
            self.results['competitors'] = competitors
            
            # Phase 3: Analyze Competitors (top 3)
            logger.info("Phase 3: Analyzing top 3 competitors")
            competitor_analysis = await self._analyze_competitors(competitors[:3])
            self.results['competitor_analysis'] = competitor_analysis
            
            # Phase 4: Find Opportunities
            logger.info("Phase 4: Finding content opportunities")
            opportunities = await self._find_opportunities(target_domain, competitor_analysis)
            self.results['opportunities'] = opportunities
            
            # Phase 5: Prioritize Keywords
            logger.info("Phase 5: Prioritizing keywords")
            prioritized_keywords = await self._prioritize_keywords(opportunities, main_topic)
            self.results['prioritized_keywords'] = prioritized_keywords
            
            # Phase 6: SERP Analysis
            logger.info("Phase 6: Analyzing SERP for top opportunities")
            serp_analysis = await self._analyze_serp(prioritized_keywords[:10])
            self.results['serp_analysis'] = serp_analysis
            
            # Phase 7: Content Quality Check
            logger.info("Phase 7: Content quality check")
            content_analysis = await self._content_quality_check(target_domain)
            self.results['content_analysis'] = content_analysis
            
            # Phase 8: On-Page Analysis
            logger.info("Phase 8: On-page analysis")
            onpage_analysis = await self._onpage_analysis(target_domain)
            self.results['onpage_analysis'] = onpage_analysis
            
            # Save results
            await self._save_results(target_domain)
            
            logger.info(f"SEO audit completed for {target_domain}")
            return self.results
            
        except Exception as e:
            logger.error(f"SEO audit failed: {e}")
            return {"error": str(e)}
    
    async def _establish_baseline(self, target_domain: str) -> Dict:
        """Phase 1: Get baseline metrics for your site"""
        start_time = datetime.now()
        results = {}
        
        try:
            # 1. Domain Metrics
            logger.info("Getting domain metrics...")
            results['domain_metrics'] = await self.dataforseo.get_domain_metrics(target_domain)
            
            # 2. Ranked Keywords
            logger.info("Getting ranked keywords...")
            results['ranked_keywords'] = await self.dataforseo.get_ranked_keywords(target_domain)
            
            # 3. Backlinks Summary
            logger.info("Getting backlinks summary...")
            results['backlinks_summary'] = await self.dataforseo.get_backlinks_summary(target_domain)
            
            # Log success
            if self.mongo_service and self.execution_id:
                execution_time = int((datetime.now() - start_time).total_seconds())
                self.mongo_service.log_execution_step(
                    self.execution_id,
                    "establish_baseline",
                    LogStatus.SUCCESS,
                    execution_time
                )
            
            return results
            
        except Exception as e:
            # Log failure
            if self.mongo_service and self.execution_id:
                execution_time = int((datetime.now() - start_time).total_seconds())
                self.mongo_service.log_execution_step(
                    self.execution_id,
                    "establish_baseline",
                    LogStatus.FAILED,
                    execution_time,
                    error_message=str(e)
                )
            raise
    
    async def _discover_competitors(self, target_domain: str) -> List[str]:
        """Phase 2: Discover competitors"""
        start_time = datetime.now()
        
        try:
            logger.info("Finding competitors...")
            competitors_result = await self.dataforseo.get_competitors(target_domain)
            
            competitors = []
            if competitors_result.get('tasks') and competitors_result['tasks'][0].get('result'):
                for item in competitors_result['tasks'][0]['result']:
                    if item.get('domain'):
                        competitors.append(item['domain'])
            
            # Store top 3 competitors in MongoDB
            top_3_competitors = competitors[:3]
            logger.info(f"Found {len(competitors)} competitors, storing top 3: {top_3_competitors}")
            
            if self.mongo_service and self.execution_id:
                self.mongo_service.update_workflow_competitors(self.execution_id, top_3_competitors)
                
                execution_time = int((datetime.now() - start_time).total_seconds())
                self.mongo_service.log_execution_step(
                    self.execution_id,
                    "discover_competitors",
                    LogStatus.SUCCESS,
                    execution_time
                )
            
            return competitors
            
        except Exception as e:
            if self.mongo_service and self.execution_id:
                execution_time = int((datetime.now() - start_time).total_seconds())
                self.mongo_service.log_execution_step(
                    self.execution_id,
                    "discover_competitors",
                    LogStatus.FAILED,
                    execution_time,
                    error_message=str(e)
                )
            raise
    
    async def _analyze_competitors(self, competitors: List[str]) -> Dict:
        """Phase 3: Analyze top competitors"""
        start_time = datetime.now()
        results = {}
        
        try:
            for i, competitor in enumerate(competitors, 1):
                logger.info(f"Analyzing competitor {i}: {competitor}")
                competitor_data = {}
                
                # Domain metrics
                competitor_data['domain_metrics'] = await self.dataforseo.get_domain_metrics(competitor)
                
                # Ranked keywords
                competitor_data['ranked_keywords'] = await self.dataforseo.get_ranked_keywords(competitor)
                
                # Backlinks summary
                competitor_data['backlinks_summary'] = await self.dataforseo.get_backlinks_summary(competitor)
                
                # Backlinks list
                competitor_data['backlinks_list'] = await self.dataforseo.get_backlinks_list(competitor)
                
                results[f'competitor_{i}'] = {
                    'domain': competitor,
                    'data': competitor_data
                }
                
                # Store competitor analysis in MongoDB
                if self.mongo_service and self.execution_id:
                    self.mongo_service.store_competitor_analysis(
                        self.execution_id,
                        competitor,
                        competitor_data
                    )
            
            # Log success
            if self.mongo_service and self.execution_id:
                execution_time = int((datetime.now() - start_time).total_seconds())
                self.mongo_service.log_execution_step(
                    self.execution_id,
                    "analyze_competitors",
                    LogStatus.SUCCESS,
                    execution_time
                )
            
            return results
            
        except Exception as e:
            if self.mongo_service and self.execution_id:
                execution_time = int((datetime.now() - start_time).total_seconds())
                self.mongo_service.log_execution_step(
                    self.execution_id,
                    "analyze_competitors",
                    LogStatus.FAILED,
                    execution_time,
                    error_message=str(e)
                )
            raise
    
    async def _find_opportunities(self, target_domain: str, competitor_analysis: Dict) -> Dict:
        """Phase 4: Find content opportunities"""
        opportunities = {}
        
        # Content gap analysis for each competitor
        for comp_key, comp_data in competitor_analysis.items():
            competitor_domain = comp_data['domain']
            logger.info(f"Finding content gaps vs {competitor_domain}")
            
            # Keyword intersection (keywords they rank for but you don't)
            intersection_result = await self.dataforseo.get_domain_intersection(
                targets={"1": target_domain, "2": competitor_domain},
                intersections="2"  # Keywords only competitor ranks for
            )
            
            opportunities[f'gap_vs_{comp_key}'] = {
                'competitor': competitor_domain,
                'intersection': intersection_result
            }
        
        # Keywords from competitor sites
        for comp_key, comp_data in competitor_analysis.items():
            competitor_domain = comp_data['domain']
            logger.info(f"Getting keywords from {competitor_domain}")
            
            keywords_from_site = await self.dataforseo.get_keywords_from_site(competitor_domain)
            opportunities[f'keywords_from_{comp_key}'] = {
                'competitor': competitor_domain,
                'keywords': keywords_from_site
            }
        
        return opportunities
    
    async def _prioritize_keywords(self, opportunities: Dict, main_topic: str = None) -> Dict:
        """Phase 5: Prioritize keywords"""
        # Collect all opportunity keywords
        all_keywords = []
        
        for opp_key, opp_data in opportunities.items():
            if 'intersection' in opp_data and opp_data['intersection'].get('tasks'):
                task_result = opp_data['intersection']['tasks'][0].get('result', [])
                for item in task_result:
                    if item.get('keyword_data') and item['keyword_data'].get('keyword'):
                        all_keywords.append(item['keyword_data']['keyword'])
        
        # Get search volume for opportunity keywords
        if all_keywords:
            logger.info(f"Getting search volume for {len(all_keywords)} opportunity keywords")
            search_volume = await self.dataforseo.get_search_volume(all_keywords[:50])  # Limit to 50
        else:
            search_volume = {}
        
        # Get keyword suggestions for main topic
        keyword_suggestions = {}
        if main_topic:
            logger.info(f"Getting keyword suggestions for: {main_topic}")
            keyword_suggestions = await self.dataforseo.get_keyword_suggestions(main_topic)
        
        return {
            'opportunity_keywords': all_keywords,
            'search_volume': search_volume,
            'keyword_suggestions': keyword_suggestions
        }
    
    async def _analyze_serp(self, top_keywords: List[str]) -> Dict:
        """Phase 6: SERP analysis for top keywords"""
        serp_results = {}
        
        for i, keyword in enumerate(top_keywords[:10], 1):  # Limit to top 10
            logger.info(f"Analyzing SERP for keyword {i}: {keyword}")
            serp_result = await self.dataforseo.get_serp_analysis(keyword)
            serp_results[f'keyword_{i}'] = {
                'keyword': keyword,
                'serp_data': serp_result
            }
        
        return serp_results
    
    async def _content_quality_check(self, target_domain: str) -> Dict:
        """Phase 7: Content quality check"""
        # This would typically require getting top pages from ranked keywords
        # For now, we'll do a basic content analysis of the homepage
        logger.info("Performing content quality check...")
        
        homepage_url = f"https://{target_domain}"
        content_analysis = await self.dataforseo.get_content_analysis(homepage_url)
        
        return {
            'homepage_analysis': content_analysis
        }
    
    async def _onpage_analysis(self, target_domain: str) -> Dict:
        """Phase 8: On-page analysis"""
        start_time = datetime.now()
        
        try:
            logger.info("Running on-page analysis...")
            
            # Start crawling task
            task_id = await self.dataforseo.onpage.start_crawling_task(
                target=target_domain,
                start_url=f"https://{target_domain}",
                max_crawl_pages=10,
                force_sitewide_checks=True,
                max_crawl_depth=2,
                store_raw_html=True,
                enable_javascript=True,
                support_javascript=True
            )
            
            if not task_id:
                raise Exception("Failed to create on-page crawling task")
            
            # Wait for task completion
            await self._wait_for_onpage_task_completion(task_id)
            
            # Get pages data
            pages_data = await self.dataforseo.onpage.get_crawled_pages(
                task_id=task_id,
                limit=10,
                filters=[
                    ["resource_type", "=", "html"],
                    "and",
                    ["meta.scripts_count", ">", 40]
                ],
                order_by=["meta.content.plain_text_word_count,desc"]
            )
            
            # Log success
            if self.mongo_service and self.execution_id:
                execution_time = int((datetime.now() - start_time).total_seconds())
                self.mongo_service.log_execution_step(
                    self.execution_id,
                    "onpage_analysis",
                    LogStatus.SUCCESS,
                    execution_time
                )
            
            return {
                'task_id': task_id,
                'pages_data': pages_data
            }
            
        except Exception as e:
            # Log failure
            if self.mongo_service and self.execution_id:
                execution_time = int((datetime.now() - start_time).total_seconds())
                self.mongo_service.log_execution_step(
                    self.execution_id,
                    "onpage_analysis",
                    LogStatus.FAILED,
                    execution_time,
                    error_message=str(e)
                )
            raise
    
    async def _wait_for_onpage_task_completion(self, task_id: str):
        """Wait for on-page task completion"""
        max_attempts = 30
        delay = 60
        
        for attempt in range(max_attempts):
            try:
                result = await self.dataforseo.onpage.get_page_summary(task_id)
                
                if result.get('tasks') and result['tasks'][0].get('status_code') == 20000:
                    logger.info("On-page task completed successfully")
                    return
                
                if attempt < max_attempts - 1:
                    logger.info(f"On-page task {task_id} not ready, waiting {delay}s (attempt {attempt + 1}/{max_attempts})")
                    await asyncio.sleep(delay)
                else:
                    raise Exception(f"On-page task {task_id} failed after {max_attempts} attempts")
                    
            except Exception as e:
                logger.error(f"Error checking on-page task status: {e}")
                if attempt == max_attempts - 1:
                    raise
                await asyncio.sleep(delay)
    
    async def _save_results(self, target_domain: str) -> str:
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"seo_audit_{target_domain.replace('.', '_')}_{timestamp}.json"
        filepath = os.path.join("results", filename)
        
        # Ensure results directory exists
        os.makedirs("results", exist_ok=True)
        
        # Add metadata
        self.results['metadata'] = {
            'target_domain': target_domain,
            'timestamp': timestamp,
            'audit_date': datetime.now().isoformat()
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {filepath}")
        return filepath
