from fastapi import APIRouter
from app.api.endpoints import health, chat

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(chat.router)
