import asyncio
from fastapi import APIRouter, Depends, HTTPException

from app.models.request import TaskListRequest
from app.services.task_manager import TaskManager
from app.api.dependencies import get_task_manager

router = APIRouter()


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    Get the status of a specific task.
    
    - **task_id**: ID of the task to retrieve
    """
    try:
        task_status = await task_manager.get_task_status(task_id)

        # if the result contains any coroutines we need to await the
        if task_status.get("status") == "completed" and task_status.get("result") is not None: 
            result = task_status.get("result")
            if asyncio.iscoroutine(result):
                try:
                    task_status["result"] = await result
                except RuntimeError as e:
                    if "cannot reuse already await coroutine" in str(e):
                        pass
                    else:
                        raise
                except Exception as e:
                    task_status["result"] = {"error": f"Error in task execution: {str(e)}"}
                    task_status["status"] = "failed"

        return task_status
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@router.get("/")
async def list_tasks(
    request: TaskListRequest = Depends(),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    List tasks with optional filtering.
    
    - **status**: Filter by task status (optional)
    - **limit**: Maximum number of tasks to return
    - **skip**: Number of tasks to skip
    """
    tasks = await task_manager.list_tasks(
        status=request.status,
        limit=request.limit,
        skip=request.skip
    )
    return tasks
