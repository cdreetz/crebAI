from fastapi import APIRouter
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()


@router.get("/")
async def health_check():
    """
    Check if the API is running.
    
    Returns basic information about the service.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
