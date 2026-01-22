"""
Message system for agent communication.
"""

from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class MessageType(str, Enum):
    """Types of messages that can be passed between agents."""

    TASK = "task"  # A task to be performed
    QUERY = "query"  # A question or information request
    RESPONSE = "response"  # A response to a query or task
    BROADCAST = "broadcast"  # A message to all agents
    SYSTEM = "system"  # System-level message
    ERROR = "error"  # Error notification


class Message(BaseModel):
    """
    A message passed between agents or from the orchestrator.
    """

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    type: MessageType
    sender: str  # Agent ID or "system"
    recipient: Optional[str] = None  # None for broadcast
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    def __str__(self) -> str:
        recipient_str = f" -> {self.recipient}" if self.recipient else ""
        return f"[{self.type.value}] {self.sender}{recipient_str}: {self.content}"
