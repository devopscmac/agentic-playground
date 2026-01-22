"""
Importance scoring algorithms for messages and memories.

These algorithms determine which messages/memories should be retained
when context pruning is needed.
"""

import math
import re
from datetime import datetime
from typing import Dict, List, Optional


def calculate_importance_score(
    content: str,
    role: str,
    timestamp: datetime,
    current_time: Optional[datetime] = None,
    has_replies: bool = False,
    metadata: Optional[Dict] = None,
) -> float:
    """
    Calculate importance score for a message or memory.

    Score is between 0.0 and 1.0, with higher scores being more important.

    The algorithm considers:
    - Recency: Recent messages score higher (exponential decay)
    - Content importance: Keywords, questions, errors, decisions
    - Interaction density: Messages with replies score higher
    - Role: User messages weighted higher than assistant messages

    Args:
        content: Message content
        role: Message role ("user", "assistant", "system")
        timestamp: When the message was created
        current_time: Current time (defaults to now)
        has_replies: Whether this message has replies
        metadata: Optional message metadata

    Returns:
        Importance score (0.0 to 1.0)
    """
    if current_time is None:
        current_time = datetime.utcnow()

    # Component weights
    RECENCY_WEIGHT = 0.3
    CONTENT_WEIGHT = 0.4
    INTERACTION_WEIGHT = 0.2
    ROLE_WEIGHT = 0.1

    # 1. Recency factor (exponential decay)
    time_diff_hours = (current_time - timestamp).total_seconds() / 3600
    # Half-life of 24 hours
    recency_factor = math.exp(-time_diff_hours / 24.0)

    # 2. Content importance
    content_importance = _calculate_content_importance(content)

    # 3. Interaction density
    interaction_factor = 1.0 if has_replies else 0.5

    # 4. Role bonus
    role_factor = {
        "user": 1.0,
        "system": 0.9,
        "assistant": 0.7,
    }.get(role.lower(), 0.7)

    # Combine factors
    score = (
        recency_factor * RECENCY_WEIGHT +
        content_importance * CONTENT_WEIGHT +
        interaction_factor * INTERACTION_WEIGHT +
        role_factor * ROLE_WEIGHT
    )

    # Clamp to [0, 1]
    return max(0.0, min(1.0, score))


def _calculate_content_importance(content: str) -> float:
    """
    Calculate importance based on content characteristics.

    Args:
        content: Message content

    Returns:
        Content importance score (0.0 to 1.0)
    """
    if not content:
        return 0.0

    score = 0.5  # Base score

    content_lower = content.lower()

    # High importance indicators
    high_importance_keywords = [
        "error", "exception", "failed", "bug", "issue",
        "important", "critical", "urgent",
        "decided", "decision", "conclusion",
        "summary", "key point", "note that",
        "remember", "don't forget",
    ]

    for keyword in high_importance_keywords:
        if keyword in content_lower:
            score += 0.1

    # Questions are important (seeking information)
    if "?" in content:
        score += 0.15

    # Code blocks are often important
    if "```" in content or "`" in content:
        score += 0.1

    # Lists and structured content
    if re.search(r'^\s*[-*\d]+\.', content, re.MULTILINE):
        score += 0.05

    # URLs (references)
    if "http://" in content or "https://" in content:
        score += 0.05

    # Long messages might contain more information
    if len(content) > 500:
        score += 0.05

    # Very short messages are less important
    if len(content) < 20:
        score -= 0.1

    # Clamp to [0, 1]
    return max(0.0, min(1.0, score))


def rank_messages_by_importance(
    messages: List[Dict],
    current_time: Optional[datetime] = None,
) -> List[tuple[int, float]]:
    """
    Rank messages by importance score.

    Args:
        messages: List of message dictionaries with keys:
                 - content (str)
                 - role (str)
                 - timestamp (datetime)
                 - has_replies (bool, optional)
                 - metadata (dict, optional)
        current_time: Current time for recency calculation

    Returns:
        List of (index, score) tuples, sorted by score descending
    """
    if current_time is None:
        current_time = datetime.utcnow()

    scored = []

    for idx, msg in enumerate(messages):
        score = calculate_importance_score(
            content=msg.get("content", ""),
            role=msg.get("role", "assistant"),
            timestamp=msg.get("timestamp", current_time),
            current_time=current_time,
            has_replies=msg.get("has_replies", False),
            metadata=msg.get("metadata"),
        )
        scored.append((idx, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored


def select_messages_to_prune(
    messages: List[Dict],
    keep_count: int,
    always_keep_recent: int = 10,
    always_keep_system: bool = True,
) -> List[int]:
    """
    Select which messages to prune from conversation history.

    Strategy:
    - Always keep system messages (if enabled)
    - Always keep the most recent N messages
    - Keep highest importance messages for the rest

    Args:
        messages: List of message dictionaries
        keep_count: Total number of messages to keep
        always_keep_recent: Number of recent messages to always keep
        always_keep_system: Whether to always keep system messages

    Returns:
        List of indices to REMOVE (prune)
    """
    if len(messages) <= keep_count:
        return []

    to_remove = []

    # Identify protected messages
    protected_indices = set()

    # Protect system messages
    if always_keep_system:
        for idx, msg in enumerate(messages):
            if msg.get("role") == "system":
                protected_indices.add(idx)

    # Protect recent messages
    recent_start = max(0, len(messages) - always_keep_recent)
    for idx in range(recent_start, len(messages)):
        protected_indices.add(idx)

    # Calculate available slots
    protected_count = len(protected_indices)
    remaining_slots = keep_count - protected_count

    if remaining_slots <= 0:
        # Need to prune all unprotected messages
        for idx in range(len(messages)):
            if idx not in protected_indices:
                to_remove.append(idx)
        return to_remove

    # Rank unprotected messages by importance
    unprotected_messages = [
        (idx, msg) for idx, msg in enumerate(messages)
        if idx not in protected_indices
    ]

    if not unprotected_messages:
        return []

    # Calculate importance scores for unprotected messages
    scored = []
    for idx, msg in unprotected_messages:
        score = calculate_importance_score(
            content=msg.get("content", ""),
            role=msg.get("role", "assistant"),
            timestamp=msg.get("timestamp", datetime.utcnow()),
            has_replies=msg.get("has_replies", False),
            metadata=msg.get("metadata"),
        )
        scored.append((idx, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Keep top N by importance, prune the rest
    keep_indices = {idx for idx, _ in scored[:remaining_slots]}

    for idx, _ in unprotected_messages:
        if idx not in keep_indices:
            to_remove.append(idx)

    return sorted(to_remove)
