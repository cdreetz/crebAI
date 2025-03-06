from fastapi import APIRouter

from app.api.endpoints import health, text_generation, chat_completion, tasks, models
from app.core.config import get_settings

settings = get_settings()

# Create the main API router
api_router = APIRouter(prefix=settings.API_V1_PREFIX)

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(text_generation.router, prefix="/text", tags=["generation"])
api_router.include_router(chat_completion.router, prefix="/chat", tags=["generation"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
