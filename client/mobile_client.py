import requests
import time
import json
from typing import Dict, List, Any, Optional, Union


class MLXMobileClient:
    """
    Synchronous client for the MLX Inference Server API, suitable for mobile apps.
    
    This client handles communication with the server and provides
    methods for text generation and chat completions. It's designed to be
    easily usable in mobile frameworks that support Python, like BeeWare/Toga
    or Kivy, or can be ported to Swift/Kotlin.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the inference server API
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.timeout = 60.0  # Long timeout for model loading
    
    def close(self):
        """Close the HTTP session"""
        self.session.close()
    
    def health_check(self) -> Dict:
        """Check if the API is healthy"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def generate_text(
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
        response = self.session.post(
            f"{self.base_url}/text/generate",
            json=request_data
        )
        response.raise_for_status()
        data = response.json()
        task_id = data["task_id"]
        
        if not wait_for_result:
            return task_id
        
        # Poll for the result
        return self._wait_for_task_result(task_id, poll_interval)
    
    def chat_completion(
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
        response = self.session.post(
            f"{self.base_url}/chat/chat",
            json=request_data
        )
        response.raise_for_status()
        data = response.json()
        task_id = data["task_id"]
        
        if not wait_for_result:
            return task_id
        
        # Poll for the result
        return self._wait_for_task_result(task_id, poll_interval)
    
    def _wait_for_task_result(self, task_id: str, poll_interval: float = 0.5):
        """Poll for a task result until it's completed or failed"""
        while True:
            status_response = self.session.get(f"{self.base_url}/tasks/{task_id}")
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                return status_data["result"]
            elif status_data["status"] == "failed":
                error = status_data.get("result", {}).get("error", "Unknown error")
                raise Exception(f"Task failed: {error}")
            
            # Wait before polling again
            time.sleep(poll_interval)
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get the status of a specific task"""
        response = self.session.get(f"{self.base_url}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def list_models(self) -> List[Dict]:
        """List all registered models and their status"""
        response = self.session.get(f"{self.base_url}/models")
        response.raise_for_status()
        return response.json()


class ChatView:
    """
    A simple chat UI example that could be integrated into a mobile app.
    
    This class provides a basic structure for a chat interface that uses
    the MLXMobileClient to communicate with the inference server.
    """
    
    def __init__(self, server_url: str):
        """Initialize the chat view"""
        self.client = MLXMobileClient(server_url)
        self.chat_history = []
        self.system_message = {"role": "system", "content": "You are a helpful assistant."}
        self.is_generating = False
        self.current_task_id = None
    
    def add_user_message(self, message: str) -> None:
        """Add a user message to the chat history"""
        self.chat_history.append({"role": "user", "content": message})
    
    def add_assistant_message(self, message: str) -> None:
        """Add an assistant message to the chat history"""
        self.chat_history.append({"role": "assistant", "content": message})
    
    def get_messages_for_api(self) -> List[Dict]:
        """Get messages formatted for the API"""
        return [self.system_message] + self.chat_history
    
    def send_message(self, message: str) -> str:
        """
        Send a user message and get a response.
        
        Args:
            message: User message to send
            
        Returns:
            Task ID for the ongoing generation
        """
        if self.is_generating:
            return None
        
        self.add_user_message(message)
        self.is_generating = True
        
        # Get all messages for context
        messages = self.get_messages_for_api()
        
        # Send asynchronously (don't wait for result)
        try:
            task_id = self.client.chat_completion(
                messages=messages,
                wait_for_result=False
            )
            self.current_task_id = task_id
            return task_id
        except Exception as e:
            self.is_generating = False
            raise e
    
    def check_response(self) -> Dict:
        """
        Check if the response is ready.
        
        Returns:
            None if still processing, response dict if ready
        """
        if not self.is_generating or not self.current_task_id:
            return None
        
        try:
            status = self.client.get_task_status(self.current_task_id)
            
            if status["status"] == "completed":
                self.is_generating = False
                result = status["result"]
                message = result["choices"][0]["message"]["content"]
                self.add_assistant_message(message)
                return result
            elif status["status"] == "failed":
                self.is_generating = False
                return {"error": status.get("result", {}).get("error", "Unknown error")}
            
            # Still processing
            return None
            
        except Exception as e:
            self.is_generating = False
            return {"error": str(e)}
    
    def cancel_generation(self) -> None:
        """Cancel the current generation"""
        self.is_generating = False
        self.current_task_id = None
    
    def close(self) -> None:
        """Close the client connection"""
        self.client.close()


def mobile_client_example():
    """Example usage of the mobile client"""
    # This would be integrated into your mobile app's UI logic
    client = MLXMobileClient("http://your-mac-ip:8000/api/v1")
    
    try:
        # Check connection
        health = client.health_check()
        print(f"Server status: {health['status']}")
        
        # List available models
        models = client.list_models()
        print(f"Available models: {json.dumps(models, indent=2)}")
        
        # Example of sending a message
        response = client.chat_completion([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! How are you doing today?"}
        ])
        
        # Extract the assistant's message
        assistant_message = response["choices"][0]["message"]["content"]
        print(f"Assistant: {assistant_message}")
        
    finally:
        client.close()


if __name__ == "__main__":
    mobile_client_example()
