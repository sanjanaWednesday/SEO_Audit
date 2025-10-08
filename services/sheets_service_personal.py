"""
Google Sheets Service - Personal OAuth Version
Uses personal Google account OAuth instead of service account
This will use your personal Drive storage (15GB) instead of service account quotas
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import gspread
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsServicePersonal:
    def __init__(self):
        """Initialize with personal OAuth credentials"""
        try:
            # Try to use existing OAuth files first
            if os.path.exists('credentials.json') and os.path.exists('token.json'):
                print("🔐 Using existing OAuth credentials")
                self.client = gspread.oauth(
                    credentials_filename="credentials.json",
                    authorized_user_filename="token.json"
                )
            else:
                # Fallback to service account if OAuth not available
                print("⚠️ OAuth files not found, falling back to service account")
                credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'pacific-destiny-473610-d0-4afd76cc0192.json')
                
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(f"Google Sheets credentials file not found: {credentials_path}")
                
                from google.oauth2.service_account import Credentials
                scope = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                
                credentials = Credentials.from_service_account_file(credentials_path, scopes=scope)
                self.client = gspread.authorize(credentials)
                
        except Exception as e:
            print(f"❌ Failed to initialize Google Sheets client: {e}")
            raise

    async def create_seo_report(self, audit_results: Dict, claude_analysis: Dict, target_domain: str, user_email: str = None) -> str:
        """Create comprehensive SEO audit report in Google Sheets"""
        try:
            # Create new spreadsheet
            spreadsheet = self.client.create(f"SEO Audit Report - {target_domain} - {datetime.now().strftime('%Y-%m-%d')}")
            
            # Share with user email if provided
            if user_email:
                try:
                    spreadsheet.share(user_email, perm_type='user', role='writer', notify=True, 
                                    email_message=f"Your SEO Audit Report for {target_domain} is ready!")
                    logger.info(f"Shared spreadsheet with user email: {user_email}")
                except Exception as e:
                    logger.warning(f"Failed to share with user email {user_email}: {e}")
            
            # Share with anyone with the link
            spreadsheet.share('', perm_type='anyone', role='reader')
            
            # Create all report sheets
            print("\n📊 Creating Google Sheets report...")
            await self._create_domain_overview_sheet(spreadsheet, audit_results, target_domain)
            await self._create_content_gap_sheet(spreadsheet, audit_results)
            await self._create_top_keywords_sheet(spreadsheet, audit_results, target_domain)
            await self._create_backlink_gap_sheet(spreadsheet, audit_results, target_domain)
            await self._create_serp_features_sheet(spreadsheet, audit_results)
            await self._create_ai_analysis_sheet(spreadsheet, claude_analysis)
            
            print("✅ Google Sheets report created successfully!")
            return spreadsheet.url
            
        except Exception as e:
            logger.error(f"Failed to create SEO report: {e}")
            raise

    # Include all the existing sheet creation methods from the original service
    # (I'll copy them from the original file)
    async def _create_domain_overview_sheet(self, spreadsheet, audit_results: Dict, target_domain: str):
        """Create domain overview sheet with key metrics"""
        try:
            # Create or get the sheet
            try:
                worksheet = spreadsheet.worksheet("Domain Overview")
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title="Domain Overview", rows=100, cols=10)
            
            # Clear existing data
            worksheet.clear()
            
            # Headers
            headers = [
                "Metric", "Value", "Source", "Date"
            ]
            worksheet.update('A1:D1', [headers])
            
            # Style headers
            worksheet.format('A1:D1', {
                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
            })
            
            # Extract domain metrics
            domain_metrics = audit_results.get('phases', {}).get('domain_metrics', {})
            if domain_metrics and not domain_metrics.get('error'):
                tasks = domain_metrics.get('tasks', [])
                if tasks and tasks[0].get('result') and tasks[0]['result'][0].get('items'):
                    item = tasks[0]['result'][0]['items'][0]
                    metrics = item.get('metrics', {})
                    
                    # Add domain metrics
                    row = 2
                    domain_data = [
                        ["Domain", target_domain, "Audit Target", datetime.now().strftime('%Y-%m-%d')],
                        ["Domain Rank", metrics.get('rank', 'N/A'), "DataForSEO", datetime.now().strftime('%Y-%m-%d')],
                        ["Organic Keywords", metrics.get('ranked_keywords', 'N/A'), "DataForSEO", datetime.now().strftime('%Y-%m-%d')],
                        ["Organic Traffic", metrics.get('ranked_serp_elements', 'N/A'), "DataForSEO", datetime.now().strftime('%Y-%m-%d')],
                    ]
                    
                    worksheet.update(f'A{row}:D{row + len(domain_data) - 1}', domain_data)
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, 3)
            
        except Exception as e:
            logger.error(f"Failed to create domain overview sheet: {e}")

    async def _create_content_gap_sheet(self, spreadsheet, audit_results: Dict):
        """Create content gap analysis sheet"""
        try:
            # Create or get the sheet
            try:
                worksheet = spreadsheet.worksheet("Content Gap Analysis")
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title="Content Gap Analysis", rows=1000, cols=8)
            
            worksheet.clear()
            
            headers = [
                "Keyword", "Search Volume", "Competitor", "Difficulty", "Opportunity Score", "Current Rank", "Potential Rank", "Notes"
            ]
            worksheet.update('A1:H1', [headers])
            
            # Style headers
            worksheet.format('A1:H1', {
                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
            })
            
            # Extract content gap data from opportunities
            opportunities = audit_results.get('phases', {}).get('opportunities', {})
            row = 2
            
            for opp_key, opp_data in opportunities.items():
                if 'intersection' in opp_data and not opp_data['intersection'].get('error'):
                    competitor = opp_data.get('competitor', 'Unknown')
                    tasks = opp_data['intersection'].get('tasks', [])
                    
                    if tasks and tasks[0].get('result') and tasks[0]['result'][0].get('items'):
                        for item in tasks[0]['result'][0]['items'][:50]:  # Limit to top 50
                            keyword_data = item.get('keyword_data', {})
                            keyword = keyword_data.get('keyword', '')
                            
                            if keyword:
                                gap_data = [
                                    keyword,
                                    keyword_data.get('search_volume', 'N/A'),
                                    competitor,
                                    keyword_data.get('keyword_difficulty', 'N/A'),
                                    'High' if keyword_data.get('search_volume', 0) > 1000 else 'Medium',
                                    'N/A',  # Current rank
                                    'TBD',  # Potential rank
                                    f"Gap vs {competitor}"
                                ]
                                worksheet.update(f'A{row}:H{row}', [gap_data])
                                row += 1
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, 7)
            
        except Exception as e:
            logger.error(f"Failed to create content gap sheet: {e}")

    async def _create_top_keywords_sheet(self, spreadsheet, audit_results: Dict, target_domain: str):
        """Create top keywords sheet"""
        try:
            try:
                worksheet = spreadsheet.worksheet("Top Keywords")
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title="Top Keywords", rows=1000, cols=6)
            
            worksheet.clear()
            
            headers = [
                "Keyword", "Current Rank", "Search Volume", "Traffic Value", "Difficulty", "Trend"
            ]
            worksheet.update('A1:F1', [headers])
            
            # Style headers
            worksheet.format('A1:F1', {
                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
            })
            
            # Extract ranked keywords
            ranked_keywords = audit_results.get('phases', {}).get('ranked_keywords', {})
            row = 2
            
            if ranked_keywords and not ranked_keywords.get('error'):
                tasks = ranked_keywords.get('tasks', [])
                if tasks and tasks[0].get('result') and tasks[0]['result'][0].get('items'):
                    for item in tasks[0]['result'][0]['items'][:100]:  # Top 100 keywords
                        keyword_data = item.get('keyword_data', {})
                        keyword = keyword_data.get('keyword', '')
                        
                        if keyword:
                            serp_item = item.get('serp_item', {})
                            keyword_row = [
                                keyword,
                                serp_item.get('rank_group', 'N/A'),
                                keyword_data.get('search_volume', 'N/A'),
                                keyword_data.get('cpc', 'N/A'),
                                keyword_data.get('keyword_difficulty', 'N/A'),
                                'Stable'
                            ]
                            worksheet.update(f'A{row}:F{row}', [keyword_row])
                            row += 1
            
            worksheet.columns_auto_resize(0, 5)
            
        except Exception as e:
            logger.error(f"Failed to create top keywords sheet: {e}")

    async def _create_backlink_gap_sheet(self, spreadsheet, audit_results: Dict, target_domain: str):
        """Create backlink gap analysis sheet"""
        try:
            try:
                worksheet = spreadsheet.worksheet("Backlink Analysis")
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title="Backlink Analysis", rows=500, cols=6)
            
            worksheet.clear()
            
            headers = [
                "Domain", "Backlinks", "Referring Domains", "Domain Rating", "Organic Traffic", "Status"
            ]
            worksheet.update('A1:F1', [headers])
            
            # Style headers
            worksheet.format('A1:F1', {
                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
            })
            
            # Extract backlink data
            row = 2
            
            # Your site
            backlinks_summary = audit_results.get('phases', {}).get('backlinks_summary', {})
            if backlinks_summary and not backlinks_summary.get('error'):
                tasks = backlinks_summary.get('tasks', [])
                if tasks and tasks[0].get('result') and tasks[0]['result'][0].get('items'):
                    item = tasks[0]['result'][0]['items'][0]
                    summary = item.get('summary', {})
                    
                    your_site_data = [
                        target_domain,
                        summary.get('backlinks', 'N/A'),
                        summary.get('referring_domains', 'N/A'),
                        summary.get('domain_rating', 'N/A'),
                        summary.get('organic_traffic', 'N/A'),
                        'Your Site'
                    ]
                    worksheet.update(f'A{row}:F{row}', [your_site_data])
                    row += 1
            
            # Competitors
            competitor_analysis = audit_results.get('phases', {}).get('competitor_analysis', {})
            for comp_key, comp_data in competitor_analysis.items():
                competitor_domain = comp_data.get('domain', 'Unknown')
                comp_backlinks = comp_data.get('data', {}).get('backlinks_summary', {})
                
                if comp_backlinks and not comp_backlinks.get('error'):
                    tasks = comp_backlinks.get('tasks', [])
                    if tasks and tasks[0].get('result') and tasks[0]['result'][0].get('items'):
                        item = tasks[0]['result'][0]['items'][0]
                        summary = item.get('summary', {})
                        
                        comp_data_row = [
                            competitor_domain,
                            summary.get('backlinks', 'N/A'),
                            summary.get('referring_domains', 'N/A'),
                            summary.get('domain_rating', 'N/A'),
                            summary.get('organic_traffic', 'N/A'),
                            'Competitor'
                        ]
                        worksheet.update(f'A{row}:F{row}', [comp_data_row])
                        row += 1
            
            worksheet.columns_auto_resize(0, 5)
            
        except Exception as e:
            logger.error(f"Failed to create backlink analysis sheet: {e}")

    async def _create_serp_features_sheet(self, spreadsheet, audit_results: Dict):
        """Create SERP features analysis sheet"""
        try:
            try:
                worksheet = spreadsheet.worksheet("SERP Features")
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title="SERP Features", rows=500, cols=8)
            
            worksheet.clear()
            
            headers = [
                "Keyword", "Featured Snippet", "People Also Ask", "Related Searches", "Images", "Videos", "News", "Shopping"
            ]
            worksheet.update('A1:H1', [headers])
            
            # Style headers
            worksheet.format('A1:H1', {
                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
            })
            
            # Extract SERP features from SERP analysis
            serp_analysis = audit_results.get('phases', {}).get('serp_analysis', {})
            row = 2
            
            for serp_key, serp_data in serp_analysis.items():
                keyword = serp_data.get('keyword', '')
                serp_result = serp_data.get('serp_data', {})
                
                if serp_result and not serp_result.get('error'):
                    tasks = serp_result.get('tasks', [])
                    if tasks and tasks[0].get('result') and tasks[0]['result'][0].get('items'):
                        item = tasks[0]['result'][0]['items'][0]
                        serp_features = item.get('serp_features', [])
                        
                        # Check for specific features
                        features = {
                            'featured_snippet': 'No',
                            'people_also_ask': 'No',
                            'related_searches': 'No',
                            'images': 'No',
                            'videos': 'No',
                            'news': 'No',
                            'shopping': 'No'
                        }
                        
                        for feature in serp_features:
                            feature_type = feature.get('feature_type', '').lower()
                            if 'snippet' in feature_type:
                                features['featured_snippet'] = 'Yes'
                            elif 'ask' in feature_type:
                                features['people_also_ask'] = 'Yes'
                            elif 'related' in feature_type:
                                features['related_searches'] = 'Yes'
                            elif 'image' in feature_type:
                                features['images'] = 'Yes'
                            elif 'video' in feature_type:
                                features['videos'] = 'Yes'
                            elif 'news' in feature_type:
                                features['news'] = 'Yes'
                            elif 'shopping' in feature_type:
                                features['shopping'] = 'Yes'
                        
                        serp_row = [
                            keyword,
                            features['featured_snippet'],
                            features['people_also_ask'],
                            features['related_searches'],
                            features['images'],
                            features['videos'],
                            features['news'],
                            features['shopping']
                        ]
                        worksheet.update(f'A{row}:H{row}', [serp_row])
                        row += 1
            
            worksheet.columns_auto_resize(0, 7)
            
        except Exception as e:
            logger.error(f"Failed to create SERP features sheet: {e}")

    async def _create_ai_analysis_sheet(self, spreadsheet, claude_analysis: Dict):
        """Create AI analysis sheet"""
        try:
            try:
                worksheet = spreadsheet.worksheet("AI Analysis")
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title="AI Analysis", rows=100, cols=2)
            
            worksheet.clear()
            
            headers = ["Analysis Type", "Insights"]
            worksheet.update('A1:B1', [headers])
            
            # Style headers
            worksheet.format('A1:B1', {
                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
            })
            
            if claude_analysis:
                row = 2
                for analysis_type, insights in claude_analysis.items():
                    worksheet.update(f'A{row}:B{row}', [[analysis_type, str(insights)]])
                    row += 1
            else:
                worksheet.update('A2:B2', [['No AI Analysis', 'Claude analysis not available']])
            
            worksheet.columns_auto_resize(0, 1)
            
        except Exception as e:
            logger.error(f"Failed to create AI analysis sheet: {e}")
