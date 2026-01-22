"""
Multi-agent debate demonstration.

This example shows multiple agents discussing a topic from different perspectives.
"""

import asyncio
from dotenv import load_dotenv

from agentic_playground import AgentConfig, Message, MessageType, Orchestrator
from agentic_playground.core import LLMAgent
from agentic_playground.llm import AnthropicProvider

# Load environment variables
load_dotenv()


async def main():
    """Run a debate between multiple agents."""

    # Create orchestrator
    orchestrator = Orchestrator()

    # Create LLM provider
    llm_provider = AnthropicProvider()

    # Create agents with different perspectives
    optimist_config = AgentConfig(
        name="optimist",
        role="Optimistic Futurist",
        system_prompt="You are an optimistic futurist who sees the positive potential in AI. Keep responses to 2-3 sentences."
    )

    pragmatist_config = AgentConfig(
        name="pragmatist",
        role="Pragmatic Engineer",
        system_prompt="You are a pragmatic engineer focused on practical challenges and solutions. Keep responses to 2-3 sentences."
    )

    skeptic_config = AgentConfig(
        name="skeptic",
        role="Critical Thinker",
        system_prompt="You are a critical thinker who questions assumptions and raises concerns. Keep responses to 2-3 sentences."
    )

    # Create agents
    optimist = LLMAgent(optimist_config, llm_provider)
    pragmatist = LLMAgent(pragmatist_config, llm_provider)
    skeptic = LLMAgent(skeptic_config, llm_provider)

    # Register agents
    orchestrator.register_agent(optimist)
    orchestrator.register_agent(pragmatist)
    orchestrator.register_agent(skeptic)

    # Start orchestrator
    await orchestrator.start()

    print("\n--- Starting Debate: The Future of AI ---\n")

    # Moderator introduces the topic (broadcast to all)
    topic = Message(
        type=MessageType.BROADCAST,
        sender="moderator",
        content="Topic for debate: Will AI make society better or worse? Each of you, please share your initial thoughts."
    )
    await orchestrator.broadcast_message(topic)

    # Let agents respond
    await asyncio.sleep(10)

    # Follow-up question to specific agent
    followup = Message(
        type=MessageType.QUERY,
        sender="moderator",
        recipient="skeptic",
        content="Skeptic, what specific concerns do you have about the optimist's view?"
    )
    await orchestrator.send_message_to_agent("skeptic", followup)

    await asyncio.sleep(5)

    # Let pragmatist weigh in
    synthesis = Message(
        type=MessageType.QUERY,
        sender="moderator",
        recipient="pragmatist",
        content="Pragmatist, can you find a middle ground between these perspectives?"
    )
    await orchestrator.send_message_to_agent("pragmatist", synthesis)

    await asyncio.sleep(5)

    # Stop orchestrator
    await orchestrator.stop()

    # Print summary
    orchestrator.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
