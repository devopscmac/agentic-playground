# LLM Integration Guide

Complete guide to integrating Large Language Models with agents.

## LLM Providers

### Anthropic Claude
```python
from agentic_playground.llm import AnthropicProvider

provider = AnthropicProvider(
    model="claude-sonnet-4-20250514",  # or claude-opus-4
    api_key="your-key",  # or set ANTHROPIC_API_KEY env var
    timeout=30.0
)
```

### OpenAI GPT
```python
from agentic_playground.llm import OpenAIProvider

provider = OpenAIProvider(
    model="gpt-4-turbo-preview",  # or gpt-3.5-turbo
    api_key="your-key",  # or set OPENAI_API_KEY env var
    timeout=30.0
)
```

## LLMAgent

### Basic Usage
```python
from agentic_playground.core import LLMAgent, AgentConfig

config = AgentConfig(
    name="assistant",
    role="Helpful assistant",
    system_prompt="You are a helpful AI assistant."
)

agent = LLMAgent(config, AnthropicProvider())
```

### How LLMAgent Works

```
1. Receive Message
   ↓
2. Format for LLM (add to conversation history)
   ↓
3. Retrieve Memories (if enabled)
   ↓
4. Prepare Context (with pruning if needed)
   ↓
5. Call LLM API
   ↓
6. Parse Response
   ↓
7. Send Response Message
   ↓
8. Save to Memory (if enabled)
```

### Conversation History

LLMAgent maintains full conversation:

```python
agent.conversation_history = [
    {"role": "system", "content": "You are helpful"},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "How are you?"},
    # ... continues
]
```

### Context Management (Automatic)

When enabled, prevents context overflow:

```python
agent = LLMAgent(
    config,
    provider,
    enable_context_management=True,  # Default
    max_context_tokens=180000  # For Claude
)
```

Features:
- Token counting
- Automatic pruning when approaching limit
- Preserves system prompt + recent messages
- Importance-based message selection

### Memory Retrieval (Automatic)

When enabled, retrieves relevant memories:

```python
agent = LLMAgent(
    config,
    provider,
    enable_memory_retrieval=True  # Default
)
```

Before each LLM call:
1. Extract keywords from message
2. Search memory for relevant context
3. Add retrieved memories to context
4. Call LLM with enriched context

## Prompt Engineering

### System Prompts

**Good System Prompts:**
```python
# Specific role
"You are a customer service agent. Be polite and helpful."

# With constraints
"You are a code reviewer. Provide constructive feedback. Be concise."

# With personality
"You are an enthusiastic teacher. Explain concepts simply with examples."
```

**Bad System Prompts:**
```python
# Too vague
"You are an AI"

# Too restrictive
"Only answer with yes or no"

# Too complex
"You are... [500 words of instructions]"
```

### Message Formatting

LLMAgent automatically formats messages:

```python
# Incoming message
Message(sender="user", content="What is AI?")

# Formatted for LLM
"Message from user (query): What is AI?"
```

You can customize this:
```python
class CustomLLMAgent(LLMAgent):
    def _format_message_for_llm(self, message):
        return LLMMessage(
            role="user",
            content=f"{message.sender} asks: {message.content}"
        )
```

## Managing Conversations

### Clear History
```python
# Clear all
agent.clear_history(keep_system_prompt=False)

# Keep system prompt
agent.clear_history(keep_system_prompt=True)
```

### Access History
```python
for msg in agent.conversation_history:
    print(f"{msg.role}: {msg.content}")
```

## Error Handling

### API Errors
```python
try:
    await agent.process_message(message)
except Exception as e:
    # LLMAgent catches and sends ERROR message
    # You can also handle in your code
    print(f"LLM error: {e}")
```

### Rate Limiting
```python
# Anthropic: ~50 requests/minute
# OpenAI: Varies by plan

# Handle with retry logic
import asyncio

async def call_with_retry(agent, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            await agent.process_message(message)
            break
        except RateLimitError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

## Cost Optimization

### Use Appropriate Models
```python
# Expensive (high quality)
provider = AnthropicProvider(model="claude-opus-4")

# Balanced
provider = AnthropicProvider(model="claude-sonnet-4-20250514")

# Cheaper (faster)
provider = OpenAIProvider(model="gpt-3.5-turbo")
```

### Limit Token Usage
```python
# Shorter responses
response = await provider.generate(
    messages=history,
    max_tokens=256  # Instead of 1024+
)

# Use context management
agent = LLMAgent(config, provider, enable_context_management=True)
```

### Cache System Prompts
Use identical system prompts across agents to benefit from caching.

## Best Practices

1. **System Prompts**: Be specific about role and behavior
2. **Context Length**: Enable context management for long conversations
3. **Error Handling**: Always handle API failures
4. **Model Selection**: Use cheapest model that works
5. **Testing**: Test with real LLMs, not mocks
6. **Monitoring**: Log token usage and costs

## Advanced: Custom LLM Provider

```python
from agentic_playground.llm.base import LLMProvider, LLMResponse

class CustomProvider(LLMProvider):
    async def generate(self, messages, **kwargs):
        # Call your LLM API
        response = await your_api_call(messages)
        
        return LLMResponse(
            content=response.text,
            model=self.model,
            usage={"prompt_tokens": 100, "completion_tokens": 50}
        )

# Use it
agent = LLMAgent(config, CustomProvider())
```

See [Memory System Guide](07_MEMORY_SYSTEM.md) for memory integration details.
