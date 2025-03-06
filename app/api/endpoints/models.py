from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Any, Optional

from app.llm.interface import LLMInterface

router = APIRouter()


@router.get("/")
async def list_models():
    """
    List all registered models and their status.
    """
    return await LLMInterface.list_models()


@router.post("/load")
async def load_model(
    model_name: str = Body(..., embed=True),
    model_type: str = Body("mlx", embed=True),
    model_path: Optional[str] = Body(None, embed=True)
):
    """
    Load a model into memory.
    
    - **model_name**: Name or identifier for the model
    - **model_type**: Type of model backend (default: "mlx")
    - **model_path**: Optional path or HF repo ID (defaults to model_name)
    """
    try:
        result = await LLMInterface.load_model(model_name, model_type, model_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@router.post("/unload/{model_name}")
async def unload_model(model_name: str):
    """
    Unload a model from memory.
    
    - **model_name**: Name of the model to unload
    """
    success = LLMInterface.unload_model(model_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found or already unloaded")
    return {"status": "success", "message": f"Model {model_name} unloaded"}
