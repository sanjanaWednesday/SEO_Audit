from pydantic import BaseModel, HttpUrl
from typing import List, Dict
from datetime import datetime

class SiteConfiguration(BaseModel):
    config_id: str
    site_url: HttpUrl
    brand_name: str
    competitors: List[str]  # JSON array in ERD
    audit_parameters: Dict  # JSON
    compliance_settings: Dict  # JSON
    created_at: datetime
