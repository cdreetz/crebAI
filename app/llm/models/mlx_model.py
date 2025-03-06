import asyncio
import time
from typing import Dict, List, Any, Optional

from app.core.logging import get_logger
from app.llm.models.base import BaseLLMModel
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class MLXModel(BaseLLMModel):
    """MLX-based LLM implementation optimized for Apple Silicon"""
    
    def __init__(self, model_name: str, model_path: Optional[str] = None):
        """
        Initialize the MLX model.
        
        Args:
            model_name: A name identifier for the model
            model_path: Path to the model or HF repo id (default: use model_name)
        """
        self._model_name = model_name
        self._model_path = model_path or model_name
        self._loaded = False
        self._model = None
        self._tokenizer = None
    
    async def load(self) -> Dict[str, Any]:
        """
        Load the model using mlx_lm.
        
        Returns:
            Dict with load status information
        """
        logger.info(f"Loading MLX model: {self._model_path}")
        
        start_time = time.time()
        
        # Use asyncio.to_thread to run sync mlx_lm load in a separate thread
        def _load_model():
            try:
                # Import here to avoid loading MLX modules when not needed
                from mlx_lm import load
                model, tokenizer = load(self._model_path)
                return model, tokenizer
            except Exception as e:
                logger.error(f"Error loading MLX model: {str(e)}")
                raise
        
        try:
            self._model, self._tokenizer = await asyncio.to_thread(_load_model)
            self._loaded = True
            load_time = time.time() - start_time
            
            logger.info(f"Successfully loaded MLX model in {load_time:.2f} seconds")
            return {
                "name": self._model_name,
                "path": self._model_path,
                "loaded": True,
                "load_time_seconds": load_time
            }
        except Exception as e:
            logger.error(f"Failed to load MLX model: {str(e)}")
            return {
                "name": self._model_name,
                "path": self._model_path,
                "loaded": False,
                "error": str(e)
            }
    
    async def generate(self, prompt: str, params: Optional[Dict] = None) -> str:
        """
        Generate text using the MLX model.
        
        Args:
            prompt: Input text prompt
            params: Generation parameters
            
        Returns:
            Generated text response
        """
        if not self._loaded:
            await self.load()
        
        params = params or {}
        
        async def _generate():
            try:
                # Import generate function inside the thread
                from mlx_lm import generate
                
                # Prepare the prompt with chat template if available
                processed_prompt = prompt
                if hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template is not None:
                    messages = [{"role": "user", "content": prompt}]
                    processed_prompt = self._tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                
                # Set generation parameters
                gen_params = {
                    "max_tokens": params.get("max_tokens", 512),
                    #"temperature": params.get("temperature", 0.7),
                    #"top_p": params.get("top_p", 0.9),
                    #"verbose": params.get("verbose", False)
                }
                
                # Generate response
                response = generate(
                    self._model, 
                    self._tokenizer, 
                    prompt=processed_prompt, 
                    **gen_params
                )
                
                return response
            except Exception as e:
                logger.error(f"Error generating text with MLX: {str(e)}")
                raise
        
        logger.info(f"Generating text with MLX model {self._model_name}")
        return await asyncio.to_thread(_generate)
    
    async def chat(self, messages: List[Dict], params: Optional[Dict] = None) -> Dict:
        """
        Generate a chat completion using the MLX model.
        
        Args:
            messages: List of chat messages in the format [{"role": "...", "content": "..."}]
            params: Generation parameters
            
        Returns:
            Chat completion response
        """
        if not self._loaded:
            await self.load()
        
        params = params or {}
        
        async def _chat():
            try:
                # Import generate function inside the thread
                from mlx_lm import generate
                
                # Apply chat template if available
                if hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template is not None:
                    processed_prompt = self._tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                else:
                    # Fallback for models without chat template
                    processed_prompt = self._format_messages(messages)
                
                # Set generation parameters
                gen_params = {
                    "max_tokens": params.get("max_tokens", 512),
                    "temp": params.get("temperature", 0.7),
                    "top_p": params.get("top_p", 0.9),
                    "verbose": params.get("verbose", False)
                }
                
                # Generate response
                response_text = generate(
                    self._model, 
                    self._tokenizer, 
                    prompt=processed_prompt, 
                    **gen_params
                )
                
                # Format response as chat completion API format
                return {
                    "id": f"mlx-{int(time.time())}",
                    "model": self._model_name,
                    "created": int(time.time()),
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response_text
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
            except Exception as e:
                logger.error(f"Error in chat completion with MLX: {str(e)}")
                raise
        
        logger.info(f"Generating chat completion with MLX model {self._model_name}")
        return await asyncio.to_thread(_chat)
    
    def _format_messages(self, messages: List[Dict]) -> str:
        """
        Format chat messages into a single prompt for models without chat templates.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted prompt string
        """
        formatted_prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                formatted_prompt += f"System: {content}\n\n"
            elif role == "user":
                formatted_prompt += f"User: {content}\n\n"
            elif role == "assistant":
                formatted_prompt += f"Assistant: {content}\n\n"
        
        formatted_prompt += "Assistant: "
        return formatted_prompt
    
    def unload(self) -> bool:
        """
        Unload the model from memory.
        
        Returns:
            True if successful, False otherwise
        """
        was_loaded = self._loaded
        self._model = None
        self._tokenizer = None
        self._loaded = False
        
        if was_loaded:
            logger.info(f"Unloaded MLX model: {self._model_name}")
        
        return was_loaded
    
    @property
    def name(self) -> str:
        return self._model_name
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
