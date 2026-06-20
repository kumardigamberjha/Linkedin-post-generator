"""LLM factory — build provider-specific CrewAI LLM instances."""

import logging
from typing import Any

from crewai import LLM

from app.core.config import Settings

logger = logging.getLogger(__name__)


def build_llm(provider: str, settings: Settings) -> Any:
    provider = provider.lower().strip()

    def _ollama():
        model = f"ollama/{settings.ollama_model}"
        logger.info("Building LLM  ▸ provider=ollama  model=%s", settings.ollama_model)
        return LLM(model=model, base_url=settings.ollama_api_base)

    if provider.startswith("ollama/"):
        logger.info("Building LLM  ▸ provider=ollama  model=%s", provider)
        return LLM(model=provider, base_url=settings.ollama_api_base)

    if provider == "ollama":
        return _ollama()

    if provider == "google" or provider.startswith("google/"):
        if not settings.gemini_api_key:
            logger.warning("Missing gemini_api_key, falling back to ollama.")
            return _ollama()

        # Default to 3.5 flash if no specific model provided
        model = provider.split("/", 1)[1] if "/" in provider else "gemini-3.5-flash"
        logger.info("Building LLM  ▸ provider=google  model=%s", model)
        return LLM(model=f"gemini/{model}", api_key=settings.gemini_api_key)

    if provider == "nvidia" or provider.startswith("nvidia/"):
        if not settings.nvidia_api_key:
            logger.warning("Missing nvidia_api_key, falling back to ollama.")
            return _ollama()

        model = provider.split("/", 1)[1] if "/" in provider else "z-ai/glm-5.1"
        logger.info("Building LLM  ▸ provider=nvidia  model=%s", model)
        return LLM(
            model=f"openai/{model}",
            api_key=settings.nvidia_api_key,
            base_url="https://integrate.api.nvidia.com/v1"
        )

    logger.warning("Unknown provider '%s', falling back to ollama.", provider)
    return _ollama()
