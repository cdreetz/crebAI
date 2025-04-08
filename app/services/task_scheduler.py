import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator

from app.core.logging import get_logger
from app.core.config import get_settings
from app.services.task_manager import TaskManager
from app.llm.interface import LLMInterface
from app.llm.models.factory import create_model, get_model, register_model

logger = get_logger(__name__)
settings = get_settings()


class TaskScheduler:
    """Schedules and processes LLM inference tasks"""
    
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        self.llm = LLMInterface()
        self.running = False
        self.worker_task = None
        self.cleanup_task = None
    
    async def start(self) -> None:
        """Start the task scheduler"""
        if self.running:
            return
        
        self.running = True
        self.worker_task = asyncio.create_task(self._task_worker())
        self.cleanup_task = asyncio.create_task(self._cleanup_worker())
        logger.info("Task scheduler started")
    
    async def stop(self) -> None:
        """Stop the task scheduler"""
        if not self.running:
            return
        
        self.running = False
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Task scheduler stopped")
    
    async def schedule_text_generation(
        self, prompt: str, model_name: Optional[str] = None, params: Optional[Dict] = None
    ) -> str:
        """
        Schedule a text generation task.
        
        Args:
            prompt: Text prompt for generation
            model_name: Name of the model to use (or default)
            params: Generation parameters
            
        Returns:
            Task ID
        """
        model_name = model_name or settings.DEFAULT_MODEL_NAME
        task_params = {
            "prompt": prompt,
            "model_name": model_name,
            "params": params or {}
        }
        return await self.task_manager.create_task("text_generation", task_params)
    
    async def schedule_chat_completion(
        self, messages: List[Dict], model_name: Optional[str] = None, params: Optional[Dict] = None
    ) -> str:
        """
        Schedule a chat completion task.
        
        Args:
            messages: List of chat messages
            model_name: Name of the model to use (or default)
            params: Generation parameters
            
        Returns:
            Task ID
        """
        model_name = model_name or settings.DEFAULT_MODEL_NAME
        task_params = {
            "messages": messages,
            "model_name": model_name,
            "params": params or {}
        }
        return await self.task_manager.create_task("chat_completion", task_params)

    async def stream_chat_completion(
        self, messages: List[Dict], model_name: Optional[str] = None, params: Optional[Dict] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream a chat completion response directly.

        Args:
            messages: List of chat messages
            model_name: Name of a model to use
            params: Generation parameters

        Yields:
            Chunks of the generated response
        """
        model_name = model_name or settings.DEFAULT_MODEL_NAME
        params = params or {}

        try:
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

            # Check if the model supports streaming
            if not hasattr(model, "chat_stream"):
                raise NotImplementedError(f"Model {model_name} does not support streaming")

            # Call the model's chat_stream method
            async for chunk in model.chat_stream(messages, params):
                yield chunk
        
        except Exception as e:
            logger.error(f"Error in streaming chat completion: {str(e)}")
            yield {
                "error": {
                    "message": str(e),
                    "type": "server_error"
                }
            }

    
    async def _process_text_generation(self, task_id: str, params: Dict) -> None:
        """Process a text generation task"""
        try:
            result = await self.llm.generate_text(
                params["prompt"], 
                params["model_name"], 
                params.get("params", {})
            )
            await self.task_manager.update_task_status(task_id, "completed", result)
        except Exception as e:
            logger.error(f"Error processing text generation task {task_id}: {str(e)}")
            await self.task_manager.update_task_status(task_id, "failed", {"error": str(e)})
    
    async def _process_chat_completion(self, task_id: str, params: Dict) -> None:
        """Process a chat completion task"""
        try:
            result = await self.llm.chat_completion(
                params["messages"], 
                params["model_name"], 
                params.get("params", {})
            )
            await self.task_manager.update_task_status(task_id, "completed", result)
        except Exception as e:
            logger.error(f"Error processing chat completion task {task_id}: {str(e)}")
            await self.task_manager.update_task_status(task_id, "failed", {"error": str(e)})
    
    async def _task_worker(self) -> None:
        """Worker that processes pending tasks"""
        while self.running:
            try:
                # Get pending tasks
                pending_tasks = await self.task_manager.list_tasks(status="pending")
                
                # Process each pending task
                for task in pending_tasks:
                    task_id = task["id"]
                    await self.task_manager.update_task_status(task_id, "processing")
                    
                    if task["type"] == "text_generation":
                        asyncio.create_task(self._process_text_generation(task_id, task["params"]))
                    elif task["type"] == "chat_completion":
                        asyncio.create_task(self._process_chat_completion(task_id, task["params"]))
                    else:
                        await self.task_manager.update_task_status(
                            task_id, "failed", {"error": f"Unknown task type: {task['type']}"}
                        )
                
                # Wait a bit before checking for new tasks
                await asyncio.sleep(0.1)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task worker: {str(e)}")
                await asyncio.sleep(1)  # Sleep longer on error
    
    async def _cleanup_worker(self) -> None:
        """Worker that periodically cleans up old tasks"""
        cleanup_interval = settings.TASK_CLEANUP_INTERVAL_HOURS * 3600  # Convert to seconds
        
        while self.running:
            try:
                await asyncio.sleep(cleanup_interval)
                await self.task_manager.clean_old_tasks()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup worker: {str(e)}")
