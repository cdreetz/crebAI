from fastapi import APIRouter, Depends, HTTPException

from app.models.request import ChatCompletionRequest
from app.models.response import TaskResponse
from app.services.task_scheduler import TaskScheduler
from app.api.dependencies import get_scheduler

router = APIRouter()


@router.post("/chat", response_model=TaskResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """
    Schedule a chat completion task.
    
    The task will be processed asynchronously, and the result can be retrieved
    using the returned task ID.
    """
    task_id = await scheduler.schedule_chat_completion(
        request.messages, request.model_name, request.params
    )
    return {"task_id": task_id}
