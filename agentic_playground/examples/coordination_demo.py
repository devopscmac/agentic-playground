"""
Demonstration of agent coordination and delegation.

This example shows how a coordinator agent can delegate tasks to worker agents.
"""

import asyncio
from dotenv import load_dotenv

from agentic_playground import AgentConfig, Message, MessageType, Orchestrator
from agentic_playground.agents import EchoAgent, CoordinatorAgent
from agentic_playground.core import LLMAgent
from agentic_playground.llm import AnthropicProvider

# Load environment variables
load_dotenv()


async def main():
    """Run a coordination demonstration."""

    # Create orchestrator
    orchestrator = Orchestrator()

    # Create worker agents
    echo1 = EchoAgent(name="echo1")
    echo2 = EchoAgent(name="echo2")

    # Create an LLM-powered assistant agent
    assistant_config = AgentConfig(
        name="assistant",
        role="Helpful Assistant",
        system_prompt="You are a helpful assistant. Answer questions concisely."
    )
    llm_provider = AnthropicProvider()
    assistant = LLMAgent(assistant_config, llm_provider)

    # Create coordinator with knowledge of available agents
    coordinator = CoordinatorAgent(
        name="coordinator",
        available_agents=["echo1", "echo2", "assistant"],
        llm_provider=llm_provider
    )

    # Register all agents
    orchestrator.register_agent(echo1)
    orchestrator.register_agent(echo2)
    orchestrator.register_agent(assistant)
    orchestrator.register_agent(coordinator)

    # Start orchestrator
    await orchestrator.start()

    print("\n--- Sending tasks to coordinator ---\n")

    # Send some tasks to the coordinator
    task1 = Message(
        type=MessageType.TASK,
        sender="system",
        recipient="coordinator",
        content="Please echo this message"
    )
    await orchestrator.send_message_to_agent("coordinator", task1)

    await asyncio.sleep(2)

    task2 = Message(
        type=MessageType.TASK,
        sender="system",
        recipient="coordinator",
        content="What is the capital of France?"
    )
    await orchestrator.send_message_to_agent("coordinator", task2)

    await asyncio.sleep(3)

    # Query coordinator status
    status_query = Message(
        type=MessageType.QUERY,
        sender="system",
        recipient="coordinator",
        content="What is your status?"
    )
    await orchestrator.send_message_to_agent("coordinator", status_query)

    await asyncio.sleep(2)

    # Stop orchestrator
    await orchestrator.stop()

    # Print summary
    orchestrator.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
