# Orchestration Guide

The Orchestrator manages agent lifecycles and message routing.

## Core Responsibilities

1. **Agent Registry**: Track all agents
2. **Message Routing**: Direct and broadcast messages
3. **Lifecycle Management**: Start/stop agents
4. **History Tracking**: Log all messages
5. **Memory Integration**: Optional session persistence

## Basic Usage

```python
from agentic_playground import Orchestrator

orch = Orchestrator()

# Register agents
orch.register_agent(agent1)
orch.register_agent(agent2)

# Start all
await orch.start()

# Send messages
await orch.send_message_to_agent("agent1", message)

# Stop all
await orch.stop()
```

## Message Routing

### Direct Messages
```python
message = Message(
    type=MessageType.TASK,
    sender="alice",
    recipient="bob",
    content="Do this"
)
await orch.send_message_to_agent("bob", message)
```

### Broadcast Messages
```python
message = Message(
    type=MessageType.BROADCAST,
    sender="system",
    content="Announcement"
)
await orch.broadcast_message(message)
# Goes to all agents except "system"
```

## Lifecycle Management

### Starting
```python
await orch.start()
# - Creates async task for each agent
# - Each agent starts its message processing loop
# - Returns immediately (non-blocking)
```

### Stopping
```python
await orch.stop()
# - Sets running flag to False for all agents
# - Cancels all agent tasks
# - Waits for graceful shutdown
```

## Message History

### Access History
```python
# All messages
all_messages = orch.message_history

# Filter by agent
alice_messages = orch.get_message_history(agent_id="alice")

# Filter by type
queries = orch.get_message_history(message_type=MessageType.QUERY)

# Both filters
alice_queries = orch.get_message_history(
    agent_id="alice",
    message_type=MessageType.QUERY
)
```

### Clear History
```python
orch.message_history.clear()
```

## Memory Integration

### Attach Memory
```python
from agentic_playground.memory import MemoryManager, SQLiteStorage

storage = SQLiteStorage("./data/sessions.db")
await storage.initialize()

memory = MemoryManager(storage)
session_id = await memory.create_session()

# Attach to orchestrator
orch.attach_memory_manager(memory, session_id)

# Now all messages are automatically persisted!
```

### Save/Restore Sessions
```python
# Save current state
await orch.save_session()

# Later, restore
await orch.restore_session(session_id)
# All messages and agent states restored!
```

## Error Handling

Orchestrator catches errors:
```python
# In _handle_message:
try:
    await agent.receive_message(message)
except Exception as e:
    error_msg = Message(
        type=MessageType.ERROR,
        sender="orchestrator",
        content=f"Error: {str(e)}"
    )
    await self._handle_message(error_msg)
```

## Agent Registration

### Register
```python
orch.register_agent(agent)
# - Adds to agents dict
# - Sets message callback
# - Attaches memory if available
```

### Unregister
```python
orch.unregister_agent("agent_id")
# - Removes from agents dict
# - Agent can no longer receive messages
```

### Check Registration
```python
if "alice" in orch.agents:
    print("Alice is registered")

# Get agent
agent = orch.agents.get("alice")
```

## Best Practices

1. **One orchestrator per application**
2. **Register all agents before starting**
3. **Always stop orchestrator when done**
4. **Use memory for persistence**
5. **Monitor message history size**

See [Core Concepts](02_CORE_CONCEPTS.md) for architecture details.
