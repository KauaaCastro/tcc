from enum import Enum
from pydantic import BaseModel
from typing import Optional, List

class AlertType(str, Enum):
    DANGER = "danger"
    WARNING = "warning"
    RESTRICTION = "restriction"
    INFO = "info"

class TrustedSourceLink(BaseModel):
    name: str
    url: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    alert_type: AlertType = AlertType.WARNING
    trusted_sources: Optional[List[TrustedSourceLink]] = None
