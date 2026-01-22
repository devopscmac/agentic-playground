"""
Quick start web UI with pre-configured agents.

This script launches the web UI with some example agents already configured,
so you can start chatting immediately.

Usage:
    python -m agentic_playground.examples.webui_quickstart

Or with UV:
    uv run python -m agentic_playground.examples.webui_quickstart
"""

from dotenv import load_dotenv
from agentic_playground import AgentConfig
from agentic_playground.core import LLMAgent
from agentic_playground.llm import AnthropicProvider
from agentic_playground.agents import EchoAgent
from agentic_playground.webui import AgenticWebUI

# Load environment variables
load_dotenv()


def main():
    """Launch the web UI with pre-configured agents."""
    print("=" * 60)
    print("🤖 Agentic Playground - Quick Start Web UI")
    print("=" * 60)
    print("\nSetting up example agents...")

    # Create the web UI
    ui = AgenticWebUI()

    try:
        # Create some example agents
        llm_provider = AnthropicProvider()

        # 1. A helpful assistant
        assistant_config = AgentConfig(
            name="assistant",
            role="Helpful Assistant",
            system_prompt="You are a friendly and helpful assistant. Keep responses concise (2-3 sentences)."
        )
        assistant = LLMAgent(assistant_config, llm_provider)
        ui.orchestrator.register_agent(assistant)
        print("  ✓ Created 'assistant' agent")

        # 2. A creative writer
        writer_config = AgentConfig(
            name="writer",
            role="Creative Writer",
            system_prompt="You are a creative writer who loves storytelling. Be imaginative and engaging. Keep responses concise."
        )
        writer = LLMAgent(writer_config, llm_provider)
        ui.orchestrator.register_agent(writer)
        print("  ✓ Created 'writer' agent")

        # 3. An analyst
        analyst_config = AgentConfig(
            name="analyst",
            role="Data Analyst",
            system_prompt="You are a logical data analyst. Provide clear, analytical responses. Keep responses concise."
        )
        analyst = LLMAgent(analyst_config, llm_provider)
        ui.orchestrator.register_agent(analyst)
        print("  ✓ Created 'analyst' agent")

        # 4. An echo agent for testing
        echo = EchoAgent(name="echo")
        ui.orchestrator.register_agent(echo)
        print("  ✓ Created 'echo' agent (for testing)")

    except Exception as e:
        print(f"\n⚠ Warning: Could not create LLM agents: {e}")
        print("  Make sure you have ANTHROPIC_API_KEY set in your .env file")
        print("  You can still create agents manually in the web UI.")

    print("\n" + "=" * 60)
    print("Pre-configured agents ready!")
    print("\nNext steps:")
    print("  1. Go to 'Agent Management' tab")
    print("  2. Click 'Start Orchestrator'")
    print("  3. Go to 'Live Chat' tab")
    print("  4. Select an agent and start chatting!")
    print("\nPress Ctrl+C to stop the server.")
    print("=" * 60)

    # Launch the UI
    ui.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860
    )


if __name__ == "__main__":
    main()
