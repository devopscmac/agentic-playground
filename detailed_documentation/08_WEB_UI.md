# Web UI Guide

Interactive Gradio-based interface for managing agents.

## Quick Start

```bash
# Install web UI dependencies
pip install -e ".[webui]"

# Launch with pre-configured agents
python -m agentic_playground.examples.webui_quickstart

# Or empty playground
python -m agentic_playground.examples.webui_demo
```

## Features

### 1. Live Chat
- Send messages to agents
- See responses in real-time
- Select specific agent or broadcast
- Message history display

### 2. Agent Management
- Create new agents via UI
- Choose LLM provider (Anthropic/OpenAI)
- Configure system prompts
- Start/stop orchestrator
- View registered agents

### 3. Message History
- View all messages
- Filter by agent or type
- See timestamps and metadata
- Export conversation logs

### 4. Memory Settings (Optional)
*From feature/memory-and-context-management branch*

- Enable/disable persistent memory
- Create and manage sessions
- Load previous conversations
- Export/import sessions
- View session statistics

### 5. Visualization
- Agent interaction network graph
- Message timeline
- Real-time updates

## Creating Agents via UI

1. Go to "Agent Management" tab
2. Fill in:
   - Agent Name (e.g., "assistant")
   - Role Description (e.g., "Helpful AI")
   - System Prompt (instructions for agent)
   - LLM Provider (Anthropic/OpenAI)
   - Model Name
3. Click "Create Agent"
4. Agent appears in agent list
5. Click "Start Orchestrator"
6. Go to "Live Chat" tab to interact

## Programmatic Usage

```python
from agentic_playground.webui import AgenticWebUI

# Create UI
webui = AgenticWebUI()

# Pre-register agents (optional)
webui.orchestrator.register_agent(my_agent)

# Launch
webui.launch(
    share=False,  # Set True for public link
    server_port=7860,
    server_name="0.0.0.0"
)
```

## Memory Management

### Enable Memory
1. Go to "Memory Settings" tab
2. Check "Enable Persistent Memory"
3. Set storage path (default: ./data/sessions.db)
4. Click "Enable Memory"

### Session Management
- **New Session**: Create fresh conversation
- **Load Session**: Restore previous conversation
- **Save Session**: Persist current state
- **Delete Session**: Remove old sessions
- **Export**: Save session to file

## Customization

### Custom Theme
```python
import gradio as gr

webui.launch(theme=gr.themes.Soft())
```

### Custom Port
```python
webui.launch(server_port=8000)
```

### Public Sharing
```python
webui.launch(share=True)
# Generates public URL
```

## Tips

- **Start Orchestrator**: Must start before chatting
- **Agent Names**: Must be unique
- **API Keys**: Set in .env file
- **Refresh**: Use refresh buttons to update data
- **History**: Filters apply on button click

See [WEBUI_GUIDE.md](../WEBUI_GUIDE.md) for complete details.
