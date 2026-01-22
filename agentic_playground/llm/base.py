"""
Base interface for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from pydantic import BaseModel


class LLMMessage(BaseModel):
    """A message in the LLM conversation."""

    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """Response from an LLM."""

    content: str
    model: str
    usage: Optional[dict[str, int]] = None
    metadata: dict[str, Any] = {}


class LLMProvider(ABC):
    """
    Base class for LLM providers.

    Provides a unified interface for different LLM APIs.
    """

    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse object
        """
        pass

    def create_message(self, role: str, content: str) -> LLMMessage:
        """Helper to create an LLM message."""
        return LLMMessage(role=role, content=content)
