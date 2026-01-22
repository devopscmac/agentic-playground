# Agentic Playground

A flexible, extensible multi-agent system framework for experimenting with AI agents. Build intelligent agents that can communicate, coordinate, and collaborate using LLMs.

## Features

- **Flexible Agent Framework**: Simple base classes for creating custom agents
- **Message-Based Communication**: Robust message passing system with different message types
- **LLM Integration**: Support for multiple LLM providers (Anthropic Claude, OpenAI GPT)
- **Orchestration**: Built-in orchestrator for managing agent lifecycles and message routing
- **Async/Await**: Full async support for efficient concurrent agent operations
- **Extensible**: Easy to extend with new agent types and capabilities

## Installation

### Option 1: UV (Recommended - Fast!)

1. Install UV if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone and setup:
```bash
git clone <repository-url>
cd agentic-playground
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

That's it! See [UV_GUIDE.md](UV_GUIDE.md) for more UV commands.

### Option 2: Traditional pip

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic-playground
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Quick Start

### Basic Agent Communication

```python
import asyncio
from agentic_playground import AgentConfig, Message, MessageType, Orchestrator
from agentic_playground.core import LLMAgent
from agentic_playground.llm import AnthropicProvider

async def main():
    # Create orchestrator
    orchestrator = Orchestrator()

    # Create an LLM-powered agent
    config = AgentConfig(
        name="assistant",
        role="Helpful Assistant",
        system_prompt="You are a helpful assistant."
    )
    agent = LLMAgent(config, AnthropicProvider())

    # Register and start
    orchestrator.register_agent(agent)
    await orchestrator.start()

    # Send a message
    message = Message(
        type=MessageType.QUERY,
        sender="user",
        recipient="assistant",
        content="Hello, how are you?"
    )
    await orchestrator.send_message_to_agent("assistant", message)

    await asyncio.sleep(3)
    await orchestrator.stop()

asyncio.run(main())
```

## Architecture

### Core Components

- **Agent**: Base class for all agents. Agents process messages and can maintain internal state.
- **LLMAgent**: Agent subclass that integrates with LLMs for intelligent responses.
- **Message**: Structured communication between agents with types (TASK, QUERY, RESPONSE, etc.).
- **Orchestrator**: Manages agent lifecycle and routes messages between agents.

### Message Types

- `TASK`: A task to be performed
- `QUERY`: A question or information request
- `RESPONSE`: A response to a query or task
- `BROADCAST`: A message to all agents
- `SYSTEM`: System-level message
- `ERROR`: Error notification

### Creating Custom Agents

Extend the `Agent` base class and implement `process_message`:

```python
from agentic_playground.core import Agent, AgentConfig, Message, MessageType

class CustomAgent(Agent):
    def __init__(self, name: str):
        config = AgentConfig(
            name=name,
            role="Custom Agent",
            capabilities=["custom_capability"]
        )
        super().__init__(config)

    async def process_message(self, message: Message) -> None:
        # Your custom logic here
        if message.type == MessageType.QUERY:
            response = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                content="Custom response"
            )
            await self.send_message(response)
```

## Examples

Run the example scripts to see the framework in action:

### Simple Conversation
```bash
python -m agentic_playground.examples.simple_conversation
```
Two LLM agents have a creative conversation.

### Coordination Demo
```bash
python -m agentic_playground.examples.coordination_demo
```
A coordinator agent delegates tasks to worker agents.

### Debate
```bash
python -m agentic_playground.examples.debate
```
Multiple agents discuss a topic from different perspectives.

## Project Structure

```
agentic-playground/
├── agentic_playground/
│   ├── core/               # Core framework
│   │   ├── agent.py        # Base agent class
│   │   ├── llm_agent.py    # LLM-powered agent
│   │   ├── message.py      # Message types
│   │   └── orchestrator.py # Agent orchestration
│   ├── llm/                # LLM integration
│   │   ├── base.py         # LLM provider interface
│   │   └── providers/      # Provider implementations
│   ├── agents/             # Example agent implementations
│   └── examples/           # Usage examples
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## LLM Providers

### Anthropic Claude

```python
from agentic_playground.llm import AnthropicProvider

provider = AnthropicProvider(model="claude-sonnet-4-20250514")
```

### OpenAI GPT

```python
from agentic_playground.llm import OpenAIProvider

provider = OpenAIProvider(model="gpt-4-turbo-preview")
```

## Advanced Usage

### Agent State Management

Agents can maintain internal state:

```python
class StatefulAgent(Agent):
    async def process_message(self, message: Message) -> None:
        # Access state
        count = self.state.get("message_count", 0)
        self.state["message_count"] = count + 1
```

### Broadcasting Messages

Send messages to all agents:

```python
broadcast_msg = Message(
    type=MessageType.BROADCAST,
    sender="system",
    content="Announcement to all agents"
)
await orchestrator.broadcast_message(broadcast_msg)
```

### Message History

Access the conversation history:

```python
# Get all messages
history = orchestrator.get_message_history()

# Filter by agent
alice_messages = orchestrator.get_message_history(agent_id="alice")

# Filter by type
queries = orchestrator.get_message_history(message_type=MessageType.QUERY)
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black agentic_playground/
ruff check agentic_playground/
```

## Future Enhancements

- [ ] Tool/function calling support for agents
- [ ] Persistent conversation history (database integration)
- [ ] Web UI for visualizing agent interactions
- [ ] More example agents (research, coding, creative writing)
- [ ] Support for local LLMs (Ollama integration)
- [ ] Agent memory and context management
- [ ] Multi-modal agent support (images, audio)

## Contributing

Contributions are welcome! This is a playground for experimentation, so feel free to:

- Add new agent types
- Implement new LLM providers
- Create interesting examples
- Improve documentation
- Add tests

## License

MIT License - feel free to use this for learning and experimentation!