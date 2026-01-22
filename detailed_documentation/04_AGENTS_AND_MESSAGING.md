# Agents & Messaging Deep Dive

A comprehensive guide to understanding agents and the message system.

## Agent Lifecycle

### Creation
```python
config = AgentConfig(name="myagent", role="Description")
agent = MyAgent(config)
```

### Registration
```python
orchestrator.register_agent(agent)
```

### Start
```python
await orchestrator.start()  # Starts all agents
# Each agent runs: async def start()
```

### Message Processing Loop
```python
while self.running:
    message = await self.inbox.get()
    await self.process_message(message)
```

### Stop
```python
await orchestrator.stop()  # Stops all agents
```

## Message Structure

### Core Fields
- `type`: MessageType enum (TASK, QUERY, RESPONSE, BROADCAST, ERROR, STATUS, SYSTEM)
- `sender`: str - agent ID who sent it
- `recipient`: str | None - target agent (None = broadcast)
- `content`: str - the actual message
- `metadata`: dict - extra data
- `id`: str - unique identifier (auto-generated)
- `timestamp`: datetime - when created

### Message Types Explained

**TASK**: Delegate work
```python
Message(type=MessageType.TASK, content="Process this data")
```

**QUERY**: Ask for information
```python
Message(type=MessageType.QUERY, content="What is the status?")
```

**RESPONSE**: Reply to task/query
```python
Message(type=MessageType.RESPONSE, content="Status: Complete")
```

**BROADCAST**: Announce to all
```python
Message(type=MessageType.BROADCAST, content="System update")
```

**ERROR**: Report problems
```python
Message(type=MessageType.ERROR, content="Failed to process")
```

## Custom Agent Development

### Minimal Agent
```python
class MinimalAgent(Agent):
    def __init__(self):
        config = AgentConfig(name="minimal", role="Basic agent")
        super().__init__(config)

    async def process_message(self, message: Message):
        print(f"Received: {message.content}")
```

### Stateful Agent
```python
class Counter Agent(Agent):
    async def process_message(self, message: Message):
        count = self._state.get("count", 0)
        self._state["count"] = count + 1
        
        response = Message(
            type=MessageType.RESPONSE,
            sender=self.id,
            recipient=message.sender,
            content=f"Message #{count + 1}"
        )
        await self.send_message(response)
```

### Agent with Capabilities
```python
class WorkerAgent(Agent):
    def __init__(self):
        config = AgentConfig(
            name="worker",
            role="Task processor",
            capabilities=["calculate", "analyze", "report"]
        )
        super().__init__(config)

    async def process_message(self, message: Message):
        if "calculate" in message.content:
            await self.do_calculation(message)
        elif "analyze" in message.content:
            await self.do_analysis(message)
```

## Message Routing

### Direct Messaging
```python
message = Message(
    type=MessageType.TASK,
    sender="alice",
    recipient="bob",  # Specific recipient
    content="Do this task"
)
await orchestrator.send_message_to_agent("bob", message)
```

### Broadcasting
```python
message = Message(
    type=MessageType.BROADCAST,
    sender="system",
    recipient=None,  # No specific recipient
    content="Important announcement"
)
await orchestrator.broadcast_message(message)
# All agents except sender receive it
```

### Routing Logic
```
if message.recipient is None:
    → Broadcast to all except sender
else if message.recipient in registered_agents:
    → Send to specific agent
else:
    → Warning: recipient not found
```

## Agent State Management

### Using State Dictionary
```python
class StatefulAgent(Agent):
    async def process_message(self, message: Message):
        # Initialize
        if "initialized" not in self._state:
            self._state["initialized"] = True
            self._state["data"] = []
        
        # Use state
        self._state["data"].append(message.content)
        
        # Read state
        total = len(self._state["data"])
```

### Persisting State (with Memory System)
```python
# Save
await agent.save_state()

# Restore
await agent.restore_state()
```

## Best Practices

1. **Message Type**: Always use appropriate type
2. **Error Handling**: Wrap processing in try/except
3. **State Management**: Use _state dict for persistence
4. **Response**: Always respond to queries/tasks
5. **Async**: All agent methods should be async

## Common Patterns

### Request-Response
```python
# Sender
request = Message(type=MessageType.QUERY, content="Question?")
await self.send_message(request)

# Receiver
response = Message(type=MessageType.RESPONSE, content="Answer")
await self.send_message(response)
```

### Task Delegation
```python
for worker_id in worker_ids:
    task = Message(
        type=MessageType.TASK,
        recipient=worker_id,
        content=f"Subtask for {worker_id}"
    )
    await self.send_message(task)
```

### Event Notification
```python
event = Message(
    type=MessageType.BROADCAST,
    content="Event occurred"
)
await self.send_message(event)
```

See [API Reference](11_API_REFERENCE.md) for complete details.
