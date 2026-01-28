"""LLM Model Configuration Utility

Provides a centralized way to configure and create LLM models based on environment variables.
Supports both OpenAI and Google Vertex AI (Gemini) models.
"""
import os
from typing import Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_llm_model(model_type: str = "default") -> Any:
    """Get configured LLM model based on environment variables.
    
    Args:
        model_type: Type of model usage ("default", "fast", "powerful").
                   - "default": balanced for most tasks
                   - "fast": optimized for speed (intent parsing, classification)
                   - "powerful": for complex reasoning tasks
    
    Returns:
        Configured model instance (OpenAIModel or GoogleModel)
        
    Environment Variables:
        LLM_PROVIDER: "openai" or "google-vertex" (default: "openai")
        
        For OpenAI:
            OPENAI_API_KEY: Your OpenAI API key
            OPENAI_MODEL: Model name (default: "gpt-4o-mini")
            OPENAI_MODEL_FAST: Fast model (default: "gpt-4o-mini")
            OPENAI_MODEL_POWERFUL: Powerful model (default: "gpt-4o")
            
        For Google Vertex AI:
            GOOGLE_API_KEY or Application Default Credentials
            GOOGLE_PROJECT: GCP project ID (required for Vertex AI)
            GOOGLE_LOCATION: GCP region (default: "us-central1")
            GOOGLE_MODEL: Model name (default: "gemini-2.0-flash-exp")
            GOOGLE_MODEL_FAST: Fast model (default: "gemini-2.0-flash-exp")
            GOOGLE_MODEL_POWERFUL: Powerful model (default: "gemini-2.0-pro-exp")
    
    Raises:
        ImportError: If required packages are not installed
        ValueError: If required environment variables are missing
    """
    provider = os.getenv('LLM_PROVIDER', 'openai').lower()

    if provider == 'openai':
        return _get_openai_model(model_type)
    if provider in ('google-vertex', 'google', 'vertexai', 'vertex'):
        return _get_google_vertex_model(model_type)

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {provider}. "
        "Supported values: 'openai', 'google-vertex'"
    )


def _get_openai_model(model_type: str) -> Any:
    """Get OpenAI model instance."""
    try:
        from pydantic_ai.models.openai import OpenAIModel
    except ImportError as e:
        raise ImportError(
            "OpenAI support requires 'openai' package. "
            "Install with: pip install 'pydantic-ai[openai]'"
        ) from e

    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI provider")

    # Select model based on type
    if model_type == "fast":
        model_name = os.getenv('OPENAI_MODEL_FAST', 'gpt-4o-mini')
    elif model_type == "powerful":
        model_name = os.getenv('OPENAI_MODEL_POWERFUL', 'gpt-4o')
    else:  # default
        model_name = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    return OpenAIModel(model_name)


def _get_google_vertex_model(model_type: str) -> Any:
    """Get Google Vertex AI model instance."""
    try:
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider
    except ImportError as e:
        raise ImportError(
            "Google Vertex AI support requires 'google-genai' package. "
            "Install with: pip install 'pydantic-ai-slim[google]'"
        ) from e

    # Select model based on type
    if model_type == "fast":
        model_name = os.getenv('GOOGLE_MODEL_FAST', 'gemini-2.0-flash-exp')
    elif model_type == "powerful":
        model_name = os.getenv('GOOGLE_MODEL_POWERFUL', 'gemini-2.0-pro-exp')
    else:  # default
        model_name = os.getenv('GOOGLE_MODEL', 'gemini-2.0-flash-exp')

    # Configure provider with Vertex AI settings
    provider_kwargs: dict[str, Any] = {
        'vertexai': True,  # Use Vertex AI instead of Generative Language API
    }

    # Add optional configuration
    if project := os.getenv('GOOGLE_PROJECT'):
        provider_kwargs['project'] = project

    if location := os.getenv('GOOGLE_LOCATION'):
        provider_kwargs['location'] = location
    else:
        provider_kwargs['location'] = 'us-central1'  # Default region

    # API key is optional if using Application Default Credentials
    if api_key := os.getenv('GOOGLE_API_KEY'):
        provider_kwargs['api_key'] = api_key

    provider = GoogleProvider(**provider_kwargs)
    return GoogleModel(model_name, provider=provider)


def get_model_name_string(model_type: str = "default") -> str:
    """Get model name string for simple agent initialization.

    For agents that accept a simple string model name (format: "provider:model"),
    this returns the appropriate string based on environment configuration.

    Args:
        model_type: Type of model usage ("default", "fast", "powerful")

    Returns:
        Model name string (e.g., "openai:gpt-4o-mini" or "google-vertex:gemini-2.0-flash-exp")
    """
    provider = os.getenv('LLM_PROVIDER', 'openai').lower()

    if provider == 'openai':
        if model_type == "fast":
            model = os.getenv('OPENAI_MODEL_FAST', 'gpt-4o-mini')
        elif model_type == "powerful":
            model = os.getenv('OPENAI_MODEL_POWERFUL', 'gpt-4o')
        else:
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        return f"openai:{model}"

    if provider in ('google-vertex', 'google', 'vertexai', 'vertex'):
        if model_type == "fast":
            model = os.getenv('GOOGLE_MODEL_FAST', 'gemini-2.0-flash-exp')
        elif model_type == "powerful":
            model = os.getenv('GOOGLE_MODEL_POWERFUL', 'gemini-2.0-pro-exp')
        else:
            model = os.getenv('GOOGLE_MODEL', 'gemini-2.0-flash-exp')

        # For string initialization, we need to configure the provider separately
        # Return a string that PydanticAI can understand
        # Note: This requires the environment to be set up with proper auth
        return f"google-vertex:{model}"

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {provider}. "
        "Supported values: 'openai', 'google-vertex'"
    )
