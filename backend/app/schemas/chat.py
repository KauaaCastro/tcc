from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.user import UserProfileType
from app.schemas.error import AlertType, TrustedSourceLink

class ChatRequest(BaseModel):
    message: str = Field(..., description="Pergunta do usuário sobre medicamentos ou bulas")
    profile_type: UserProfileType = Field(default=UserProfileType.PATIENT, description="Perfil do usuário: PROFESSIONAL ou PATIENT")
    user_id: Optional[str] = Field(default=None, description="ID do usuário cadastrado (opcional)")

class ChatResponse(BaseModel):
    answer: str
    alert_type: AlertType = AlertType.INFO
    profile_type: UserProfileType
    sources_used: Optional[List[str]] = None
    trusted_sources: Optional[List[TrustedSourceLink]] = None
