"""
Base agent class for the multi-agent system.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Callable, Awaitable
from pydantic import BaseModel, Field

from .message import Message, MessageType


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    name: str
    role: str  # High-level role description
    system_prompt: Optional[str] = None  # System prompt for LLM-based agents
    capabilities: list[str] = Field(default_factory=list)
    max_iterations: int = 10
    metadata: dict = Field(default_factory=dict)


class Agent(ABC):
    """
    Base class for all agents in the system.

    Agents can:
    - Receive and process messages
    - Send messages to other agents or broadcast
    - Use LLMs for reasoning (optional)
    - Maintain internal state
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = config.name
        self.inbox: asyncio.Queue[Message] = asyncio.Queue()
        self.running = False
        self.message_callback: Optional[Callable[[Message], Awaitable[None]]] = None
        self._state: dict = {}

    @property
    def state(self) -> dict:
        """Access agent's internal state."""
        return self._state

    def set_message_callback(
        self, callback: Callable[[Message], Awaitable[None]]
    ) -> None:
        """Set callback for sending messages (typically set by orchestrator)."""
        self.message_callback = callback

    async def send_message(self, message: Message) -> None:
        """Send a message through the orchestrator."""
        if self.message_callback:
            await self.message_callback(message)
        else:
            raise RuntimeError(f"Agent {self.id} has no message callback set")

    async def receive_message(self, message: Message) -> None:
        """Receive a message into the inbox."""
        await self.inbox.put(message)

    @abstractmethod
    async def process_message(self, message: Message) -> None:
        """
        Process an incoming message. Must be implemented by subclasses.

        Args:
            message: The message to process
        """
        pass

    async def start(self) -> None:
        """Start the agent's message processing loop."""
        self.running = True
        while self.running:
            try:
                message = await asyncio.wait_for(self.inbox.get(), timeout=0.1)
                await self.process_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                error_msg = Message(
                    type=MessageType.ERROR,
                    sender=self.id,
                    content=f"Error processing message: {str(e)}",
                    metadata={"error": str(e)}
                )
                if self.message_callback:
                    await self.message_callback(error_msg)

    async def stop(self) -> None:
        """Stop the agent's message processing loop."""
        self.running = False

    def __str__(self) -> str:
        return f"Agent({self.id}, role={self.config.role})"
