from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class TaskResponse(BaseModel):
    """Response model for task creation endpoints"""
    task_id: str = Field(..., description="ID of the created task")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "LLM Inference Server",
                "version": "1.0.0"
            }
        }


class ModelResponse(BaseModel):
    """Response model for model information"""
    name: str = Field(..., description="Model name or identifier")
    type: str = Field(..., description="Model type")
    loaded: bool = Field(..., description="Whether the model is loaded")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Llama-3.2-3B-Instruct-4bit",
                "type": "MLXModel",
                "loaded": True
            }
        }


class ModelLoadResponse(BaseModel):
    """Response model for model loading endpoint"""
    name: str = Field(..., description="Model name")
    loaded: bool = Field(..., description="Whether the model was loaded successfully")
    cached: Optional[bool] = Field(None, description="Whether the model was already loaded")
    load_time_seconds: Optional[float] = Field(None, description="Time taken to load the model")
    error: Optional[str] = Field(None, description="Error message if loading failed")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Llama-3.2-3B-Instruct-4bit",
                "loaded": True,
                "cached": False,
                "load_time_seconds": 5.23
            }
        }


class TaskStatusResponse(BaseModel):
    """Response model for task status endpoint"""
    id: str = Field(..., description="Task ID")
    type: str = Field(..., description="Task type")
    status: str = Field(..., description="Task status")
    created_at: float = Field(..., description="Task creation timestamp")
    completed_at: Optional[float] = Field(None, description="Task completion timestamp")
    params: Dict = Field(..., description="Task parameters")
    result: Optional[Any] = Field(None, description="Task result if completed")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "type": "text_generation",
                "status": "completed",
                "created_at": 1646393271.32,
                "completed_at": 1646393273.45,
                "params": {
                    "prompt": "Explain quantum computing",
                    "model_name": "Llama-3.2-3B-Instruct-4bit"
                },
                "result": "Quantum computing is..."
            }
        }
