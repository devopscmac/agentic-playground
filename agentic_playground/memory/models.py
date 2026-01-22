"""
Data models for the memory system.

This module defines the core data structures used throughout the memory system,
including sessions, messages, memories, and their associated metadata.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import uuid


class MemoryType(str, Enum):
    """Types of memories that can be stored."""
    WORKING = "working"  # Current conversation context (auto-managed)
    EPISODIC = "episodic"  # Specific past interactions
    SEMANTIC = "semantic"  # Extracted facts and knowledge


class MessageType(str, Enum):
    """Types of messages that can be stored."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    BROADCAST = "broadcast"


class Session(BaseModel):
    """Represents a conversation session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StoredMessage(BaseModel):
    """Represents a message stored in the memory system."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: MessageType
    sender: str
    recipient: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationEntry(BaseModel):
    """Represents a single entry in an LLM conversation history."""
    id: Optional[int] = None
    agent_id: str
    session_id: str
    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Memory(BaseModel):
    """Represents a stored memory (episodic or semantic)."""
    id: Optional[int] = None
    agent_id: str
    session_id: str
    memory_type: MemoryType
    content: str
    embedding_text: str  # Searchable text representation
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = Field(default=0)
    last_accessed: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentState(BaseModel):
    """Represents the saved state of an agent."""
    agent_id: str
    session_id: str
    state_data: Dict[str, Any]
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContextWindow(BaseModel):
    """Represents a prepared context window for LLM consumption."""
    messages: list[Dict[str, str]]
    total_tokens: int
    pruned_count: int = 0
    retrieved_memories: list[Memory] = Field(default_factory=list)
