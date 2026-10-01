from fastapi import APIRouter
from app.api.endpoints import chat

api_router = APIRouter()

# Registra os endpoints do chat sob o prefixo /api
api_router.include_router(chat.router, prefix="", tags=["Chat & RAG"])
