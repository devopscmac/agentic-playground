"""
Memory and context management system for agentic-playground.

This package provides persistent storage, session management, context window handling,
and semantic memory search capabilities for the multi-agent framework.

Key Components:
- MemoryManager: Main orchestrator for memory operations
- StorageBackend: Abstract interface for storage implementations
- SQLiteStorage: SQLite-based storage backend
- ContextManager: Token limit and context window management
- QueryEngine: Memory retrieval and semantic search

Example Usage:
    from agentic_playground.memory import MemoryManager, SQLiteStorage

    # Initialize storage
    storage = SQLiteStorage("./data/sessions.db")
    await storage.initialize()

    # Create memory manager
    memory_manager = MemoryManager(storage)

    # Create session
    session_id = await memory_manager.create_session()

    # Attach to orchestrator
    orchestrator.attach_memory_manager(memory_manager, session_id)
"""

from agentic_playground.memory.models import (
    MemoryType,
    MessageType,
    Session,
    StoredMessage,
    ConversationEntry,
    Memory,
    AgentState,
    ContextWindow,
)

__all__ = [
    "MemoryType",
    "MessageType",
    "Session",
    "StoredMessage",
    "ConversationEntry",
    "Memory",
    "AgentState",
    "ContextWindow",
    "MemoryManager",
    "SQLiteStorage",
]

# Import these after to avoid circular imports
def __getattr__(name):
    """Lazy import for heavy dependencies."""
    if name == "MemoryManager":
        from agentic_playground.memory.manager import MemoryManager
        return MemoryManager
    elif name == "SQLiteStorage":
        from agentic_playground.memory.storage.sqlite import SQLiteStorage
        return SQLiteStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
