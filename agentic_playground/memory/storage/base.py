"""
Abstract base class for storage backends.

This module defines the interface that all storage backends must implement.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from agentic_playground.memory.models import (
    Session,
    StoredMessage,
    ConversationEntry,
    Memory,
    AgentState,
    MemoryType,
)


class StorageBackend(ABC):
    """
    Abstract base class for memory storage backends.

    All storage implementations (SQLite, PostgreSQL, Redis, etc.) must
    implement this interface to be compatible with the MemoryManager.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the storage backend.

        This should create necessary database tables, indexes, connections, etc.
        Must be called before any other operations.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the storage backend and clean up resources.

        Should close database connections, file handles, etc.
        """
        pass

    # Session operations
    @abstractmethod
    async def create_session(self, session: Session) -> str:
        """
        Create a new session.

        Args:
            session: Session object to create

        Returns:
            The session_id of the created session
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID.

        Args:
            session_id: The session identifier

        Returns:
            Session object if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_sessions(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "last_active"
    ) -> List[Session]:
        """
        List all sessions.

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            order_by: Field to order by (e.g., "created_at", "last_active")

        Returns:
            List of Session objects
        """
        pass

    @abstractmethod
    async def update_session(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """
        Update session metadata.

        Args:
            session_id: The session identifier
            metadata: New metadata to merge with existing metadata
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session and all associated data.

        Args:
            session_id: The session identifier
        """
        pass

    # Message operations
    @abstractmethod
    async def store_message(self, message: StoredMessage) -> str:
        """
        Store a message.

        Args:
            message: StoredMessage object to store

        Returns:
            The message ID
        """
        pass

    @abstractmethod
    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        sender: Optional[str] = None,
    ) -> List[StoredMessage]:
        """
        Retrieve messages for a session.

        Args:
            session_id: The session identifier
            limit: Maximum number of messages to return (None for all)
            offset: Number of messages to skip
            sender: Filter by sender (optional)

        Returns:
            List of StoredMessage objects
        """
        pass

    @abstractmethod
    async def get_message_count(self, session_id: str) -> int:
        """
        Get the total number of messages in a session.

        Args:
            session_id: The session identifier

        Returns:
            Number of messages
        """
        pass

    # Conversation history operations
    @abstractmethod
    async def store_conversation_entry(self, entry: ConversationEntry) -> int:
        """
        Store a conversation entry (for LLM context).

        Args:
            entry: ConversationEntry object to store

        Returns:
            The entry ID
        """
        pass

    @abstractmethod
    async def get_conversation_history(
        self,
        agent_id: str,
        session_id: str,
        limit: Optional[int] = None,
        min_importance: float = 0.0,
    ) -> List[ConversationEntry]:
        """
        Retrieve conversation history for an agent.

        Args:
            agent_id: The agent identifier
            session_id: The session identifier
            limit: Maximum number of entries to return (None for all)
            min_importance: Minimum importance score filter

        Returns:
            List of ConversationEntry objects, ordered by timestamp
        """
        pass

    @abstractmethod
    async def delete_conversation_entries(
        self,
        agent_id: str,
        session_id: str,
        entry_ids: List[int]
    ) -> None:
        """
        Delete specific conversation entries (for pruning).

        Args:
            agent_id: The agent identifier
            session_id: The session identifier
            entry_ids: List of entry IDs to delete
        """
        pass

    # Agent state operations
    @abstractmethod
    async def save_agent_state(self, state: AgentState) -> None:
        """
        Save agent state.

        Args:
            state: AgentState object to save
        """
        pass

    @abstractmethod
    async def load_agent_state(
        self,
        agent_id: str,
        session_id: str
    ) -> Optional[AgentState]:
        """
        Load agent state.

        Args:
            agent_id: The agent identifier
            session_id: The session identifier

        Returns:
            AgentState object if found, None otherwise
        """
        pass

    # Memory operations (Phase 5)
    @abstractmethod
    async def store_memory(self, memory: Memory) -> int:
        """
        Store a memory.

        Args:
            memory: Memory object to store

        Returns:
            The memory ID
        """
        pass

    @abstractmethod
    async def retrieve_memories(
        self,
        agent_id: str,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """
        Retrieve memories matching a query.

        Args:
            agent_id: The agent identifier
            query: Search query string
            memory_type: Filter by memory type (optional)
            limit: Maximum number of memories to return
            min_importance: Minimum importance score filter

        Returns:
            List of Memory objects, ordered by relevance
        """
        pass

    @abstractmethod
    async def update_memory_access(self, memory_id: int) -> None:
        """
        Update memory access tracking.

        Increments access count and updates last_accessed timestamp.

        Args:
            memory_id: The memory identifier
        """
        pass

    @abstractmethod
    async def delete_memories(
        self,
        agent_id: str,
        memory_ids: List[int]
    ) -> None:
        """
        Delete specific memories.

        Args:
            agent_id: The agent identifier
            memory_ids: List of memory IDs to delete
        """
        pass
