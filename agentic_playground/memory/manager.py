"""
Main memory manager class that orchestrates all memory operations.

The MemoryManager provides a high-level interface for session management,
message storage, agent state persistence, and memory retrieval.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from agentic_playground.memory.storage.base import StorageBackend
from agentic_playground.memory.models import (
    Session,
    StoredMessage,
    ConversationEntry,
    Memory,
    AgentState,
    MemoryType,
    MessageType,
)
from agentic_playground.memory.utils import generate_session_id, format_session_metadata


class MemoryManager:
    """
    Main orchestrator for memory and context management.

    The MemoryManager coordinates storage operations, session lifecycle,
    and provides a unified interface for agents and orchestrators to
    interact with the memory system.

    Args:
        storage: Storage backend implementation

    Example:
        storage = SQLiteStorage("./data/sessions.db")
        await storage.initialize()
        manager = MemoryManager(storage)

        # Create session
        session_id = await manager.create_session(metadata={"user": "alice"})

        # Store messages
        await manager.store_message(
            session_id=session_id,
            sender="user",
            content="Hello!",
            message_type=MessageType.USER
        )
    """

    def __init__(self, storage: StorageBackend):
        self.storage = storage

    # Session management
    async def create_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new session.

        Args:
            session_id: Optional custom session ID (generated if not provided)
            metadata: Optional metadata to attach to the session

        Returns:
            The session ID
        """
        if session_id is None:
            session_id = generate_session_id()

        session = Session(
            session_id=session_id,
            metadata=format_session_metadata(metadata or {}),
        )

        await self.storage.create_session(session)
        return session_id

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID.

        Args:
            session_id: The session identifier

        Returns:
            Session object if found, None otherwise
        """
        return await self.storage.get_session(session_id)

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
            order_by: Field to order by ("created_at", "last_active")

        Returns:
            List of Session objects
        """
        return await self.storage.list_sessions(limit, offset, order_by)

    async def update_session_metadata(
        self,
        session_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Update session metadata.

        Args:
            session_id: The session identifier
            metadata: Metadata to merge with existing metadata
        """
        formatted = format_session_metadata(metadata)
        await self.storage.update_session(session_id, formatted)

    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session and all associated data.

        Args:
            session_id: The session identifier
        """
        await self.storage.delete_session(session_id)

    # Message operations
    async def store_message(
        self,
        session_id: str,
        sender: str,
        content: str,
        message_type: MessageType = MessageType.AGENT,
        recipient: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5,
    ) -> str:
        """
        Store a message in the session.

        Args:
            session_id: The session identifier
            sender: Message sender identifier
            content: Message content
            message_type: Type of message (USER, AGENT, SYSTEM, BROADCAST)
            recipient: Optional recipient identifier
            metadata: Optional message metadata
            importance_score: Importance score (0.0 to 1.0)

        Returns:
            The message ID
        """
        message = StoredMessage(
            session_id=session_id,
            sender=sender,
            content=content,
            type=message_type,
            recipient=recipient,
            metadata=metadata or {},
            importance_score=importance_score,
        )

        return await self.storage.store_message(message)

    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        sender: Optional[str] = None,
    ) -> List[StoredMessage]:
        """
        Retrieve messages from a session.

        Args:
            session_id: The session identifier
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            sender: Filter by sender (optional)

        Returns:
            List of StoredMessage objects
        """
        return await self.storage.get_messages(session_id, limit, offset, sender)

    async def get_message_count(self, session_id: str) -> int:
        """
        Get the total number of messages in a session.

        Args:
            session_id: The session identifier

        Returns:
            Number of messages
        """
        return await self.storage.get_message_count(session_id)

    # Conversation history operations
    async def store_conversation_entry(
        self,
        agent_id: str,
        session_id: str,
        role: str,
        content: str,
        importance_score: float = 0.5,
    ) -> int:
        """
        Store a conversation entry for LLM context.

        Args:
            agent_id: The agent identifier
            session_id: The session identifier
            role: Message role ("user", "assistant", "system")
            content: Message content
            importance_score: Importance score (0.0 to 1.0)

        Returns:
            The entry ID
        """
        entry = ConversationEntry(
            agent_id=agent_id,
            session_id=session_id,
            role=role,
            content=content,
            importance_score=importance_score,
        )

        return await self.storage.store_conversation_entry(entry)

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
            limit: Maximum number of entries to return
            min_importance: Minimum importance score filter

        Returns:
            List of ConversationEntry objects
        """
        return await self.storage.get_conversation_history(
            agent_id, session_id, limit, min_importance
        )

    async def prune_conversation_history(
        self,
        agent_id: str,
        session_id: str,
        entry_ids: List[int]
    ) -> None:
        """
        Remove specific conversation entries (for context management).

        Args:
            agent_id: The agent identifier
            session_id: The session identifier
            entry_ids: List of entry IDs to delete
        """
        await self.storage.delete_conversation_entries(agent_id, session_id, entry_ids)

    # Agent state operations
    async def save_agent_state(
        self,
        agent_id: str,
        session_id: str,
        state_data: Dict[str, Any]
    ) -> None:
        """
        Save agent state.

        Args:
            agent_id: The agent identifier
            session_id: The session identifier
            state_data: State data to persist
        """
        state = AgentState(
            agent_id=agent_id,
            session_id=session_id,
            state_data=state_data,
        )

        await self.storage.save_agent_state(state)

    async def load_agent_state(
        self,
        agent_id: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load agent state.

        Args:
            agent_id: The agent identifier
            session_id: The session identifier

        Returns:
            State data dictionary if found, None otherwise
        """
        state = await self.storage.load_agent_state(agent_id, session_id)
        return state.state_data if state else None

    # Memory operations (Phase 5)
    async def store_memory(
        self,
        agent_id: str,
        session_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        embedding_text: Optional[str] = None,
        importance_score: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Store a memory.

        Args:
            agent_id: The agent identifier
            session_id: The session identifier
            content: Memory content
            memory_type: Type of memory (WORKING, EPISODIC, SEMANTIC)
            embedding_text: Searchable text (defaults to content)
            importance_score: Importance score (0.0 to 1.0)
            metadata: Optional memory metadata

        Returns:
            The memory ID
        """
        memory = Memory(
            agent_id=agent_id,
            session_id=session_id,
            memory_type=memory_type,
            content=content,
            embedding_text=embedding_text or content,
            importance_score=importance_score,
            metadata=metadata or {},
        )

        return await self.storage.store_memory(memory)

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
            List of Memory objects
        """
        memories = await self.storage.retrieve_memories(
            agent_id, query, memory_type, limit, min_importance
        )

        # Update access tracking for retrieved memories
        for memory in memories:
            if memory.id:
                await self.storage.update_memory_access(memory.id)

        return memories

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
        await self.storage.delete_memories(agent_id, memory_ids)

    # Utility methods
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of a session.

        Args:
            session_id: The session identifier

        Returns:
            Dictionary with session information
        """
        session = await self.get_session(session_id)
        if not session:
            return {}

        message_count = await self.get_message_count(session_id)

        return {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "last_active": session.last_active,
            "message_count": message_count,
            "metadata": session.metadata,
        }
