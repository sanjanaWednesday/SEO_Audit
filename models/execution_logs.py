from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LogStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"

class ExecutionLogs(BaseModel):
    log_id: str
    execution_id: str
    step_name: str
    status: LogStatus
    error_message: Optional[str] = None
    execution_time: int  # in seconds
    timestamp: datetime
