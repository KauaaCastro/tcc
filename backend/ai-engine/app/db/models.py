from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.session import Base


class BulaChunk(Base):
    """
    Representa a tabela 'bula_chunks' no PostgreSQL com suporte a PGVector.
    
    Cada registro armazena um fragmento clínico de uma bula da ANVISA
    juntamente com seu vetor semântico gerado pelo modelo de inteligência artificial.
    """
    __tablename__ = "bula_chunks"

    # 1. Identificação única do fragmento
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 2. Nome padronizado do medicamento (ex: 'Atorvastatina Calcica', 'Dipirona')
    # O index=True acelera buscas textuais diretas por medicamento
    med_name = Column(String(255), nullable=False, index=True)

    # 3. Posição ordinal do chunk dentro da bula (ex: 0, 1, 2... do mesmo remédio)
    chunk_index = Column(Integer, nullable=False, default=0)

    # 4. Texto clínico extraído daquela seção da bula
    content = Column(Text, nullable=False)

    # 5. Vetor semântico de 768 dimensões gerado pelo Gemini
    # Permite consultas semânticas no PostgreSQL por similaridade de cosseno (<=>)
    embedding = Column(Vector(768), nullable=True)

    # 6. Data e hora do registro no banco
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        """Representação textual amigável para depuração no console."""
        return f"<BulaChunk(id={self.id}, med='{self.med_name}', chunk={self.chunk_index})>"

    def to_dict(self) -> Dict[str, Any]:
        """Converte a entidade do banco em um dicionário Python simples."""
        return {
            "id": self.id,
            "med_name": self.med_name,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
