"""
Query engine for memory retrieval.

Provides semantic search and keyword-based retrieval of memories.
"""

from typing import List, Optional, TYPE_CHECKING
from agentic_playground.memory.models import Memory, MemoryType

if TYPE_CHECKING:
    from agentic_playground.memory.manager import MemoryManager


class QueryEngine:
    """
    Query engine for retrieving relevant memories.

    Supports keyword-based search using SQLite FTS (Full-Text Search).
    Can be extended to support vector embeddings for semantic search.

    Args:
        memory_manager: MemoryManager instance
    """

    def __init__(self, memory_manager: "MemoryManager"):
        self.memory_manager = memory_manager

    async def search(
        self,
        agent_id: str,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """
        Search for memories matching a query.

        Uses keyword-based search with SQLite FTS.

        Args:
            agent_id: Agent identifier
            query: Search query string
            memory_type: Optional filter by memory type
            limit: Maximum number of results
            min_importance: Minimum importance score

        Returns:
            List of matching Memory objects
        """
        # Preprocess query for FTS
        processed_query = self._preprocess_query(query)

        # Retrieve from storage
        memories = await self.memory_manager.retrieve_memories(
            agent_id=agent_id,
            query=processed_query,
            memory_type=memory_type,
            limit=limit,
            min_importance=min_importance,
        )

        return memories

    async def search_by_keywords(
        self,
        agent_id: str,
        keywords: List[str],
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """
        Search for memories matching any of the given keywords.

        Args:
            agent_id: Agent identifier
            keywords: List of keywords to search for
            memory_type: Optional filter by memory type
            limit: Maximum number of results
            min_importance: Minimum importance score

        Returns:
            List of matching Memory objects
        """
        if not keywords:
            return []

        # Build FTS query with OR operator
        query = " OR ".join(keywords)

        return await self.search(
            agent_id=agent_id,
            query=query,
            memory_type=memory_type,
            limit=limit,
            min_importance=min_importance,
        )

    async def search_recent(
        self,
        agent_id: str,
        query: str,
        session_id: str,
        limit: int = 5,
    ) -> List[Memory]:
        """
        Search for recent memories from current session.

        Args:
            agent_id: Agent identifier
            query: Search query
            session_id: Session identifier
            limit: Maximum number of results

        Returns:
            List of matching Memory objects
        """
        # This is a simplified version - in production, you'd filter by session_id
        # For now, we search across all sessions but limit results
        memories = await self.search(
            agent_id=agent_id,
            query=query,
            limit=limit,
            min_importance=0.3,  # Higher threshold for recent memories
        )

        # Filter by session (the storage backend should ideally do this)
        # For MVP, we return all results
        return memories

    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess query for FTS search.

        Handles:
        - Lowercase conversion
        - Basic tokenization
        - Stop word handling (optional)

        Args:
            query: Raw query string

        Returns:
            Preprocessed query string
        """
        if not query:
            return ""

        # Convert to lowercase
        query = query.lower()

        # Remove special characters that might break FTS
        # Keep alphanumeric, spaces, and basic punctuation
        import re
        query = re.sub(r'[^a-z0-9\s\-]', ' ', query)

        # Remove extra whitespace
        query = ' '.join(query.split())

        return query

    async def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """
        Extract keywords from text for search.

        Simple implementation using word frequency and common words filtering.

        Args:
            text: Input text
            top_k: Number of keywords to extract

        Returns:
            List of extracted keywords
        """
        if not text:
            return []

        # Convert to lowercase and tokenize
        import re
        words = re.findall(r'\b\w+\b', text.lower())

        # Common stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where',
            'why', 'how', 'this', 'that', 'these', 'those'
        }

        # Filter stop words and short words
        filtered_words = [
            word for word in words
            if word not in stop_words and len(word) > 3
        ]

        # Count word frequencies
        from collections import Counter
        word_counts = Counter(filtered_words)

        # Return top k words
        top_words = [word for word, _ in word_counts.most_common(top_k)]

        return top_words


class MemoryRetriever:
    """
    High-level interface for memory retrieval in agent context.

    Combines query engine with context awareness to retrieve
    the most relevant memories for the current conversation.
    """

    def __init__(self, query_engine: QueryEngine):
        self.query_engine = query_engine

    async def retrieve_for_message(
        self,
        agent_id: str,
        message_content: str,
        session_id: str,
        limit: int = 3,
    ) -> List[Memory]:
        """
        Retrieve relevant memories for processing a message.

        Args:
            agent_id: Agent identifier
            message_content: Content of the incoming message
            session_id: Current session identifier
            limit: Maximum number of memories to retrieve

        Returns:
            List of relevant Memory objects
        """
        # Extract keywords from message
        keywords = await self.query_engine.extract_keywords(message_content, top_k=5)

        if not keywords:
            # Fall back to full message search
            return await self.query_engine.search(
                agent_id=agent_id,
                query=message_content,
                limit=limit,
                min_importance=0.4,
            )

        # Search using extracted keywords
        memories = await self.query_engine.search_by_keywords(
            agent_id=agent_id,
            keywords=keywords,
            limit=limit,
            min_importance=0.4,
        )

        return memories

    async def retrieve_semantic_memories(
        self,
        agent_id: str,
        query: str,
        limit: int = 5,
    ) -> List[Memory]:
        """
        Retrieve semantic memories (facts, knowledge).

        Args:
            agent_id: Agent identifier
            query: Search query
            limit: Maximum number of results

        Returns:
            List of semantic Memory objects
        """
        return await self.query_engine.search(
            agent_id=agent_id,
            query=query,
            memory_type=MemoryType.SEMANTIC,
            limit=limit,
            min_importance=0.5,
        )

    async def retrieve_episodic_memories(
        self,
        agent_id: str,
        query: str,
        limit: int = 5,
    ) -> List[Memory]:
        """
        Retrieve episodic memories (past interactions).

        Args:
            agent_id: Agent identifier
            query: Search query
            limit: Maximum number of results

        Returns:
            List of episodic Memory objects
        """
        return await self.query_engine.search(
            agent_id=agent_id,
            query=query,
            memory_type=MemoryType.EPISODIC,
            limit=limit,
            min_importance=0.4,
        )
