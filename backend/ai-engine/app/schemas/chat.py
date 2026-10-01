from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class ProfileType(str, Enum):
    """
    Define os perfis de usuário suportados pela plataforma.
    O perfil Selecionado determina o vocabulário, profundidade farmacológica e o tom da resposta gerada pela IA
    """
    
    PROFESSIONAL = "PROFESSIONAL"
    PATIENT = "PATIENT"
    
class AlertType(str, Enum):
    """
    Padronização dos 4 tipos de alertas visuais exibidos na interface
    Controla o nível de severidade clínica na UI e as cores
    """
    
    DANGER = "danger"
    WARNING = "warning"
    RESTRICTION = "restriction"
    INFO = "info"
    
# Modelos auxiliares e fontes confiáveis

class OfficialLink(BaseModel):
    """
    Representa um link clínico oficial (Anvisa) para consulta segura
    """
    name: str = Field(..., description="Nome da fonte para consulta")
    url: str = Field(..., description="Link de url oficial validada")
    
# Modelos de entrada (request DTOs)

class QueryRequest(BaseModel):
    """
    Payload em JSON enviado pelo frontend ao submeter uma análise medicamentosa.
    """
    
    question: str = Field(
            ...,
            min_length=3,
            max_length=1500,
            description="Pergunta clínica digitada pelo usuário ou prompt de consulta",
            json_schema_extra={"example": "Posso tomar Atorvastatina e Claritromicina juntos?"}
        )
    profile: ProfileType = Field(
            default=ProfileType.PATIENT,
            description="Perfil do usuário que está consultando (PROFESSIONAL ou PATIENT)"
        )
    medications: List[str] = Field(
            default_factory=list,
            description="Lista opcional de medicamentos selecionados via tags na interface",
            json_schema_extra={"example": ["Atorvastatina", "Claritromicina"]}
        )


    # ---------------------------------------------------------
    # 4. Modelos de Saída (Response DTOs)
    # ---------------------------------------------------------

class StreamChunkResponse(BaseModel):
    """
    Formato de cada fragmento enviado em tempo real via Server-Sent Events (SSE).
    Permite à interface renderizar o texto palavra por palavra.
    """
    chunk: str = Field(..., description="Fragmento de texto emitido pelo modelo de IA")
    alert_type: Optional[AlertType] = Field(
            default=None,
        description="Tipo de alerta detectado na análise (enviado no início ou no laudo)"
    )
    is_final: bool = Field(
            default=False,
        description="Sinaliza se a resposta de streaming foi encerrada"
    )


class QueryResponse(BaseModel):
    """
    Resposta estruturada completa para consultas não-streaming ou emissão de laudo.
    """
    answer: str = Field(..., description="Laudo clínico completo gerado pela IA com RAG")
    alert_type: AlertType = Field(
        default=AlertType.INFO,
        description="Classificação de severidade da interação medicamentosa"
    )
    profile: ProfileType = Field(..., description="Perfil para o qual a resposta foi adaptada")
    medications_analyzed: List[str] = Field(
        default_factory=list,
        description="Medicamentos identificados e avaliados na consulta"
    )
    sources: List[OfficialLink] = Field(
        default_factory=list,
        description="Fontes oficiais da ANVISA ou científicas utilizadas como base"
    )
    disclaimer: str = Field(
        default="Esta análise é um suporte informativo baseado em bulas oficiais e não substitui a consulta médica presencial.",
        description="Aviso legal de responsabilidade clínica"
    )

# Modelo de erro e fallback para segurança

class ErrorDetail(BaseModel):
    """Estrutura detalhada de erros contendo os metadados exigidos pela UI
    """
    code: str = Field(..., description = "Código do erro (ex: AI_SERVICE_UNAVAILBLE, SCOPE_VIOLATION)")
    title: str = Field(..., description="Título amigável para o modal ou toast da UI")
    message: str = Field(..., description="Explicação detalhada do erro ou orientação clínica")
    alert_type: AlertType = Field(
        default=AlertType.DANGER,
        description="Tipo de alerta visual a ser renderizado na UI"
    )
    status_code: int = Field(default=500, description="Código de status HTTP correspondente")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data e hora do erro em UTC")
    links: List[OfficialLink] = Field(
        default_factory=list,
        description="Links oficiais de contingência (Bulário ANVISA, Medscape) em caso de fallback"
    )


class ErrorResponse(BaseModel):
    """Wrapper padronizado para respostas de erro da API."""
    error: ErrorDetail