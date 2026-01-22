# Getting Started with Agentic Playground

This guide will walk you through setting up and running your first multi-agent system.

## Prerequisites

- Python 3.10 or higher
- An API key from Anthropic or OpenAI (for LLM-powered agents)

## Installation

### 1. Set Up the Environment

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# You need at least one:
# - ANTHROPIC_API_KEY for Claude
# - OPENAI_API_KEY for GPT models
```

## Your First Agent System

Let's build a simple agent system step by step.

### Step 1: Create a Basic Agent

Create a file `my_first_agent.py`:

```python
import asyncio
from agentic_playground import AgentConfig, Message, MessageType, Orchestrator
from agentic_playground.agents import EchoAgent

async def main():
    # Create an orchestrator
    orchestrator = Orchestrator()

    # Create a simple echo agent
    echo = EchoAgent(name="echo")

    # Register the agent
    orchestrator.register_agent(echo)

    # Start the orchestrator (this starts all agents)
    await orchestrator.start()

    # Send a message to the agent
    message = Message(
        type=MessageType.QUERY,
        sender="user",
        recipient="echo",
        content="Hello, echo agent!"
    )

    await orchestrator.send_message_to_agent("echo", message)

    # Wait a bit for processing
    await asyncio.sleep(1)

    # Stop the orchestrator
    await orchestrator.stop()

    # Print what happened
    orchestrator.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python my_first_agent.py
```

### Step 2: Add an LLM-Powered Agent

Now let's add an intelligent agent that uses an LLM:

```python
import asyncio
from dotenv import load_dotenv
from agentic_playground import AgentConfig, Message, MessageType, Orchestrator
from agentic_playground.core import LLMAgent
from agentic_playground.llm import AnthropicProvider

load_dotenv()

async def main():
    orchestrator = Orchestrator()

    # Create an LLM-powered agent
    config = AgentConfig(
        name="assistant",
        role="Helpful Assistant",
        system_prompt="You are a friendly and helpful assistant. Keep responses brief."
    )

    # Create the LLM provider
    llm = AnthropicProvider()

    # Create the agent
    assistant = LLMAgent(config, llm)

    # Register and start
    orchestrator.register_agent(assistant)
    await orchestrator.start()

    # Ask the agent a question
    message = Message(
        type=MessageType.QUERY,
        sender="user",
        recipient="assistant",
        content="What is the capital of France?"
    )

    await orchestrator.send_message_to_agent("assistant", message)

    # Wait for response
    await asyncio.sleep(3)

    await orchestrator.stop()
    orchestrator.print_summary()

asyncio.run(main())
```

### Step 3: Agent-to-Agent Communication

Let's make two agents talk to each other:

```python
import asyncio
from dotenv import load_dotenv
from agentic_playground import AgentConfig, Message, MessageType, Orchestrator
from agentic_playground.core import LLMAgent
from agentic_playground.llm import AnthropicProvider

load_dotenv()

async def main():
    orchestrator = Orchestrator()
    llm = AnthropicProvider()

    # Create a teacher agent
    teacher_config = AgentConfig(
        name="teacher",
        role="Teacher",
        system_prompt="You are a patient teacher. Explain things simply."
    )
    teacher = LLMAgent(teacher_config, llm)

    # Create a student agent
    student_config = AgentConfig(
        name="student",
        role="Curious Student",
        system_prompt="You are a curious student who asks questions. Keep it brief."
    )
    student = LLMAgent(student_config, llm)

    # Register agents
    orchestrator.register_agent(teacher)
    orchestrator.register_agent(student)

    await orchestrator.start()

    # Student asks teacher a question
    question = Message(
        type=MessageType.QUERY,
        sender="student",
        recipient="teacher",
        content="Can you explain what photosynthesis is?"
    )
    await orchestrator.send_message_to_agent("teacher", question)

    # Let the conversation unfold
    await asyncio.sleep(5)

    await orchestrator.stop()
    orchestrator.print_summary()

asyncio.run(main())
```

## Key Concepts

### Messages

Messages are how agents communicate. Each message has:
- `type`: What kind of message (QUERY, TASK, RESPONSE, etc.)
- `sender`: Who sent it
- `recipient`: Who should receive it (optional, None for broadcast)
- `content`: The actual message content
- `metadata`: Additional data (optional)

### Message Types

- **QUERY**: Ask a question
- **TASK**: Request an action
- **RESPONSE**: Reply to a query or task
- **BROADCAST**: Message all agents
- **SYSTEM**: System-level notification
- **ERROR**: Error message

### The Orchestrator

The orchestrator:
1. Manages agent lifecycle (starting/stopping)
2. Routes messages between agents
3. Maintains message history
4. Provides coordination services

### Creating Custom Agents

Extend the `Agent` class:

```python
from agentic_playground.core import Agent, AgentConfig, Message, MessageType

class MyAgent(Agent):
    def __init__(self):
        config = AgentConfig(
            name="my_agent",
            role="My Custom Role"
        )
        super().__init__(config)

    async def process_message(self, message: Message) -> None:
        # Your custom logic here
        print(f"Received: {message.content}")

        # Send a response
        response = Message(
            type=MessageType.RESPONSE,
            sender=self.id,
            recipient=message.sender,
            content="Got your message!"
        )
        await self.send_message(response)
```

## Next Steps

1. **Run the Examples**: Check out the examples in `agentic_playground/examples/`
   - `simple_conversation.py`: Two agents chatting
   - `coordination_demo.py`: Task delegation
   - `debate.py`: Multi-perspective discussion

2. **Experiment**: Try creating agents with different personalities and roles

3. **Build Something**: Create your own multi-agent application:
   - Research assistants
   - Creative writing collaborations
   - Problem-solving teams
   - Code review systems

## Troubleshooting

### "API key not found"
Make sure you've set up your `.env` file with the correct API keys.

### Agents not responding
Check that:
1. The orchestrator is started with `await orchestrator.start()`
2. You're waiting long enough for responses (`await asyncio.sleep()`)
3. The recipient name matches an registered agent

### Import errors
Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

## Resources

- [Main README](README.md) - Complete documentation
- [Examples](agentic_playground/examples/) - Working examples
- [Tests](tests/) - Test suite for reference

## Get Help

This is a learning playground. Experiment, break things, and have fun!
