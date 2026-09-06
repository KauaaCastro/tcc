import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "MedInteract API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    PORT: int = int(os.getenv("PORT", 5000))
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgrespassword@localhost:5432/medinteract"
    )

    class Config:
        case_sensitive = True

settings = Settings()
