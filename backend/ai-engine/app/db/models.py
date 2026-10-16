import uuid
from typing import Dict, Any, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Numeric,
    Boolean,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.session import Base


# Tabela 'user_register': Credenciais de login do usuário (UUID, apelido/nome, email e senha)
class UserRegister(Base):
    __tablename__ = "user_register"

    id_usuario = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    apelido = Column(String(50), nullable=False)
    email = Column(String(100), nullable=True, unique=True)
    password = Column(String(255), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "idUsuario": str(self.id_usuario),
            "apelido": self.apelido,
            "email": self.email,
        }


# Alias de compatibilidade caso algum módulo importe PerfilUsuario
PerfilUsuario = UserRegister


# Tabela 'farm_history': Ficha clínica do usuário vinculada ao user_register
class FarmHistory(Base):
    __tablename__ = "farm_history"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_register.id_usuario", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    idade = Column(Integer, nullable=True)
    peso = Column(Numeric(5, 2), nullable=True)
    altura = Column(Numeric(3, 2), nullable=True)
    gestante_lactante = Column(Boolean, default=False, server_default="false")
    alergias = Column(Text, nullable=True)
    problemas_saude = Column(Text, nullable=True)
    medicacoes_continuas = Column(Text, nullable=True)
    pratica_esportes = Column(Text, nullable=True)
    horas_sono = Column(Numeric(3, 1), nullable=True)
    atualizado_em = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Calcula o IMC (peso / altura²) caso ambos os valores sejam válidos
    def calcular_imc(self) -> Optional[float]:
        if self.peso is not None and self.altura is not None and float(self.altura) > 0:
            return round(float(self.peso) / (float(self.altura) ** 2), 2)
        return None

    def to_dict(self, apelido: Optional[str] = None) -> Dict[str, Any]:
        return {
            "idUsuario": str(self.user_id),
            "apelido": apelido or "Paciente",
            "idade": self.idade,
            "peso": float(self.peso) if self.peso is not None else None,
            "altura": float(self.altura) if self.altura is not None else None,
            "imc": self.calcular_imc(),
            "gestanteLactante": bool(self.gestante_lactante),
            "alergias": self.alergias,
            "problemasSaude": self.problemas_saude,
            "medicacoesContinuas": self.medicacoes_continuas,
            "praticaEsportes": self.pratica_esportes,
            "horasSono": float(self.horas_sono) if self.horas_sono is not None else None,
            "atualizadoEm": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }


# Tabela 'historico_consultas': Histórico de perguntas e respostas vinculado ao UUID
class HistoricoConsultas(Base):
    __tablename__ = "historico_consultas"

    id_consulta = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(
        UUID(as_uuid=True),
        ForeignKey("user_register.id_usuario", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    pergunta_usuario = Column(Text, nullable=False)
    resposta_ia = Column(Text, nullable=False)
    data_hora = Column(DateTime(timezone=False), server_default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "idConsulta": self.id_consulta,
            "idUsuario": str(self.id_usuario) if self.id_usuario else None,
            "perguntaUsuario": self.pergunta_usuario,
            "respostaIa": self.resposta_ia,
            "dataHora": self.data_hora.isoformat() if self.data_hora else None,
        }


# Tabela 'bula_chunks': Fragmentos de bulas da ANVISA vetorizados em 768 dimensões (PGVector)
class BulaChunk(Base):
    __tablename__ = "bula_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    med_name = Column(String(255), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, default=0)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<BulaChunk(id={self.id}, med='{self.med_name}', chunk={self.chunk_index})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "med_name": self.med_name,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
