from contextlib import asynccontextmanager
import os
import sys

# Garante que o diretório base do ai-engine esteja no sys.path para resolver os imports de 'app'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.utils.logger import logger
from app.api.router import api_router


# Gerencia o ciclo de vida da aplicação FastAPI sincronizando tabelas e índices na inicialização
@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import init_db
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"[STARTUP] Aviso ao inicializar tabelas no banco: {e}")
    logger.info(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} iniciado com sucesso na porta {settings.PORT}.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configuração de CORS restrita às origens locais de desenvolvimento e container
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Registra os roteadores da API (/api)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
        app_dir=BASE_DIR,
    )


