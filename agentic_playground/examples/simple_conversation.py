"""
Simple conversation between two LLM-powered agents.

This example demonstrates basic agent-to-agent communication using LLMs.
"""

import asyncio
from dotenv import load_dotenv

from agentic_playground import AgentConfig, Message, MessageType, Orchestrator
from agentic_playground.core import LLMAgent
from agentic_playground.llm import AnthropicProvider

# Load environment variables
load_dotenv()


async def main():
    """Run a simple conversation between two agents."""

    # Create orchestrator
    orchestrator = Orchestrator()

    # Create two LLM agents with different roles
    alice_config = AgentConfig(
        name="alice",
        role="Creative Writer",
        system_prompt="You are Alice, a creative writer who loves telling stories. Keep your responses concise (1-2 sentences)."
    )

    bob_config = AgentConfig(
        name="bob",
        role="Logical Analyst",
        system_prompt="You are Bob, a logical analyst who likes to question things. Keep your responses concise (1-2 sentences)."
    )

    # Create LLM provider
    llm_provider = AnthropicProvider()

    # Create agents
    alice = LLMAgent(alice_config, llm_provider)
    bob = LLMAgent(bob_config, llm_provider)

    # Register agents
    orchestrator.register_agent(alice)
    orchestrator.register_agent(bob)

    # Start orchestrator
    await orchestrator.start()

    # Send initial message from system to Alice
    initial_message = Message(
        type=MessageType.QUERY,
        sender="system",
        recipient="alice",
        content="Tell me about a mysterious door you discovered."
    )
    await orchestrator.send_message_to_agent("alice", initial_message)

    # Let them chat for a bit
    await asyncio.sleep(5)

    # Alice responds to Bob
    message_to_bob = Message(
        type=MessageType.QUERY,
        sender="alice",
        recipient="bob",
        content="What do you think we should do about the mysterious door?"
    )
    await alice.send_message(message_to_bob)

    # Wait for conversation to unfold
    await asyncio.sleep(5)

    # Stop orchestrator
    await orchestrator.stop()

    # Print summary
    orchestrator.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
