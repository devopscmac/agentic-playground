"""
Coordinator agent - demonstrates agent orchestration and delegation.
"""

from typing import Optional
from ..core import Agent, AgentConfig, Message, MessageType
from ..llm import LLMProvider, LLMMessage


class CoordinatorAgent(Agent):
    """
    A coordinator agent that can delegate tasks to other agents.

    This agent can optionally use an LLM to decide how to delegate tasks.
    """

    def __init__(
        self,
        name: str = "coordinator",
        available_agents: Optional[list[str]] = None,
        llm_provider: Optional[LLMProvider] = None
    ):
        config = AgentConfig(
            name=name,
            role="Coordinate and delegate tasks to other agents",
            capabilities=["delegation", "task_planning", "coordination"]
        )
        super().__init__(config)

        self.available_agents = available_agents or []
        self.llm_provider = llm_provider
        self.pending_tasks: dict[str, Message] = {}

    async def process_message(self, message: Message) -> None:
        """Process incoming messages and coordinate responses."""

        if message.type == MessageType.TASK:
            await self._handle_task(message)
        elif message.type == MessageType.RESPONSE:
            await self._handle_response(message)
        elif message.type == MessageType.QUERY:
            await self._handle_query(message)

    async def _handle_task(self, message: Message) -> None:
        """Handle a task by delegating to appropriate agents."""

        # Store the task
        self.pending_tasks[message.id] = message

        if self.llm_provider:
            # Use LLM to decide how to delegate
            await self._llm_delegate_task(message)
        else:
            # Simple round-robin delegation
            if self.available_agents:
                agent_id = self.available_agents[0]
                delegate_msg = Message(
                    type=MessageType.TASK,
                    sender=self.id,
                    recipient=agent_id,
                    content=message.content,
                    metadata={"delegated_from": message.id}
                )
                await self.send_message(delegate_msg)
            else:
                # No agents available, send back a response
                response = Message(
                    type=MessageType.RESPONSE,
                    sender=self.id,
                    recipient=message.sender,
                    content="No agents available to handle this task",
                    metadata={"original_task": message.id}
                )
                await self.send_message(response)

    async def _llm_delegate_task(self, message: Message) -> None:
        """Use LLM to intelligently delegate a task."""

        agent_list = ", ".join(self.available_agents)
        prompt = f"""You are a coordinator agent. You need to delegate this task to one of the available agents: {agent_list}

Task: {message.content}

Which agent should handle this task? Reply with just the agent name."""

        llm_message = LLMMessage(role="user", content=prompt)

        try:
            response = await self.llm_provider.generate(
                messages=[llm_message],
                temperature=0.3,
                max_tokens=50
            )

            # Extract agent name from response
            chosen_agent = response.content.strip().lower()

            if chosen_agent in self.available_agents:
                delegate_msg = Message(
                    type=MessageType.TASK,
                    sender=self.id,
                    recipient=chosen_agent,
                    content=message.content,
                    metadata={"delegated_from": message.id}
                )
                await self.send_message(delegate_msg)
            else:
                # Fallback to first agent
                delegate_msg = Message(
                    type=MessageType.TASK,
                    sender=self.id,
                    recipient=self.available_agents[0],
                    content=message.content,
                    metadata={"delegated_from": message.id}
                )
                await self.send_message(delegate_msg)

        except Exception as e:
            error_msg = Message(
                type=MessageType.ERROR,
                sender=self.id,
                recipient=message.sender,
                content=f"Error delegating task: {str(e)}",
                metadata={"error": str(e)}
            )
            await self.send_message(error_msg)

    async def _handle_response(self, message: Message) -> None:
        """Handle a response from a delegated agent."""

        # Just forward the response to the original requester
        # In a more complex system, you might aggregate responses
        pass

    async def _handle_query(self, message: Message) -> None:
        """Handle a query about the coordinator's state."""

        if "status" in message.content.lower():
            status = f"Managing {len(self.available_agents)} agents. {len(self.pending_tasks)} pending tasks."
            response = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                content=status
            )
            await self.send_message(response)
