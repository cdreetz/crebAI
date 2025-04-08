import asyncio
import uuid
import time
from typing import Dict, List, Any, Optional, AsyncGenerator
import os

from app.core.logging import get_logger
from app.core.config import get_settings
from app.llm.models.factory import create_model, get_model, register_model

settings = get_settings()
logger = get_logger(__name__)


class LLMInterface:
    """Interface for LLM operations using MLX models"""
    
    @classmethod
    async def load_model(cls, model_name: str, model_type: str = "mlx", model_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load a model into memory.
        
        Args:
            model_name: Name or identifier for the model
            model_type: Type of model backend to use
            model_path: Optional path or HF repo ID for the model
            
        Returns:
            Dict containing model info
        """
        logger.info(f"Loading model: {model_name} (type: {model_type})")
        
        # Check if model is already loaded
        model = get_model(model_name)
        if model and model.is_loaded:
            logger.info(f"Model {model_name} already loaded")
            return {"name": model_name, "loaded": True, "cached": True}
        
        # Create and load the model
        if not model:
            model = create_model(model_type, model_name, model_path)
            register_model(model)
        
        # Load the model
        result = await model.load()
        return result
    
    @classmethod
    async def generate_text(cls, prompt: str, model_name: Optional[str] = None, params: Optional[Dict] = None) -> str:
        """
        Generate text using the specified model.
        
        Args:
            prompt: Input text prompt
            model_name: Name of the model to use
            params: Generation parameters
            
        Returns:
            Generated text
        """
        # if no model provided use default from config
        if not model_name:
            from app.core.config_loader import get_default_model
            model_name = get_default_model() or "mlx-community/Llama-3.2-3B-Instruct-4bit"

        logger.info(f"Generating text with model {model_name}")
        params = params or {}
        
        # Get the model (load if necessary)
        model = get_model(model_name)
        if not model:
            # Default to MLX model if not specified
            model_path = params.get("model_path", model_name)
            model = create_model("mlx", model_name, model_path)
            register_model(model)
            await model.load()
        elif not model.is_loaded:
            await model.load()
        
        # Generate text
        return await model.generate(prompt, params)

    @classmethod
    async def chat_completion(cls, messages: List[Dict], model_name: str, params: Optional[Dict] = None) -> Dict:
        """
        Generate a chat completion using the specified model.
        
        Args:
            messages: List of chat messages
            model_name: Name of the model to use
            params: Generation parameters
            
        Returns:
            Chat completion response
        """
        logger.info(f"Generating chat completion with model {model_name}")
        params = params or {}
        
        # Get the model (load if necessary)
        model = get_model(model_name)
        if not model:
            # Default to MLX model if not specified
            model_path = params.get("model_path", model_name)
            model = create_model("mlx", model_name, model_path)
            register_model(model)
            await model.load()
        elif not model.is_loaded:
            await model.load()
        
        # Generate chat completion
        return await model.chat(messages, params)

    @classmethod
    async def stream_chat_completion(cls, messages: List[Dict], model_name: str, params: Optional[Dict] = None) -> AsyncGenerator[Dict, None]:
        """
        Stream a chat completion using the specified model.
        
        Args:
            messages: List of chat messages
            model_name: Name of the model to use
            params: Generation parameters
            
        Returns:
            Chat completion response
        """
        logger.info(f"Generating chat completion with model {model_name}")
        params = params or {}

        stream_params = {**params, "stream": True}
        
        # Get the model (load if necessary)
        model = get_model(model_name)
        if not model:
            # Default to MLX model if not specified
            model_path = params.get("model_path", model_name)
            model = create_model("mlx", model_name, model_path)
            register_model(model)
            await model.load()
        elif not model.is_loaded:
            await model.load()

        if not hasattr(model, "chat_stream"):
            raise NotImplementedError(f"Model {model_name} does not support streaming")

        async for chunk in model.chat_stream(messages, stream_params):
            yield chunk
        
    
    @classmethod
    def unload_model(cls, model_name: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_name: Name of the model to unload
            
        Returns:
            True if successful, False otherwise
        """
        model = get_model(model_name)
        if model:
            logger.info(f"Unloading model: {model_name}")
            return model.unload()
        return False
    
    @classmethod
    async def list_models(cls) -> List[Dict[str, Any]]:
        """
        List all registered models and their status.
        
        Returns:
            List of model information dictionaries
        """
        from app.llm.models.factory import _LOADED_MODELS
        
        models_info = []
        for name, model in _LOADED_MODELS.items():
            models_info.append({
                "name": name,
                "type": model.__class__.__name__,
                "loaded": model.is_loaded
            })
        
        return models_info
