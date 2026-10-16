from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# Perfis de visualização suportados pela plataforma
class ProfileType(str, Enum):
    PROFESSIONAL = "PROFESSIONAL"
    PATIENT = "PATIENT"


# Tipos de alertas visuais de severidade exibidos na UI
class AlertType(str, Enum):
    DANGER = "danger"
    WARNING = "warning"
    RESTRICTION = "restriction"
    INFO = "info"


# Link clínico oficial (ANVISA / Medscape) para contingência
class OfficialLink(BaseModel):
    name: str = Field(..., description="Nome da fonte para consulta")
    url: str = Field(..., description="Link de URL oficial validada")


# Payload para salvar/atualizar o Perfil Clínico Anônimo via UUID v4
class PerfilUsuarioPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_usuario: UUID = Field(..., alias="idUsuario")
    apelido: str = Field(..., max_length=50)
    idade: Optional[int] = Field(default=None, ge=0, le=130)
    peso: Optional[float] = Field(default=None, gt=0)
    altura: Optional[float] = Field(default=None, gt=0)
    gestante_lactante: bool = Field(default=False, alias="gestanteLactante")
    alergias: Optional[str] = Field(default=None)
    problemas_saude: Optional[str] = Field(default=None, alias="problemasSaude")
    medicacoes_continuas: Optional[str] = Field(default=None, alias="medicacoesContinuas")
    pratica_esportes: Optional[str] = Field(default=None, alias="praticaEsportes")
    horas_sono: Optional[float] = Field(default=None, alias="horasSono", ge=0, le=24)


# Payload de entrada para consulta clínica de medicamentos
class QueryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_usuario: Optional[UUID] = Field(default=None, alias="idUsuario")
    question: str = Field(..., min_length=3, max_length=1500)
    profile: ProfileType = Field(default=ProfileType.PATIENT)
    medications: List[str] = Field(default_factory=list)


# Fragmento enviado em tempo real via Server-Sent Events (SSE)
class StreamChunkResponse(BaseModel):
    chunk: str
    alert_type: Optional[AlertType] = Field(default=None)
    is_final: bool = Field(default=False)


# Resposta estruturada para consultas via POST /api/ai/query
class QueryResponse(BaseModel):
    response: str
    sources: List[str] = Field(default_factory=list)
    severity: AlertType = Field(default=AlertType.INFO)


# Metadados de erro e Fallback Seguro para a UI
class ErrorDetail(BaseModel):
    code: str
    title: str
    message: str
    alert_type: AlertType = Field(default=AlertType.DANGER)
    status_code: int = Field(default=500)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    links: List[OfficialLink] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorDetail