from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional

class AuditResults(BaseModel):
    result_id: str
    execution_id: str
    site_url: HttpUrl
    technical_issues: List[Dict]  # JSON
    keyword_insights: List[Dict]  # JSON
    competitive_insights: List[Dict]  # JSON
    implementation_code: Optional[str] = None  # TEXT
    priority_score: Optional[int] = None  # INT
