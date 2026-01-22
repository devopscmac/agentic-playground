# Getting Started Tutorial

Welcome! This hands-on tutorial will get you up and running with the Agentic Playground framework in under 30 minutes.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Your First Agent](#your-first-agent)
- [Agent Communication](#agent-communication)
- [Using LLM Agents](#using-llm-agents)
- [Running Examples](#running-examples)
- [Common Patterns](#common-patterns)
- [Next Steps](#next-steps)

---

## Prerequisites

### What You Need

✅ **Python 3.10 or higher**
```bash
python --version  # Should show 3.10+
```

✅ **Basic Python knowledge**
- Functions and classes
- Async/await basics
- Using pip

✅ **API Keys** (for LLM agents)
- Anthropic API key (for Claude) OR
- OpenAI API key (for GPT)

Get keys at:
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/devopscmac/agentic-playground.git
cd agentic-playground
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install core dependencies
pip install -e .

# Install development tools (optional)
pip install -e ".[dev]"

# Install web UI (optional)
pip install -e ".[webui]"
```

### Step 4: Configure API Keys

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
```

### Step 5: Verify Installation

```bash
# Test imports
python -c "from agentic_playground import Agent, Orchestrator; print('✓ Installation successful!')"
```

---

## Your First Agent

Let's build a simple echo agent that responds to messages.

### Step 1: Create a File

Create `my_first_agent.py`:

```python
"""My first agent example."""

import asyncio
from agentic_playground.core import Agent, AgentConfig, Message, MessageType


class EchoAgent(Agent):
    """An agent that echoes back what it receives."""

    def __init__(self, name: str):
        # Configure the agent
        config = AgentConfig(
            name=name,
            role="Echo messages back to sender",
            capabilities=["echo"]
        )
        super().__init__(config)

    async def process_message(self, message: Message) -> None:
        """Process incoming messages by echoing them back."""
        print(f"[{self.id}] Received: {message.content}")

        # Create response
        response = Message(
            type=MessageType.RESPONSE,
            sender=self.id,
            recipient=message.sender,
            content=f"Echo: {message.content}"
        )

        # Send response
        await self.send_message(response)


async def main():
    """Run the echo agent."""
    # Import at function level to avoid circular imports
    from agentic_playground.core import Orchestrator

    # Create orchestrator
    orchestrator = Orchestrator()

    # Create agent
    echo_agent = EchoAgent(name="echo_bot")

    # Register agent with orchestrator
    orchestrator.register_agent(echo_agent)

    # Start orchestrator (starts all agents)
    await orchestrator.start()

    # Send a message to the agent
    test_message = Message(
        type=MessageType.QUERY,
        sender="user",
        recipient="echo_bot",
        content="Hello, agent!"
    )

    await orchestrator.send_message_to_agent("echo_bot", test_message)

    # Wait a bit for processing
    await asyncio.sleep(1)

    # Check message history
    print(f"\nMessage history: {len(orchestrator.message_history)} messages")
    for msg in orchestrator.message_history:
        print(f"  {msg.sender} → {msg.recipient}: {msg.content}")

    # Stop orchestrator
    await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2: Run It

```bash
python my_first_agent.py
```

**Expected Output:**
```
Registered agent: Agent(echo_bot, role=Echo messages back to sender)
Starting orchestrator with 1 agents...
All agents started

[QUERY] user → echo_bot: Hello, agent!
[echo_bot] Received: Hello, agent!

[RESPONSE] echo_bot → user: Echo: Hello, agent!

Message history: 2 messages
  user → echo_bot: Hello, agent!
  echo_bot → user: Echo: Hello, agent!

Stopping orchestrator...
All agents stopped
```

### Understanding the Code

1. **Agent Class**: Inherit from `Agent` and implement `process_message()`
2. **Configuration**: Set name, role, and capabilities
3. **Orchestrator**: Manages agents and routes messages
4. **Messages**: Structured communication with type, sender, recipient
5. **Async**: Everything uses `async`/`await` for concurrency

---

## Agent Communication

Now let's create two agents that talk to each other.

### Multi-Agent Example

Create `talking_agents.py`:

```python
"""Two agents having a conversation."""

import asyncio
from agentic_playground.core import Agent, AgentConfig, Message, MessageType, Orchestrator


class GreeterAgent(Agent):
    """Agent that greets others."""

    def __init__(self):
        config = AgentConfig(
            name="greeter",
            role="Greets other agents",
        )
        super().__init__(config)

    async def process_message(self, message: Message) -> None:
        if message.type == MessageType.QUERY:
            response = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                content=f"Hello {message.sender}! How can I help you?"
            )
            await self.send_message(response)


class CounterAgent(Agent):
    """Agent that counts messages."""

    def __init__(self):
        config = AgentConfig(
            name="counter",
            role="Counts messages received",
        )
        super().__init__(config)
        # Use state to track count
        self._state["count"] = 0

    async def process_message(self, message: Message) -> None:
        # Increment counter
        self._state["count"] += 1
        count = self._state["count"]

        print(f"[Counter] Message #{count} from {message.sender}")

        # Respond
        response = Message(
            type=MessageType.RESPONSE,
            sender=self.id,
            recipient=message.sender,
            content=f"This is message #{count} I've received!"
        )
        await self.send_message(response)


async def main():
    # Create orchestrator
    orch = Orchestrator()

    # Create and register agents
    orch.register_agent(GreeterAgent())
    orch.register_agent(CounterAgent())

    # Start
    await orch.start()

    # Greeter asks Counter a question
    msg1 = Message(
        type=MessageType.QUERY,
        sender="greeter",
        recipient="counter",
        content="How many messages have you received?"
    )
    await orch.send_message_to_agent("counter", msg1)

    await asyncio.sleep(0.5)

    # Counter asks Greeter a question
    msg2 = Message(
        type=MessageType.QUERY,
        sender="counter",
        recipient="greeter",
        content="Can you greet me?"
    )
    await orch.send_message_to_agent("greeter", msg2)

    await asyncio.sleep(0.5)

    # Print conversation
    print("\n=== Conversation ===")
    for msg in orch.message_history:
        print(f"{msg.sender} → {msg.recipient}: {msg.content}")

    await orch.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

### Run It

```bash
python talking_agents.py
```

---

## Using LLM Agents

Now let's use AI! This requires an API key.

### LLM Agent Example

Create `llm_agent_example.py`:

```python
"""LLM-powered agent example."""

import asyncio
from agentic_playground.core import AgentConfig, Message, MessageType, Orchestrator, LLMAgent
from agentic_playground.llm import AnthropicProvider


async def main():
    # Create orchestrator
    orch = Orchestrator()

    # Configure LLM agent
    config = AgentConfig(
        name="assistant",
        role="Helpful AI assistant",
        system_prompt="You are a helpful assistant. Keep responses concise."
    )

    # Create LLM agent with Anthropic provider
    assistant = LLMAgent(config, AnthropicProvider())

    # Register and start
    orch.register_agent(assistant)
    await orch.start()

    # Ask a question
    question = Message(
        type=MessageType.QUERY,
        sender="user",
        recipient="assistant",
        content="What are three benefits of multi-agent systems?"
    )

    print(f"Question: {question.content}\n")
    await orch.send_message_to_agent("assistant", question)

    # Wait for response
    await asyncio.sleep(5)

    # Get response
    for msg in orch.message_history:
        if msg.type == MessageType.RESPONSE:
            print(f"Answer: {msg.content}")

    await orch.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

### Run It

```bash
python llm_agent_example.py
```

> 💡 **Tip**: You can also use OpenAI:
> ```python
> from agentic_playground.llm import OpenAIProvider
> assistant = LLMAgent(config, OpenAIProvider())
> ```

---

## Running Examples

The repository includes several examples.

### 1. Simple Conversation

Two LLM agents have a creative conversation:

```bash
python -m agentic_playground.examples.simple_conversation
```

### 2. Coordination Demo

A coordinator delegates tasks to worker agents:

```bash
python -m agentic_playground.examples.coordination_demo
```

### 3. Web UI

Interactive web interface:

```bash
# Install web UI dependencies first
pip install -e ".[webui]"

# Launch with pre-configured agents
python -m agentic_playground.examples.webui_quickstart
```

### 4. Memory System Demo

Session persistence and memory:

```bash
# Requires memory system (from feature branch)
python -m agentic_playground.examples.memory_demo
```

---

## Common Patterns

### Pattern 1: Broadcast Messages

Send a message to all agents:

```python
broadcast = Message(
    type=MessageType.BROADCAST,
    sender="system",
    content="Important announcement!"
)
await orchestrator.broadcast_message(broadcast)
```

### Pattern 2: Agent State

Track information across messages:

```python
class StatefulAgent(Agent):
    async def process_message(self, message: Message):
        # Read state
        visits = self._state.get("visits", 0)

        # Update state
        self._state["visits"] = visits + 1

        # Use state
        response = f"This is visit #{visits + 1}"
```

### Pattern 3: Message Filtering

Only process certain message types:

```python
async def process_message(self, message: Message):
    if message.type == MessageType.TASK:
        await self.handle_task(message)
    elif message.type == MessageType.QUERY:
        await self.handle_query(message)
    else:
        # Ignore other types
        pass
```

### Pattern 4: Error Handling

Gracefully handle errors:

```python
async def process_message(self, message: Message):
    try:
        result = await self.do_work(message)
        await self.send_response(result)
    except Exception as e:
        error_msg = Message(
            type=MessageType.ERROR,
            sender=self.id,
            recipient=message.sender,
            content=f"Error: {str(e)}"
        )
        await self.send_message(error_msg)
```

### Pattern 5: Task Delegation

Coordinator pattern:

```python
class CoordinatorAgent(Agent):
    async def process_message(self, message: Message):
        # Break into subtasks
        subtasks = self.break_down_task(message.content)

        # Delegate to workers
        for worker_id, subtask in subtasks:
            task_msg = Message(
                type=MessageType.TASK,
                sender=self.id,
                recipient=worker_id,
                content=subtask
            )
            await self.send_message(task_msg)
```

---

## Troubleshooting

### Issue: Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'agentic_playground'

# Solution: Install in development mode
pip install -e .
```

### Issue: API Key Not Found

```bash
# Error: anthropic.APIKeyError

# Solution: Check .env file
cat .env  # Should show ANTHROPIC_API_KEY=...

# Make sure to load it
from dotenv import load_dotenv
load_dotenv()
```

### Issue: Async Errors

```python
# Error: RuntimeWarning: coroutine was never awaited

# Wrong:
result = my_async_function()

# Right:
result = await my_async_function()
```

### Issue: Agents Not Responding

```python
# Make sure to:
1. Register agents: orch.register_agent(agent)
2. Start orchestrator: await orch.start()
3. Wait for processing: await asyncio.sleep(1)
```

---

## Quick Reference

### Essential Imports

```python
# Core components
from agentic_playground.core import (
    Agent,
    AgentConfig,
    Message,
    MessageType,
    Orchestrator,
    LLMAgent
)

# LLM providers
from agentic_playground.llm import (
    AnthropicProvider,
    OpenAIProvider
)

# Memory system (optional)
from agentic_playground.memory import (
    MemoryManager,
    SQLiteStorage
)
```

### Basic Workflow

```python
# 1. Create orchestrator
orch = Orchestrator()

# 2. Create agents
agent = MyAgent(config)

# 3. Register
orch.register_agent(agent)

# 4. Start
await orch.start()

# 5. Send messages
await orch.send_message_to_agent(agent_id, message)

# 6. Stop
await orch.stop()
```

---

## Next Steps

### Continue Learning

**Deep Dive into Agents**: [Agents & Messaging →](04_AGENTS_AND_MESSAGING.md)

**Learn LLM Integration**: [LLM Integration →](05_LLM_INTEGRATION.md)

**Build Applications**: [Building Applications →](09_BUILDING_APPLICATIONS.md)

### Experiment

1. **Modify the examples**: Change prompts, add agents
2. **Create custom agents**: Implement your own logic
3. **Build a project**: Customer service bot, research assistant, etc.

### Get Help

- **Documentation**: Read component-specific guides
- **Examples**: Check `examples/` folder
- **Issues**: Open GitHub issue
- **Troubleshooting**: [Troubleshooting Guide](12_TROUBLESHOOTING.md)

---

**Congratulations!** You've successfully:
✅ Installed the framework
✅ Created your first agent
✅ Made agents communicate
✅ Used LLM agents
✅ Run examples

**Ready for more?** [Continue to Agents & Messaging →](04_AGENTS_AND_MESSAGING.md)
