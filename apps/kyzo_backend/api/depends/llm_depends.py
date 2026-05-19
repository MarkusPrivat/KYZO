"""
Dependency providers for AI and LLM services in the Kyzo backend.
"""
from apps.kyzo_backend.services import (
    llm_orchestrator_instance,
    image_processing_instance,
    LLMOrchestrator,
    ImageProcessingService
)

def get_llm_orchestrator() -> LLMOrchestrator:
    """
    FastAPI dependency provider that yields a thread-safe, single-instance
    LLMOrchestrator to prevent client re-initialization overhead.
    """
    return llm_orchestrator_instance


def get_image_service() -> ImageProcessingService:
    """
    FastAPI dependency provider that yields a single-instance ImageProcessingService.
    """
    return image_processing_instance