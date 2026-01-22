"""
Context window management for LLM agents.

Handles token limits, message pruning, and context preparation.
"""

from datetime import datetime
from typing import List, Dict, Optional, TYPE_CHECKING

from agentic_playground.memory.utils.tokens import (
    estimate_tokens_for_messages,
    calculate_tokens_per_message,
)
from agentic_playground.memory.importance import (
    calculate_importance_score,
    select_messages_to_prune,
)
from agentic_playground.memory.models import ConversationEntry, ContextWindow

if TYPE_CHECKING:
    from agentic_playground.memory.manager import MemoryManager


class ContextManager:
    """
    Manages context window size and message pruning for LLM agents.

    Ensures conversation history stays within token limits by:
    - Counting tokens in conversation history
    - Pruning low-importance messages when approaching limits
    - Preserving system messages and recent context
    - Optionally retrieving relevant memories

    Args:
        max_tokens: Maximum tokens for context window (default: 180000 for Claude)
        buffer_tokens: Token buffer to leave for response (default: 20000)
        always_keep_recent: Number of recent messages to always keep
        always_keep_system: Whether to always keep system messages
    """

    def __init__(
        self,
        max_tokens: int = 180000,
        buffer_tokens: int = 20000,
        always_keep_recent: int = 10,
        always_keep_system: bool = True,
    ):
        self.max_tokens = max_tokens
        self.buffer_tokens = buffer_tokens
        self.always_keep_recent = always_keep_recent
        self.always_keep_system = always_keep_system
        self.effective_max_tokens = max_tokens - buffer_tokens

    def prepare_context(
        self,
        messages: List[Dict[str, str]],
        memories: Optional[List[Dict[str, str]]] = None,
    ) -> ContextWindow:
        """
        Prepare context window from messages and optional memories.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            memories: Optional list of retrieved memory dicts

        Returns:
            ContextWindow with prepared messages and metadata
        """
        # Start with messages
        context_messages = messages.copy()

        # Calculate current token count
        current_tokens = estimate_tokens_for_messages(context_messages)

        # Prune if needed
        pruned_count = 0
        if current_tokens > self.effective_max_tokens:
            context_messages, pruned_count = self._prune_messages(context_messages)
            current_tokens = estimate_tokens_for_messages(context_messages)

        # Add memories if provided and space available
        memory_objects = []
        if memories:
            available_tokens = self.effective_max_tokens - current_tokens
            memory_messages, memory_objects = self._format_memories(
                memories, available_tokens
            )
            if memory_messages:
                # Insert memories after system messages but before conversation
                system_count = sum(
                    1 for msg in context_messages if msg.get("role") == "system"
                )
                context_messages = (
                    context_messages[:system_count] +
                    memory_messages +
                    context_messages[system_count:]
                )
                current_tokens = estimate_tokens_for_messages(context_messages)

        return ContextWindow(
            messages=context_messages,
            total_tokens=current_tokens,
            pruned_count=pruned_count,
            retrieved_memories=memory_objects,
        )

    def _prune_messages(
        self,
        messages: List[Dict[str, str]]
    ) -> tuple[List[Dict[str, str]], int]:
        """
        Prune messages to fit within token limit.

        Args:
            messages: Original message list

        Returns:
            Tuple of (pruned messages, count of messages removed)
        """
        if not messages:
            return messages, 0

        # Calculate how many messages we can keep
        current_tokens = estimate_tokens_for_messages(messages)
        target_tokens = self.effective_max_tokens

        if current_tokens <= target_tokens:
            return messages, 0

        # Binary search for the right number of messages to keep
        # while respecting token limits
        min_keep = self.always_keep_recent + sum(
            1 for msg in messages if msg.get("role") == "system"
        )
        max_keep = len(messages)

        best_keep = min_keep
        for keep_count in range(max_keep, min_keep - 1, -1):
            # Convert messages to format expected by importance scorer
            scored_messages = [
                {
                    "content": msg.get("content", ""),
                    "role": msg.get("role", "assistant"),
                    "timestamp": msg.get("timestamp", datetime.utcnow()),
                }
                for msg in messages
            ]

            # Get indices to remove
            to_remove_indices = select_messages_to_prune(
                scored_messages,
                keep_count=keep_count,
                always_keep_recent=self.always_keep_recent,
                always_keep_system=self.always_keep_system,
            )

            # Create pruned list
            pruned = [
                msg for idx, msg in enumerate(messages)
                if idx not in to_remove_indices
            ]

            # Check if it fits
            pruned_tokens = estimate_tokens_for_messages(pruned)
            if pruned_tokens <= target_tokens:
                best_keep = keep_count
                break

        # Perform final pruning with best keep count
        scored_messages = [
            {
                "content": msg.get("content", ""),
                "role": msg.get("role", "assistant"),
                "timestamp": msg.get("timestamp", datetime.utcnow()),
            }
            for msg in messages
        ]

        to_remove_indices = select_messages_to_prune(
            scored_messages,
            keep_count=best_keep,
            always_keep_recent=self.always_keep_recent,
            always_keep_system=self.always_keep_system,
        )

        pruned_messages = [
            msg for idx, msg in enumerate(messages)
            if idx not in to_remove_indices
        ]

        pruned_count = len(to_remove_indices)

        return pruned_messages, pruned_count

    def _format_memories(
        self,
        memories: List[Dict[str, str]],
        available_tokens: int,
    ) -> tuple[List[Dict[str, str]], List]:
        """
        Format memories as messages and fit within token budget.

        Args:
            memories: List of memory dicts
            available_tokens: Available token budget

        Returns:
            Tuple of (formatted messages, memory objects)
        """
        if not memories or available_tokens <= 0:
            return [], []

        # Format as system message
        memory_lines = ["## Relevant Context from Memory:"]

        included_memories = []
        current_tokens = estimate_tokens_for_messages([{
            "role": "system",
            "content": memory_lines[0]
        }])

        for memory in memories:
            memory_text = f"- {memory.get('content', '')}"
            memory_tokens = len(memory_text) // 4  # Approximate

            if current_tokens + memory_tokens > available_tokens:
                break

            memory_lines.append(memory_text)
            included_memories.append(memory)
            current_tokens += memory_tokens

        if len(memory_lines) == 1:
            # Only header, no memories fit
            return [], []

        memory_message = {
            "role": "system",
            "content": "\n".join(memory_lines)
        }

        return [memory_message], included_memories

    async def prepare_context_with_storage(
        self,
        agent_id: str,
        session_id: str,
        memory_manager: "MemoryManager",
        additional_messages: Optional[List[Dict[str, str]]] = None,
    ) -> ContextWindow:
        """
        Prepare context by loading from storage.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier
            memory_manager: MemoryManager instance
            additional_messages: Additional messages to append

        Returns:
            ContextWindow with prepared context
        """
        # Load conversation history from storage
        entries = await memory_manager.get_conversation_history(
            agent_id=agent_id,
            session_id=session_id,
        )

        # Convert to message format
        messages = [
            {
                "role": entry.role,
                "content": entry.content,
                "timestamp": entry.timestamp,
            }
            for entry in entries
        ]

        # Add additional messages if provided
        if additional_messages:
            messages.extend(additional_messages)

        # Prepare context
        return self.prepare_context(messages)

    def should_prune(self, messages: List[Dict[str, str]]) -> bool:
        """
        Check if messages should be pruned.

        Args:
            messages: Message list to check

        Returns:
            True if pruning is needed
        """
        current_tokens = estimate_tokens_for_messages(messages)
        return current_tokens > self.effective_max_tokens

    def get_token_usage(self, messages: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Get detailed token usage information.

        Args:
            messages: Message list

        Returns:
            Dictionary with token usage details
        """
        total_tokens = estimate_tokens_for_messages(messages)
        per_message_tokens = calculate_tokens_per_message(messages)

        return {
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "effective_max_tokens": self.effective_max_tokens,
            "buffer_tokens": self.buffer_tokens,
            "available_tokens": max(0, self.effective_max_tokens - total_tokens),
            "message_count": len(messages),
            "per_message_tokens": per_message_tokens,
            "needs_pruning": total_tokens > self.effective_max_tokens,
        }
