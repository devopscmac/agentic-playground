"""
Storage backends for the memory system.
"""

from agentic_playground.memory.storage.base import StorageBackend

__all__ = [
    "StorageBackend",
    "SQLiteStorage",
]

def __getattr__(name):
    """Lazy import for storage implementations."""
    if name == "SQLiteStorage":
        from agentic_playground.memory.storage.sqlite import SQLiteStorage
        return SQLiteStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
