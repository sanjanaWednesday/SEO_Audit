"""
CrewAI SEO Audit Orchestrator
Main crew that runs the complete SEO audit workflow
"""
from crewai import Crew, Process
from agents import create_all_agents
from tasks import create_load_config_task, create_dynamic_task
from datetime import datetime
from pathlib import Path
import json
import time
import asyncio
import os

# Import all tools
from tools.config_reader_tool import ConfigReaderTool
from tools.dataforseo_tool import DataForSEOTool
from tools.onpage_crawler_tool import OnPageCrawlerTool
from tools.claude_analysis_tool import ClaudeAnalysisTool
from tools.csv_generator_tool import CSVGeneratorTool


class SEOAuditCrew:
    """Main SEO Audit Crew orchestrator"""
    
    def __init__(self, config_path="config.yaml", verbose=True):
        self.config_path = config_path
        self.verbose = verbose
        self.agents = create_all_agents()  # Keep agents available for future use
        self.results = {}
        self.output_dir = None
        
    def run(self):
        """Execute the complete SEO audit workflow (fully synchronous)"""
        print("🚀 " + "="*70)
        print("   CREWAI SEO AUDIT SYSTEM")
        print("="*70)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        start_time = time.time()
        
        try:
            # Task 1: Load Configuration (directly using tool, not agent)
            print("\n📋 TASK 1: LOADING CONFIGURATION")
            print("-" * 70)
            
            # Use ConfigReaderTool directly for structured data
            config_tool = ConfigReaderTool()
            config_data = config_tool._run(config_path=self.config_path)
            
            domain = config_data.get('website', '')
            max_pages = config_data.get('max_crawl_pages', 10)
            
            # Initialize all_results structure
            all_results = {
                'domain': domain,
                'audit_date': datetime.now().isoformat(),
                'config': config_data,
                'phases': {},
                'onpage_data': {},
                'claude_analysis': None
            }
            
            if not config_data.get('success'):
                print(f"❌ Configuration loading failed: {config_data.get('error')}")
                return None
            
            self.results['config'] = config_data
            
            print(f"✅ Configuration loaded successfully")
            print(f"   🌐 Website: {config_data.get('website')}")
            print(f"   🏢 Competitors: {len(config_data.get('competitors', []))} configured")
            print(f"   🔑 Keywords: {len(config_data.get('keywords', []))} configured")
            
            # Setup output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain_safe = config_data['website'].replace('.', '_')
            self.output_dir = Path(config_data.get('output_dir', 'output')) / f"{domain_safe}_{timestamp}"
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"   📁 Output Directory: {self.output_dir}")
            
            # Task 2: Baseline Analysis (use tool directly)
            print("\n📊 TASK 2: BASELINE ANALYSIS")
            print("-" * 70)
            
            dataforseo_tool = DataForSEOTool()
            
            print(f"Getting domain metrics for {domain}...")
            domain_metrics = dataforseo_tool._run(action='domain_metrics', target=domain)
            all_results['phases']['domain_metrics'] = domain_metrics
            time.sleep(2)
            
            print(f"Getting ranked keywords for {domain}...")
            ranked_keywords = dataforseo_tool._run(action='ranked_keywords', target=domain, limit=15)
            all_results['phases']['ranked_keywords'] = ranked_keywords
            time.sleep(2)
            
            baseline_data = {
                'domain_metrics': domain_metrics,
                'ranked_keywords': ranked_keywords
            }
            self.results['baseline'] = baseline_data
            print("✅ Baseline analysis complete")
            
            # Task 3: Competitor Discovery (config first!)
            print("\n🏢 TASK 3: COMPETITOR DISCOVERY")
            print("-" * 70)
            
            competitor_domains = []
            
            if config_data.get('competitors'):
                # Use config competitors - NO API CALL
                competitor_domains = config_data['competitors'][:3]
                print(f"✅ Using {len(competitor_domains)} competitors from config:")
                for comp in competitor_domains:
                    print(f"   - {comp}")
                all_results['phases']['competitors'] = {'source': 'config', 'domains': competitor_domains}
            else:
                # Call API to discover
                print("No config competitors, discovering via API...")
                competitors_api = dataforseo_tool._run(action='competitors', target=domain, limit=10)
                all_results['phases']['competitors'] = competitors_api
                
                if competitors_api.get('success'):
                    items = competitors_api.get('tasks', [{}])[0].get('result', [{}])[0].get('items', [])
                    for item in items[:3]:
                        if item.get('domain'):
                            competitor_domains.append(item['domain'])
                            print(f"   - {item['domain']}")
                
                time.sleep(2)
            
            competitor_list = {'competitors': competitor_domains}
            self.results['competitor_discovery'] = competitor_list
            print(f"✅ Found {len(competitor_domains)} competitors")
            
            # Task 4: Competitor Analysis (use tool directly)
            print("\n🔍 TASK 4: COMPETITOR DEEP ANALYSIS")
            print("-" * 70)
            
            competitor_analysis = {}
            for i, competitor in enumerate(competitor_domains, 1):
                print(f"Analyzing competitor {i}: {competitor}")
                
                comp_data = {}
                comp_metrics = dataforseo_tool._run(action='domain_metrics', target=competitor)
                comp_data['domain_metrics'] = comp_metrics
                time.sleep(2)
                
                comp_keywords = dataforseo_tool._run(action='ranked_keywords', target=competitor, limit=15)
                comp_data['ranked_keywords'] = comp_keywords
                time.sleep(2)
                
                competitor_analysis[f'competitor_{i}'] = {
                    'domain': competitor,
                    'data': comp_data
                }
            
            all_results['phases']['competitor_analysis'] = competitor_analysis
            competitor_data = competitor_analysis
            self.results['competitor_analysis'] = competitor_analysis
            print(f"✅ Analyzed {len(competitor_domains)} competitors")
            
            # Task 5: Keyword Gap Analysis (use tool directly)
            print("\n🎯 TASK 5: KEYWORD GAP ANALYSIS")
            print("-" * 70)
            
            opportunities = {}
            all_opportunity_keywords = set()
            
            # Add config keywords first (priority)
            if config_data.get('keywords'):
                print(f"Adding {len(config_data['keywords'])} keywords from config (priority)")
                all_opportunity_keywords.update(config_data['keywords'])
            
            # Find gaps vs each competitor
            for i, competitor in enumerate(competitor_domains, 1):
                print(f"Finding gaps vs {competitor}...")
                
                intersection = dataforseo_tool._run(
                    action='domain_intersection',
                    target=domain,
                    target2=competitor,
                    intersections=False,
                    limit=15
                )
                
                opportunities[f'gap_vs_competitor_{i}'] = {
                    'competitor': competitor,
                    'intersection': intersection
                }
                
                # Extract keywords
                if intersection.get('success'):
                    items = intersection.get('tasks', [{}])[0].get('result', [{}])[0].get('items', [])
                    for item in items:
                        kw_data = item.get('keyword_data', {})
                        if kw_data.get('keyword'):
                            all_opportunity_keywords.add(kw_data['keyword'])
                
                time.sleep(3)
            
            all_results['phases']['opportunities'] = opportunities
            keyword_gap_data = {
                'opportunities': opportunities,
                'all_opportunity_keywords': list(all_opportunity_keywords)
            }
            self.results['keyword_gap'] = keyword_gap_data
            print(f"✅ Found {len(all_opportunity_keywords)} opportunity keywords")
            
            # Task 6: Keyword Prioritization (use tool directly)
            print("\n📈 TASK 6: KEYWORD PRIORITIZATION")
            print("-" * 70)
            
            if all_opportunity_keywords:
                keywords_list = list(all_opportunity_keywords)[:15]
                print(f"Getting search volume for {len(keywords_list)} keywords...")
                
                search_volume = dataforseo_tool._run(action='search_volume', keywords=keywords_list)
                all_results['phases']['search_volume'] = search_volume
                time.sleep(2)
            
            if config_data.get('main_topic'):
                print(f"Getting keyword suggestions for '{config_data['main_topic']}'...")
                keyword_suggestions = dataforseo_tool._run(
                    action='keyword_suggestions',
                    target=config_data['main_topic'],
                    limit=15
                )
                all_results['phases']['keyword_suggestions'] = keyword_suggestions
                time.sleep(2)
            
            keyword_data = {
                'search_volume': all_results['phases'].get('search_volume'),
                'keyword_suggestions': all_results['phases'].get('keyword_suggestions'),
                'all_keywords': list(all_opportunity_keywords)
            }
            self.results['keyword_prioritization'] = keyword_data
            print("✅ Keywords prioritized")
            
            # Task 7: SERP Analysis (use tool directly)
            print("\n🔍 TASK 7: SERP ANALYSIS")
            print("-" * 70)
            
            # Use config keywords if available, otherwise discovered keywords
            keywords_to_analyze = config_data.get('keywords', [])[:5] if config_data.get('keywords') else list(all_opportunity_keywords)[:5]
            
            serp_analysis = {}
            for i, keyword in enumerate(keywords_to_analyze, 1):
                print(f"Analyzing SERP for: {keyword}")
                
                serp_result = dataforseo_tool._run(action='serp_analysis', target=keyword)
                serp_analysis[f'keyword_{i}'] = {
                    'keyword': keyword,
                    'serp_data': serp_result
                }
                time.sleep(3)
            
            all_results['phases']['serp_analysis'] = serp_analysis
            serp_data = serp_analysis
            self.results['serp_analysis'] = serp_analysis
            print(f"✅ Analyzed {len(keywords_to_analyze)} keywords")
            
            # Task 8: Technical Crawl (use tool directly)
            print("\n🔧 TASK 8: TECHNICAL SEO CRAWL")
            print("-" * 70)
            
            crawler_tool = OnPageCrawlerTool()
            
            print(f"Starting crawl for {domain} (max {max_pages} pages)...")
            start_result = crawler_tool._run(action='start_crawl', domain=domain, max_pages=max_pages)
            
            if not start_result.get('success'):
                print(f"❌ Failed to start crawl: {start_result.get('error')}")
                crawl_data = {}
            else:
                task_id = start_result['task_id']
                print(f"✅ Crawl task started: {task_id}")
                all_results['onpage_data']['task_id'] = task_id
                
                # Wait for completion
                print("⏳ Waiting for crawl to complete (this takes 5-10 minutes)...")
                max_wait = 600
                check_interval = 30
                elapsed = 0
                
                while elapsed < max_wait:
                    time.sleep(check_interval)
                    elapsed += check_interval
                    
                    status_result = crawler_tool._run(action='check_status', task_id=task_id)
                    
                    if status_result.get('is_complete'):
                        print(f"✅ Crawl complete! {status_result.get('pages_crawled', 0)} pages")
                        break
                    elif status_result.get('is_failed'):
                        print(f"❌ Crawl failed: {status_result.get('status')}")
                        break
                    else:
                        print(f"   ... {status_result.get('status')} ({status_result.get('pages_crawled', 0)} pages)")
                
                # Get results
                print("Getting crawl results...")
                pages_result = crawler_tool._run(action='get_results', task_id=task_id)
                all_results['onpage_data']['pages'] = pages_result
                
                summary_result = crawler_tool._run(action='get_summary', task_id=task_id)
                all_results['onpage_data']['summary'] = summary_result
                
                crawl_data = {
                    'task_id': task_id,
                    'pages': pages_result,
                    'summary': summary_result
                }
                self.results['technical_crawl'] = crawl_data
                print("✅ On-page crawl complete")
            
            # Task 9: AI Code Fixes (use tool directly - this DOES need Claude)
            print("\n🤖 TASK 9: AI CODE FIX GENERATION")
            print("-" * 70)
            
            claude_tool = ClaudeAnalysisTool()
            ai_data = {}
            if all_results['onpage_data'].get('pages'):
                
                print("Analyzing technical issues with Claude...")
                onpage_json = json.dumps(all_results['onpage_data'])
                claude_result = claude_tool._run(onpage_data=onpage_json, domain=domain)
                
                if claude_result.get('success'):
                    ai_data = claude_result
                    all_results['claude_analysis'] = claude_result
                    self.results['ai_fixes'] = claude_result
                    print(f"✅ Claude analysis complete")
                    print(f"   Platform: {claude_result.get('platform')}")
                    print(f"   URLs analyzed: {claude_result.get('urls_analyzed', 0)}")
                    print(f"   Issues found: {claude_result.get('total_issues', 0)}")
                else:
                    print(f"⚠️ Claude analysis failed: {claude_result.get('error')}")
            else:
                print("⚠️ No on-page data available for Claude analysis")
            
            # Compile all audit data (already in all_results)
            complete_audit_data = all_results
            
            # Save complete results JSON
            json_file = self.output_dir / "full_results.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(complete_audit_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Complete audit data saved to {json_file}")
            
            # Task 10: Generate Reports (use tool directly)
            print("\n📊 TASK 10: GENERATING CSV REPORTS")
            print("-" * 70)
            
            csv_tool = CSVGeneratorTool()
            
            audit_json = json.dumps(complete_audit_data)
            csv_result = csv_tool._run(
                action='generate_all',
                audit_data=audit_json,
                output_dir=str(self.output_dir)
            )
            
            if csv_result.get('success'):
                report_data = csv_result
                self.results['reports'] = csv_result
                print(f"✅ Generated {csv_result.get('count', 0)} CSV files")
                for file_path in csv_result.get('files_created', []):
                    print(f"   📄 {Path(file_path).name}")
            else:
                print(f"❌ CSV generation failed: {csv_result.get('error')}")
                report_data = {}
            
            # Final Summary
            elapsed_time = time.time() - start_time
            print("\n" + "="*70)
            print("🎉 SEO AUDIT COMPLETE!")
            print("="*70)
            print(f"⏱️  Total Time: {elapsed_time/60:.1f} minutes")
            print(f"📁 Output Location: {self.output_dir}")
            print(f"🌐 Domain: {domain}")
            print(f"🏢 Competitors Analyzed: {len(competitor_domains)}")
            print(f"🔑 Keywords Analyzed: {len(keywords_to_analyze)}")
            print(f"📄 CSV Files Generated: {report_data.get('count', 0)}")
            if ai_data:
                print(f"🔧 Technical Issues Found: {ai_data.get('total_issues', 0)}")
            print(f"✅ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*70)
            
            return {
                'success': True,
                'output_dir': str(self.output_dir),
                'results': self.results,
                'summary': {
                    'domain': domain,
                    'csv_files': report_data.get('count', 0),
                    'issues_found': ai_data.get('total_issues', 0) if ai_data else 0,
                    'competitors_analyzed': len(competitor_domains),
                    'keywords_analyzed': len(keywords_to_analyze),
                    'elapsed_time': elapsed_time
                }
            }
            
        except Exception as e:
            print(f"\n❌ SEO AUDIT FAILED")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_result(self, result):
        """Parse CrewAI task result into dictionary"""
        if isinstance(result, dict):
            return result
        elif isinstance(result, str):
            try:
                return json.loads(result)
            except:
                return {'raw_result': result}
        else:
            try:
                return json.loads(str(result))
            except:
                return {'raw_result': str(result)}


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run CrewAI-powered SEO Audit',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Check env vars
    required_vars = ['DATAFORSEO_USERNAME', 'DATAFORSEO_PASSWORD', 'CLAUDE_API_KEY']
    missing = [v for v in required_vars if not os.getenv(v)]
    
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        print("Please set them in your .env file")
        return 1
    
    # Create and run the crew
    crew = SEOAuditCrew(config_path=args.config, verbose=args.verbose)
    result = crew.run()  # Synchronous - runs one step at a time
    
    if result and result.get('success'):
        print("\n✅ Audit completed successfully!")
        print(f"📁 Check results in: {result['output_dir']}")
        return 0
    else:
        print("\n❌ Audit failed!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

