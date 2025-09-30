"""
Google Sheets Service
Handles creating and populating SEO audit reports in Google Sheets
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any
import gspread
from google.oauth2.service_account import Credentials
import logging

logger = logging.getLogger(__name__)

# class GoogleSheetsService:
#     def __init__(self):
#         self.credentials = self._get_credentials()
#         self.client = gspread.authorize(self.credentials)
        
#     def _get_credentials(self):
#         """Get Google Sheets credentials from service account"""
#         try:
#             # Define required scopes for Google Sheets and Drive
#             SCOPES = [
#                 "https://www.googleapis.com/auth/spreadsheets",
#                 "https://www.googleapis.com/auth/drive"
#             ]
            
#             # Try to get credentials from environment variable (JSON string)
#             creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
#             if creds_json:
#                 creds_dict = json.loads(creds_json)
#                 return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            
#             # Try to get from file
#             creds_file = os.getenv('GOOGLE_SHEETS_CREDS', 'credentials.json')
#             if os.path.exists(creds_file):
#                 return Credentials.from_service_account_file(creds_file, scopes=SCOPES)
            
#             raise Exception("No Google Sheets credentials found")
            
#         except Exception as e:
#             logger.error(f"Failed to get Google Sheets credentials: {e}")
#             raise
class GoogleSheetsService:
    def __init__(self):
        # ❌ Commented service account code
        # self.credentials = self._get_credentials()
        # self.client = gspread.authorize(self.credentials)
        
        # ✅ Temporary: use your own Google account via OAuth
        self.client = gspread.oauth(
            credentials_filename="credentials.json",
            authorized_user_filename="token.json"
        )


    def _get_credentials(self):
        """Get Google Sheets credentials from service account"""
        try:
            # Define required scopes for Google Sheets and Drive
            SCOPES = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Try to get credentials from environment variable (JSON string)
            creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
            if creds_json:
                creds_dict = json.loads(creds_json)
                return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            
            # Try to get from file
            creds_file = os.getenv('GOOGLE_SHEETS_CREDS')
            if os.path.exists(creds_file):
                return Credentials.from_service_account_file(creds_file, scopes=SCOPES)
            
            raise Exception("No Google Sheets credentials found")
            
        except Exception as e:
            logger.error(f"Failed to get Google Sheets credentials: {e}")
            raise

    
    async def create_seo_report(self, audit_results: Dict, claude_analysis: Dict, target_domain: str, user_email: str = None) -> str:
        """Create comprehensive SEO audit report in Google Sheets"""
        try:
            # Create new spreadsheet
            spreadsheet = self.client.create(f"SEO Audit Report - {target_domain} - {datetime.now().strftime('%Y-%m-%d')}")
            
            # Share with user email if provided (with edit permissions)
            if user_email:
                try:
                    spreadsheet.share(user_email, perm_type='user', role='writer', notify=True, email_message=f"Your SEO Audit Report for {target_domain} is ready!")
                    logger.info(f"Shared spreadsheet with user email: {user_email}")
                except Exception as e:
                    logger.warning(f"Failed to share with user email {user_email}: {e}")
            
            # Also share with anyone with the link (as backup)
            spreadsheet.share('', perm_type='anyone', role='reader')
            
            # Create all report sheets
            await self._create_domain_overview_sheet(spreadsheet, audit_results, target_domain)
            await self._create_content_gap_sheet(spreadsheet, audit_results)
            await self._create_top_keywords_sheet(spreadsheet, audit_results)
            await self._create_backlink_gap_sheet(spreadsheet, audit_results)
            await self._create_serp_features_sheet(spreadsheet, audit_results)
            await self._create_ai_analysis_sheet(spreadsheet, claude_analysis)
            
            # Return the URL
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
            
        except Exception as e:
            logger.error(f"Failed to create SEO report: {e}")
            raise
    
    async def _create_domain_overview_sheet(self, spreadsheet, audit_results: Dict, target_domain: str):
        """Create domain overview comparison sheet"""
        try:
            worksheet = spreadsheet.add_worksheet(title="Domain Overview", rows=100, cols=10)
            
            # Headers
            headers = [
                "Metric", "Your Site", "Competitor 1", "Competitor 2", "Competitor 3", 
                "Gap Analysis", "Priority", "Action Items"
            ]
            worksheet.append_row(headers)
            
            # Extract baseline data
            baseline = audit_results.get('baseline', {})
            domain_metrics = baseline.get('domain_metrics', {})
            ranked_keywords = baseline.get('ranked_keywords', {})
            backlinks = baseline.get('backlinks_summary', {})
            
            # Your site metrics
            your_traffic = self._extract_metric(domain_metrics, 'organic_traffic')
            your_keywords = self._extract_metric(ranked_keywords, 'total_keywords')
            your_backlinks = self._extract_metric(backlinks, 'total_backlinks')
            
            # Competitor metrics
            competitor_data = []
            for i in range(1, 4):
                comp_key = f'competitor_{i}'
                if comp_key in audit_results.get('competitor_analysis', {}):
                    comp_data = audit_results['competitor_analysis'][comp_key]['data']
                    comp_traffic = self._extract_metric(comp_data.get('domain_metrics', {}), 'organic_traffic')
                    comp_keywords = self._extract_metric(comp_data.get('ranked_keywords', {}), 'total_keywords')
                    comp_backlinks = self._extract_metric(comp_data.get('backlinks_summary', {}), 'total_backlinks')
                    competitor_data.append([comp_traffic, comp_keywords, comp_backlinks])
                else:
                    competitor_data.append(["N/A", "N/A", "N/A"])
            
            # Add data rows
            metrics = [
                ["Organic Traffic", your_traffic] + [comp[0] for comp in competitor_data],
                ["Ranked Keywords", your_keywords] + [comp[1] for comp in competitor_data],
                ["Total Backlinks", your_backlinks] + [comp[2] for comp in competitor_data]
            ]
            
            for metric_row in metrics:
                # Add gap analysis and priority
                gap_analysis = self._calculate_gap_analysis(metric_row[1], metric_row[2:5])
                priority = self._determine_priority(gap_analysis)
                action_items = self._get_action_items(metric_row[0], gap_analysis)
                
                full_row = metric_row + [gap_analysis, priority, action_items]
                worksheet.append_row(full_row)
            
            # Format the sheet
            worksheet.format('A1:H1', {'textFormat': {'bold': True}})
            
        except Exception as e:
            logger.error(f"Error creating domain overview sheet: {e}")
    
    async def _create_content_gap_sheet(self, spreadsheet, audit_results: Dict):
        """Create content gap analysis sheet"""
        try:
            worksheet = spreadsheet.add_worksheet(title="Content Gap Analysis", rows=1000, cols=8)
            
            headers = [
                "Keyword", "Search Volume", "CPC", "Competition", "Competitor Ranking", 
                "Your Ranking", "Priority", "Content Strategy"
            ]
            worksheet.append_row(headers)
            
            # Extract opportunity keywords
            opportunities = audit_results.get('opportunities', {})
            prioritized = audit_results.get('prioritized_keywords', {})
            
            # Process gap analysis results
            for opp_key, opp_data in opportunities.items():
                if 'intersection' in opp_data:
                    intersection_data = opp_data['intersection']
                    if intersection_data.get('tasks'):
                        for task in intersection_data['tasks']:
                            if task.get('result'):
                                for item in task['result']:
                                    keyword_data = item.get('keyword_data', {})
                                    if keyword_data.get('keyword'):
                                        keyword = keyword_data['keyword']
                                        search_volume = keyword_data.get('search_volume', 'N/A')
                                        cpc = keyword_data.get('cpc', 'N/A')
                                        competition = keyword_data.get('competition', 'N/A')
                                        
                                        # Get competitor ranking
                                        comp_ranking = item.get('rank_group_info', [{}])[0].get('rank_group_serp_item', [{}])[0].get('rank_group_absolute_rank', 'N/A')
                                        
                                        # Your ranking (would be N/A since it's a gap)
                                        your_ranking = "Not Ranking"
                                        
                                        # Priority calculation
                                        priority = self._calculate_keyword_priority(search_volume, cpc, competition)
                                        
                                        # Content strategy
                                        strategy = self._get_content_strategy(keyword, priority)
                                        
                                        row = [keyword, search_volume, cpc, competition, comp_ranking, your_ranking, priority, strategy]
                                        worksheet.append_row(row)
            
            # Format the sheet
            worksheet.format('A1:H1', {'textFormat': {'bold': True}})
            
        except Exception as e:
            logger.error(f"Error creating content gap sheet: {e}")
    
    async def _create_top_keywords_sheet(self, spreadsheet, audit_results: Dict):
        """Create top keywords analysis sheet"""
        try:
            worksheet = spreadsheet.add_worksheet(title="Your Top Keywords", rows=1000, cols=10)
            
            headers = [
                "Keyword", "Position", "Search Volume", "CPC", "Traffic Value", 
                "Estimated Clicks", "Competition", "Trend", "Action Required", "Priority"
            ]
            worksheet.append_row(headers)
            
            # Extract your ranked keywords
            baseline = audit_results.get('baseline', {})
            ranked_keywords = baseline.get('ranked_keywords', {})
            
            if ranked_keywords.get('tasks'):
                for task in ranked_keywords['tasks']:
                    if task.get('result'):
                        for item in task['result']:
                            keyword_data = item.get('keyword_data', {})
                            if keyword_data.get('keyword'):
                                keyword = keyword_data['keyword']
                                position = keyword_data.get('rank_group_info', [{}])[0].get('rank_group_serp_item', [{}])[0].get('rank_group_absolute_rank', 'N/A')
                                search_volume = keyword_data.get('search_volume', 'N/A')
                                cpc = keyword_data.get('cpc', 'N/A')
                                
                                # Calculate traffic value and estimated clicks
                                traffic_value = self._calculate_traffic_value(position, search_volume, cpc)
                                estimated_clicks = self._calculate_estimated_clicks(position, search_volume)
                                
                                # Determine action required
                                action_required = self._get_keyword_action(position, search_volume)
                                priority = self._get_keyword_priority_level(position, search_volume)
                                
                                row = [keyword, position, search_volume, cpc, traffic_value, estimated_clicks, 
                                      keyword_data.get('competition', 'N/A'), 'N/A', action_required, priority]
                                worksheet.append_row(row)
            
            # Format the sheet
            worksheet.format('A1:J1', {'textFormat': {'bold': True}})
            
        except Exception as e:
            logger.error(f"Error creating top keywords sheet: {e}")
    
    async def _create_backlink_gap_sheet(self, spreadsheet, audit_results: Dict):
        """Create backlink gap analysis sheet"""
        try:
            worksheet = spreadsheet.add_worksheet(title="Backlink Gap Analysis", rows=1000, cols=8)
            
            headers = [
                "Referring Domain", "Domain Authority", "Backlink Type", "Competitor", 
                "Your Status", "Outreach Priority", "Contact Info", "Notes"
            ]
            worksheet.append_row(headers)
            
            # This would require more complex analysis of competitor backlinks
            # For now, add placeholder data
            worksheet.append_row([
                "Example Domain", "85", "Guest Post", "Competitor 1", 
                "Not Linking", "HIGH", "contact@example.com", "High DA guest post opportunity"
            ])
            
            # Format the sheet
            worksheet.format('A1:H1', {'textFormat': {'bold': True}})
            
        except Exception as e:
            logger.error(f"Error creating backlink gap sheet: {e}")
    
    async def _create_serp_features_sheet(self, spreadsheet, audit_results: Dict):
        """Create SERP features analysis sheet"""
        try:
            worksheet = spreadsheet.add_worksheet(title="SERP Features", rows=500, cols=6)
            
            headers = [
                "Keyword", "SERP Features", "Featured Snippet", "Your Position", 
                "Opportunity", "Action Items"
            ]
            worksheet.append_row(headers)
            
            # Extract SERP analysis
            serp_analysis = audit_results.get('serp_analysis', {})
            
            for serp_key, serp_data in serp_analysis.items():
                keyword = serp_data.get('keyword', '')
                serp_info = serp_data.get('serp_data', {})
                
                # Extract SERP features
                features = self._extract_serp_features(serp_info)
                featured_snippet = self._check_featured_snippet(serp_info)
                your_position = self._get_your_position(serp_info)
                opportunity = self._assess_serp_opportunity(features, your_position)
                action_items = self._get_serp_action_items(features, opportunity)
                
                row = [keyword, features, featured_snippet, your_position, opportunity, action_items]
                worksheet.append_row(row)
            
            # Format the sheet
            worksheet.format('A1:F1', {'textFormat': {'bold': True}})
            
        except Exception as e:
            logger.error(f"Error creating SERP features sheet: {e}")
    
    async def _create_ai_analysis_sheet(self, spreadsheet, claude_analysis: Dict):
        """Create AI analysis summary sheet"""
        try:
            worksheet = spreadsheet.add_worksheet(title="AI Analysis", rows=100, cols=2)
            
            # Add AI insights
            worksheet.append_row(["AI Analysis Summary", ""])
            worksheet.append_row(["", ""])
            
            summary = claude_analysis.get('summary', 'No analysis available')
            worksheet.append_row(["Summary", summary])
            worksheet.append_row(["", ""])
            
            # Add key insights
            insights = claude_analysis.get('insights', [])
            worksheet.append_row(["Key Insights", ""])
            for i, insight in enumerate(insights, 1):
                worksheet.append_row([f"Insight {i}", insight])
            
            # Add recommendations
            recommendations = claude_analysis.get('recommendations', [])
            worksheet.append_row(["", ""])
            worksheet.append_row(["Recommendations", ""])
            for i, rec in enumerate(recommendations, 1):
                worksheet.append_row([f"Recommendation {i}", rec])
            
            # Format the sheet
            worksheet.format('A1:B1', {'textFormat': {'bold': True}})
            
        except Exception as e:
            logger.error(f"Error creating AI analysis sheet: {e}")
    
    def _extract_metric(self, data: Dict, metric_name: str) -> str:
        """Extract metric value from API response"""
        try:
            if data.get('tasks'):
                for task in data['tasks']:
                    if task.get('result'):
                        return str(task['result'].get(metric_name, 'N/A'))
            return 'N/A'
        except:
            return 'N/A'
    
    def _calculate_gap_analysis(self, your_value: str, competitor_values: List[str]) -> str:
        """Calculate gap analysis between your metrics and competitors"""
        try:
            your_num = float(your_value) if your_value != 'N/A' else 0
            comp_nums = [float(comp) if comp != 'N/A' else 0 for comp in competitor_values]
            
            if your_num == 0:
                return "No data available"
            
            max_comp = max(comp_nums) if comp_nums else 0
            if max_comp > your_num:
                gap = ((max_comp - your_num) / your_num) * 100
                return f"Behind by {gap:.1f}%"
            else:
                return "Leading"
        except:
            return "Unable to calculate"
    
    def _determine_priority(self, gap_analysis: str) -> str:
        """Determine priority based on gap analysis"""
        if "Behind by" in gap_analysis:
            gap_percent = float(gap_analysis.split("Behind by ")[1].split("%")[0])
            if gap_percent > 200:
                return "CRITICAL"
            elif gap_percent > 100:
                return "HIGH"
            else:
                return "MEDIUM"
        elif "Leading" in gap_analysis:
            return "LOW"
        else:
            return "UNKNOWN"
    
    def _get_action_items(self, metric: str, gap_analysis: str) -> str:
        """Get action items based on metric and gap analysis"""
        if "Behind by" in gap_analysis:
            if "Traffic" in metric:
                return "Improve content quality, increase backlinks, optimize for featured snippets"
            elif "Keywords" in metric:
                return "Expand keyword targeting, create topic clusters, improve content depth"
            elif "Backlinks" in metric:
                return "Start link building campaign, guest posting, resource page outreach"
        return "Monitor and maintain current performance"
    
    def _calculate_keyword_priority(self, search_volume: str, cpc: str, competition: str) -> str:
        """Calculate keyword priority based on metrics"""
        try:
            volume = float(search_volume) if search_volume != 'N/A' else 0
            cpc_val = float(cpc) if cpc != 'N/A' else 0
            
            if volume > 10000 and cpc_val > 2:
                return "HIGH"
            elif volume > 1000 and cpc_val > 1:
                return "MEDIUM"
            else:
                return "LOW"
        except:
            return "UNKNOWN"
    
    def _get_content_strategy(self, keyword: str, priority: str) -> str:
        """Get content strategy for keyword"""
        if priority == "HIGH":
            return f"Create comprehensive guide targeting '{keyword}'"
        elif priority == "MEDIUM":
            return f"Create blog post or landing page for '{keyword}'"
        else:
            return f"Consider long-tail variations of '{keyword}'"
    
    def _calculate_traffic_value(self, position: str, search_volume: str, cpc: str) -> str:
        """Calculate traffic value for keyword"""
        try:
            pos = float(position) if position != 'N/A' else 0
            volume = float(search_volume) if search_volume != 'N/A' else 0
            cpc_val = float(cpc) if cpc != 'N/A' else 0
            
            if pos > 0 and pos <= 10:
                # Estimate clicks based on position
                click_rate = max(0.1, 0.3 - (pos - 1) * 0.02)
                estimated_clicks = volume * click_rate
                return f"${estimated_clicks * cpc_val:.2f}"
            return "$0.00"
        except:
            return "N/A"
    
    def _calculate_estimated_clicks(self, position: str, search_volume: str) -> str:
        """Calculate estimated monthly clicks"""
        try:
            pos = float(position) if position != 'N/A' else 0
            volume = float(search_volume) if search_volume != 'N/A' else 0
            
            if pos > 0 and pos <= 10:
                click_rate = max(0.1, 0.3 - (pos - 1) * 0.02)
                return f"{int(volume * click_rate)}"
            return "0"
        except:
            return "N/A"
    
    def _get_keyword_action(self, position: str, search_volume: str) -> str:
        """Get action required for keyword"""
        try:
            pos = float(position) if position != 'N/A' else 0
            volume = float(search_volume) if search_volume != 'N/A' else 0
            
            if pos > 0 and pos <= 3:
                return "Maintain position"
            elif pos > 3 and pos <= 10:
                return "Optimize to improve ranking"
            elif pos > 10 and pos <= 20:
                return "Focus on improving to page 1"
            else:
                return "Not ranking - create content"
        except:
            return "Unknown"
    
    def _get_keyword_priority_level(self, position: str, search_volume: str) -> str:
        """Get priority level for keyword"""
        try:
            pos = float(position) if position != 'N/A' else 0
            volume = float(search_volume) if search_volume != 'N/A' else 0
            
            if pos > 0 and pos <= 10 and volume > 1000:
                return "HIGH"
            elif pos > 0 and pos <= 20 and volume > 100:
                return "MEDIUM"
            else:
                return "LOW"
        except:
            return "UNKNOWN"
    
    def _extract_serp_features(self, serp_info: Dict) -> str:
        """Extract SERP features from analysis"""
        features = []
        # This would need to be implemented based on actual SERP data structure
        return ", ".join(features) if features else "Standard results"
    
    def _check_featured_snippet(self, serp_info: Dict) -> str:
        """Check if featured snippet is present"""
        # This would need to be implemented based on actual SERP data structure
        return "No"
    
    def _get_your_position(self, serp_info: Dict) -> str:
        """Get your position in SERP"""
        # This would need to be implemented based on actual SERP data structure
        return "N/A"
    
    def _assess_serp_opportunity(self, features: str, your_position: str) -> str:
        """Assess SERP opportunity"""
        if your_position == "N/A":
            return "Not ranking"
        elif your_position in ["1", "2", "3"]:
            return "Maintain position"
        else:
            return "Improve ranking"
    
    def _get_serp_action_items(self, features: str, opportunity: str) -> str:
        """Get action items for SERP"""
        if "Featured" in features:
            return "Optimize for featured snippet"
        elif opportunity == "Improve ranking":
            return "Optimize content and build authority"
        else:
            return "Monitor performance"
