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

# Conexão assíncrona com o PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

# Fábrica de sessões do banco
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


# Habilita a extensão vector, sincroniza as tabelas e cria o índice HNSW
async def init_db() -> None:
    try:
        async with engine.begin() as connection:
            import app.db.models  # noqa: F401

            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await connection.run_sync(Base.metadata.create_all)
            await connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bula_chunks_embedding 
                ON bula_chunks 
                USING hnsw (embedding vector_cosine_ops);
            """))
            logger.info("[DB] Banco de dados e indice HNSW verificados.")
    except Exception as e:
        logger.error(f"[DB] Erro ao inicializar banco de dados: {str(e)}")
        raise


# Fornece uma sessão assíncrona para as rotas do FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"[DB] Erro na sessao do banco: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()
