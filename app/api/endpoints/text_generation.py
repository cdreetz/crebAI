from fastapi import APIRouter, Depends, HTTPException

from app.models.request import TextGenerationRequest
from app.models.response import TaskResponse
from app.services.task_scheduler import TaskScheduler
from app.api.dependencies import get_scheduler

router = APIRouter()


@router.post("/generate", response_model=TaskResponse)
async def generate_text(
    request: TextGenerationRequest,
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """
    Schedule a text generation task.
    
    The task will be processed asynchronously, and the result can be retrieved
    using the returned task ID.
    """
    task_id = await scheduler.schedule_text_generation(
        request.prompt, request.model_name, request.params
    )
    return {"task_id": task_id}
