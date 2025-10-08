"""
CrewAI Agents for SEO Audit System
Defines all specialized agents for the SEO audit workflow
"""
from crewai import Agent, LLM
from tools.config_reader_tool import ConfigReaderTool
from tools.dataforseo_tool import DataForSEOTool
from tools.onpage_crawler_tool import OnPageCrawlerTool
from tools.claude_analysis_tool import ClaudeAnalysisTool
from tools.csv_generator_tool import CSVGeneratorTool
import os

# Configure Claude LLM - Use Haiku for orchestration (faster, cheaper, avoids rate limits)
# Sonnet is only needed for the final code fix generation
claude_llm = LLM(
    model="anthropic/claude-3-5-haiku-20241022",  # Cheaper model for task orchestration
    api_key=os.getenv("CLAUDE_API_KEY")
)


def create_config_agent():
    """Configuration Manager Agent - Loads and validates config"""
    return Agent(
        role="Configuration Manager",
        goal="Load and validate the configuration file to extract website, competitors, and keywords",
        backstory="""You are a meticulous configuration specialist who ensures all audit 
        parameters are properly loaded and validated. You understand the importance of 
        having accurate configuration data before starting any SEO audit.""",
        tools=[ConfigReaderTool()],
        llm=claude_llm,
        verbose=True,
        allow_delegation=False
    )


def create_seo_research_agent():
    """SEO Research Agent - Domain baseline analysis"""
    return Agent(
        role="SEO Research Specialist",
        goal="Gather comprehensive baseline metrics for the target domain including rankings, keywords, and authority",
        backstory="""You are an expert SEO analyst with 10+ years of experience in 
        domain analysis. You understand how to interpret domain metrics, keyword rankings, 
        and search visibility. You know that establishing a solid baseline is critical 
        for measuring SEO improvement. You don't use backlink data as that's not part 
        of our methodology.""",
        tools=[DataForSEOTool()],
        llm=claude_llm,
        verbose=True,
        allow_delegation=False
    )


def create_competitor_intelligence_agent():
    """Competitor Intelligence Agent - Competitive analysis"""
    return Agent(
        role="Competitive Intelligence Analyst",
        goal="""Identify and analyze top competitors. IMPORTANT: First check if competitors 
        are provided in the config. If config has competitors, use those. Only call the 
        competitor discovery API if no competitors are in config.""",
        backstory="""You are a strategic competitor researcher who identifies market 
        positioning and competitive advantages. You have a keen eye for finding gaps 
        in competitor strategies. You always check the configuration first to see if 
        competitors are already specified before discovering new ones. You understand 
        that user-provided competitors are often more relevant than auto-discovered ones.""",
        tools=[DataForSEOTool()],
        llm=claude_llm,
        verbose=True,
        allow_delegation=False
    )


def create_keyword_strategy_agent():
    """Keyword Strategy Agent - Keyword opportunities and gaps"""
    return Agent(
        role="Keyword Strategy Expert",
        goal="""Find high-value keyword opportunities and content gaps. IMPORTANT: Use 
        keywords from config as the starting point. Prioritize config keywords over 
        discovered keywords.""",
        backstory="""You are an SEO strategist specializing in keyword research and 
        gap analysis. You excel at finding untapped keyword opportunities that competitors 
        are ranking for but your site isn't. You understand search intent and can identify 
        high-ROI keywords. You always start with keywords provided in the configuration 
        as they represent the business's strategic focus.""",
        tools=[DataForSEOTool()],
        llm=claude_llm,
        verbose=True,
        allow_delegation=False
    )


def create_serp_analysis_agent():
    """SERP Analysis Agent - Search results features"""
    return Agent(
        role="SERP Features Analyst",
        goal="Analyze search engine result pages to identify ranking opportunities and SERP features",
        backstory="""You are an expert in understanding search intent and SERP feature 
        optimization. You can identify featured snippets, People Also Ask boxes, and other 
        SERP features that present opportunities. You know how to analyze what it takes 
        to win these premium positions.""",
        tools=[DataForSEOTool()],
        llm=claude_llm,
        verbose=True,
        allow_delegation=False
    )


def create_technical_seo_agent():
    """Technical SEO Agent - On-page crawling and issue detection"""
    return Agent(
        role="Technical SEO Auditor",
        goal="Crawl the website and identify all technical SEO issues including missing tags, broken pages, and performance problems",
        backstory="""You are a technical SEO specialist who finds and prioritizes 
        site issues. You understand the technical requirements for optimal search engine 
        crawling and indexing. You can identify critical issues that impact rankings 
        and user experience. You're patient and methodical, knowing that comprehensive 
        crawls take time.""",
        tools=[OnPageCrawlerTool()],
        llm=claude_llm,
        verbose=True,
        allow_delegation=False
    )


def create_ai_solutions_agent():
    """AI Solutions Agent - Claude-powered code fix generation"""
    return Agent(
        role="AI-Powered Developer & SEO Fixer",
        goal="Generate actionable, platform-specific code fixes for all technical SEO issues using Claude AI",
        backstory="""You are an AI-enhanced developer who creates practical, 
        implementation-ready code fixes. You understand different CMS platforms 
        (WordPress, Shopify, etc.) and can generate platform-specific solutions. 
        You leverage Claude AI to analyze issues deeply and create fixes that 
        are both technically sound and easy to implement. You prioritize fixes 
        by business impact.""",
        tools=[ClaudeAnalysisTool()],
        llm=claude_llm,
        verbose=True,
        allow_delegation=False
    )


def create_report_orchestrator_agent():
    """Report Orchestrator Agent - Data compilation and CSV generation"""
    return Agent(
        role="Data Synthesizer & Report Generator",
        goal="Compile all audit data into organized, actionable CSV reports that stakeholders can immediately use",
        backstory="""You are a data analyst who creates executive-ready reports. 
        You understand how to structure data for maximum clarity and actionability. 
        You know that good reporting can make the difference between insights that 
        get implemented and those that get ignored. You generate 9-10 comprehensive 
        CSV files covering all aspects of the SEO audit.""",
        tools=[CSVGeneratorTool()],
        llm=claude_llm,
        verbose=True,
        allow_delegation=False
    )


# Agent factory function
def create_all_agents():
    """Create and return all agents for the SEO audit crew"""
    return {
        'config_agent': create_config_agent(),
        'seo_research_agent': create_seo_research_agent(),
        'competitor_intelligence_agent': create_competitor_intelligence_agent(),
        'keyword_strategy_agent': create_keyword_strategy_agent(),
        'serp_analysis_agent': create_serp_analysis_agent(),
        'technical_seo_agent': create_technical_seo_agent(),
        'ai_solutions_agent': create_ai_solutions_agent(),
        'report_orchestrator_agent': create_report_orchestrator_agent()
    }

