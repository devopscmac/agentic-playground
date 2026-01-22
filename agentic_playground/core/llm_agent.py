"""
LLM-powered agent implementation.
"""

from typing import Optional
from .agent import Agent, AgentConfig
from .message import Message, MessageType
from ..llm import LLMProvider, LLMMessage


class LLMAgent(Agent):
    """
    An agent that uses an LLM for reasoning and generating responses.
    """

    def __init__(self, config: AgentConfig, llm_provider: LLMProvider):
        super().__init__(config)
        self.llm_provider = llm_provider
        self.conversation_history: list[LLMMessage] = []

        # Initialize with system prompt if provided
        if config.system_prompt:
            self.conversation_history.append(
                LLMMessage(role="system", content=config.system_prompt)
            )

    async def process_message(self, message: Message) -> None:
        """
        Process an incoming message using the LLM.

        The agent will:
        1. Add the message to its conversation history
        2. Generate a response using the LLM
        3. Send the response back to the sender or as specified
        """

        # Format the incoming message for the LLM
        user_message = self._format_message_for_llm(message)
        self.conversation_history.append(user_message)

        try:
            # Generate response using LLM
            response = await self.llm_provider.generate(
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=1024
            )

            # Add assistant response to history
            self.conversation_history.append(
                LLMMessage(role="assistant", content=response.content)
            )

            # Send response back
            response_message = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                content=response.content,
                metadata={
                    "model": response.model,
                    "usage": response.usage,
                    "in_reply_to": message.id
                }
            )

            await self.send_message(response_message)

        except Exception as e:
            error_message = Message(
                type=MessageType.ERROR,
                sender=self.id,
                recipient=message.sender,
                content=f"Error generating response: {str(e)}",
                metadata={"error": str(e)}
            )
            await self.send_message(error_message)

    def _format_message_for_llm(self, message: Message) -> LLMMessage:
        """
        Format an incoming message for the LLM.

        Converts the agent message into a format the LLM understands.
        """
        content = f"Message from {message.sender} ({message.type.value}): {message.content}"

        if message.metadata:
            content += f"\nMetadata: {message.metadata}"

        return LLMMessage(role="user", content=content)

    def clear_history(self, keep_system_prompt: bool = True) -> None:
        """
        Clear the conversation history.

        Args:
            keep_system_prompt: If True, keep the system prompt in history
        """
        if keep_system_prompt and self.conversation_history:
            system_messages = [
                msg for msg in self.conversation_history
                if msg.role == "system"
            ]
            self.conversation_history = system_messages
        else:
            self.conversation_history = []
