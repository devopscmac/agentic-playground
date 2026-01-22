"""
SQLite storage backend implementation.

Provides persistent storage using SQLite with async support via aiosqlite.
"""

import json
import aiosqlite
from datetime import datetime
from pathlib import Path
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


class SQLiteStorage(StorageBackend):
    """
    SQLite-based storage backend for the memory system.

    Uses aiosqlite for async database operations. Provides ACID compliance
    and zero-configuration setup.

    Args:
        db_path: Path to the SQLite database file
    """

    def __init__(self, db_path: str = "./data/sessions.db"):
        self.db_path = Path(db_path)
        self.db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Initialize the database and create tables."""
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Open connection
        self.db = await aiosqlite.connect(str(self.db_path))
        self.db.row_factory = aiosqlite.Row

        # Create tables
        await self._create_tables()

    async def close(self) -> None:
        """Close the database connection."""
        if self.db:
            await self.db.close()
            self.db = None

    async def _create_tables(self) -> None:
        """Create all necessary database tables."""
        async with self.db.execute("PRAGMA foreign_keys = ON"):
            pass

        # Sessions table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP NOT NULL,
                last_active TIMESTAMP NOT NULL,
                metadata JSON
            )
        """)

        # Messages table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                type TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT,
                content TEXT NOT NULL,
                metadata JSON,
                importance_score REAL DEFAULT 0.5,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)

        # Agent state table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS agent_states (
                agent_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                state_data JSON NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                PRIMARY KEY (agent_id, session_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)

        # Conversation history table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                importance_score REAL DEFAULT 0.5,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)

        # Memories table (Phase 5)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding_text TEXT NOT NULL,
                importance_score REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                created_at TIMESTAMP NOT NULL,
                metadata JSON
            )
        """)

        # Create indexes
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id, timestamp)
        """)

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_conv_history_agent
            ON conversation_history(agent_id, session_id, timestamp)
        """)

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_agent
            ON memories(agent_id, memory_type, importance_score DESC)
        """)

        # Create FTS virtual table for memory search (Phase 5)
        await self.db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
            USING fts5(content, embedding_text, content=memories, content_rowid=id)
        """)

        await self.db.commit()

    # Session operations
    async def create_session(self, session: Session) -> str:
        """Create a new session."""
        await self.db.execute(
            """
            INSERT INTO sessions (session_id, created_at, last_active, metadata)
            VALUES (?, ?, ?, ?)
            """,
            (
                session.session_id,
                session.created_at.isoformat(),
                session.last_active.isoformat(),
                json.dumps(session.metadata),
            ),
        )
        await self.db.commit()
        return session.session_id

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
        async with self.db.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (session_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Session(
                    session_id=row["session_id"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_active=datetime.fromisoformat(row["last_active"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
            return None

    async def list_sessions(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "last_active"
    ) -> List[Session]:
        """List all sessions."""
        # Validate order_by to prevent SQL injection
        valid_order_fields = {"created_at", "last_active", "session_id"}
        if order_by not in valid_order_fields:
            order_by = "last_active"

        query = f"""
            SELECT * FROM sessions
            ORDER BY {order_by} DESC
            LIMIT ? OFFSET ?
        """

        async with self.db.execute(query, (limit, offset)) as cursor:
            rows = await cursor.fetchall()
            return [
                Session(
                    session_id=row["session_id"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_active=datetime.fromisoformat(row["last_active"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in rows
            ]

    async def update_session(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """Update session metadata and last_active timestamp."""
        # Get existing session
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Merge metadata
        updated_metadata = {**session.metadata, **metadata}

        await self.db.execute(
            """
            UPDATE sessions
            SET last_active = ?, metadata = ?
            WHERE session_id = ?
            """,
            (
                datetime.utcnow().isoformat(),
                json.dumps(updated_metadata),
                session_id,
            ),
        )
        await self.db.commit()

    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all associated data."""
        await self.db.execute(
            "DELETE FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        await self.db.commit()

    # Message operations
    async def store_message(self, message: StoredMessage) -> str:
        """Store a message."""
        await self.db.execute(
            """
            INSERT INTO messages (id, session_id, timestamp, type, sender, recipient, content, metadata, importance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.id,
                message.session_id,
                message.timestamp.isoformat(),
                message.type.value,
                message.sender,
                message.recipient,
                message.content,
                json.dumps(message.metadata),
                message.importance_score,
            ),
        )
        await self.db.commit()

        # Update session last_active
        await self.db.execute(
            "UPDATE sessions SET last_active = ? WHERE session_id = ?",
            (datetime.utcnow().isoformat(), message.session_id),
        )
        await self.db.commit()

        return message.id

    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        sender: Optional[str] = None,
    ) -> List[StoredMessage]:
        """Retrieve messages for a session."""
        query = "SELECT * FROM messages WHERE session_id = ?"
        params: List[Any] = [session_id]

        if sender:
            query += " AND sender = ?"
            params.append(sender)

        query += " ORDER BY timestamp ASC"

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        async with self.db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                StoredMessage(
                    id=row["id"],
                    session_id=row["session_id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    type=MessageType(row["type"]),
                    sender=row["sender"],
                    recipient=row["recipient"],
                    content=row["content"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    importance_score=row["importance_score"],
                )
                for row in rows
            ]

    async def get_message_count(self, session_id: str) -> int:
        """Get the total number of messages in a session."""
        async with self.db.execute(
            "SELECT COUNT(*) as count FROM messages WHERE session_id = ?",
            (session_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    # Conversation history operations
    async def store_conversation_entry(self, entry: ConversationEntry) -> int:
        """Store a conversation entry."""
        async with self.db.execute(
            """
            INSERT INTO conversation_history (agent_id, session_id, role, content, timestamp, importance_score)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entry.agent_id,
                entry.session_id,
                entry.role,
                entry.content,
                entry.timestamp.isoformat(),
                entry.importance_score,
            ),
        ) as cursor:
            entry_id = cursor.lastrowid

        await self.db.commit()
        return entry_id

    async def get_conversation_history(
        self,
        agent_id: str,
        session_id: str,
        limit: Optional[int] = None,
        min_importance: float = 0.0,
    ) -> List[ConversationEntry]:
        """Retrieve conversation history for an agent."""
        query = """
            SELECT * FROM conversation_history
            WHERE agent_id = ? AND session_id = ? AND importance_score >= ?
            ORDER BY timestamp ASC
        """
        params: List[Any] = [agent_id, session_id, min_importance]

        if limit is not None:
            # Get the most recent entries
            query = """
                SELECT * FROM (
                    SELECT * FROM conversation_history
                    WHERE agent_id = ? AND session_id = ? AND importance_score >= ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ) ORDER BY timestamp ASC
            """
            params.append(limit)

        async with self.db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                ConversationEntry(
                    id=row["id"],
                    agent_id=row["agent_id"],
                    session_id=row["session_id"],
                    role=row["role"],
                    content=row["content"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    importance_score=row["importance_score"],
                )
                for row in rows
            ]

    async def delete_conversation_entries(
        self,
        agent_id: str,
        session_id: str,
        entry_ids: List[int]
    ) -> None:
        """Delete specific conversation entries."""
        if not entry_ids:
            return

        placeholders = ",".join("?" * len(entry_ids))
        await self.db.execute(
            f"""
            DELETE FROM conversation_history
            WHERE agent_id = ? AND session_id = ? AND id IN ({placeholders})
            """,
            [agent_id, session_id] + entry_ids,
        )
        await self.db.commit()

    # Agent state operations
    async def save_agent_state(self, state: AgentState) -> None:
        """Save agent state."""
        await self.db.execute(
            """
            INSERT OR REPLACE INTO agent_states (agent_id, session_id, state_data, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                state.agent_id,
                state.session_id,
                json.dumps(state.state_data),
                state.updated_at.isoformat(),
            ),
        )
        await self.db.commit()

    async def load_agent_state(
        self,
        agent_id: str,
        session_id: str
    ) -> Optional[AgentState]:
        """Load agent state."""
        async with self.db.execute(
            "SELECT * FROM agent_states WHERE agent_id = ? AND session_id = ?",
            (agent_id, session_id),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return AgentState(
                    agent_id=row["agent_id"],
                    session_id=row["session_id"],
                    state_data=json.loads(row["state_data"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            return None

    # Memory operations (Phase 5)
    async def store_memory(self, memory: Memory) -> int:
        """Store a memory."""
        async with self.db.execute(
            """
            INSERT INTO memories (agent_id, session_id, memory_type, content, embedding_text,
                                 importance_score, access_count, last_accessed, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory.agent_id,
                memory.session_id,
                memory.memory_type.value,
                memory.content,
                memory.embedding_text,
                memory.importance_score,
                memory.access_count,
                memory.last_accessed.isoformat() if memory.last_accessed else None,
                memory.created_at.isoformat(),
                json.dumps(memory.metadata),
            ),
        ) as cursor:
            memory_id = cursor.lastrowid

        # Update FTS index
        await self.db.execute(
            """
            INSERT INTO memories_fts (rowid, content, embedding_text)
            VALUES (?, ?, ?)
            """,
            (memory_id, memory.content, memory.embedding_text),
        )

        await self.db.commit()
        return memory_id

    async def retrieve_memories(
        self,
        agent_id: str,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """Retrieve memories matching a query using FTS."""
        # Build the query
        base_query = """
            SELECT m.* FROM memories m
            JOIN memories_fts fts ON m.id = fts.rowid
            WHERE m.agent_id = ? AND m.importance_score >= ?
        """
        params: List[Any] = [agent_id, min_importance]

        if memory_type:
            base_query += " AND m.memory_type = ?"
            params.append(memory_type.value)

        # Add FTS search condition
        base_query += " AND memories_fts MATCH ?"
        params.append(query)

        # Order by relevance (FTS rank) and importance
        base_query += " ORDER BY m.importance_score DESC, m.created_at DESC LIMIT ?"
        params.append(limit)

        async with self.db.execute(base_query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                Memory(
                    id=row["id"],
                    agent_id=row["agent_id"],
                    session_id=row["session_id"],
                    memory_type=MemoryType(row["memory_type"]),
                    content=row["content"],
                    embedding_text=row["embedding_text"],
                    importance_score=row["importance_score"],
                    access_count=row["access_count"],
                    last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in rows
            ]

    async def update_memory_access(self, memory_id: int) -> None:
        """Update memory access tracking."""
        await self.db.execute(
            """
            UPDATE memories
            SET access_count = access_count + 1, last_accessed = ?
            WHERE id = ?
            """,
            (datetime.utcnow().isoformat(), memory_id),
        )
        await self.db.commit()

    async def delete_memories(
        self,
        agent_id: str,
        memory_ids: List[int]
    ) -> None:
        """Delete specific memories."""
        if not memory_ids:
            return

        placeholders = ",".join("?" * len(memory_ids))

        # Delete from FTS index first
        await self.db.execute(
            f"DELETE FROM memories_fts WHERE rowid IN ({placeholders})",
            memory_ids,
        )

        # Delete from main table
        await self.db.execute(
            f"""
            DELETE FROM memories
            WHERE agent_id = ? AND id IN ({placeholders})
            """,
            [agent_id] + memory_ids,
        )
        await self.db.commit()
