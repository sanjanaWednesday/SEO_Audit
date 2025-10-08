"""
ConfigReaderTool - Reads and validates config.yaml
"""
from crewai.tools import BaseTool
from typing import Type, Dict, List
from pydantic import BaseModel, Field
import yaml
import os


class ConfigReaderInput(BaseModel):
    """Input schema for ConfigReaderTool"""
    config_path: str = Field(default="config.yaml", description="Path to config.yaml file")


class ConfigReaderTool(BaseTool):
    name: str = "Config Reader Tool"
    description: str = """
    Reads and validates the config.yaml file to extract:
    - Website domain (required)
    - Competitor websites (optional)
    - Target keywords (optional)
    - Main topic (optional)
    - Max crawl pages (optional)
    Returns validated configuration dictionary.
    """
    args_schema: Type[BaseModel] = ConfigReaderInput
    
    def _run(self, config_path: str = "config.yaml") -> Dict:
        """
        Load and validate configuration from YAML file
        
        Args:
            config_path: Path to config file
            
        Returns:
            Dictionary with validated configuration
        """
        if not os.path.exists(config_path):
            return {
                "error": f"Configuration file not found: {config_path}",
                "success": False
            }
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required fields
            if not config.get('website'):
                return {
                    "error": "'website' field is required in config.yaml",
                    "success": False
                }
            
            # Set defaults
            config.setdefault('competitors', [])
            config.setdefault('keywords', [])
            config.setdefault('main_topic', None)
            config.setdefault('max_crawl_pages', 10)
            config.setdefault('output_dir', 'output')
            
            # Clean up website domain
            config['website'] = config['website'].strip().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
            
            # Clean up competitors
            cleaned_competitors = []
            for comp in config.get('competitors', []):
                if comp:
                    cleaned = comp.strip().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
                    if cleaned:
                        cleaned_competitors.append(cleaned)
            config['competitors'] = cleaned_competitors
            
            # Clean up keywords
            cleaned_keywords = []
            for kw in config.get('keywords', []):
                if kw and kw.strip():
                    cleaned_keywords.append(kw.strip())
            config['keywords'] = cleaned_keywords
            
            return {
                "success": True,
                "config": config,
                "website": config['website'],
                "competitors": config['competitors'],
                "keywords": config['keywords'],
                "main_topic": config.get('main_topic'),
                "max_crawl_pages": config.get('max_crawl_pages', 10),
                "has_competitors": len(config['competitors']) > 0,
                "has_keywords": len(config['keywords']) > 0
            }
            
        except Exception as e:
            return {
                "error": f"Failed to load config: {str(e)}",
                "success": False
            }

