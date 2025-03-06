from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.services.task_manager import TaskManager
from app.services.task_scheduler import TaskScheduler
from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    
    Handles startup and shutdown tasks:
    - Initializes the task manager and scheduler
    - Starts the scheduler
    - Stops the scheduler on shutdown
    """
    # Initialize services
    logger.info("Initializing application services...")
    task_manager = TaskManager()
    scheduler = TaskScheduler(task_manager)
    
    # Make them available to routes
    app.state.task_manager = task_manager
    app.state.scheduler = scheduler
    
    # Preload models if configured
    # TODO: Add config for preloading models
    
    # Start the scheduler
    logger.info("Starting task scheduler...")
    await scheduler.start()
    
    # Yield control to FastAPI
    yield
    
    # Shutdown tasks
    logger.info("Stopping task scheduler...")
    await scheduler.stop()
    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="FastAPI server for running LLM inference tasks asynchronously",
        version=settings.VERSION,
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # Include API router
    app.include_router(api_router)
    
    return app


# Create the application instance
app = create_application()


# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
