"""
OpenAI LLM provider.
"""

import os
from typing import Optional
from openai import AsyncOpenAI

from ..base import LLMProvider, LLMMessage, LLMResponse


class OpenAIProvider(LLMProvider):
    """
    Provider for OpenAI models (GPT-4, GPT-3.5, etc.).
    """

    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        api_key: Optional[str] = None
    ):
        super().__init__(model, api_key or os.getenv("OPENAI_API_KEY"))
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate a response using OpenAI."""

        # Format messages for OpenAI API
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Make API call
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Extract response
        content = response.choices[0].message.content or ""

        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=content,
            model=response.model,
            usage=usage,
            metadata={"id": response.id}
        )
