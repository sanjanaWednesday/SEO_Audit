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
        self.model = "claude-3-5-sonnet-20241022"  
        
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
    
    async def generate_onpage_code_fixes(self, url: str, combined_data: Dict, platform: str = "Unknown") -> Dict:
        """
        Generate specific code fixes for OnPage SEO issues
        
        Args:
            url: The URL being analyzed
            combined_data: Combined issue and page data
            platform: Platform/CMS detected (Shopify, WordPress, etc.)
            
        Returns:
            Dict containing code fixes and implementation instructions
        """
        try:
            # Build detailed prompt for Claude
            prompt = self._create_onpage_fixes_prompt(url, combined_data, platform)
            
            # Send to Claude
            response = await self._send_to_claude(prompt)
            
            # Parse response
            fixes = self._parse_onpage_fixes_response(response)
            
            return fixes
            
        except Exception as e:
            logger.error(f"Error generating onpage fixes: {e}")
            return {
                "error": str(e),
                "analysis": "Failed to generate fixes",
                "fixes": []
            }
    
    def _create_onpage_fixes_prompt(self, url: str, combined_data: Dict, platform: str) -> str:
        """Create detailed prompt for OnPage code fixes"""
        
        issues = combined_data.get('issues', [])
        current_state = combined_data.get('current_state', {})
        onpage_score = combined_data.get('onpage_score', 0)
        
        # Format issues list
        issues_text = []
        for issue in issues:
            issue_type = issue.get('Issue Type', 'Unknown')
            severity = issue.get('Severity', 'Medium')
            description = issue.get('Description', '')
            issues_text.append(f"- {issue_type} ({severity}): {description}")
        
        issues_formatted = '\n'.join(issues_text) if issues_text else "No specific issues listed"
        
        # Format H1 tags
        h1_list = current_state.get('h1_tags', [])
        h1_display = ', '.join([f'"{h1}"' for h1 in h1_list]) if h1_list else "❌ NONE (Missing H1)"
        
        # Format H2 tags (show first 3)
        h2_list = current_state.get('h2_tags', [])
        h2_display = ', '.join([f'"{h2}"' for h2 in h2_list[:3]])
        if len(h2_list) > 3:
            h2_display += f' ... and {len(h2_list) - 3} more'
        
        # Platform-specific guidance
        platform_guidance = ""
        if platform == "Shopify":
            platform_guidance = """
PLATFORM: Shopify
Template files typically located in:
- Homepage: sections/header.liquid, templates/index.liquid
- Collections: templates/collection.liquid, sections/collection-template.liquid
- Products: templates/product.liquid, sections/product-template.liquid

Suggest Liquid template modifications where appropriate."""
        elif platform == "WordPress":
            platform_guidance = """
PLATFORM: WordPress
Template files typically located in:
- Homepage: header.php, front-page.php, index.php
- Archives: archive.php, category.php
- Single posts: single.php, content.php

Suggest PHP/WordPress theme modifications where appropriate."""
        else:
            platform_guidance = f"PLATFORM: {platform}\nSuggest general HTML/template modifications."
        
        prompt = f"""You are an expert SEO developer specializing in on-page optimization. Analyze the following page and generate specific, actionable code fixes.

URL: {url}
Current OnPage Score: {onpage_score:.1f}/100

{platform_guidance}

═══════════════════════════════════════════════════════════════════

IDENTIFIED ISSUES:
{issues_formatted}

═══════════════════════════════════════════════════════════════════

CURRENT PAGE STATE:

Meta Tags:
- Title: "{current_state.get('title', '')}" ({current_state.get('title_length', 0)} characters)
- Description: "{current_state.get('description', '') or '❌ NONE'}" ({current_state.get('description_length', 0)} characters)
- Canonical: {current_state.get('canonical', 'Not set')}

Content Structure:
- H1 Tags: {h1_display}
- H2 Tags: {h2_display}
- H3 Tags: {len(current_state.get('h3_tags', []))} found
- Word Count: {current_state.get('word_count', 0)} words
- Content-to-HTML Ratio: {current_state.get('plain_text_rate', 0):.2%}

Links & Media:
- Internal Links: {current_state.get('internal_links', 0)}
- External Links: {current_state.get('external_links', 0)}
- Images: {current_state.get('images_count', 0)}

Social Media Tags:
{self._format_social_tags(current_state.get('social_media_tags', {}))}

═══════════════════════════════════════════════════════════════════

TASK: Generate specific code fixes for each issue.

For EACH issue, provide:
1. **Root Cause Analysis** - Why this issue exists based on current page state
2. **Specific HTML/Code Fix** - Actual copy-paste ready code
3. **Implementation Location** - Where to add/modify code (be specific about template files)
4. **Priority Level** - 1 (Critical), 2 (High), 3 (Medium)
5. **Expected Impact** - How this fix will improve SEO
6. **Implementation Time** - Estimated time to implement

IMPORTANT INSTRUCTIONS:
- Generate code based on ACTUAL current content (H2s, title patterns, etc.)
- For missing H1: Suggest an H1 that makes sense given the H2s and content
- For duplicate titles/descriptions: Create unique variations based on the URL path
- For low content: Suggest WHERE to add content, not just "add content"
- Be SPECIFIC and ACTIONABLE - no generic advice
- Use proper HTML syntax with appropriate classes/attributes
- Consider SEO best practices (keywords, length, hierarchy)

Return your response in the following JSON format:
{{
  "analysis": "Brief 2-3 sentence summary of the main issues and their impact",
  "fixes": [
    {{
      "issue": "Issue name (e.g., Missing H1)",
      "priority": 1,
      "root_cause": "Why this issue exists",
      "code": "Actual HTML/code to implement",
      "location": "Where to add this code (specific template/file and location)",
      "explanation": "Why this fix works",
      "expected_impact": "Expected SEO improvement",
      "implementation_time": "Estimated time",
      "testing_steps": ["Step 1", "Step 2"]
    }}
  ],
  "estimated_score_improvement": "Expected OnPage score improvement (e.g., +8-10 points)"
}}

Generate fixes now:"""
        
        return prompt
    
    def _format_social_tags(self, social_tags: Dict) -> str:
        """Format social media tags for display"""
        if not social_tags:
            return "- None found"
        
        formatted = []
        for key, value in list(social_tags.items())[:5]:  # Show first 5
            if value and key not in ['og:image', 'og:image:secure_url']:  # Skip images
                formatted.append(f"- {key}: {value[:60]}{'...' if len(str(value)) > 60 else ''}")
        
        return '\n'.join(formatted) if formatted else "- Basic tags present"
    
    def _parse_onpage_fixes_response(self, response: str) -> Dict:
        """Parse OnPage fixes response from Claude"""
        try:
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                # Find JSON block
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                
                parsed = json.loads(json_str)
                return parsed
            else:
                # Return raw response if no JSON found
                return {
                    "analysis": response[:500],
                    "fixes": [],
                    "raw_response": response
                }
        
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse JSON from Claude response: {e}")
            # Try alternative parsing: escape problematic characters
            try:
                # Claude sometimes puts code blocks with newlines that break JSON
                # Try to fix by replacing literal newlines in code blocks
                import re
                
                # Find code blocks and escape newlines within them
                def escape_code_block(match):
                    code = match.group(1)
                    # Escape newlines and other special chars in code
                    escaped = code.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    return f'"code": "{escaped}"'
                
                # Pattern to find "code": "..." blocks
                fixed_json = re.sub(r'"code":\s*"(.*?)"(?=\s*[,}])', escape_code_block, json_str, flags=re.DOTALL)
                
                parsed = json.loads(fixed_json)
                logger.info("✓ Successfully parsed after escaping code blocks")
                return parsed
                
            except Exception as e2:
                logger.warning(f"Alternative parsing also failed: {e2}")
                # Return with FULL raw response (not truncated)
                return {
                    "analysis": "See raw response for details",
                    "fixes": [],
                    "raw_response": response  # FULL response, not truncated
                }
        
        except Exception as e:
            logger.error(f"Error parsing onpage fixes response: {e}")
            return {
                "error": str(e),
                "analysis": "Failed to parse response",
                "fixes": [],
                "raw_response": response  # Keep full response
            }