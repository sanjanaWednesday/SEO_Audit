from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class WorkflowExecution(BaseModel):
    execution_id: str
    site_url: HttpUrl
    slack_user_id: str
    status: str  # ENUM: started, completed, failed
    started_at: datetime
    completed_at: Optional[datetime] = None
    report_url: Optional[str] = None
