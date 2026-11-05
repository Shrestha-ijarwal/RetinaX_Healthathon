from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import ConfigDict, BaseModel

class AuditEventOut(BaseModel):
    id: int
    user_id: Optional[str]
    user_name: str
    user_role: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = ""
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
