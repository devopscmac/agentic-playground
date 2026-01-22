# Web UI Guide

The Agentic Playground includes a powerful web interface built with Gradio for managing and interacting with your multi-agent system.

## Features

- **💬 Live Chat Interface**: Send messages to agents and see responses in real-time
- **⚙️ Agent Management**: Create, configure, and manage agents through the UI
- **📜 Message History**: View conversation history with filtering by agent or message type
- **📊 Visualization**: Interactive network graphs and timelines of agent interactions

## Installation

The web UI requires additional dependencies. Install them with:

```bash
# With UV (recommended)
uv sync --extra webui

# With pip
pip install gradio plotly pandas
```

## Quick Start

### Option 1: Pre-configured Agents (Recommended)

Launch with example agents already set up:

```bash
uv run python -m agentic_playground.examples.webui_quickstart
```

This creates:
- An assistant agent
- A creative writer agent
- A data analyst agent
- An echo agent for testing

### Option 2: Empty Playground

Start with no agents and create your own:

```bash
uv run python -m agentic_playground.examples.webui_demo
```

The web interface will open automatically in your browser at `http://localhost:7860`.

## Using the Web UI

### 1. Agent Management Tab

**Create a New Agent:**

1. Enter an agent **name** (e.g., "assistant", "researcher")
2. Add a **role description** (e.g., "Helpful Assistant")
3. Write a **system prompt** with instructions for the agent
4. Select an **LLM provider**:
   - **Anthropic**: For Claude models (requires `ANTHROPIC_API_KEY`)
   - **OpenAI**: For GPT models (requires `OPENAI_API_KEY`)
   - **None (Echo Agent)**: Simple echo agent without LLM
5. Optionally specify a **model name**
6. Click **Create Agent**

**Start the Orchestrator:**

Before chatting, you must start the orchestrator:
1. Go to the "Agent Management" tab
2. Click **Start Orchestrator**
3. Wait for the "✓ Orchestrator started" message

### 2. Live Chat Tab

**Send Messages:**

1. Select a recipient from the **Send to Agent** dropdown (or leave empty for broadcast)
2. Choose a **Message Type**:
   - **QUERY**: Ask a question
   - **TASK**: Request an action
   - **BROADCAST**: Send to all agents
3. Type your message
4. Click **Send** or press Enter

**View Responses:**

- Agent responses appear in the chat interface
- Each message shows the sender and content
- The chat updates in real-time as agents respond

**Tips:**
- Use BROADCAST to get multiple perspectives on the same question
- Direct messages to specific agents for focused conversations
- Click **Clear Chat** to reset the conversation view

### 3. Message History Tab

**View All Messages:**

1. Go to the "Message History" tab
2. Click **Refresh** to load the latest messages

**Filter Messages:**

- **Filter by Agent**: Select an agent to see only their messages
- **Filter by Message Type**: Select a type (QUERY, TASK, RESPONSE, etc.)
- Click **Refresh** to apply filters

**Statistics:**

The bottom panel shows:
- Total message count
- Filtered message count
- Breakdown by message type

### 4. Visualization Tab

**Agent Interaction Network:**

- Shows agents as nodes
- Lines represent message flows between agents
- Line thickness indicates message volume
- Hover over elements for details

**Message Timeline:**

- Shows when messages were sent
- Color-coded by message type
- Hover to see message content

Click **Refresh Visualization** to update with latest data.

## Programmatic Usage

You can also use the WebUI in your own Python scripts:

```python
from dotenv import load_dotenv
from agentic_playground import AgentConfig
from agentic_playground.core import LLMAgent
from agentic_playground.llm import AnthropicProvider
from agentic_playground.webui import AgenticWebUI

load_dotenv()

# Create the UI
ui = AgenticWebUI()

# Pre-register some agents
config = AgentConfig(
    name="assistant",
    role="Helpful Assistant",
    system_prompt="You are a helpful assistant."
)
agent = LLMAgent(config, AnthropicProvider())
ui.orchestrator.register_agent(agent)

# Launch the interface
ui.launch(
    share=False,  # Set True for public share link
    server_port=7860
)
```

## Configuration Options

### Launch Options

```python
ui.launch(
    share=False,          # Create public Gradio share link
    server_name="0.0.0.0",  # Allow network access
    server_port=7860,     # Port number
    show_api=False,       # Show API documentation
    inbrowser=True,       # Open browser automatically
    prevent_thread_lock=False  # For running in background
)
```

### Creating Public Share Links

To create a temporary public URL (useful for demos):

```python
ui.launch(share=True)
```

Gradio will generate a public URL (valid for 72 hours) that you can share with others.

## Tips and Best Practices

### Performance

- **Start Simple**: Begin with 2-3 agents to understand the system
- **Monitor History**: Use the Message History tab to track conversation flow
- **Clear When Needed**: Large conversation histories can slow down the UI

### Agent Design

- **Clear System Prompts**: Give agents specific, clear instructions
- **Define Roles**: Distinct roles lead to more interesting interactions
- **Test First**: Use the Echo agent to test message routing before adding LLM agents

### Troubleshooting

**"Orchestrator is not running"**
- Go to Agent Management tab
- Click "Start Orchestrator"

**"Error: API key not found"**
- Check your `.env` file has the required API keys
- Restart the web UI after adding keys

**"Agent not responding"**
- Check the Message History tab to see if messages are being sent
- Verify the orchestrator is running
- Check for error messages in the console

**Visualization not showing**
- Make sure you've sent some messages first
- Click "Refresh Visualization"
- Check browser console for errors

## Advanced Features

### Multiple Agent Conversations

Create specialized agents and have them collaborate:

1. Create a "researcher" agent
2. Create an "analyst" agent
3. Create a "writer" agent
4. Send a BROADCAST query to all
5. Watch them each respond with their unique perspective

### Custom Agent Types

You can register custom agent classes programmatically:

```python
from agentic_playground.core import Agent, AgentConfig

class CustomAgent(Agent):
    async def process_message(self, message):
        # Your custom logic
        pass

# Register with the UI
custom = CustomAgent(AgentConfig(name="custom", role="Custom"))
ui.orchestrator.register_agent(custom)
```

## Keyboard Shortcuts

- **Enter**: Send message (in chat input)
- **Ctrl+C**: Stop the server (in terminal)

## Examples

### Example 1: Brainstorming Session

1. Create agents with different perspectives (optimist, pragmatist, critic)
2. Send a BROADCAST: "What are the pros and cons of AI in education?"
3. Watch each agent respond from their unique viewpoint

### Example 2: Research Collaboration

1. Create a "researcher" to gather information
2. Create an "analyst" to analyze data
3. Create a "writer" to summarize findings
4. Send sequential messages to each agent
5. View the full conversation in Message History

### Example 3: Creative Writing

1. Create a "storyteller" agent
2. Create a "editor" agent
3. Have the storyteller create a story
4. Have the editor provide feedback
5. Use the visualization to see the collaboration flow

## Deployment

### Local Network Access

To allow access from other devices on your network:

```python
ui.launch(server_name="0.0.0.0", server_port=7860)
```

Then access from other devices at: `http://YOUR_IP:7860`

### Cloud Deployment

The UI can be deployed to cloud platforms:

**Hugging Face Spaces:**
- Create a new Space
- Upload your code
- Add a `app.py` with the webui_demo code
- Add your API keys as Space secrets

**Other Platforms:**
- Railway, Render, Fly.io all support Gradio apps
- Ensure your `.env` variables are set
- Expose port 7860

## API Access

Gradio automatically creates an API for the interface. Enable it with:

```python
ui.launch(show_api=True)
```

Then visit `/docs` to see the API documentation.

## Resources

- [Gradio Documentation](https://www.gradio.app/docs)
- [Plotly Visualization Guide](https://plotly.com/python/)
- [Main README](README.md)
- [Getting Started Guide](GETTING_STARTED.md)

## Feedback

Found a bug or have a feature request for the Web UI? Please open an issue on GitHub!
