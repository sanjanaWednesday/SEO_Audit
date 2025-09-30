from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional

class CompetitorAnalysis(BaseModel):
    analysis_id: str
    execution_id: str
    competitor_domain: str
    keyword_ranking: List[Dict]
    content_gaps: List[Dict]
    schema_markup: List[Dict]
    core_web_vitals: List[Dict]
    technical_score: Optional[int] = None
    domain_authority: Optional[float] = None
    organic_traffic: Optional[int] = None
    