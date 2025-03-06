from typing import Dict, Optional

from app.core.logging import get_logger
from app.llm.models.base import BaseLLMModel
from app.llm.models.mlx_model import MLXModel

logger = get_logger(__name__)


# Registry of available model backends
_MODEL_REGISTRY = {
    "mlx": MLXModel,
}

# Cache of loaded models
_LOADED_MODELS: Dict[str, BaseLLMModel] = {}


def create_model(
    model_type: str, 
    model_name: str, 
    model_path: Optional[str] = None,
    **kwargs
) -> BaseLLMModel:
    """
    Create a model instance of the specified type.
    
    Args:
        model_type: Type of model backend (e.g., "mlx")
        model_name: Name identifier for the model
        model_path: Optional path or HF repo ID for the model
        **kwargs: Additional arguments for the model constructor
        
    Returns:
        Instance of a BaseLLMModel
        
    Raises:
        ValueError: If the model type is not supported
    """
    if model_type not in _MODEL_REGISTRY:
        supported = ", ".join(_MODEL_REGISTRY.keys())
        raise ValueError(f"Unsupported model type: {model_type}. Supported types: {supported}")
    
    model_class = _MODEL_REGISTRY[model_type]
    return model_class(model_name, model_path, **kwargs)


def get_model(model_name: str, load: bool = False) -> Optional[BaseLLMModel]:
    """
    Get a model from the cache or return None if not found.
    
    Args:
        model_name: Name of the model to retrieve
        load: Whether to load the model if it's not loaded
        
    Returns:
        Model instance or None if not found
    """
    model = _LOADED_MODELS.get(model_name)
    
    if model and load and not model.is_loaded:
        logger.info(f"Model {model_name} found in cache but not loaded, will load")
    
    return model


def register_model(model: BaseLLMModel) -> None:
    """
    Register a model in the cache.
    
    Args:
        model: Model instance to register
    """
    _LOADED_MODELS[model.name] = model
    logger.info(f"Registered model in cache: {model.name}")


def unregister_model(model_name: str) -> bool:
    """
    Remove a model from the cache.
    
    Args:
        model_name: Name of the model to remove
        
    Returns:
        True if the model was removed, False otherwise
    """
    if model_name in _LOADED_MODELS:
        model = _LOADED_MODELS.pop(model_name)
        if model.is_loaded:
            model.unload()
        logger.info(f"Unregistered model from cache: {model_name}")
        return True
    return False
