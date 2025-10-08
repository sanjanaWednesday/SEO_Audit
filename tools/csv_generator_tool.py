"""
CSVGeneratorTool - Generates all SEO audit CSV files
"""
from crewai.tools import BaseTool
from typing import Type, Dict, List
from pydantic import BaseModel, Field
import csv
import json
from pathlib import Path
from datetime import datetime


class CSVGeneratorInput(BaseModel):
    """Input schema for CSVGeneratorTool"""
    action: str = Field(..., description="Action: generate_all, generate_single")
    audit_data: str = Field(..., description="JSON string of complete audit data")
    output_dir: str = Field(..., description="Output directory path")
    csv_type: str = Field(None, description="For generate_single: domain_overview, top_keywords, competitors, content_gaps, backlink_gap, serp_features, onpage_pages, technical_issues, issues_summary, claude_fixes")


class CSVGeneratorTool(BaseTool):
    name: str = "CSV Generator Tool"
    description: str = """
    Generates SEO audit CSV reports. Actions:
    - generate_all: Create all 10 CSV files
    - generate_single: Create one specific CSV
    
    CSV types: domain_overview, top_keywords, competitors, content_gaps, 
    serp_features, onpage_pages, technical_issues, issues_summary, claude_fixes
    
    Note: No backlink_gap as we don't use backlink data.
    """
    args_schema: Type[BaseModel] = CSVGeneratorInput
    
    def _run(self, action: str, audit_data: str, output_dir: str, csv_type: str = None) -> Dict:
        """
        Generate CSV reports
        
        Args:
            action: Action to perform
            audit_data: Complete audit data as JSON string
            output_dir: Output directory
            csv_type: Specific CSV type for single generation
            
        Returns:
            Result with list of generated files
        """
        try:
            # Parse audit data
            if isinstance(audit_data, str):
                data = json.loads(audit_data)
            else:
                data = audit_data
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            if action == 'generate_all':
                return self._generate_all(data, output_path)
            elif action == 'generate_single' and csv_type:
                return self._generate_single(data, output_path, csv_type)
            else:
                return {"error": "Invalid action or missing csv_type", "success": False}
                
        except Exception as e:
            return {"error": f"CSV generation failed: {str(e)}", "success": False}
    
    def _generate_all(self, data: Dict, output_dir: Path) -> Dict:
        """Generate all CSV files"""
        files_created = []
        
        generators = [
            ('domain_overview', self._gen_domain_overview),
            ('top_keywords', self._gen_top_keywords),
            ('competitors', self._gen_competitors),
            ('content_gaps', self._gen_content_gaps),
            ('serp_features', self._gen_serp_features),
            ('onpage_pages', self._gen_onpage_pages),
            ('technical_issues', self._gen_technical_issues),
            ('issues_summary', self._gen_issues_summary),
        ]
        
        for csv_name, generator_func in generators:
            try:
                filepath = generator_func(data, output_dir)
                if filepath:
                    files_created.append(str(filepath))
            except Exception as e:
                print(f"Warning: Failed to generate {csv_name}: {e}")
        
        # Generate Claude fixes if available
        if data.get('claude_analysis'):
            try:
                filepath = self._gen_claude_fixes(data, output_dir)
                if filepath:
                    files_created.append(str(filepath))
            except Exception as e:
                print(f"Warning: Failed to generate claude_fixes: {e}")
        
        return {
            "success": True,
            "files_created": files_created,
            "count": len(files_created),
            "output_dir": str(output_dir)
        }
    
    def _generate_single(self, data: Dict, output_dir: Path, csv_type: str) -> Dict:
        """Generate single CSV file"""
        generator_map = {
            'domain_overview': self._gen_domain_overview,
            'top_keywords': self._gen_top_keywords,
            'competitors': self._gen_competitors,
            'content_gaps': self._gen_content_gaps,
            'serp_features': self._gen_serp_features,
            'onpage_pages': self._gen_onpage_pages,
            'technical_issues': self._gen_technical_issues,
            'issues_summary': self._gen_issues_summary,
            'claude_fixes': self._gen_claude_fixes,
        }
        
        if csv_type not in generator_map:
            return {"error": f"Unknown CSV type: {csv_type}", "success": False}
        
        filepath = generator_map[csv_type](data, output_dir)
        
        return {
            "success": True,
            "file": str(filepath),
            "csv_type": csv_type
        }
    
    # CSV Generation Methods
    
    def _gen_domain_overview(self, data: Dict, output_dir: Path) -> str:
        """Generate domain overview CSV"""
        filename = output_dir / "1_domain_overview.csv"
        phases = data.get('phases', {})
        domain = data.get('domain', 'Your Site')
        
        domain_metrics = phases.get('domain_metrics', {})
        ranked_keywords = phases.get('ranked_keywords', {})
        
        your_etv = self._get_nested(domain_metrics, ['tasks', 0, 'result', 0, 'items', 0, 'metrics', 'organic', 'etv'], 0)
        your_keywords = self._count_items(ranked_keywords)
        
        rows = [
            ['Metric', domain, 'Competitor 1', 'Competitor 2', 'Competitor 3', 'Gap vs Best', 'Priority'],
            ['Organic Traffic Value ($)', your_etv, '', '', '', '', 'HIGH'],
            ['Total Ranked Keywords', your_keywords, '', '', '', '', 'MEDIUM'],
        ]
        
        # Add competitor data
        competitor_analysis = phases.get('competitor_analysis', {})
        for i, (comp_key, comp_data) in enumerate(competitor_analysis.items(), 2):
            if i > 4:
                break
            
            comp_data_obj = comp_data.get('data', {})
            comp_etv = self._get_nested(comp_data_obj.get('domain_metrics', {}), 
                                       ['tasks', 0, 'result', 0, 'items', 0, 'metrics', 'organic', 'etv'], 0)
            comp_keywords = self._count_items(comp_data_obj.get('ranked_keywords', {}))
            
            rows[1][i] = comp_etv
            rows[2][i] = comp_keywords
        
        self._write_csv(filename, rows)
        return filename
    
    def _gen_top_keywords(self, data: Dict, output_dir: Path) -> str:
        """Generate top keywords CSV"""
        filename = output_dir / "2_top_keywords.csv"
        ranked_keywords = data.get('phases', {}).get('ranked_keywords', {})
        
        rows = [
            ['Keyword', 'Position', 'Search Volume', 'CPC ($)', 'Est. Monthly Clicks', 
             'Est. Monthly Value ($)', 'Competition', 'Action']
        ]
        
        items = self._get_nested(ranked_keywords, ['tasks', 0, 'result', 0, 'items'], [])
        
        for item in items[:15]:
            keyword_data = item.get('keyword_data', {})
            keyword = keyword_data.get('keyword', 'N/A')
            position = self._get_keyword_position(item)
            
            keyword_info = keyword_data.get('keyword_info', {})
            search_volume = keyword_info.get('search_volume', 0) or 0
            cpc = keyword_info.get('cpc', 0) or 0
            competition = keyword_info.get('competition', 0) or 0
            
            est_clicks = self._calc_clicks(position, search_volume)
            est_value = est_clicks * cpc
            action = self._get_action(position, search_volume)
            
            rows.append([keyword, position, search_volume, f"{cpc:.2f}",
                        est_clicks, f"{est_value:.2f}", f"{competition:.2f}", action])
        
        if len(rows) > 1:
            self._write_csv(filename, rows)
            return filename
        return None
    
    def _gen_competitors(self, data: Dict, output_dir: Path) -> str:
        """Generate competitors CSV"""
        filename = output_dir / "3_competitors.csv"
        competitors = data.get('phases', {}).get('competitors', {})
        
        rows = [
            ['Rank', 'Domain', 'Avg Position', 'Sum Position', 'Intersections', 
             'Full Domain Metrics', 'Relevance Score']
        ]
        
        items = self._get_nested(competitors, ['tasks', 0, 'result', 0, 'items'], [])
        
        for i, item in enumerate(items, 1):
            rows.append([
                i, item.get('domain', 'N/A'),
                round(item.get('avg_position', 0), 2),
                item.get('sum_position', 0),
                item.get('intersections', 0),
                item.get('full_domain_metrics', 'N/A'),
                round(item.get('relevance', 0), 2)
            ])
        
        if len(rows) > 1:
            self._write_csv(filename, rows)
            return filename
        return None
    
    def _gen_content_gaps(self, data: Dict, output_dir: Path) -> str:
        """Generate content gaps CSV"""
        filename = output_dir / "4_content_gaps.csv"
        opportunities = data.get('phases', {}).get('opportunities', {})
        
        rows = [
            ['Keyword', 'Search Volume', 'CPC ($)', 'Competition', 'Competitor', 
             'Competitor Rank', 'Priority', 'Est. Monthly Value ($)']
        ]
        
        for opp_key, opp_data in opportunities.items():
            if 'gap_vs_competitor' not in opp_key:
                continue
            
            competitor = opp_data.get('competitor', 'Unknown')
            intersection = opp_data.get('intersection', {})
            items = self._get_nested(intersection, ['tasks', 0, 'result', 0, 'items'], [])
            
            for item in items[:10]:
                keyword_data = item.get('keyword_data', {})
                keyword = keyword_data.get('keyword', 'N/A')
                
                keyword_info = keyword_data.get('keyword_info', {})
                search_volume = keyword_info.get('search_volume', 0) or 0
                cpc = keyword_info.get('cpc', 0) or 0
                competition = keyword_info.get('competition', 0) or 0
                
                intersection_result = item.get('intersection_result', {})
                comp_info = intersection_result.get(competitor, {})
                comp_position = self._get_nested(comp_info, 
                    ['ranked_serp_element', 'serp_item', 'rank_absolute'], 'N/A')
                
                priority = self._calc_priority(search_volume, cpc, competition, comp_position)
                est_value = self._calc_clicks(comp_position if comp_position != 'N/A' else 999, search_volume) * cpc
                
                rows.append([keyword, search_volume, f"{cpc:.2f}", f"{competition:.2f}",
                           competitor, comp_position, priority, f"{est_value:.2f}"])
        
        if len(rows) > 1:
            self._write_csv(filename, rows)
            return filename
        return None
    
    def _gen_serp_features(self, data: Dict, output_dir: Path) -> str:
        """Generate SERP features CSV"""
        filename = output_dir / "5_serp_features.csv"
        serp_analysis = data.get('phases', {}).get('serp_analysis', {})
        
        rows = [
            ['Keyword', 'SERP Features', 'Featured Snippet Owner', 'Total Results', 
             'Opportunity Type', 'Action Required']
        ]
        
        for serp_key, serp_data in serp_analysis.items():
            keyword = serp_data.get('keyword', 'Unknown')
            serp_result = serp_data.get('serp_data', {})
            items = self._get_nested(serp_result, ['tasks', 0, 'result', 0, 'items'], [])
            
            features = []
            snippet_owner = 'None'
            
            for item in items:
                item_type = item.get('type', '')
                if item_type == 'featured_snippet':
                    features.append('Featured Snippet')
                    snippet_owner = item.get('domain', 'Unknown')
                elif item_type == 'people_also_ask':
                    features.append('People Also Ask')
                elif item_type == 'knowledge_graph':
                    features.append('Knowledge Graph')
            
            features_str = ', '.join(set(features)) if features else 'Standard organic'
            
            if 'Featured Snippet' in features:
                opportunity, action = 'Target Featured Snippet', 'Create structured content'
            elif 'People Also Ask' in features:
                opportunity, action = 'PAA Optimization', 'Add FAQ section'
            else:
                opportunity, action = 'Standard Ranking', 'Focus on on-page SEO'
            
            rows.append([keyword, features_str, snippet_owner, len(items), opportunity, action])
        
        if len(rows) > 1:
            self._write_csv(filename, rows)
            return filename
        return None
    
    def _gen_onpage_pages(self, data: Dict, output_dir: Path) -> str:
        """Generate on-page pages CSV"""
        filename = output_dir / "6_onpage_pages.csv"
        onpage_data = data.get('onpage_data', {})
        pages_response = onpage_data.get('pages', {})
        
        rows = [
            ['URL', 'Status', 'OnPage Score', 'Title', 'Meta Description', 'Title Length', 
             'Desc Length', 'Word Count', 'H1', 'H2', 'Load Time (ms)', 'Issues Count', 'Priority']
        ]
        
        items = self._get_nested(pages_response, ['tasks', 0, 'result', 0, 'items'], [])
        
        for item in items:
            if item.get('resource_type') != 'html':
                continue
            
            meta = item.get('meta', {})
            content = meta.get('content', {})
            checks = item.get('checks', {})
            page_timing = item.get('page_timing', {})
            htags = meta.get('htags', {})
            
            issues_count = sum([
                checks.get('is_broken', False),
                checks.get('no_h1_tag', False),
                checks.get('no_title', False),
                checks.get('duplicate_title', False),
                checks.get('high_loading_time', False)
            ])
            
            priority = 'CRITICAL' if issues_count >= 5 else 'HIGH' if issues_count >= 3 else 'MEDIUM' if issues_count >= 1 else 'LOW'
            
            rows.append([
                item.get('url', ''),
                item.get('status_code', ''),
                round(item.get('onpage_score', 0), 2),
                (meta.get('title') or '')[:50],
                (meta.get('description') or '')[:75],
                meta.get('title_length', 0),
                meta.get('description_length', 0),
                content.get('plain_text_word_count', 0),
                len(htags.get('h1', [])),
                len(htags.get('h2', [])),
                page_timing.get('time_to_interactive', 0),
                issues_count,
                priority
            ])
        
        if len(rows) > 1:
            self._write_csv(filename, rows)
            return filename
        return None
    
    def _gen_technical_issues(self, data: Dict, output_dir: Path) -> str:
        """Generate technical issues CSV"""
        filename = output_dir / "7_technical_issues.csv"
        onpage_data = data.get('onpage_data', {})
        pages_response = onpage_data.get('pages', {})
        
        rows = [
            ['Issue Type', 'Severity', 'Page URL', 'Status Code', 'Description', 
             'Recommendation', 'Priority Score', 'Impact']
        ]
        
        items = self._get_nested(pages_response, ['tasks', 0, 'result', 0, 'items'], [])
        
        issue_checks = [
            ('is_broken', 'Broken Page', 'Critical', 'Page returns error status code', 
             'Fix or redirect broken page', 10),
            ('no_h1_tag', 'Missing H1', 'Critical', 'Page missing H1 heading tag', 
             'Add descriptive H1 tag', 9),
            ('no_title', 'Missing Title', 'Critical', 'Page missing title tag', 
             'Add unique title tag', 10),
            ('no_description', 'Missing Meta Description', 'High', 'Missing meta description', 
             'Write compelling meta description', 7),
            ('duplicate_title', 'Duplicate Title', 'High', 'Title duplicated across pages', 
             'Create unique title', 8),
            ('high_loading_time', 'Slow Page Load', 'High', 'Load time exceeds 3 seconds', 
             'Optimize page speed', 8),
        ]
        
        for item in items:
            if item.get('resource_type') != 'html':
                continue
            
            url = item.get('url', '')
            checks = item.get('checks', {})
            status_code = item.get('status_code', '')
            
            for check_key, issue_name, severity, description, recommendation, priority_score in issue_checks:
                if checks.get(check_key, False):
                    impact = 'High' if severity in ['Critical', 'High'] else 'Medium'
                    rows.append([issue_name, severity, url, status_code, description,
                               recommendation, priority_score, impact])
        
        if len(rows) > 1:
            self._write_csv(filename, rows)
            return filename
        return None
    
    def _gen_issues_summary(self, data: Dict, output_dir: Path) -> str:
        """Generate issues summary CSV"""
        filename = output_dir / "8_issues_summary.csv"
        onpage_data = data.get('onpage_data', {})
        pages_response = onpage_data.get('pages', {})
        items = self._get_nested(pages_response, ['tasks', 0, 'result', 0, 'items'], [])
        
        issue_counts = {'Critical': 0, 'High': 0, 'Medium': 0}
        total_pages = sum(1 for item in items if item.get('resource_type') == 'html')
        
        rows = [
            ['SEO TECHNICAL ISSUES SUMMARY'],
            [''],
            ['OVERALL STATISTICS'],
            ['Total Pages Analyzed', total_pages],
            [''],
            ['ISSUES BY SEVERITY', 'Count'],
            ['Critical', issue_counts['Critical']],
            ['High', issue_counts['High']],
            ['Medium', issue_counts['Medium']],
        ]
        
        self._write_csv(filename, rows)
        return filename
    
    def _gen_claude_fixes(self, data: Dict, output_dir: Path) -> str:
        """Generate Claude fixes CSV"""
        filename = output_dir / "9_claude_fixes.csv"
        claude_data = data.get('claude_analysis', {})
        
        if not claude_data or not claude_data.get('analysis'):
            return None
        
        analysis = claude_data['analysis']
        rows = [
            ['URL', 'Issue Type', 'Severity', 'AI Priority', 'Fix Description', 
             'Implementation Location', 'Code Fix', 'Additional Notes']
        ]
        
        for url_data in analysis.get('urls', []):
            url = url_data.get('url', '')
            ai_analysis = url_data.get('ai_analysis', {})
            fixes = ai_analysis.get('fixes', [])
            
            for fix in fixes:
                rows.append([
                    url,
                    fix.get('issue_type', ''),
                    fix.get('severity', ''),
                    fix.get('priority', ''),
                    fix.get('description', ''),
                    fix.get('implementation_location', ''),
                    fix.get('code', ''),
                    fix.get('notes', '')
                ])
        
        if len(rows) > 1:
            self._write_csv(filename, rows)
            return filename
        return None
    
    # Helper methods
    
    def _write_csv(self, filename: Path, rows: List[List]):
        """Write rows to CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    
    def _get_nested(self, data: Dict, keys: List, default=None):
        """Safely get nested dictionary value"""
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and isinstance(key, int) and key < len(current):
                current = current[key]
            else:
                return default
            if current is None:
                return default
        return current
    
    def _count_items(self, data: Dict) -> int:
        """Count items in API response"""
        items = self._get_nested(data, ['tasks', 0, 'result', 0, 'items'], [])
        return len(items)
    
    def _get_keyword_position(self, item: Dict) -> int:
        """Extract keyword position"""
        position = self._get_nested(item, 
            ['ranked_serp_element', 'serp_item', 'rank_absolute'], 999)
        return int(position) if position != 'N/A' else 999
    
    def _calc_clicks(self, position: int, search_volume: int) -> int:
        """Calculate estimated clicks"""
        if position == 999 or search_volume == 0:
            return 0
        ctr_map = {1: 0.316, 2: 0.158, 3: 0.106, 4: 0.082, 5: 0.067,
                  6: 0.049, 7: 0.039, 8: 0.032, 9: 0.028, 10: 0.025}
        ctr = ctr_map.get(position, 0.02) if position <= 10 else 0.01 if position <= 20 else 0.005
        return int(search_volume * ctr)
    
    def _get_action(self, position: int, search_volume: int) -> str:
        """Determine keyword action"""
        if position <= 3:
            return "MAINTAIN" if search_volume > 1000 else "Maintain"
        elif position <= 10:
            return "OPTIMIZE" if search_volume > 1000 else "Optimize"
        else:
            return "PRIORITY" if search_volume > 1000 else "Improve"
    
    def _calc_priority(self, search_volume: int, cpc: float, competition: float, comp_position) -> str:
        """Calculate priority"""
        score = 0
        if search_volume > 5000:
            score += 3
        elif search_volume > 1000:
            score += 2
        if cpc > 5:
            score += 3
        elif cpc > 2:
            score += 2
        return "HIGH" if score >= 8 else "MEDIUM" if score >= 5 else "LOW"

