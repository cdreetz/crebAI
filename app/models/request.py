from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class TextGenerationRequest(BaseModel):
    """Request model for text generation endpoint"""
    prompt: str = Field(..., description="Input text prompt")
    model_name: Optional[str] = Field(None, description="Model to use for generation")
    params: Optional[Dict[str, Any]] = Field(None, description="Generation parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "Explain quantum computing in simple terms",
                "model_name": "gpt2-xl",
                "params": {
                    "temperature": 0.7,
                    "max_tokens": 100,
                    "top_p": 0.9
                }
            }
        }


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion endpoint"""
    messages: List[Dict[str, str]] = Field(
        ..., 
        description="List of messages in the conversation"
    )
    model_name: Optional[str] = Field(None, description="Model to use for generation")
    params: Optional[Dict[str, Any]] = Field(None, description="Generation parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Tell me about the solar system."}
                ],
                "model_name": "gpt-3.5",
                "params": {
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            }
        }

class ChatCompletionChunk(BaseModel):
    """Single chunk of a streaming chat completion response"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


class TaskListRequest(BaseModel):
    """Request model for listing tasks"""
    status: Optional[str] = Field(None, description="Filter by task status")
    limit: int = Field(100, description="Maximum number of tasks to return")
    skip: int = Field(0, description="Number of tasks to skip")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "completed",
                "limit": 20,
                "skip": 0
            }
        }
