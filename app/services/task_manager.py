import asyncio
import uuid
import time
from typing import Dict, List, Any, Optional

from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class TaskManager:
    """Manages the lifecycle of inference tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, Any] = {}
        self.lock = asyncio.Lock()
    
    async def create_task(self, task_type: str, params: Dict) -> str:
        """
        Create a new task and return its ID.
        
        Args:
            task_type: Type of task (e.g., "text_generation", "chat_completion")
            params: Task parameters
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        async with self.lock:
            self.tasks[task_id] = {
                "id": task_id,
                "type": task_type,
                "params": params,
                "status": "pending",
                "created_at": time.time(),
            }
        
        logger.info(f"Created task {task_id} of type {task_type}")
        return task_id
    
    async def update_task_status(self, task_id: str, status: str, result: Optional[Any] = None) -> None:
        """
        Update the status of a task and optionally store its result.
        
        Args:
            task_id: ID of the task to update
            status: New status (e.g., "processing", "completed", "failed")
            result: Optional result data to store
        
        Raises:
            KeyError: If the task ID doesn't exist
        """
        async with self.lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")
            
            self.tasks[task_id]["status"] = status
            
            if result is not None:
                self.results[task_id] = result
                self.tasks[task_id]["completed_at"] = time.time()
            
            logger.debug(f"Updated task {task_id} status to {status}")
    
    async def get_task_status(self, task_id: str) -> Dict:
        """
        Get the current status and info for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task information dictionary
            
        Raises:
            KeyError: If the task ID doesn't exist
        """
        async with self.lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")
            
            task_info = self.tasks[task_id].copy()
            if task_info["status"] == "completed" and task_id in self.results:
                task_info["result"] = self.results[task_id]
            
            return task_info

    async def list_tasks(self, status: Optional[str] = None, limit: int = 100, skip: int = 0) -> List[Dict]:
        """
        List tasks with optional filtering.
        
        Args:
            status: Filter by status
            limit: Maximum number of tasks to return
            skip: Number of tasks to skip
            
        Returns:
            List of task information dictionaries
        """
        async with self.lock:
            tasks = list(self.tasks.values())
            
            if status:
                tasks = [task for task in tasks if task["status"] == status]
            
            # Sort by creation time (newest first)
            tasks.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Apply pagination
            tasks = tasks[skip:skip+limit]
            
            return tasks
    
    async def clean_old_tasks(self, max_age_hours: Optional[int] = None) -> int:
        """
        Remove tasks older than max_age_hours.
        
        Args:
            max_age_hours: Maximum age in hours (default from settings)
            
        Returns:
            Number of tasks removed
        """
        max_age_hours = max_age_hours or settings.TASK_MAX_AGE_HOURS
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        removed_count = 0
        async with self.lock:
            to_remove = []
            for task_id, task in self.tasks.items():
                if current_time - task["created_at"] > max_age_seconds:
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                self.tasks.pop(task_id, None)
                self.results.pop(task_id, None)
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} tasks older than {max_age_hours} hours")
        
        return removed_count
