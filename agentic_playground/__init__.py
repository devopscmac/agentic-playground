"""
Agentic Playground - A multi-agent system framework for experimentation.
"""

__version__ = "0.1.0"

from .core.agent import Agent, AgentConfig
from .core.message import Message, MessageType
from .core.orchestrator import Orchestrator

__all__ = [
    "Agent",
    "AgentConfig",
    "Message",
    "MessageType",
    "Orchestrator",
]
