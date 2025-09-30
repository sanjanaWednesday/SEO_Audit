from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional

class CompetitorAnalysis(BaseModel):
    keyword_ranking: List[Dict]
    content_gaps: List[Dict]
    schema_markup: List[Dict]
    core_web_vitals: List[Dict]
    analysis_id: str
    execution_id: str
    technical_score: int
    