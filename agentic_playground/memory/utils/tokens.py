"""
Token counting utilities for context window management.

Provides approximate token counting for Claude models using a simple
character-based heuristic. Can be extended to use tiktoken or other
tokenizers if needed.
"""

from typing import List, Dict


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text using character-based heuristic.

    Uses the approximation of ~4 characters per token, which works
    reasonably well for Claude models.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    # Approximate: 4 characters per token
    char_count = len(text)
    return max(1, char_count // 4)


def estimate_tokens_for_messages(messages: List[Dict[str, str]]) -> int:
    """
    Estimate total token count for a list of messages.

    Includes overhead for message formatting (role, delimiters, etc.).

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys

    Returns:
        Estimated total token count
    """
    if not messages:
        return 0

    total_tokens = 0

    for message in messages:
        # Count tokens in role and content
        role_tokens = estimate_tokens(message.get("role", ""))
        content_tokens = estimate_tokens(message.get("content", ""))

        # Add overhead for message formatting (~10 tokens per message)
        message_overhead = 10

        total_tokens += role_tokens + content_tokens + message_overhead

    # Add overhead for conversation structure
    conversation_overhead = 5

    return total_tokens + conversation_overhead


def truncate_text_to_tokens(text: str, max_tokens: int) -> str:
    """
    Truncate text to approximately fit within token limit.

    Args:
        text: Input text
        max_tokens: Maximum token count

    Returns:
        Truncated text
    """
    if estimate_tokens(text) <= max_tokens:
        return text

    # Approximate: 4 characters per token
    max_chars = max_tokens * 4

    if len(text) <= max_chars:
        return text

    # Truncate and add ellipsis
    truncated = text[:max_chars - 3] + "..."
    return truncated


def calculate_tokens_per_message(messages: List[Dict[str, str]]) -> List[int]:
    """
    Calculate token count for each message individually.

    Args:
        messages: List of message dictionaries

    Returns:
        List of token counts corresponding to each message
    """
    return [
        estimate_tokens(msg.get("role", "")) +
        estimate_tokens(msg.get("content", "")) +
        10  # Message overhead
        for msg in messages
    ]
