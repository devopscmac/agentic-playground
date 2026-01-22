"""
Session management utilities.
"""

import uuid
from datetime import datetime
from typing import Any, Dict


def generate_session_id() -> str:
    """
    Generate a unique session ID.

    Returns:
        A UUID string suitable for use as a session identifier
    """
    return str(uuid.uuid4())


def format_session_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format session metadata for storage.

    Ensures datetime objects are converted to ISO format strings
    and other complex types are handled appropriately.

    Args:
        metadata: Raw metadata dictionary

    Returns:
        Formatted metadata dictionary safe for JSON serialization
    """
    formatted = {}
    for key, value in metadata.items():
        if isinstance(value, datetime):
            formatted[key] = value.isoformat()
        elif isinstance(value, (str, int, float, bool, type(None))):
            formatted[key] = value
        elif isinstance(value, (list, dict)):
            formatted[key] = value
        else:
            # Convert other types to string representation
            formatted[key] = str(value)
    return formatted
