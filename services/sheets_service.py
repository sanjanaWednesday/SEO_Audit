"""
Google Sheets Service - COMPLETE VERSION WITH ON-PAGE INTEGRATION
Handles creating and populating SEO audit reports in Google Sheets
Each API has its own extraction function to handle unique response structures
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import gspread
from google.oauth2.service_account import Credentials
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        # Using Service Account authentication
        credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'pacific-destiny-473610-d0-4afd76cc0192.json')
        
        # Check if credentials file exists
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Google Sheets credentials file not found: {credentials_path}")
        
        # Set up service account credentials
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(credentials_path, scopes=scope)
        self.client = gspread.authorize(credentials)

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
            
            # Add on-page analysis sheets if available
            onpage_data = audit_results.get('onpage_data', {})
            
            if onpage_data:
                print("  → Processing On-Page data...")
                
                # Extract and create On-Page Pages sheet
                pages_response = onpage_data.get('pages', {})
                if pages_response:
                    pages_data = self.extract_onpage_pages_data(pages_response)
                    if pages_data:
                        await self._create_onpage_pages_sheet(spreadsheet, pages_data)
                
                # Extract and create Technical Issues sheet
                technical_response = onpage_data.get('technical_issues', {})
                if technical_response:
                    issues_data = self.extract_technical_issues_data(technical_response)
                    if issues_data:
                        await self._create_technical_issues_sheet(spreadsheet, issues_data)
                        
                        # Create aggregated summary sheet
                        await self._create_issues_summary_sheet(spreadsheet, issues_data, pages_data if 'pages_data' in locals() else [])
            
            # Delete default "Sheet1"
            try:
                default_sheet = spreadsheet.worksheet("Sheet1")
                spreadsheet.del_worksheet(default_sheet)
            except:
                pass
            
            print(f"\n✅ Report created successfully!")
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
            
        except Exception as e:
            logger.error(f"Failed to create SEO report: {e}")
            raise

    # ============================================================================
    # ON-PAGE DATA EXTRACTION METHODS
    # ============================================================================

    def extract_onpage_pages_data(self, pages_response: Dict) -> List[Dict]:
        """
        Extract page-level data from on_page/pages API
        
        Returns: List of page dictionaries with key metrics
        """
        pages_data = []
        
        try:
            tasks = pages_response.get('tasks', [])
            if not tasks or tasks[0].get('status_code') != 20000:
                logger.warning("Invalid tasks data in on_page/pages response")
                return []
            
            result = tasks[0].get('result', [])
            if not result or not result[0].get('items'):
                logger.warning("No items found in on_page/pages result")
                return []
            
            items = result[0]['items']
            logger.info(f"Processing {len(items)} pages from on_page/pages API")
            
            for item in items:
                # Only process HTML pages
                if item.get('resource_type') != 'html':
                    continue
                
                meta = item.get('meta', {})
                content = meta.get('content', {})
                checks = item.get('checks', {})
                page_timing = item.get('page_timing', {})
                htags = meta.get('htags', {})
                
                page_data = {
                    # Basic Info
                    'url': item.get('url', ''),
                    'status_code': item.get('status_code', ''),
                    'title': meta.get('title', ''),
                    'meta_description': meta.get('description', ''),
                    'canonical': meta.get('canonical', ''),
                    
                    # SEO Score
                    'onpage_score': round(item.get('onpage_score', 0), 2),
                    
                    # Content Metrics
                    'word_count': content.get('plain_text_word_count', 0),
                    'title_length': meta.get('title_length', 0),
                    'description_length': meta.get('description_length', 0),
                    'h1_count': len(htags.get('h1', [])),
                    'h2_count': len(htags.get('h2', [])),
                    'h3_count': len(htags.get('h3', [])),
                    
                    # Performance (Core Web Vitals)
                    'load_time': page_timing.get('time_to_interactive', 0),
                    'dom_complete': page_timing.get('dom_complete', 0),
                    'lcp': page_timing.get('largest_contentful_paint', 0),
                    'cls': item.get('cumulative_layout_shift', 0),
                    'fid': page_timing.get('first_input_delay', 0),
                    
                    # Links & Images
                    'internal_links': meta.get('internal_links_count', 0),
                    'external_links': meta.get('external_links_count', 0),
                    'images_count': meta.get('images_count', 0),
                    'broken_links': item.get('broken_links', False),
                    
                    # Technical Issues
                    'is_broken': checks.get('is_broken', False),
                    'is_redirect': checks.get('is_redirect', False),
                    'has_4xx': checks.get('is_4xx_code', False),
                    'has_5xx': checks.get('is_5xx_code', False),
                    'no_h1': checks.get('no_h1_tag', False),
                    'no_title': checks.get('no_title', False),
                    'no_description': checks.get('no_description', False),
                    'duplicate_title': item.get('duplicate_title', False),
                    'duplicate_description': item.get('duplicate_description', False),
                    'is_orphan': checks.get('is_orphan_page', False),
                    'has_redirect_chain': checks.get('redirect_chain', False),
                    'high_loading_time': checks.get('high_loading_time', False),
                    
                    # Mobile & Usability
                    'is_https': checks.get('is_https', False),
                    'is_http': checks.get('is_http', False),
                    'page_size_bytes': item.get('size', 0),
                    'large_page': checks.get('large_page_size', False),
                    'has_meta_viewport': item.get('meta', {}).get('viewport') is not None,
                    
                    # Content Quality
                    'low_content_rate': checks.get('low_content_rate', False),
                    'high_content_rate': checks.get('high_content_rate', False),
                    'readability_score': content.get('flesch_kincaid_readability_index', 0),
                    
                    # Additional checks
                    'title_too_long': checks.get('title_too_long', False),
                    'title_too_short': checks.get('title_too_short', False),
                    'no_favicon': checks.get('no_favicon', False),
                    'no_image_alt': checks.get('no_image_alt', False),
                }
                
                pages_data.append(page_data)
            
            logger.info(f"Successfully extracted {len(pages_data)} HTML pages")
            return pages_data
            
        except Exception as e:
            logger.error(f"Failed to extract on-page pages data: {e}")
            return []

    def extract_technical_issues_data(self, technical_issues_response: Dict) -> List[Dict]:
        """
        Extract technical SEO issues from on_page/pages data by analyzing checks
        
        Returns: List of technical issue dictionaries
        """
        issues_data = []
        
        try:
            tasks = technical_issues_response.get('tasks', [])
            if not tasks or tasks[0].get('status_code') != 20000:
                logger.warning("Invalid tasks data in technical issues response")
                return []
            
            result = tasks[0].get('result', [])
            if not result or not result[0].get('items'):
                logger.warning("No items found in technical issues result")
                return []
            
            items = result[0]['items']
            logger.info(f"Processing {len(items)} pages for technical issues")
            
            # Process each page and extract issues
            for item in items:
                if item.get('resource_type') != 'html':
                    continue
                
                url = item.get('url', '')
                checks = item.get('checks', {})
                
                # Define issue checks and their properties
                issue_checks = [
                    ('is_broken', 'Broken Page', 'Page returns error status code'),
                    ('is_4xx_code', '4XX Error', 'Page returns 4XX client error'),
                    ('is_5xx_code', '5XX Error', 'Page returns 5XX server error'),
                    ('no_h1_tag', 'Missing H1', 'Page missing H1 heading tag'),
                    ('no_title', 'Missing Title', 'Page missing title tag'),
                    ('no_description', 'Missing Meta Description', 'Missing meta description'),
                    ('duplicate_title', 'Duplicate Title', 'Title duplicated across pages'),
                    ('duplicate_description', 'Duplicate Description', 'Meta description duplicated'),
                    ('is_redirect', 'Redirect', 'Page redirects to another URL'),
                    ('broken_links', 'Broken Links', 'Page contains broken links'),
                    ('high_loading_time', 'Slow Page Load', 'Load time exceeds 3 seconds'),
                    ('large_page_size', 'Large Page Size', 'Page size exceeds 1MB'),
                    ('low_content_rate', 'Low Content Rate', 'Low text-to-HTML ratio'),
                    ('is_orphan_page', 'Orphan Page', 'No internal links to this page'),
                    ('redirect_chain', 'Redirect Chain', 'Multiple redirects'),
                    ('title_too_long', 'Title Too Long', 'Title exceeds 65 characters'),
                    ('title_too_short', 'Title Too Short', 'Title less than 30 characters'),
                    ('no_favicon', 'Missing Favicon', 'Site missing favicon'),
                    ('no_image_alt', 'Missing Image Alt Tags', 'Images without alt text'),
                    ('is_http', 'Not HTTPS', 'Page not using secure HTTPS protocol'),
                ]
                
                # Check each issue type
                for check_key, issue_name, description in issue_checks:
                    if checks.get(check_key, False) or item.get(check_key, False):
                        issue_data = {
                            'page_url': url,
                            'issue_type': issue_name,
                            'severity': self._calculate_issue_severity(check_key),
                            'issue_name': issue_name,
                            'description': description,
                            'status_code': item.get('status_code', ''),
                            'check_name': check_key,
                            'recommendation': self._get_issue_recommendation(check_key),
                            'priority_score': self._calculate_issue_priority(check_key),
                        }
                        
                        issues_data.append(issue_data)
            
            logger.info(f"Successfully extracted {len(issues_data)} technical issues")
            return issues_data
            
        except Exception as e:
            logger.error(f"Failed to extract technical issues data: {e}")
            return []

    def _calculate_issue_severity(self, check_name: str) -> str:
        """Determine issue severity based on check type"""
        # Critical issues
        critical_checks = ['is_broken', 'is_4xx_code', 'is_5xx_code', 'no_h1_tag', 
                          'no_title']
        
        # High priority issues
        high_checks = ['no_description', 'duplicate_title', 'duplicate_description',
                      'broken_links', 'high_loading_time', 'is_orphan_page', 'is_http']
        
        # Medium priority issues
        medium_checks = ['large_page_size', 'low_content_rate', 'redirect_chain',
                        'title_too_long', 'title_too_short', 'no_favicon']
        
        # Low priority issues
        low_checks = ['no_image_alt', 'is_redirect']
        
        if check_name in critical_checks:
            return 'Critical'
        elif check_name in high_checks:
            return 'High'
        elif check_name in medium_checks:
            return 'Medium'
        else:
            return 'Low'

    def _get_issue_recommendation(self, check_name: str) -> str:
        """Generate actionable recommendation"""
        recommendations = {
            'is_broken': 'Fix or redirect broken page; ensure proper 200 status code',
            'is_4xx_code': 'Fix broken URL or implement 301 redirect to relevant page',
            'is_5xx_code': 'Fix server error; check hosting and application logs',
            'no_h1_tag': 'Add descriptive H1 tag with target keyword',
            'no_title': 'Add unique, keyword-rich title tag (50-60 characters)',
            'no_description': 'Write compelling meta description (150-160 characters)',
            'duplicate_title': 'Create unique title for each page',
            'duplicate_description': 'Write unique meta descriptions for each page',
            'is_redirect': 'Update internal links to point directly to final destination',
            'broken_links': 'Fix or remove broken links; update to valid URLs',
            'high_loading_time': 'Optimize images, leverage caching, minimize CSS/JS',
            'large_page_size': 'Optimize images, minify CSS/JS, enable compression',
            'low_content_rate': 'Add substantive content; target 300+ words minimum',
            'is_orphan_page': 'Add internal links from relevant pages',
            'redirect_chain': 'Reduce redirect chain to single redirect',
            'title_too_long': 'Shorten title to 50-60 characters',
            'title_too_short': 'Expand title to at least 30 characters',
            'no_favicon': 'Add favicon.ico to improve branding',
            'no_image_alt': 'Add descriptive alt text to all images',
            'is_http': 'Migrate to HTTPS with SSL certificate',
        }
        
        return recommendations.get(check_name, 'Review and resolve technical issue')

    def _calculate_issue_priority(self, check_name: str) -> int:
        """Calculate priority score (1-10) for fixing issue"""
        severity = self._calculate_issue_severity(check_name)
        
        priority_map = {
            'Critical': 10,
            'High': 7,
            'Medium': 4,
            'Low': 2
        }
        
        return priority_map.get(severity, 5)

    # ============================================================================
    # DOMAIN OVERVIEW & COMPETITIVE DATA EXTRACTION
    # ============================================================================

    def _extract_domain_overview_data(self, domain_metrics: Dict) -> Dict[str, Any]:
        """Extract domain overview metrics from domain_rank_overview API"""
        try:
            if not domain_metrics.get('tasks'):
                return {'error': 'No tasks in response'}
            
            task = domain_metrics['tasks'][0]
            if task.get('status_code') != 20000:
                return {'error': f"API error: {task.get('status_message', 'Unknown')}"}
            
            result = task.get('result', [])
            if not result or not result[0].get('items'):
                return {'error': 'No items in result'}
            
            item = result[0]['items'][0]
            metrics = item.get('metrics', {})
            organic = metrics.get('organic', {})
            
            return {
                'organic_etv': organic.get('etv', 0),
                'organic_count': organic.get('count', 0),
                'organic_pos_1': organic.get('pos_1', 0),
                'organic_pos_2_3': organic.get('pos_2_3', 0),
                'organic_pos_4_10': organic.get('pos_4_10', 0),
                'organic_pos_11_20': organic.get('pos_11_20', 0),
                'organic_pos_21_30': organic.get('pos_21_30', 0),
            }
        except Exception as e:
            logger.error(f"Error extracting domain overview: {e}")
            return {'error': str(e)}

    def _extract_ranked_keywords_summary(self, ranked_keywords: Dict) -> Dict[str, Any]:
        """Extract summary from ranked_keywords API"""
        try:
            if not ranked_keywords.get('tasks'):
                return {'total_keywords': 0, 'keywords': []}
            
            task = ranked_keywords['tasks'][0]
            if task.get('status_code') != 20000:
                return {'total_keywords': 0, 'keywords': []}
            
            result = task.get('result', [])
            if not result or not result[0].get('items'):
                return {'total_keywords': 0, 'keywords': []}
            
            items = result[0]['items']
            
            pos_1_3 = sum(1 for item in items if self._get_keyword_position(item) <= 3)
            pos_4_10 = sum(1 for item in items if 4 <= self._get_keyword_position(item) <= 10)
            pos_11_20 = sum(1 for item in items if 11 <= self._get_keyword_position(item) <= 20)
            
            return {
                'total_keywords': len(items),
                'pos_1_3': pos_1_3,
                'pos_4_10': pos_4_10,
                'pos_11_20': pos_11_20,
                'keywords': items[:10]
            }
        except Exception as e:
            logger.error(f"Error extracting ranked keywords summary: {e}")
            return {'total_keywords': 0, 'keywords': []}

    def _extract_ranked_keywords_detailed(self, ranked_keywords: Dict, limit: int = 10) -> List[Dict]:
        """Extract detailed keyword data from ranked_keywords API"""
        try:
            if not ranked_keywords.get('tasks'):
                return []
            
            task = ranked_keywords['tasks'][0]
            if task.get('status_code') != 20000:
                return []
            
            result = task.get('result', [])
            if not result or not result[0].get('items'):
                return []
            
            items = result[0]['items']
            keywords_data = []
            
            for item in items[:limit]:
                keyword_info = item.get('keyword_data', {})
                keyword = keyword_info.get('keyword', 'N/A')
                
                position = self._get_keyword_position(item)
                search_volume = keyword_info.get('keyword_info', {}).get('search_volume', 0)
                cpc = keyword_info.get('keyword_info', {}).get('cpc', 0)
                competition = keyword_info.get('keyword_info', {}).get('competition', 0)
                
                estimated_traffic = self._calculate_estimated_clicks(position, search_volume)
                traffic_value = self._calculate_traffic_value(position, search_volume, cpc)
                
                keywords_data.append({
                    'keyword': keyword,
                    'position': position,
                    'search_volume': search_volume,
                    'cpc': cpc,
                    'competition': competition,
                    'estimated_traffic': estimated_traffic,
                    'traffic_value': traffic_value
                })
            
            return keywords_data
            
        except Exception as e:
            logger.error(f"Error extracting ranked keywords detailed: {e}")
            return []

    def _extract_backlinks_summary(self, backlinks: Dict) -> Dict[str, Any]:
        """Extract backlinks summary from backlinks/summary API"""
        try:
            if not backlinks.get('tasks'):
                return {'total_backlinks': 0, 'referring_domains': 0}
            
            task = backlinks['tasks'][0]
            if task.get('status_code') != 20000:
                return {'total_backlinks': 0, 'referring_domains': 0}
            
            result = task.get('result', [])
            if not result:
                return {'total_backlinks': 0, 'referring_domains': 0}
            
            summary = result[0]
            
            return {
                'total_backlinks': summary.get('backlinks', 0),
                'referring_domains': summary.get('referring_domains', 0),
                'referring_domains_nofollow': summary.get('referring_domains_nofollow', 0),
                'referring_main_domains': summary.get('referring_main_domains', 0),
                'referring_ips': summary.get('referring_ips', 0),
                'rank': summary.get('rank', 0)
            }
        except Exception as e:
            logger.error(f"Error extracting backlinks summary: {e}")
            return {'total_backlinks': 0, 'referring_domains': 0}

    def _extract_intersection_keywords(self, intersection: Dict, competitor_domain: str, limit: int = 10) -> List[Dict]:
        """Extract keywords from domain_intersection API (content gaps)"""
        try:
            if not intersection.get('tasks'):
                return []
            
            task = intersection['tasks'][0]
            if task.get('status_code') != 20000:
                return []
            
            result = task.get('result', [])
            if not result or not result[0].get('items'):
                return []
            
            items = result[0]['items']
            gap_keywords = []
            
            for item in items[:limit]:
                keyword_data = item.get('keyword_data', {})
                keyword_info = keyword_data.get('keyword_info', {})
                
                intersection_result = item.get('intersection_result', {})
                target2_info = intersection_result.get(competitor_domain, {})
                
                serp_info = target2_info.get('ranked_serp_element', {}).get('serp_item', {})
                competitor_position = serp_info.get('rank_absolute', 'N/A')
                
                gap_keywords.append({
                    'keyword': keyword_data.get('keyword', 'N/A'),
                    'search_volume': keyword_info.get('search_volume', 0),
                    'cpc': keyword_info.get('cpc', 0),
                    'competition': keyword_info.get('competition', 0),
                    'competitor': competitor_domain,
                    'competitor_position': competitor_position,
                    'priority_score': self._calculate_opportunity_priority(
                        keyword_info.get('search_volume', 0),
                        keyword_info.get('cpc', 0),
                        keyword_info.get('competition', 0),
                        competitor_position
                    )
                })
            
            return gap_keywords
            
        except Exception as e:
            logger.error(f"Error extracting intersection keywords: {e}")
            return []

    def _extract_serp_features(self, serp_data: Dict, keyword: str) -> Dict[str, Any]:
        """Extract SERP features from serp/google/organic API"""
        try:
            if not serp_data.get('tasks'):
                return {'keyword': keyword, 'features': [], 'your_position': 'N/A'}
            
            task = serp_data['tasks'][0]
            if task.get('status_code') != 20000:
                return {'keyword': keyword, 'features': [], 'your_position': 'N/A'}
            
            result = task.get('result', [])
            if not result or not result[0].get('items'):
                return {'keyword': keyword, 'features': [], 'your_position': 'N/A'}
            
            items = result[0]['items']
            
            features = set()
            featured_snippet_owner = None
            
            for item in items:
                item_type = item.get('type', '')
                
                if item_type == 'featured_snippet':
                    features.add('Featured Snippet')
                    featured_snippet_owner = item.get('domain', 'Unknown')
                elif item_type == 'people_also_ask':
                    features.add('People Also Ask')
                elif item_type == 'knowledge_graph':
                    features.add('Knowledge Graph')
                elif item_type == 'video':
                    features.add('Video Results')
                elif item_type == 'images':
                    features.add('Image Pack')
                elif item_type == 'local_pack':
                    features.add('Local Pack')
                elif item_type == 'shopping':
                    features.add('Shopping Results')
            
            return {
                'keyword': keyword,
                'features': list(features),
                'featured_snippet_owner': featured_snippet_owner,
                'total_results': len(items),
                'your_position': 'N/A'
            }
            
        except Exception as e:
            logger.error(f"Error extracting SERP features: {e}")
            return {'keyword': keyword, 'features': [], 'your_position': 'N/A'}

    # ============================================================================
    # HELPER FUNCTIONS
    # ============================================================================

    def _get_keyword_position(self, keyword_item: Dict) -> int:
        """Extract ranking position from ranked_keywords API item"""
        try:
            ranked_element = keyword_item.get('ranked_serp_element', {})
            serp_item = ranked_element.get('serp_item', {})
            position = serp_item.get('rank_absolute', 999)
            return int(position) if position != 'N/A' else 999
        except:
            return 999

    def _calculate_estimated_clicks(self, position: int, search_volume: int) -> int:
        """Calculate estimated monthly clicks based on position and search volume"""
        try:
            if position == 999 or search_volume == 0:
                return 0
            
            ctr_map = {
                1: 0.316, 2: 0.158, 3: 0.106, 4: 0.082, 5: 0.067,
                6: 0.049, 7: 0.039, 8: 0.032, 9: 0.028, 10: 0.025
            }
            
            if position <= 10:
                ctr = ctr_map.get(position, 0.02)
            elif position <= 20:
                ctr = 0.01
            else:
                ctr = 0.005
            
            return int(search_volume * ctr)
        except:
            return 0

    def _calculate_traffic_value(self, position: int, search_volume: int, cpc: float) -> float:
        """Calculate estimated monthly traffic value"""
        try:
            clicks = self._calculate_estimated_clicks(position, search_volume)
            return round(clicks * float(cpc), 2)
        except:
            return 0.0

    def _calculate_opportunity_priority(self, search_volume: int, cpc: float, competition: float, competitor_position: int) -> str:
        """Calculate priority score for content gap opportunities"""
        try:
            score = 0
            
            if search_volume > 5000:
                score += 3
            elif search_volume > 1000:
                score += 2
            elif search_volume > 100:
                score += 1
            
            if cpc > 5:
                score += 3
            elif cpc > 2:
                score += 2
            elif cpc > 1:
                score += 1
            
            if competition < 0.3:
                score += 2
            elif competition < 0.6:
                score += 1
            
            if competitor_position != 'N/A' and int(competitor_position) <= 10:
                score += 2
            
            if score >= 8:
                return "HIGH"
            elif score >= 5:
                return "MEDIUM"
            else:
                return "LOW"
        except:
            return "UNKNOWN"

    def _calculate_gap_percentage(self, your_value: float, competitor_values: List[float]) -> str:
        """Calculate percentage gap between your metrics and best competitor"""
        try:
            if your_value == 0:
                return "No data"
            
            max_competitor = max(competitor_values) if competitor_values else 0
            
            if max_competitor == 0:
                return "Leading"
            
            if max_competitor > your_value:
                gap = ((max_competitor - your_value) / your_value) * 100
                return f"-{gap:.1f}%"
            else:
                gap = ((your_value - max_competitor) / max_competitor) * 100
                return f"+{gap:.1f}%"
        except:
            return "N/A"

    # ============================================================================
    # SHEET CREATION METHODS - ON-PAGE DATA
    # ============================================================================

    async def _create_onpage_pages_sheet(self, spreadsheet, pages_data: List[Dict]):
        """Create detailed on-page pages analysis sheet"""
        try:
            print("  → Creating On-Page Pages sheet...")
            worksheet = spreadsheet.add_worksheet(title="On-Page Pages", rows=1000, cols=30)
            
            headers = [
                "URL", "Status", "OnPage Score", "Title", "Meta Description",
                "Title Length", "Desc Length", "Word Count", "H1", "H2", "H3",
                "Load Time (ms)", "LCP", "CLS", "FID", "Internal Links", "External Links",
                "Images", "Broken Links", "Duplicate Title", "Duplicate Desc",
                "Is HTTPS", "Page Size (KB)", "Readability", "Issues Count", "Priority", "Recommendations"
            ]
            
            worksheet.append_row(headers)
            
            for page in pages_data:
                # Count critical issues
                issues_count = sum([
                    page.get('is_broken', False),
                    page.get('has_4xx', False),
                    page.get('has_5xx', False),
                    page.get('no_h1', False),
                    page.get('no_title', False),
                    page.get('no_description', False),
                    page.get('duplicate_title', False),
                    page.get('duplicate_description', False),
                    page.get('is_orphan', False),
                    page.get('high_loading_time', False),
                ])
                
                # Determine priority
                if issues_count >= 5:
                    priority = "CRITICAL"
                elif issues_count >= 3:
                    priority = "HIGH"
                elif issues_count >= 1:
                    priority = "MEDIUM"
                else:
                    priority = "LOW"
                
                # Generate recommendations
                recommendations = []
                if page.get('no_h1'):
                    recommendations.append("Add H1 tag")
                if page.get('no_title'):
                    recommendations.append("Add title tag")
                if page.get('duplicate_title'):
                    recommendations.append("Make title unique")
                if page.get('high_loading_time'):
                    recommendations.append("Optimize page speed")
                if page.get('is_orphan'):
                    recommendations.append("Add internal links")
                
                recommendations_str = "; ".join(recommendations[:3]) if recommendations else "No critical issues"
                
                row = [
                    page['url'],
                    page['status_code'],
                    page['onpage_score'],
                    page['title'][:50] if page['title'] else '',
                    page['meta_description'][:75] if page['meta_description'] else '',
                    page['title_length'],
                    page['description_length'],
                    page['word_count'],
                    page['h1_count'],
                    page['h2_count'],
                    page['h3_count'],
                    page['load_time'],
                    round(page['lcp'], 2),
                    round(page['cls'], 3),
                    round(page['fid'], 2),
                    page['internal_links'],
                    page['external_links'],
                    page['images_count'],
                    'Yes' if page['broken_links'] else 'No',
                    'Yes' if page['duplicate_title'] else 'No',
                    'Yes' if page['duplicate_description'] else 'No',
                    'Yes' if page['is_https'] else 'No',
                    round(page['page_size_bytes'] / 1024, 1),
                    round(page['readability_score'], 1),
                    issues_count,
                    priority,
                    recommendations_str
                ]
                
                worksheet.append_row(row)
            
            # Format headers
            worksheet.format('A1:AA1', {
                'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                'horizontalAlignment': 'CENTER'
            })
            
            # Color-code OnPage Score (column C)
            if len(pages_data) > 0:
                worksheet.format(f'C2:C{len(pages_data)+1}', {
                    'numberFormat': {'type': 'NUMBER', 'pattern': '0.00'}
                })
            
            print(f"    ✓ On-Page Pages complete ({len(pages_data)} pages)")
            
        except Exception as e:
            logger.error(f"Error creating on-page pages sheet: {e}")
            print(f"    ✗ On-Page Pages failed: {e}")

    async def _create_technical_issues_sheet(self, spreadsheet, issues_data: List[Dict]):
        """Create technical SEO issues sheet"""
        try:
            print("  → Creating Technical Issues sheet...")
            worksheet = spreadsheet.add_worksheet(title="Technical Issues", rows=1000, cols=12)
            
            headers = [
                "Issue Type", "Severity", "Page URL", "Status Code",
                "Description", "Recommendation", "Priority Score", 
                "Impact", "Status", "Date Fixed", "Fixed By", "Notes"
            ]
            
            worksheet.append_row(headers)
            
            for issue in issues_data:
                # Calculate impact
                impact = "High" if issue['severity'] in ['Critical', 'High'] else "Medium" if issue['severity'] == 'Medium' else "Low"
                
                row = [
                    issue['issue_type'],
                    issue['severity'],
                    issue['page_url'],
                    issue['status_code'],
                    issue['description'],
                    issue['recommendation'],
                    issue['priority_score'],
                    impact,
                    'Open',  # Default status
                    '',      # Date Fixed
                    '',      # Fixed By
                    ''       # Notes
                ]
                
                worksheet.append_row(row)
            
            # Format headers
            worksheet.format('A1:L1', {
                'backgroundColor': {'red': 0.8, 'green': 0.2, 'blue': 0.2},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                'horizontalAlignment': 'CENTER'
            })
            
            # Conditional formatting for severity (column B)
            if len(issues_data) > 0:
                # Critical - Dark Red
                worksheet.format(f'B2:B{len(issues_data)+1}', {
                    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                })
            
            print(f"    ✓ Technical Issues complete ({len(issues_data)} issues)")
            
        except Exception as e:
            logger.error(f"Error creating technical issues sheet: {e}")
            print(f"    ✗ Technical Issues failed: {e}")

    async def _create_issues_summary_sheet(self, spreadsheet, issues_data: List[Dict], pages_data: List[Dict]):
        """Create aggregated issues summary with metrics"""
        try:
            print("  → Creating Issues Summary sheet...")
            worksheet = spreadsheet.add_worksheet(title="Issues Summary", rows=100, cols=8)
            
            # Title
            worksheet.append_row(["SEO TECHNICAL ISSUES SUMMARY", "", "", "", "", "", "", ""])
            worksheet.append_row(["", "", "", "", "", "", "", ""])
            
            # Overall Stats
            worksheet.append_row(["OVERALL STATISTICS", "", "", "", "", "", "", ""])
            
            total_pages = len(pages_data)
            total_issues = len(issues_data)
            
            # Count by severity
            critical_count = sum(1 for issue in issues_data if issue['severity'] == 'Critical')
            high_count = sum(1 for issue in issues_data if issue['severity'] == 'High')
            medium_count = sum(1 for issue in issues_data if issue['severity'] == 'Medium')
            low_count = sum(1 for issue in issues_data if issue['severity'] == 'Low')
            
            # Calculate average onpage score
            avg_onpage_score = sum(page['onpage_score'] for page in pages_data) / total_pages if total_pages > 0 else 0
            
            worksheet.append_row(["Total Pages Analyzed:", total_pages, "", "", "", "", "", ""])
            worksheet.append_row(["Total Issues Found:", total_issues, "", "", "", "", "", ""])
            worksheet.append_row(["Average OnPage Score:", f"{avg_onpage_score:.2f}", "", "", "", "", "", ""])
            worksheet.append_row(["", "", "", "", "", "", "", ""])
            
            # Issues by Severity
            worksheet.append_row(["ISSUES BY SEVERITY", "Count", "% of Total", "", "", "", "", ""])
            worksheet.append_row(["Critical", critical_count, f"{(critical_count/total_issues*100):.1f}%" if total_issues > 0 else "0%", "", "", "", "", ""])
            worksheet.append_row(["High", high_count, f"{(high_count/total_issues*100):.1f}%" if total_issues > 0 else "0%", "", "", "", "", ""])
            worksheet.append_row(["Medium", medium_count, f"{(medium_count/total_issues*100):.1f}%" if total_issues > 0 else "0%", "", "", "", "", ""])
            worksheet.append_row(["Low", low_count, f"{(low_count/total_issues*100):.1f}%" if total_issues > 0 else "0%", "", "", "", "", ""])
            worksheet.append_row(["", "", "", "", "", "", "", ""])
            
            # Top Issue Types
            worksheet.append_row(["TOP ISSUE TYPES", "Count", "Severity", "Priority", "", "", "", ""])
            
            # Count issues by type
            issue_type_counts = {}
            for issue in issues_data:
                issue_type = issue['issue_type']
                if issue_type not in issue_type_counts:
                    issue_type_counts[issue_type] = {
                        'count': 0,
                        'severity': issue['severity'],
                        'priority': issue['priority_score']
                    }
                issue_type_counts[issue_type]['count'] += 1
            
            # Sort by count
            sorted_issues = sorted(issue_type_counts.items(), key=lambda x: x[1]['count'], reverse=True)
            
            for issue_type, data in sorted_issues[:10]:
                worksheet.append_row([
                    issue_type,
                    data['count'],
                    data['severity'],
                    data['priority'],
                    "", "", "", ""
                ])
            
            worksheet.append_row(["", "", "", "", "", "", "", ""])
            
            # Pages with Most Issues
            worksheet.append_row(["PAGES WITH MOST ISSUES", "URL", "Issue Count", "", "", "", "", ""])
            
            # Count issues per page
            page_issue_counts = {}
            for issue in issues_data:
                url = issue['page_url']
                page_issue_counts[url] = page_issue_counts.get(url, 0) + 1
            
            # Sort by issue count
            sorted_pages = sorted(page_issue_counts.items(), key=lambda x: x[1], reverse=True)
            
            for url, count in sorted_pages[:10]:
                worksheet.append_row(["", url[:80], count, "", "", "", "", ""])
            
            # Format
            worksheet.format('A1:H1', {
                'backgroundColor': {'red': 0.1, 'green': 0.1, 'blue': 0.1},
                'textFormat': {'bold': True, 'fontSize': 14, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                'horizontalAlignment': 'CENTER'
            })
            
            worksheet.format('A3:H3', {
                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            worksheet.format('A8:H8', {
                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            print(f"    ✓ Issues Summary complete")
            
        except Exception as e:
            logger.error(f"Error creating issues summary sheet: {e}")
            print(f"    ✗ Issues Summary failed: {e}")

    # ============================================================================
    # SHEET CREATION METHODS - COMPETITIVE DATA
    # ============================================================================

    async def _create_domain_overview_sheet(self, spreadsheet, audit_results: Dict, target_domain: str):
        """Create domain overview comparison sheet"""
        try:
            print("  → Creating Domain Overview sheet...")
            worksheet = spreadsheet.add_worksheet(title="Domain Overview", rows=100, cols=20)
            
            phases = audit_results.get('phases', {})
            
            your_domain_data = self._extract_domain_overview_data(phases.get('domain_metrics', {}))
            your_keywords_data = self._extract_ranked_keywords_summary(phases.get('ranked_keywords', {}))
            your_backlinks_data = self._extract_backlinks_summary(phases.get('backlinks_summary', {}))
            
            competitor_analysis = phases.get('competitor_analysis', {})
            competitors = []
            
            for i in range(1, 10):
                comp_key = f'competitor_{i}'
                if comp_key in competitor_analysis:
                    comp_info = competitor_analysis[comp_key]
                    comp_domain = comp_info.get('domain', f'Competitor {i}')
                    comp_data = comp_info.get('data', {})
                    
                    comp_domain_data = self._extract_domain_overview_data(comp_data.get('domain_metrics', {}))
                    comp_keywords_data = self._extract_ranked_keywords_summary(comp_data.get('ranked_keywords', {}))
                    comp_backlinks_data = self._extract_backlinks_summary(comp_data.get('backlinks_summary', {}))
                    
                    competitors.append({
                        'domain': comp_domain,
                        'domain_data': comp_domain_data,
                        'keywords_data': comp_keywords_data,
                        'backlinks_data': comp_backlinks_data
                    })
            
            headers = ["Metric", target_domain]
            for comp in competitors:
                headers.append(comp['domain'])
            headers.extend(["Gap vs Best", "Priority"])
            
            worksheet.append_row(headers)
            
            if not your_domain_data.get('error'):
                your_etv = your_domain_data.get('organic_etv', 0)
                row = ["Organic Traffic Value ($)", your_etv]
                comp_etvs = [comp['domain_data'].get('organic_etv', 0) for comp in competitors]
                row.extend(comp_etvs)
                gap = self._calculate_gap_percentage(float(your_etv), [float(x) for x in comp_etvs])
                priority = "HIGH" if "-" in str(gap) and "%" in str(gap) else "MEDIUM"
                row.extend([gap, priority])
                worksheet.append_row(row)
                
                your_keywords = your_keywords_data.get('total_keywords', 0)
                row = ["Total Ranked Keywords", your_keywords]
                comp_keywords = [comp['keywords_data'].get('total_keywords', 0) for comp in competitors]
                row.extend(comp_keywords)
                gap = self._calculate_gap_percentage(float(your_keywords), [float(x) for x in comp_keywords])
                priority = "HIGH" if "-" in str(gap) and "%" in str(gap) else "MEDIUM"
                row.extend([gap, priority])
                worksheet.append_row(row)
            
            if not your_backlinks_data.get('error'):
                your_backlinks = your_backlinks_data.get('total_backlinks', 0)
                row = ["Total Backlinks", your_backlinks]
                comp_backlinks = [comp['backlinks_data'].get('total_backlinks', 0) for comp in competitors]
                row.extend(comp_backlinks)
                gap = self._calculate_gap_percentage(float(your_backlinks), [float(x) for x in comp_backlinks])
                priority = "HIGH" if "-" in str(gap) else "LOW"
                row.extend([gap, priority])
                worksheet.append_row(row)
                
                your_ref_domains = your_backlinks_data.get('referring_domains', 0)
                row = ["Referring Domains", your_ref_domains]
                comp_ref_domains = [comp['backlinks_data'].get('referring_domains', 0) for comp in competitors]
                row.extend(comp_ref_domains)
                gap = self._calculate_gap_percentage(float(your_ref_domains), [float(x) for x in comp_ref_domains])
                priority = "HIGH" if "-" in str(gap) else "LOW"
                row.extend([gap, priority])
                worksheet.append_row(row)
            
            worksheet.format('A1:Z1', {
                'textFormat': {'bold': True, 'fontSize': 11},
                'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.8}
            })
            
            print(f"    ✓ Domain Overview complete ({len(competitors)} competitors)")
            
        except Exception as e:
            logger.error(f"Error creating domain overview sheet: {e}")
            print(f"    ✗ Domain Overview failed: {e}")

    async def _create_content_gap_sheet(self, spreadsheet, audit_results: Dict):
        """Create content gap analysis sheet"""
        try:
            print("  → Creating Content Gap Analysis sheet...")
            worksheet = spreadsheet.add_worksheet(title="Content Gap Analysis", rows=1000, cols=10)
            
            headers = [
                "Keyword", "Search Volume", "CPC ($)", "Competition", 
                "Competitor", "Competitor Rank", "Priority", "Estimated Monthly Value ($)"
            ]
            worksheet.append_row(headers)
            
            phases = audit_results.get('phases', {})
            opportunities = phases.get('opportunities', {})
            
            all_gaps = []
            
            for opp_key, opp_data in opportunities.items():
                if 'gap_vs_competitor' in opp_key and 'intersection' in opp_data:
                    competitor = opp_data.get('competitor', 'Unknown')
                    intersection = opp_data.get('intersection', {})
                    
                    gap_keywords = self._extract_intersection_keywords(intersection, competitor, limit=10)
                    all_gaps.extend(gap_keywords)
            
            priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'UNKNOWN': 3}
            all_gaps.sort(key=lambda x: (priority_order.get(x['priority_score'], 3), -x['search_volume']))
            
            for gap in all_gaps[:10]:
                estimated_value = self._calculate_traffic_value(
                    int(gap['competitor_position']) if gap['competitor_position'] != 'N/A' else 999,
                    gap['search_volume'],
                    gap['cpc']
                )
                
                row = [
                    gap['keyword'],
                    gap['search_volume'],
                    f"${gap['cpc']:.2f}",
                    f"{gap['competition']:.2f}",
                    gap['competitor'],
                    gap['competitor_position'],
                    gap['priority_score'],
                    f"${estimated_value:.2f}"
                ]
                worksheet.append_row(row)
            
            if not all_gaps:
                worksheet.append_row(["No content gaps found", "", "", "", "", "", "", ""])
            
            worksheet.format('A1:H1', {
                'textFormat': {'bold': True, 'fontSize': 11},
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.2}
            })
            
            print(f"    ✓ Content Gap Analysis complete ({len(all_gaps[:10])} opportunities)")
            
        except Exception as e:
            logger.error(f"Error creating content gap sheet: {e}")
            print(f"    ✗ Content Gap Analysis failed: {e}")

    async def _create_top_keywords_sheet(self, spreadsheet, audit_results: Dict, target_domain: str):
        """Create your top keywords sheet"""
        try:
            print("  → Creating Your Top Keywords sheet...")
            worksheet = spreadsheet.add_worksheet(title="Your Top Keywords", rows=1000, cols=10)
            
            headers = [
                "Keyword", "Position", "Search Volume", "CPC ($)", 
                "Est. Monthly Clicks", "Est. Monthly Value ($)", "Competition", "Action"
            ]
            worksheet.append_row(headers)
            
            phases = audit_results.get('phases', {})
            ranked_keywords = phases.get('ranked_keywords', {})
            
            keywords_data = self._extract_ranked_keywords_detailed(ranked_keywords, limit=10)
            
            for kw in keywords_data:
                action = self._get_keyword_action(kw['position'], kw['search_volume'])
                
                row = [
                    kw['keyword'],
                    kw['position'],
                    kw['search_volume'],
                    f"${kw['cpc']:.2f}",
                    kw['estimated_traffic'],
                    f"${kw['traffic_value']:.2f}",
                    f"{kw['competition']:.2f}",
                    action
                ]
                worksheet.append_row(row)
            
            if not keywords_data:
                worksheet.append_row(["No ranked keywords found", "", "", "", "", "", "", ""])
            
            worksheet.format('A1:H1', {
                'textFormat': {'bold': True, 'fontSize': 11},
                'backgroundColor': {'red': 0.8, 'green': 0.4, 'blue': 0.2}
            })
            
            print(f"    ✓ Your Top Keywords complete ({len(keywords_data)} keywords)")
            
        except Exception as e:
            logger.error(f"Error creating top keywords sheet: {e}")
            print(f"    ✗ Your Top Keywords failed: {e}")

    async def _create_backlink_gap_sheet(self, spreadsheet, audit_results: Dict, target_domain: str):
        """Create backlink gap analysis sheet"""
        try:
            print("  → Creating Backlink Gap Analysis sheet...")
            worksheet = spreadsheet.add_worksheet(title="Backlink Gap", rows=1000, cols=8)
            
            headers = [
                "Referring Domain", "Links to Competitors", "Domain Rank", 
                "Opportunity Score", "Link Type", "Status", "Priority"
            ]
            worksheet.append_row(headers)
            
            phases = audit_results.get('phases', {})
            your_backlinks = self._extract_backlinks_summary(phases.get('backlinks_summary', {}))
            
            competitor_analysis = phases.get('competitor_analysis', {})
            
            worksheet.append_row([
                "SUMMARY",
                "",
                "",
                "",
                "",
                "",
                ""
            ])
            
            worksheet.append_row([
                f"Your Referring Domains: {your_backlinks.get('referring_domains', 0)}",
                "",
                "",
                "",
                "",
                "",
                ""
            ])
            
            for i, (comp_key, comp_data) in enumerate(competitor_analysis.items(), 1):
                comp_domain = comp_data.get('domain', f'Competitor {i}')
                comp_backlinks = self._extract_backlinks_summary(comp_data.get('data', {}).get('backlinks_summary', {}))
                
                worksheet.append_row([
                    f"{comp_domain}: {comp_backlinks.get('referring_domains', 0)} domains",
                    "",
                    "",
                    "",
                    "",
                    "",
                    ""
                ])
            
            worksheet.append_row(["", "", "", "", "", "", ""])
            worksheet.append_row([
                "Note: Detailed backlink gap analysis requires comparing individual referring domains.",
                "",
                "",
                "",
                "",
                "",
                ""
            ])
            
            worksheet.format('A1:G1', {
                'textFormat': {'bold': True, 'fontSize': 11},
                'backgroundColor': {'red': 0.4, 'green': 0.2, 'blue': 0.8}
            })
            
            print(f"    ✓ Backlink Gap complete (summary view)")
            
        except Exception as e:
            logger.error(f"Error creating backlink gap sheet: {e}")
            print(f"    ✗ Backlink Gap failed: {e}")

    async def _create_serp_features_sheet(self, spreadsheet, audit_results: Dict):
        """Create SERP features analysis sheet"""
        try:
            print("  → Creating SERP Features sheet...")
            worksheet = spreadsheet.add_worksheet(title="SERP Features", rows=500, cols=8)
            
            headers = [
                "Keyword", "SERP Features Present", "Featured Snippet Owner", 
                "Total Results", "Opportunity Type", "Action Required"
            ]
            worksheet.append_row(headers)
            
            phases = audit_results.get('phases', {})
            serp_analysis = phases.get('serp_analysis', {})
            
            serp_count = 0
            for serp_key, serp_data in serp_analysis.items():
                keyword = serp_data.get('keyword', 'Unknown')
                serp_info = serp_data.get('serp_data', {})
                
                features_data = self._extract_serp_features(serp_info, keyword)
                
                features_list = features_data.get('features', [])
                features_str = ", ".join(features_list) if features_list else "Standard organic results"
                
                snippet_owner = features_data.get('featured_snippet_owner', 'None')
                total_results = features_data.get('total_results', 0)
                
                if 'Featured Snippet' in features_list:
                    opportunity = "Target Featured Snippet"
                    action = "Create comprehensive, structured content to win snippet"
                elif 'People Also Ask' in features_list:
                    opportunity = "PAA Optimization"
                    action = "Add FAQ section answering related questions"
                elif 'Video Results' in features_list:
                    opportunity = "Video Content"
                    action = "Consider creating video content for this keyword"
                else:
                    opportunity = "Standard Ranking"
                    action = "Focus on traditional on-page SEO"
                
                row = [
                    keyword,
                    features_str,
                    snippet_owner,
                    total_results,
                    opportunity,
                    action
                ]
                worksheet.append_row(row)
                serp_count += 1
            
            if serp_count == 0:
                worksheet.append_row(["No SERP analysis data available", "", "", "", "", ""])
            
            worksheet.format('A1:F1', {
                'textFormat': {'bold': True, 'fontSize': 11},
                'backgroundColor': {'red': 0.6, 'green': 0.2, 'blue': 0.6}
            })
            
            print(f"    ✓ SERP Features complete ({serp_count} keywords analyzed)")
            
        except Exception as e:
            logger.error(f"Error creating SERP features sheet: {e}")
            print(f"    ✗ SERP Features failed: {e}")

    async def _create_ai_analysis_sheet(self, spreadsheet, claude_analysis: Dict):
        """Create AI analysis summary sheet"""
        try:
            print("  → Creating AI Analysis sheet...")
            worksheet = spreadsheet.add_worksheet(title="AI Analysis", rows=200, cols=3)
            
            worksheet.append_row(["AI-Generated SEO Analysis", "", ""])
            worksheet.append_row(["", "", ""])
            
            summary = claude_analysis.get('summary', 'Analysis not yet generated')
            worksheet.append_row(["SUMMARY", "", ""])
            worksheet.append_row([summary, "", ""])
            worksheet.append_row(["", "", ""])
            
            insights = claude_analysis.get('insights', [])
            if insights:
                worksheet.append_row(["KEY INSIGHTS", "", ""])
                for i, insight in enumerate(insights, 1):
                    worksheet.append_row([f"{i}.", insight, ""])
                worksheet.append_row(["", "", ""])
            
            recommendations = claude_analysis.get('recommendations', [])
            if recommendations:
                worksheet.append_row(["RECOMMENDATIONS", "", ""])
                for i, rec in enumerate(recommendations, 1):
                    worksheet.append_row([f"{i}.", rec, ""])
                worksheet.append_row(["", "", ""])
            
            priority_actions = claude_analysis.get('priority_actions', [])
            if priority_actions:
                worksheet.append_row(["PRIORITY ACTIONS (Next 30 Days)", "", ""])
                for i, action in enumerate(priority_actions, 1):
                    worksheet.append_row([f"{i}.", action, ""])
            
            if not summary or summary == 'Analysis not yet generated':
                worksheet.append_row(["", "", ""])
                worksheet.append_row(["Note: AI analysis will be generated after data collection is complete.", "", ""])
            
            worksheet.format('A1:C1', {
                'textFormat': {'bold': True, 'fontSize': 14},
                'backgroundColor': {'red': 0.2, 'green': 0.8, 'blue': 0.8}
            })
            worksheet.format('A3', {'textFormat': {'bold': True, 'fontSize': 12}})
            worksheet.format('A7', {'textFormat': {'bold': True, 'fontSize': 12}})
            
            print(f"    ✓ AI Analysis complete")
            
        except Exception as e:
            logger.error(f"Error creating AI analysis sheet: {e}")
            print(f"    ✗ AI Analysis failed: {e}")

    def _get_keyword_action(self, position: int, search_volume: int) -> str:
        """Determine action required for a keyword based on position and volume"""
        try:
            if position <= 3:
                if search_volume > 1000:
                    return "MAINTAIN - High value position"
                else:
                    return "Maintain position"
            elif position <= 10:
                if search_volume > 1000:
                    return "OPTIMIZE - Push to top 3"
                else:
                    return "Optimize content"
            elif position <= 20:
                if search_volume > 1000:
                    return "PRIORITY - Move to page 1"
                else:
                    return "Improve to page 1"
            else:
                return "Review - Low ranking"
        except:
            return "Review"