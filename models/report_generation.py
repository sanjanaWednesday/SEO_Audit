from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional, datetime

class ReportGeneration(BaseModel):
    sheets_url: HttpUrl
    report_tabs: List[Dict]
    generated_at: datetime
    ai_analysis: Optional[str] = None
    report_id: str
    execution_id: str
    