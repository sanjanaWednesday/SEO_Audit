from enum import Enum
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional, datetime

class ExecutionLogs(BaseModel):
    status: Enum
    error_message: Optional[str] = None
    excecution_time: int
    timestamp: datetime
    log_id : int
    execution_id : str
    step_name : str
