from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List
from enum import Enum

class WorkflowStatus(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowExecution(BaseModel):
    execution_id: str
    site_url: HttpUrl
    slack_user_id: str
    user_email: Optional[str] = None
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    report_url: Optional[str] = None
    main_topic: Optional[str] = None
    top_competitors: Optional[List[str]] = None
    error_message: Optional[str] = None
