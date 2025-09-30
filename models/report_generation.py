from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional
from datetime import datetime

class ReportGeneration(BaseModel):
    report_id: str
    execution_id: str
    sheets_url: HttpUrl
    report_tabs: List[Dict]
    generated_at: datetime
    ai_analysis: Optional[str] = None
    user_email: Optional[str] = None
    