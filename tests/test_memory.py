"""
Tests for the memory system.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime
from pathlib import Path


class TestMemoryModels:
    """Test memory data models."""

    def test_session_model(self):
        """Test Session model creation."""
        from agentic_playground.memory.models import Session

        session = Session(
            session_id="test-123",
            metadata={"user": "alice"}
        )

        assert session.session_id == "test-123"
        assert session.metadata["user"] == "alice"
        assert isinstance(session.created_at, datetime)

    def test_memory_types(self):
        """Test MemoryType enum."""
        from agentic_playground.memory.models import MemoryType

        assert MemoryType.WORKING == "working"
        assert MemoryType.EPISODIC == "episodic"
        assert MemoryType.SEMANTIC == "semantic"

    def test_message_type(self):
        """Test MessageType enum."""
        from agentic_playground.memory.models import MessageType as MemMessageType

        assert MemMessageType.USER == "user"
        assert MemMessageType.AGENT == "agent"
        assert MemMessageType.SYSTEM == "system"


@pytest.mark.asyncio
class TestSQLiteStorage:
    """Test SQLite storage backend."""

    async def test_storage_initialization(self):
        """Test storage initialization."""
        from agentic_playground.memory.storage.sqlite import SQLiteStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(db_path)

            await storage.initialize()
            assert Path(db_path).exists()

            await storage.close()

    async def test_create_and_get_session(self):
        """Test creating and retrieving a session."""
        from agentic_playground.memory.storage.sqlite import SQLiteStorage
        from agentic_playground.memory.models import Session

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(db_path)
            await storage.initialize()

            # Create session
            session = Session(
                session_id="test-session-1",
                metadata={"test": True}
            )
            await storage.create_session(session)

            # Retrieve session
            retrieved = await storage.get_session("test-session-1")
            assert retrieved is not None
            assert retrieved.session_id == "test-session-1"
            assert retrieved.metadata["test"] is True

            await storage.close()

    async def test_store_and_get_messages(self):
        """Test storing and retrieving messages."""
        from agentic_playground.memory.storage.sqlite import SQLiteStorage
        from agentic_playground.memory.models import Session, StoredMessage, MessageType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(db_path)
            await storage.initialize()

            # Create session first
            session = Session(session_id="test-session")
            await storage.create_session(session)

            # Store message
            message = StoredMessage(
                session_id="test-session",
                sender="alice",
                recipient="bob",
                content="Hello!",
                type=MessageType.USER
            )
            await storage.store_message(message)

            # Get messages
            messages = await storage.get_messages("test-session")
            assert len(messages) == 1
            assert messages[0].content == "Hello!"
            assert messages[0].sender == "alice"

            await storage.close()

    async def test_agent_state_save_load(self):
        """Test saving and loading agent state."""
        from agentic_playground.memory.storage.sqlite import SQLiteStorage
        from agentic_playground.memory.models import Session, AgentState

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(db_path)
            await storage.initialize()

            # Create session
            session = Session(session_id="test-session")
            await storage.create_session(session)

            # Save agent state
            state = AgentState(
                agent_id="agent1",
                session_id="test-session",
                state_data={"counter": 42, "status": "active"}
            )
            await storage.save_agent_state(state)

            # Load agent state
            loaded = await storage.load_agent_state("agent1", "test-session")
            assert loaded is not None
            assert loaded.state_data["counter"] == 42
            assert loaded.state_data["status"] == "active"

            await storage.close()


@pytest.mark.asyncio
class TestMemoryManager:
    """Test MemoryManager."""

    async def test_memory_manager_creation(self):
        """Test creating a memory manager."""
        from agentic_playground.memory import MemoryManager, SQLiteStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(db_path)
            await storage.initialize()

            manager = MemoryManager(storage)
            assert manager is not None

            await storage.close()

    async def test_session_creation(self):
        """Test creating a session through memory manager."""
        from agentic_playground.memory import MemoryManager, SQLiteStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(db_path)
            await storage.initialize()

            manager = MemoryManager(storage)

            # Create session
            session_id = await manager.create_session(
                metadata={"user": "test_user"}
            )

            assert session_id is not None
            assert len(session_id) > 0

            # Get session
            session = await manager.get_session(session_id)
            assert session is not None
            assert session.metadata["user"] == "test_user"

            await storage.close()

    async def test_message_storage(self):
        """Test storing messages through memory manager."""
        from agentic_playground.memory import MemoryManager, SQLiteStorage
        from agentic_playground.memory.models import MessageType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(db_path)
            await storage.initialize()

            manager = MemoryManager(storage)
            session_id = await manager.create_session()

            # Store message
            msg_id = await manager.store_message(
                session_id=session_id,
                sender="user",
                content="Test message",
                message_type=MessageType.USER
            )

            assert msg_id is not None

            # Get messages
            messages = await manager.get_messages(session_id)
            assert len(messages) == 1
            assert messages[0].content == "Test message"

            await storage.close()


@pytest.mark.asyncio
class TestTokenCounting:
    """Test token counting utilities."""

    def test_estimate_tokens(self):
        """Test token estimation."""
        from agentic_playground.memory.utils.tokens import estimate_tokens

        # Short text
        tokens = estimate_tokens("Hello world")
        assert tokens > 0
        assert tokens < 10

        # Empty text
        tokens = estimate_tokens("")
        assert tokens == 0

        # Long text
        long_text = "This is a longer piece of text " * 50
        tokens = estimate_tokens(long_text)
        assert tokens > 100

    def test_estimate_tokens_for_messages(self):
        """Test token estimation for message lists."""
        from agentic_playground.memory.utils.tokens import estimate_tokens_for_messages

        messages = [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there! How can I help?"},
        ]

        tokens = estimate_tokens_for_messages(messages)
        assert tokens > 0
        assert tokens > 10  # Should account for message overhead


class TestImportanceScoring:
    """Test importance scoring algorithms."""

    def test_calculate_importance_score(self):
        """Test importance score calculation."""
        from agentic_playground.memory.importance import calculate_importance_score

        # Recent user message with important content
        score = calculate_importance_score(
            content="This is an error we need to fix",
            role="user",
            timestamp=datetime.utcnow(),
            current_time=datetime.utcnow()
        )

        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be relatively important

    def test_content_importance(self):
        """Test content importance calculation."""
        from agentic_playground.memory.importance import _calculate_content_importance

        # Error message should have high importance
        score1 = _calculate_content_importance("Error: Something failed!")
        assert score1 > 0.6

        # Question should have higher importance
        score2 = _calculate_content_importance("What is the status?")
        assert score2 > 0.5

        # Short message should have lower importance
        score3 = _calculate_content_importance("ok")
        assert score3 < 0.5


@pytest.mark.asyncio
class TestContextManager:
    """Test context window management."""

    def test_context_manager_creation(self):
        """Test creating a context manager."""
        from agentic_playground.memory.context import ContextManager

        cm = ContextManager(max_tokens=1000)
        assert cm.max_tokens == 1000
        assert cm.effective_max_tokens < 1000

    def test_should_prune(self):
        """Test pruning detection."""
        from agentic_playground.memory.context import ContextManager

        cm = ContextManager(max_tokens=100)

        # Small conversation shouldn't need pruning
        small_messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"}
        ]
        assert not cm.should_prune(small_messages)

        # Large conversation should need pruning
        large_messages = [
            {"role": "user", "content": "x" * 1000}
            for _ in range(100)
        ]
        assert cm.should_prune(large_messages)

    def test_prepare_context(self):
        """Test context preparation."""
        from agentic_playground.memory.context import ContextManager

        cm = ContextManager(max_tokens=1000)

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        context = cm.prepare_context(messages)
        assert context is not None
        assert len(context.messages) > 0
        assert context.total_tokens > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
