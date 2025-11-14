"""
LLM Client for NVIDIA minimax-m2 model.

This client uses NVIDIA API exclusively (no fallback providers).
Requires NVIDIA_API_KEY to be set in .env file.

Get your NVIDIA API key from: https://build.nvidia.com
"""

import os
from typing import Dict, Optional, Any
from langchain_openai import ChatOpenAI


class LLMClientError(Exception):
    """Custom exception for LLM client errors."""
    pass


def _get_nvidia_headers() -> Dict[str, str]:
    """Get NVIDIA API headers."""
    return {}


def _get_openrouter_headers() -> Dict[str, str]:
    """Get OpenRouter attribution headers."""
    headers: Dict[str, str] = {}
    site = os.getenv("OPENROUTER_SITE_URL")
    app = os.getenv("OPENROUTER_APP_NAME")
    if site:
        headers["HTTP-Referer"] = site
    if app:
        headers["X-Title"] = app
    return headers


def create_llm_client(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs: Any
) -> ChatOpenAI:
    """
    Create LLM client using NVIDIA minimax-m2 model.
    
    This application uses NVIDIA API exclusively for reliability.
    No fallback providers to avoid authentication issues.
    
    Args:
        model: Optional model override (will still use NVIDIA API)
        temperature: Optional temperature override (default: 0.7)
        **kwargs: Additional ChatOpenAI parameters
        
    Returns:
        ChatOpenAI: Configured NVIDIA LLM client
        
    Raises:
        LLMClientError: If NVIDIA_API_KEY is not found in .env
    """
    temp_val = temperature if temperature is not None else float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # If user explicitly provides a model, use it with best-guess provider
    if model:
        return _create_with_explicit_model(model, temp_val, **kwargs)
    
    # NVIDIA ONLY - No fallback to prevent OpenRouter errors
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if not nvidia_key:
        raise LLMClientError(
            "NVIDIA_API_KEY not found in .env file.\n"
            "This application requires NVIDIA API for minimax-m2 model.\n"
            "Get your key from: https://build.nvidia.com"
        )
    
    print(f"✨ Using NVIDIA minimax-m2 (no fallback)")
    return _create_nvidia_client(temp_val, **kwargs)


def _create_nvidia_client(temperature: float, **kwargs: Any) -> ChatOpenAI:
    """Create NVIDIA client for minimax-m2."""
    # For CrewAI compatibility, use OpenAI format since NVIDIA API is OpenAI-compatible
    model = os.getenv("DEFAULT_MODEL", "minimaxai/minimax-m2")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key:
        raise LLMClientError("NVIDIA_API_KEY not found")
    
    print(f"✨ Using NVIDIA {model}")
    
    # Use openai_api_base and openai_api_key for CrewAI/LiteLLM compatibility
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_base=base_url,
        openai_api_key=api_key,
        default_headers=_get_nvidia_headers(),
        **kwargs
    )


def _create_deepseek_client(temperature: float, **kwargs: Any) -> ChatOpenAI:
    """Create DeepSeek client with thinking enabled."""
    model = os.getenv("FALLBACK_MODEL", "deepseek-ai/deepseek-v3.1-terminus")
    base_url = os.getenv("FALLBACK_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.getenv("OPENROUTER_API_KEY")
    thinking_enabled = os.getenv("DEEPSEEK_THINKING", "True").lower() == "true"
    
    if not api_key:
        raise LLMClientError("OPENROUTER_API_KEY not found")
    
    print(f"✨ Using DeepSeek {model} (thinking={'on' if thinking_enabled else 'off'})")
    
    # Build model_kwargs with thinking option
    model_kwargs = kwargs.pop("model_kwargs", {})
    if thinking_enabled:
        model_kwargs["extra_body"] = {
            "chat_template_kwargs": {"thinking": True}
        }
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=base_url,
        api_key=api_key,
        default_headers=_get_openrouter_headers(),
        model_kwargs=model_kwargs,
        **kwargs
    )


def _create_openrouter_fallback_client(temperature: float, **kwargs: Any) -> ChatOpenAI:
    """Create OpenRouter fallback client."""
    model = os.getenv("OPENROUTER_FALLBACK_MODEL", "z-ai/glm-4.5-air:free")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        raise LLMClientError("OPENROUTER_API_KEY not found")
    
    print(f"✨ Using OpenRouter {model}")
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=base_url,
        api_key=api_key,
        default_headers=_get_openrouter_headers(),
        **kwargs
    )


def _create_with_explicit_model(model: str, temperature: float, **kwargs: Any) -> ChatOpenAI:
    """Create client when user explicitly provides a model name."""
    print(f"✨ Using explicit model: {model}")
    
    # This application only supports NVIDIA models
    # Force NVIDIA API regardless of model name
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key:
        raise LLMClientError(
            f"NVIDIA_API_KEY required for model: {model}\n"
            "Get your key from: https://build.nvidia.com"
        )
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=base_url,
        api_key=api_key,
        default_headers=_get_nvidia_headers(),
        **kwargs
    )


# Backward compatibility function
def create_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs: Any
) -> ChatOpenAI:
    """Alias for create_llm_client for backward compatibility."""
    return create_llm_client(model, temperature, **kwargs)

