"""
Orchestrator for managing multiple agents and their communication.
"""

import asyncio
from typing import Optional, TYPE_CHECKING
from collections import defaultdict

from .agent import Agent
from .message import Message, MessageType

if TYPE_CHECKING:
    from agentic_playground.memory import MemoryManager
    from agentic_playground.memory.models import MessageType as MemMessageType


class Orchestrator:
    """
    Manages a collection of agents and routes messages between them.
    """

    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self.message_history: list[Message] = []
        self.running = False
        self._agent_tasks: list[asyncio.Task] = []
        self.memory_manager: Optional["MemoryManager"] = None
        self.session_id: Optional[str] = None

    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the orchestrator."""
        if agent.id in self.agents:
            raise ValueError(f"Agent {agent.id} is already registered")

        self.agents[agent.id] = agent
        agent.set_message_callback(self._handle_message)

        # Attach memory manager if available
        if self.memory_manager and self.session_id:
            agent.set_memory_manager(self.memory_manager, self.session_id)

        print(f"Registered agent: {agent}")

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the orchestrator."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            print(f"Unregistered agent: {agent_id}")

    def attach_memory_manager(
        self,
        memory_manager: "MemoryManager",
        session_id: Optional[str] = None
    ) -> str:
        """
        Attach a memory manager to the orchestrator.

        Args:
            memory_manager: MemoryManager instance
            session_id: Optional session ID (creates new session if not provided)

        Returns:
            The session ID
        """
        self.memory_manager = memory_manager
        if session_id is None:
            # Will be created when needed
            self.session_id = None
        else:
            self.session_id = session_id

        # Attach to all registered agents
        if self.session_id:
            for agent in self.agents.values():
                agent.set_memory_manager(memory_manager, self.session_id)

        return self.session_id or ""

    async def restore_session(self, session_id: str) -> None:
        """
        Restore a session from memory storage.

        This restores:
        - Message history
        - Agent states
        - Session metadata

        Args:
            session_id: The session identifier to restore
        """
        if not self.memory_manager:
            raise RuntimeError("No memory manager attached")

        # Verify session exists
        session = await self.memory_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        self.session_id = session_id

        # Restore message history
        from agentic_playground.memory.models import MessageType as MemMessageType

        stored_messages = await self.memory_manager.get_messages(session_id)

        # Convert stored messages to Message objects
        mem_to_core_type = {
            MemMessageType.AGENT: MessageType.RESPONSE,
            MemMessageType.USER: MessageType.TASK,
            MemMessageType.SYSTEM: MessageType.STATUS,
            MemMessageType.BROADCAST: MessageType.BROADCAST,
        }

        self.message_history = [
            Message(
                type=mem_to_core_type.get(msg.type, MessageType.RESPONSE),
                sender=msg.sender,
                recipient=msg.recipient,
                content=msg.content,
                metadata=msg.metadata,
            )
            for msg in stored_messages
        ]

        # Restore agent states
        for agent in self.agents.values():
            agent.set_memory_manager(self.memory_manager, session_id)
            await agent.restore_state()

        print(f"Restored session {session_id} with {len(self.message_history)} messages")

    async def save_session(self) -> None:
        """
        Save the current session state to memory storage.

        This saves:
        - All agent states
        - Session metadata update
        """
        if not self.memory_manager or not self.session_id:
            raise RuntimeError("No memory manager or session attached")

        # Save all agent states
        for agent in self.agents.values():
            await agent.save_state()

        # Update session metadata
        await self.memory_manager.update_session_metadata(
            self.session_id,
            {"last_saved": asyncio.get_event_loop().time()}
        )

        print(f"Saved session {self.session_id}")

    async def _handle_message(self, message: Message) -> None:
        """
        Handle a message sent by an agent.

        Routes the message to the appropriate recipient(s).
        """
        self.message_history.append(message)
        print(f"\n{message}")

        # Persist message if memory is enabled
        if self.memory_manager and self.session_id:
            from agentic_playground.memory.models import MessageType as MemMessageType

            # Map MessageType to memory MessageType
            mem_type_map = {
                MessageType.TASK: MemMessageType.AGENT,
                MessageType.RESPONSE: MemMessageType.AGENT,
                MessageType.BROADCAST: MemMessageType.BROADCAST,
                MessageType.ERROR: MemMessageType.SYSTEM,
                MessageType.STATUS: MemMessageType.SYSTEM,
            }

            await self.memory_manager.store_message(
                session_id=self.session_id,
                sender=message.sender,
                content=message.content,
                message_type=mem_type_map.get(message.type, MemMessageType.AGENT),
                recipient=message.recipient,
                metadata=message.metadata,
            )

        if message.type == MessageType.BROADCAST or message.recipient is None:
            # Broadcast to all agents except sender
            for agent_id, agent in self.agents.items():
                if agent_id != message.sender:
                    await agent.receive_message(message)
        elif message.recipient in self.agents:
            # Direct message to specific agent
            await self.agents[message.recipient].receive_message(message)
        else:
            print(f"Warning: Recipient {message.recipient} not found")

    async def send_message_to_agent(self, agent_id: str, message: Message) -> None:
        """Send a message to a specific agent from the orchestrator."""
        if agent_id in self.agents:
            await self.agents[agent_id].receive_message(message)
        else:
            raise ValueError(f"Agent {agent_id} not found")

    async def broadcast_message(self, message: Message) -> None:
        """Broadcast a message to all agents."""
        message.type = MessageType.BROADCAST
        await self._handle_message(message)

    async def start(self) -> None:
        """Start all registered agents."""
        if self.running:
            print("Orchestrator is already running")
            return

        self.running = True
        print(f"\nStarting orchestrator with {len(self.agents)} agents...")

        # Start all agents
        for agent in self.agents.values():
            task = asyncio.create_task(agent.start())
            self._agent_tasks.append(task)

        print("All agents started")

    async def stop(self) -> None:
        """Stop all registered agents."""
        if not self.running:
            return

        print("\nStopping orchestrator...")
        self.running = False

        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()

        # Cancel all tasks
        for task in self._agent_tasks:
            task.cancel()

        # Wait for all tasks to complete
        await asyncio.gather(*self._agent_tasks, return_exceptions=True)
        self._agent_tasks.clear()

        print("All agents stopped")

    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[MessageType] = None
    ) -> list[Message]:
        """
        Get message history, optionally filtered by agent or message type.
        """
        history = self.message_history

        if agent_id:
            history = [
                msg for msg in history
                if msg.sender == agent_id or msg.recipient == agent_id
            ]

        if message_type:
            history = [msg for msg in history if msg.type == message_type]

        return history

    def print_summary(self) -> None:
        """Print a summary of the orchestrator state."""
        print("\n" + "=" * 60)
        print("ORCHESTRATOR SUMMARY")
        print("=" * 60)
        print(f"Registered Agents: {len(self.agents)}")
        for agent in self.agents.values():
            print(f"  - {agent}")
        print(f"\nTotal Messages: {len(self.message_history)}")

        msg_counts = defaultdict(int)
        for msg in self.message_history:
            msg_counts[msg.type] += 1

        for msg_type, count in msg_counts.items():
            print(f"  - {msg_type.value}: {count}")
        print("=" * 60 + "\n")
