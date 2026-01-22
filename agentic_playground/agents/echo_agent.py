"""
Simple echo agent - demonstrates basic agent without LLM.
"""

from ..core import Agent, AgentConfig, Message, MessageType


class EchoAgent(Agent):
    """
    A simple agent that echoes back any message it receives.

    Useful for testing and demonstrating basic agent communication.
    """

    def __init__(self, name: str = "echo"):
        config = AgentConfig(
            name=name,
            role="Echo messages back to sender",
            capabilities=["echo", "basic_response"]
        )
        super().__init__(config)

    async def process_message(self, message: Message) -> None:
        """Echo the message back to the sender."""

        if message.type == MessageType.QUERY:
            response = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                content=f"Echo: {message.content}",
                metadata={"original_message": message.id}
            )
            await self.send_message(response)
        elif message.type == MessageType.TASK:
            response = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                content=f"Acknowledged task: {message.content}",
                metadata={"original_message": message.id}
            )
            await self.send_message(response)
