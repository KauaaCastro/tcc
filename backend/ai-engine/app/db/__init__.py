"""
Pacote da Camada de Banco de Dados (ORM e Conexões) do MedInteract.

Exporta as classes e utilitários principais para que outros módulos
possam importar diretamente de `app.db`.
"""

from app.db.session import (
    Base,
    engine,
    AsyncSessionLocal,
    get_db,
    init_db,
)
from app.db.models import BulaChunk

__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "init_db",
    "BulaChunk",
]
