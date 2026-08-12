from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    """
    Verificação de integridade da API MedInteract.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
