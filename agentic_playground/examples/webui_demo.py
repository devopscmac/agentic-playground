"""
Web UI demonstration for the agentic playground.

This script launches a web interface where you can:
- Create and manage agents
- Send messages and interact with agents in real-time
- View conversation history
- Visualize agent interactions

Usage:
    python -m agentic_playground.examples.webui_demo

Or with UV:
    uv run python -m agentic_playground.examples.webui_demo

The web interface will open in your browser automatically.
"""

from dotenv import load_dotenv
from agentic_playground.webui import AgenticWebUI

# Load environment variables
load_dotenv()


def main():
    """Launch the web UI."""
    print("=" * 60)
    print("🤖 Agentic Playground - Web UI")
    print("=" * 60)
    print("\nInitializing web interface...")
    print("\nThe interface will open in your browser.")
    print("You can:")
    print("  1. Create agents in the 'Agent Management' tab")
    print("  2. Start the orchestrator")
    print("  3. Chat with agents in the 'Live Chat' tab")
    print("  4. View history and visualizations")
    print("\nPress Ctrl+C to stop the server.")
    print("=" * 60)

    # Create and launch the web UI
    ui = AgenticWebUI()
    ui.launch(
        share=False,  # Set to True to create a public share link
        server_name="0.0.0.0",  # Allow access from other devices on network
        server_port=7860
    )


if __name__ == "__main__":
    main()
