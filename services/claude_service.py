"""
Claude AI Service
Handles AI analysis of SEO audit results using Claude API
"""
import os
import json
import aiohttp
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        self.api_key = os.getenv('CLAUDE_API_KEY')
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-sonnet-20240229"
        
    async def analyze_audit_results(self, audit_results: Dict, target_domain: str) -> Dict:
        """
        Analyze SEO audit results using Claude AI
        
        Args:
            audit_results: Complete audit results from DataForSEO
            target_domain: The audited domain
            
        Returns:
            Dict containing AI analysis and recommendations
        """
        try:
            # Prepare the prompt
            prompt = self._create_analysis_prompt(audit_results, target_domain)
            
            # Send to Claude
            analysis = await self._send_to_claude(prompt)
            
            # Parse and structure the response
            structured_analysis = self._parse_claude_response(analysis)
            
            return structured_analysis
            
        except Exception as e:
            logger.error(f"Error in Claude analysis: {e}")
            return {
                "summary": f"Analysis failed: {str(e)}",
                "insights": [],
                "recommendations": []
            }
    
    def _create_analysis_prompt(self, audit_results: Dict, target_domain: str) -> str:
        """Create comprehensive prompt for Claude analysis"""
        
        # Extract key data for analysis
        baseline = audit_results.get('baseline', {})
        competitors = audit_results.get('competitor_analysis', {})
        opportunities = audit_results.get('opportunities', {})
        prioritized_keywords = audit_results.get('prioritized_keywords', {})
        serp_analysis = audit_results.get('serp_analysis', {})
        
        prompt = f"""
You are an expert SEO analyst. Analyze the following SEO audit data for {target_domain} and provide actionable insights and recommendations.

## AUDIT DATA SUMMARY

### Your Site Baseline:
- Domain Metrics: {self._extract_domain_metrics(baseline.get('domain_metrics', {}))}
- Ranked Keywords: {self._extract_keyword_count(baseline.get('ranked_keywords', {}))}
- Backlinks: {self._extract_backlink_count(baseline.get('backlinks_summary', {}))}

### Competitor Analysis:
{self._extract_competitor_summary(competitors)}

### Content Opportunities:
{self._extract_opportunities_summary(opportunities)}

### Keyword Prioritization:
{self._extract_prioritized_keywords(prioritized_keywords)}

### SERP Analysis:
{self._extract_serp_summary(serp_analysis)}

## ANALYSIS REQUIREMENTS

Please provide a comprehensive analysis in the following JSON format:

{{
    "summary": "2-3 sentence executive summary of the audit findings",
    "critical_issues": [
        "List of critical issues that need immediate attention"
    ],
    "opportunities": [
        "List of high-value opportunities identified"
    ],
    "competitive_insights": [
        "Key insights about competitor performance"
    ],
    "recommendations": [
        "Specific, actionable recommendations with priority levels"
    ],
    "priority_matrix": {{
        "high_impact_low_effort": ["Quick wins to implement"],
        "high_impact_high_effort": ["Strategic initiatives requiring more work"],
        "low_impact_low_effort": ["Easy improvements with moderate impact"],
        "low_impact_high_effort": ["Avoid these unless necessary"]
    }},
    "next_steps": [
        "Immediate next steps to take within 30 days"
    ],
    "estimated_impact": "Assessment of potential traffic/ranking improvements",
    "timeline": "Recommended timeline for implementation"
}}

Focus on:
1. Critical issues that need immediate attention
2. High-value content opportunities
3. Competitive gaps and advantages
4. Technical SEO improvements
5. Link building opportunities
6. Content strategy recommendations

Be specific and actionable in your recommendations.
"""
        
        return prompt
    
    def _extract_domain_metrics(self, domain_metrics: Dict) -> str:
        """Extract key domain metrics for prompt"""
        try:
            if domain_metrics.get('tasks'):
                for task in domain_metrics['tasks']:
                    if task.get('result'):
                        result = task['result']
                        return f"Traffic: {result.get('organic_traffic', 'N/A')}, Keywords: {result.get('organic_keywords', 'N/A')}, Visibility: {result.get('organic_visibility', 'N/A')}"
            return "No data available"
        except:
            return "Error extracting metrics"
    
    def _extract_keyword_count(self, ranked_keywords: Dict) -> str:
        """Extract keyword count for prompt"""
        try:
            if ranked_keywords.get('tasks'):
                for task in ranked_keywords['tasks']:
                    if task.get('result'):
                        return f"{len(task['result'])} keywords"
            return "No keywords found"
        except:
            return "Error extracting keywords"
    
    def _extract_backlink_count(self, backlinks: Dict) -> str:
        """Extract backlink count for prompt"""
        try:
            if backlinks.get('tasks'):
                for task in backlinks['tasks']:
                    if task.get('result'):
                        result = task['result']
                        return f"Total: {result.get('total_backlinks', 'N/A')}, Domains: {result.get('referring_domains', 'N/A')}"
            return "No backlink data"
        except:
            return "Error extracting backlinks"
    
    def _extract_competitor_summary(self, competitors: Dict) -> str:
        """Extract competitor analysis summary"""
        summary = []
        for comp_key, comp_data in competitors.items():
            domain = comp_data.get('domain', 'Unknown')
            data = comp_data.get('data', {})
            
            # Extract key metrics
            domain_metrics = data.get('domain_metrics', {})
            keywords = data.get('ranked_keywords', {})
            backlinks = data.get('backlinks_summary', {})
            
            comp_summary = f"- {domain}: {self._extract_domain_metrics(domain_metrics)}"
            summary.append(comp_summary)
        
        return "\n".join(summary) if summary else "No competitor data"
    
    def _extract_opportunities_summary(self, opportunities: Dict) -> str:
        """Extract content opportunities summary"""
        opp_count = 0
        for opp_key, opp_data in opportunities.items():
            if 'intersection' in opp_data:
                intersection = opp_data['intersection']
                if intersection.get('tasks'):
                    for task in intersection['tasks']:
                        if task.get('result'):
                            opp_count += len(task['result'])
        
        return f"Found {opp_count} content opportunities"
    
    def _extract_prioritized_keywords(self, prioritized: Dict) -> str:
        """Extract prioritized keywords summary"""
        keywords = prioritized.get('opportunity_keywords', [])
        return f"Prioritized {len(keywords)} opportunity keywords"
    
    def _extract_serp_summary(self, serp_analysis: Dict) -> str:
        """Extract SERP analysis summary"""
        return f"Analyzed SERP for {len(serp_analysis)} keywords"
    
    async def _send_to_claude(self, prompt: str) -> str:
        """Send prompt to Claude API"""
        try:
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            data = {
                'model': self.model,
                'max_tokens': 4000,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['content'][0]['text']
                    else:
                        error_text = await response.text()
                        logger.error(f"Claude API error {response.status}: {error_text}")
                        return f"API Error: {response.status}"
        
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return f"Error: {str(e)}"
    
    def _parse_claude_response(self, response: str) -> Dict:
        """Parse Claude response into structured format"""
        try:
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                # Find JSON block in response
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                
                parsed = json.loads(json_str)
                return parsed
            else:
                # Fallback to basic parsing
                return {
                    "summary": response[:500] + "..." if len(response) > 500 else response,
                    "insights": ["Analysis completed - see summary for details"],
                    "recommendations": ["Review the full analysis for specific recommendations"]
                }
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return structured text response
            return {
                "summary": response[:500] + "..." if len(response) > 500 else response,
                "insights": ["Analysis completed - see summary for details"],
                "recommendations": ["Review the full analysis for specific recommendations"],
                "critical_issues": ["Unable to parse detailed analysis"],
                "opportunities": ["See summary for opportunities"],
                "competitive_insights": ["See summary for competitive insights"],
                "priority_matrix": {
                    "high_impact_low_effort": ["Review summary for quick wins"],
                    "high_impact_high_effort": ["Review summary for strategic initiatives"],
                    "low_impact_low_effort": ["Review summary for easy improvements"],
                    "low_impact_high_effort": ["Review summary for long-term projects"]
                },
                "next_steps": ["Review the full analysis and create action plan"],
                "estimated_impact": "Review analysis for impact assessment",
                "timeline": "Review analysis for recommended timeline"
            }
        
        except Exception as e:
            logger.error(f"Error parsing Claude response: {e}")
            return {
                "summary": f"Analysis completed but parsing failed: {str(e)}",
                "insights": ["Error in response parsing"],
                "recommendations": ["Manual review required"]
            }
