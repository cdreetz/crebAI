from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import asyncio


class BaseLLMModel(ABC):
    """Base class for LLM model implementations"""
    
    @abstractmethod
    async def load(self) -> Dict[str, Any]:
        """Load the model into memory"""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, params: Optional[Dict] = None) -> str:
        """Generate text from a prompt"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict], params: Optional[Dict] = None) -> Dict:
        """Generate a response from a conversation"""
        pass
    
    @abstractmethod
    def unload(self) -> bool:
        """Unload the model from memory"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the model name"""
        pass
    
    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if the model is loaded"""
        pass


class MockLLMModel(BaseLLMModel):
    """Mock implementation of LLM model for testing"""
    
    def __init__(self, model_name: str):
        self._model_name = model_name
        self._loaded = False
        self._model_data = None
    
    async def load(self) -> Dict[str, Any]:
        """Mock loading the model"""
        await asyncio.sleep(2)  # Simulate loading time
        self._loaded = True
        self._model_data = {"loaded_at": asyncio.get_event_loop().time()}
        return {"name": self._model_name, "loaded": True}
    
    async def generate(self, prompt: str, params: Optional[Dict] = None) -> str:
        """Mock generating text"""
        if not self._loaded:
            await self.load()
        
        params = params or {}
        processing_time = max(1, min(5, len(prompt) / 200))
        await asyncio.sleep(processing_time)
        
        return f"Response to: {prompt[:50]}... [Generated with {self._model_name}]"
    
    async def chat(self, messages: List[Dict], params: Optional[Dict] = None) -> Dict:
        """Mock chat completion"""
        if not self._loaded:
            await self.load()
        
        params = params or {}
        prompt_length = sum(len(msg.get("content", "")) for msg in messages)
        processing_time = max(1, min(5, prompt_length / 200))
        await asyncio.sleep(processing_time)
        
        last_message = messages[-1]["content"] if messages else ""
        return {
            "id": "mock-id",
            "model": self._model_name,
            "created": asyncio.get_event_loop().time(),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Response to: {last_message[:50]}... [Generated with {self._model_name}]"
                    },
                    "finish_reason": "stop"
                }
            ]
        }
    
    def unload(self) -> bool:
        """Mock unloading the model"""
        was_loaded = self._loaded
        self._loaded = False
        self._model_data = None
        return was_loaded
    
    @property
    def name(self) -> str:
        return self._model_name
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
