"""
Anthropic (Claude) LLM provider.
"""

import os
from typing import Optional
from anthropic import AsyncAnthropic

from ..base import LLMProvider, LLMMessage, LLMResponse


class AnthropicProvider(LLMProvider):
    """
    Provider for Anthropic's Claude models.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None
    ):
        super().__init__(model, api_key or os.getenv("ANTHROPIC_API_KEY"))
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = AsyncAnthropic(api_key=self.api_key)

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate a response using Claude."""

        # Extract system message if present
        system_message = None
        formatted_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Make API call
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message if system_message else None,
            messages=formatted_messages,
            **kwargs
        )

        # Extract response content
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            metadata={"id": response.id}
        )
