import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        file_path: Path to the YAML config file
        
    Returns:
        Dictionary with configuration values
    """
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        logger.info(f"Loaded configuration from {file_path}")
        return config or {}
    except Exception as e:
        logger.error(f"Error loading config from {file_path}: {str(e)}")
        return {}


def get_config_path() -> str:
    """
    Get the path to the configuration file.
    
    Checks for a config file in the following locations:
    1. Path specified by CONFIG_FILE environment variable
    2. ./config.yaml in the current directory
    3. ~/.config/llm_inference_server/config.yaml
    4. /etc/llm_inference_server/config.yaml
    
    Returns:
        Path to the config file, or None if not found
    """
    # Check environment variable
    if os.environ.get("CONFIG_FILE"):
        return os.environ["CONFIG_FILE"]
    
    # Check current directory
    if Path("config.yaml").exists():
        return "config.yaml"
    
    # Check user config directory
    user_config = Path.home() / ".config" / "llm_inference_server" / "config.yaml"
    if user_config.exists():
        return str(user_config)
    
    # Check system config directory
    system_config = Path("/etc") / "llm_inference_server" / "config.yaml"
    if system_config.exists():
        return str(system_config)
    
    logger.warning("No config file found, using default settings")
    return ""


def get_configured_models() -> List[Dict[str, Any]]:
    """
    Get the list of configured models from the config file.
    
    Returns:
        List of model configurations
    """
    config_path = get_config_path()
    if not config_path:
        return []
    
    config = load_yaml_config(config_path)
    return config.get("models", [])


def get_default_model() -> Optional[str]:
    """
    Get the name of the default model from the config file.
    
    Returns:
        Name of the default model, or None if not specified
    """
    models = get_configured_models()
    for model in models:
        if model.get("default", False):
            return model.get("name")
    
    # If no default is specified, use the first model
    if models:
        return models[0].get("name")
    
    return None
