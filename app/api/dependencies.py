from fastapi import Depends, Request

from app.services.task_manager import TaskManager
from app.services.task_scheduler import TaskScheduler


def get_task_manager(request: Request):
    """Get the task manager from app state"""
    return request.app.state.task_manager


def get_scheduler(request: Request, task_manager: TaskManager = Depends(get_task_manager)):
    """Get the task scheduler from app state"""
    return request.app.state.scheduler
