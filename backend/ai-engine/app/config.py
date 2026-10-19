import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Carrega variáveis do .env na raiz do repositório e na pasta local do ai-engine
_AI_ENGINE_DIR = Path(__file__).resolve().parent.parent
_ROOT_DIR = _AI_ENGINE_DIR.parent.parent
load_dotenv(_ROOT_DIR / ".env")
load_dotenv(_AI_ENGINE_DIR / ".env", override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "MedInteract API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    PORT: int = int(os.getenv("PORT", 5000))
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    GEMINI_FALLBACK_MODEL: str = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    AUTH_SECRET: str = os.getenv("AUTH_SECRET", "medinteract-tcc-secret-key-2026")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgrespassword@localhost:5432/medinteract"
    )

    class Config:
        case_sensitive = True
        extra = "ignore"

settings = Settings()
