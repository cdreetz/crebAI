import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

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


async def stream_response(request: ChatCompletionRequest, scheduler: TaskScheduler) -> AsyncGenerator[bytes, None]:
    """
    Generator for streaming chat completion responses.
    
    Args:
        request: Chat completion request
        scheduler: Task scheduler instance
        
    Yields:
        SSE formatted response chunks
    """
    try:
        # Get streaming parameters
        stream_params = request.params.copy() if request.params else {}
        stream_params["stream"] = True
        
        async_generator = scheduler.stream_chat_completion(
            request.messages, request.model_name, stream_params
        )

        async for chunk in async_generator:
            # Format the chunk as SSE
            yield b"data: " + json.dumps(chunk).encode() + b"\n\n"
        
        # Send the [DONE] message to indicate completion
        yield b"data: [DONE]\n\n"
    except Exception as e:
        # Send an error message
        error_json = {"error": {"message": str(e), "type": "server_error"}}
        yield b"data: " + json.dumps(error_json).encode() + b"\n\n"
        yield b"data: [DONE]\n\n"


@router.post("/chat/stream")
async def stream_chat_completion(
    request: ChatCompletionRequest,
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """
    Stream a chat completion response directly.
    
    This endpoint streams the response as it's generated, following the OpenAI streaming format.
    """
    return StreamingResponse(
        stream_response(request, scheduler),
        media_type="text/event-stream"
    )
