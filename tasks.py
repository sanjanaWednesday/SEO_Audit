"""
CrewAI Tasks for SEO Audit System
Defines all tasks for the sequential SEO audit workflow
"""
from crewai import Task
import json


def create_load_config_task(agent, config_path="config.yaml"):
    """Task 1: Load and validate configuration"""
    return Task(
        description=f"""Load and validate the SEO audit configuration from {config_path}.
        
        Extract:
        - Website domain (required)
        - Competitor websites (optional - may be empty list)
        - Target keywords (optional - may be empty list)
        - Main topic for keyword suggestions
        - Max pages to crawl
        
        Return the validated configuration as a dictionary.
        """,
        agent=agent,
        expected_output="""A dictionary containing:
        - website: the target domain
        - competitors: list of competitor domains (may be empty)
        - keywords: list of target keywords (may be empty)
        - main_topic: main business topic
        - max_crawl_pages: number of pages to crawl
        - has_competitors: boolean indicating if competitors provided
        - has_keywords: boolean indicating if keywords provided""",
        output_file=None
    )


def create_baseline_analysis_task(agent, config_data):
    """Task 2: Domain baseline analysis"""
    domain = config_data.get('website', '')
    
    return Task(
        description=f"""Gather comprehensive baseline metrics for {domain}.
        
        Required API calls:
        1. Get domain metrics (traffic value, rankings)
        2. Get ranked keywords (what keywords the domain ranks for)
        
        NO BACKLINK DATA - We don't use backlink APIs.
        
        Use the DataForSEOTool with these actions:
        - domain_metrics with target={domain}
        - ranked_keywords with target={domain}, limit=15
        
        Return a dictionary with both results.
        """,
        agent=agent,
        expected_output=f"""Dictionary containing:
        - domain_metrics: Full API response with organic traffic value and rankings
        - ranked_keywords: List of top 15 keywords the domain ranks for with positions
        - domain: {domain}""",
        output_file=None
    )


def create_competitor_discovery_task(agent, config_data):
    """Task 3: Discover or use configured competitors"""
    domain = config_data.get('website', '')
    has_competitors = config_data.get('has_competitors', False)
    config_competitors = config_data.get('competitors', [])
    
    return Task(
        description=f"""Identify top competitors for {domain}.
        
        IMPORTANT LOGIC:
        1. Check if competitors are provided in config: {has_competitors}
        2. Config competitors: {config_competitors}
        3. If config has competitors, use those directly - DO NOT call the API
        4. If config has NO competitors, then call the competitor discovery API
        
        Only use DataForSEOTool action 'competitors' if config competitors list is empty.
        
        Return a list of up to 3 competitor domains.
        """,
        agent=agent,
        expected_output="""Dictionary containing:
        - competitors: List of 3 competitor domains
        - source: 'config' or 'api' indicating where competitors came from
        - competitor_data: Full API response if API was used, or None if from config""",
        output_file=None
    )


def create_competitor_analysis_task(agent, competitor_list):
    """Task 4: Deep analysis of each competitor"""
    competitors = competitor_list.get('competitors', [])
    
    return Task(
        description=f"""Analyze each competitor in detail: {', '.join(competitors)}.
        
        For EACH competitor, get:
        1. Domain metrics (traffic value, rankings)
        2. Ranked keywords (what keywords they rank for)
        
        NO BACKLINK DATA - We don't analyze backlinks.
        
        Use DataForSEOTool with these actions for each competitor:
        - domain_metrics with target=<competitor_domain>
        - ranked_keywords with target=<competitor_domain>, limit=15
        
        Return structured data for all competitors.
        """,
        agent=agent,
        expected_output="""Dictionary containing:
        - competitor_analysis: Dictionary with keys 'competitor_1', 'competitor_2', etc.
        - Each competitor entry contains:
          - domain: competitor domain name
          - domain_metrics: Full API response
          - ranked_keywords: Full API response""",
        output_file=None
    )


def create_keyword_gap_task(agent, config_data, baseline_data, competitor_data):
    """Task 5: Find keyword opportunities and content gaps"""
    domain = config_data.get('website', '')
    has_keywords = config_data.get('has_keywords', False)
    config_keywords = config_data.get('keywords', [])
    competitors = competitor_data.get('competitors', [])
    
    return Task(
        description=f"""Find high-value keyword opportunities for {domain}.
        
        IMPORTANT LOGIC FOR KEYWORDS:
        1. Config has keywords: {has_keywords}
        2. Config keywords: {config_keywords}
        3. Use config keywords as PRIMARY source
        4. Then find gaps vs competitors: {', '.join(competitors)}
        
        Steps:
        1. Start with config keywords if provided
        2. For each competitor, get domain intersection to find gaps
        3. Get keywords each competitor ranks for
        4. Identify opportunities where competitors rank but we don't
        
        Use DataForSEOTool actions:
        - domain_intersection with target={domain}, target2=<competitor>
        - keywords_from_site with target=<competitor>
        
        Return comprehensive opportunity data.
        """,
        agent=agent,
        expected_output="""Dictionary containing:
        - config_keywords: Keywords from config (if any)
        - opportunities: Dictionary with content gaps per competitor
        - all_opportunity_keywords: Combined list of all discovered keywords
        - source_priority: 'config' if config keywords exist, else 'discovered'""",
        output_file=None
    )


def create_keyword_prioritization_task(agent, keyword_gap_data, config_data):
    """Task 6: Prioritize keywords with search volume"""
    return Task(
        description="""Prioritize keyword opportunities based on search volume and value.
        
        Steps:
        1. Take all discovered opportunity keywords
        2. Get search volume data for top 15 keywords
        3. If main_topic is provided, get keyword suggestions
        4. Calculate priority scores
        
        Use DataForSEOTool actions:
        - search_volume with keywords=<list_of_keywords>
        - keyword_suggestions with target=<main_topic> (if main_topic exists)
        
        Return prioritized keyword list.
        """,
        agent=agent,
        expected_output="""Dictionary containing:
        - search_volume: API response with volume data for opportunity keywords
        - keyword_suggestions: API response for main topic (if applicable)
        - prioritized_keywords: List of keywords sorted by opportunity value""",
        output_file=None
    )


def create_serp_analysis_task(agent, keyword_data, config_data):
    """Task 7: Analyze SERP features for target keywords"""
    has_keywords = config_data.get('has_keywords', False)
    config_keywords = config_data.get('keywords', [])
    
    return Task(
        description="""Analyze search engine result pages for target keywords.
        
        IMPORTANT LOGIC FOR KEYWORD SELECTION:
        1. If config has keywords, analyze those first (priority)
        2. Otherwise, use top 5 discovered opportunity keywords
        3. Look for SERP features: featured snippets, PAA, knowledge graph
        
        For each keyword:
        - Get SERP analysis to see ranking features
        - Identify snippet opportunities
        - Assess competition level
        
        Use DataForSEOTool action:
        - serp_analysis with target=<keyword>
        
        Return SERP feature data for all analyzed keywords.
        """,
        agent=agent,
        expected_output="""Dictionary containing:
        - serp_analysis: Dictionary with analysis for each keyword
        - keywords_analyzed: List of keywords that were analyzed
        - feature_opportunities: Summary of SERP feature opportunities""",
        output_file=None
    )


def create_technical_crawl_task(agent, config_data):
    """Task 8: On-page technical crawl"""
    domain = config_data.get('website', '')
    max_pages = config_data.get('max_crawl_pages', 10)
    
    return Task(
        description=f"""Perform comprehensive technical SEO crawl of {domain}.
        
        Steps:
        1. Start crawl task with max_pages={max_pages}
        2. Wait for crawl to complete (may take 5-10 minutes)
        3. Check status periodically
        4. Once complete, get full crawl results
        5. Get crawl summary
        
        Use OnPageCrawlerTool actions:
        - start_crawl with domain={domain}, max_pages={max_pages}
        - check_status with task_id (in loop until complete)
        - get_results with task_id
        - get_summary with task_id
        
        Return complete crawl data with all pages and issues.
        """,
        agent=agent,
        expected_output="""Dictionary containing:
        - task_id: Crawl task ID
        - crawl_status: Final status
        - pages_crawled: Number of pages analyzed
        - pages: Full API response with all page data
        - summary: Crawl summary with statistics
        - technical_issues: Extracted list of all issues found""",
        output_file=None
    )


def create_ai_code_fixes_task(agent, crawl_data, config_data):
    """Task 9: Generate AI-powered code fixes"""
    domain = config_data.get('website', '')
    
    return Task(
        description=f"""Generate platform-specific code fixes for {domain} using Claude AI.
        
        Steps:
        1. Take on-page crawl data with all technical issues
        2. Detect website platform (WordPress, Shopify, custom, etc.)
        3. Use Claude AI to analyze each issue deeply
        4. Generate specific, copy-paste-ready code fixes
        5. Prioritize fixes by business impact
        6. Include implementation locations
        
        Use ClaudeAnalysisTool:
        - Pass complete on-page data as JSON
        - Get back AI-generated fixes for each issue
        
        Return structured fix recommendations.
        """,
        agent=agent,
        expected_output="""Dictionary containing:
        - platform: Detected platform
        - urls_analyzed: Number of URLs with issues
        - total_issues: Total number of issues found
        - analysis: Full Claude analysis with fixes for each URL/issue
        - fixes_by_priority: Fixes grouped by priority (Critical/High/Medium)""",
        output_file=None
    )


def create_report_generation_task(agent, all_audit_data, config_data, output_dir):
    """Task 10: Generate all CSV reports"""
    domain = config_data.get('website', '')
    
    return Task(
        description=f"""Generate comprehensive CSV reports for {domain}.
        
        Create these CSV files:
        1. Domain Overview (your site vs competitors)
        2. Top Keywords (your current rankings)
        3. Competitors Analysis (competitor details)
        4. Content Gaps (keyword opportunities)
        5. SERP Features (snippet opportunities)
        6. On-Page Pages (all crawled pages)
        7. Technical Issues (all SEO issues)
        8. Issues Summary (aggregated statistics)
        9. Claude Fixes (AI-generated code fixes)
        
        NO backlink_gap CSV - we don't use backlink data.
        
        Use CSVGeneratorTool:
        - action='generate_all'
        - Pass complete audit_data as JSON
        - output_dir={output_dir}
        
        Return list of generated files.
        """,
        agent=agent,
        expected_output=f"""Dictionary containing:
        - files_created: List of all generated CSV file paths
        - count: Number of files created (should be 9)
        - output_dir: {output_dir}
        - summary: Brief summary of what was generated""",
        output_file=f"{output_dir}/audit_summary.txt"
    )


# Task factory function
def create_all_tasks(agents, config_path="config.yaml"):
    """
    Create all tasks with proper dependencies
    
    Note: Tasks will be created in sequence as results from previous tasks
    are passed to subsequent tasks. This factory creates the initial
    config task only. Other tasks are created dynamically based on results.
    """
    return {
        'load_config': create_load_config_task(
            agent=agents['config_agent'],
            config_path=config_path
        )
    }


def create_dynamic_task(task_name, agent, **kwargs):
    """
    Helper to create tasks dynamically based on previous results
    """
    task_creators = {
        'baseline_analysis': create_baseline_analysis_task,
        'competitor_discovery': create_competitor_discovery_task,
        'competitor_analysis': create_competitor_analysis_task,
        'keyword_gap': create_keyword_gap_task,
        'keyword_prioritization': create_keyword_prioritization_task,
        'serp_analysis': create_serp_analysis_task,
        'technical_crawl': create_technical_crawl_task,
        'ai_code_fixes': create_ai_code_fixes_task,
        'report_generation': create_report_generation_task,
    }
    
    if task_name in task_creators:
        return task_creators[task_name](agent, **kwargs)
    
    raise ValueError(f"Unknown task: {task_name}")

