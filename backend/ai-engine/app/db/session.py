from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from app.config import settings
from app.utils.logger import logger

# ---------------------------------------------------------
# 1. Motor de Conexão Assíncrona (Engine)
# ---------------------------------------------------------
# O engine gerencia o pool de conexões com o PostgreSQL via asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Altere para True caso queira ver os comandos SQL no terminal
    future=True,
)

# ---------------------------------------------------------
# 2. Fábrica de Sessões (Sessionmaker)
# ---------------------------------------------------------
# Cada sessão representa uma transação de leitura/escrita no banco
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# ---------------------------------------------------------
# 3. Base Declarativa
# ---------------------------------------------------------
# Todos os modelos (tabelas) herdam desta classe Base
Base = declarative_base()


# ---------------------------------------------------------
# 4. Inicializador do Banco e Extensão PGVector
# ---------------------------------------------------------
async def init_db() -> None:
    """
    Inicializa o banco de dados:
    1. Habilita a extensão 'vector' do PGVector no PostgreSQL.
    2. Cria todas as tabelas mapeadas (como 'bula_chunks') se não existirem.
    """
    try:
        async with engine.begin() as connection:
            # Garante que a extensão de vetores do PostgreSQL esteja ativada
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("[DB] Extensao PGVector habilitada com sucesso.")

            # Cria as tabelas definidas nos modelos que herdam de Base
            await connection.run_sync(Base.metadata.create_all)
            logger.info("[DB] Tabelas do banco de dados sincronizadas com sucesso.")
    except Exception as e:
        logger.error(f"[DB] Erro ao inicializar o banco de dados: {str(e)}")
        raise


# ---------------------------------------------------------
# 5. Dependência do FastAPI (get_db)
# ---------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Injeta uma sessão assíncrona nas rotas do FastAPI e fecha
    automaticamente a conexão após a resposta ser enviada.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"[DB] Erro na sessao do banco: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()
