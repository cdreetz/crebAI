import asyncio
import json
import httpx
import time
import sys
from typing import Dict, List, Any, Optional, Union


class MLXInferenceClient:
    """
    Asynchronous client for the MLX Inference Server API.
    
    This client handles communication with the server and provides
    methods for text generation, chat completions, and model management.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the inference server API
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)  # Long timeout for model loading
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def health_check(self) -> Dict:
        """Check if the API is healthy"""
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def generate_text(
        self, 
        prompt: str, 
        model_name: Optional[str] = None,
        params: Optional[Dict] = None,
        wait_for_result: bool = True,
        poll_interval: float = 0.5
    ) -> Union[str, str]:
        """
        Generate text using the API.
        
        Args:
            prompt: Input text prompt
            model_name: Name of the model to use (optional)
            params: Additional generation parameters (optional)
            wait_for_result: Whether to wait for the result (True) or return the task ID (False)
            poll_interval: Interval in seconds between polling for task status
            
        Returns:
            Generated text if wait_for_result is True, otherwise task ID
        """
        request_data = {"prompt": prompt}
        if model_name:
            request_data["model_name"] = model_name
        if params:
            request_data["params"] = params
        
        # Submit the generation request
        response = await self.client.post(
            f"{self.base_url}/text/generate",
            json=request_data
        )
        response.raise_for_status()
        data = response.json()
        task_id = data["task_id"]
        
        if not wait_for_result:
            return task_id
        
        # Poll for the result
        return await self._wait_for_task_result(task_id, poll_interval)
    
    async def chat_completion(
        self, 
        messages: List[Dict],
        model_name: Optional[str] = None,
        params: Optional[Dict] = None,
        wait_for_result: bool = True,
        poll_interval: float = 0.5
    ) -> Union[Dict, str]:
        """
        Get a chat completion using the API.
        
        Args:
            messages: List of messages in the format [{"role": "...", "content": "..."}]
            model_name: Name of the model to use (optional)
            params: Additional generation parameters (optional)
            wait_for_result: Whether to wait for the result (True) or return the task ID (False)
            poll_interval: Interval in seconds between polling for task status
            
        Returns:
            Chat completion response if wait_for_result is True, otherwise task ID
        """
        request_data = {"messages": messages}
        if model_name:
            request_data["model_name"] = model_name
        if params:
            request_data["params"] = params
        
        # Submit the chat completion request
        response = await self.client.post(
            f"{self.base_url}/chat/chat",
            json=request_data
        )
        response.raise_for_status()
        data = response.json()
        task_id = data["task_id"]
        
        if not wait_for_result:
            return task_id
        
        # Poll for the result
        return await self._wait_for_task_result(task_id, poll_interval)
    
    async def _wait_for_task_result(self, task_id: str, poll_interval: float = 0.5):
        """Poll for a task result until it's completed or failed"""
        while True:
            status_response = await self.client.get(f"{self.base_url}/tasks/{task_id}")
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                return status_data["result"]
            elif status_data["status"] == "failed":
                error = status_data.get("result", {}).get("error", "Unknown error")
                raise Exception(f"Task failed: {error}")
            
            # Wait before polling again
            await asyncio.sleep(poll_interval)
    
    async def get_task_status(self, task_id: str) -> Dict:
        """Get the status of a specific task"""
        response = await self.client.get(f"{self.base_url}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    
    async def list_tasks(
        self, status: Optional[str] = None, limit: int = 100, skip: int = 0
    ) -> List[Dict]:
        """List tasks with optional filtering"""
        params = {}
        if status:
            params["status"] = status
        params["limit"] = limit
        params["skip"] = skip
        
        response = await self.client.get(f"{self.base_url}/tasks", params=params)
        response.raise_for_status()
        return response.json()
    
    async def list_models(self) -> List[Dict]:
        """List all registered models and their status"""
        response = await self.client.get(f"{self.base_url}/models")
        response.raise_for_status()
        return response.json()
    
    async def load_model(
        self, model_name: str, model_type: str = "mlx", model_path: Optional[str] = None
    ) -> Dict:
        """
        Load a model into memory.
        
        Args:
            model_name: Name or identifier for the model
            model_type: Type of model backend (default: "mlx")
            model_path: Optional path or HF repo ID
            
        Returns:
            Response containing load status
        """
        request_data = {
            "model_name": model_name,
            "model_type": model_type
        }
        if model_path:
            request_data["model_path"] = model_path
        
        response = await self.client.post(
            f"{self.base_url}/models/load",
            json=request_data
        )
        response.raise_for_status()
        return response.json()
    
    async def unload_model(self, model_name: str) -> Dict:
        """Unload a model from memory"""
        response = await self.client.post(f"{self.base_url}/models/unload/{model_name}")
        response.raise_for_status()
        return response.json()


async def main():
    """Run a simple test of the API client"""
    client = MLXInferenceClient()
    
    try:
        # Check if the API is healthy
        print("Checking API health...")
        health = await client.health_check()
        print(f"API health: {health}")
        print("\n" + "-"*50 + "\n")
        
        # List available models
        print("Listing available models...")
        models = await client.list_models()
        print(f"Available models: {models}")
        print("\n" + "-"*50 + "\n")
        
        # Load the Llama 3.2 model
        print("Loading Llama 3.2 model...")
        model_name = "mlx-community/Llama-3.2-3B-Instruct-4bit"
        load_result = await client.load_model(model_name)
        print(f"Load result: {load_result}")
        print("\n" + "-"*50 + "\n")
        
        # Test text generation
        print("Testing text generation...")
        prompt = "Explain quantum computing in simple terms"
        start_time = time.time()
        result = await client.generate_text(prompt, model_name)
        elapsed = time.time() - start_time
        print(f"Result received in {elapsed:.2f} seconds:")
        print(result)
        print("\n" + "-"*50 + "\n")
        
        # Test chat completion
        print("Testing chat completion...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me about the solar system."}
        ]
        start_time = time.time()
        result = await client.chat_completion(messages, model_name)
        elapsed = time.time() - start_time
        print(f"Result received in {elapsed:.2f} seconds:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
