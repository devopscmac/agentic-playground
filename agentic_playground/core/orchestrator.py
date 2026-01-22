"""
Orchestrator for managing multiple agents and their communication.
"""

import asyncio
from typing import Optional
from collections import defaultdict

from .agent import Agent
from .message import Message, MessageType


class Orchestrator:
    """
    Manages a collection of agents and routes messages between them.
    """

    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self.message_history: list[Message] = []
        self.running = False
        self._agent_tasks: list[asyncio.Task] = []

    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the orchestrator."""
        if agent.id in self.agents:
            raise ValueError(f"Agent {agent.id} is already registered")

        self.agents[agent.id] = agent
        agent.set_message_callback(self._handle_message)
        print(f"Registered agent: {agent}")

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the orchestrator."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            print(f"Unregistered agent: {agent_id}")

    async def _handle_message(self, message: Message) -> None:
        """
        Handle a message sent by an agent.

        Routes the message to the appropriate recipient(s).
        """
        self.message_history.append(message)
        print(f"\n{message}")

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
