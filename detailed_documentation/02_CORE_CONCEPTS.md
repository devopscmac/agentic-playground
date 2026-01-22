# Core Concepts & Architecture

This guide provides a technical overview of the Agentic Playground framework's architecture, design principles, and component relationships.

## Table of Contents
- [System Architecture](#system-architecture)
- [Design Principles](#design-principles)
- [Core Components](#core-components)
- [Message Flow](#message-flow)
- [Async/Await Patterns](#asyncawait-patterns)
- [Component Relationships](#component-relationships)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  (Your code, Web UI, CLI tools, Custom integrations)   │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                  Orchestration Layer                     │
│         ┌─────────────────────────────────┐            │
│         │       Orchestrator              │            │
│         │  - Agent management             │            │
│         │  - Message routing              │            │
│         │  - Lifecycle control            │            │
│         └─────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                     Agent Layer                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐          │
│  │  Agent 1  │  │  Agent 2  │  │  Agent 3  │          │
│  │  - State  │  │  - State  │  │  - State  │          │
│  │  - Logic  │  │  - Logic  │  │  - Logic  │          │
│  └───────────┘  └───────────┘  └───────────┘          │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                   Integration Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ LLM         │  │   Memory    │  │   Storage   │   │
│  │ Providers   │  │   System    │  │   Backend   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Layered Architecture

#### 1. Application Layer
Where your code lives. You interact with the framework through this layer:
- Create agents
- Send messages
- Handle results
- Build UIs

#### 2. Orchestration Layer
The control center that manages agents:
- Registers and tracks agents
- Routes messages between agents
- Manages agent lifecycles
- Handles errors and exceptions

#### 3. Agent Layer
Individual agents that do the actual work:
- Process messages
- Make decisions
- Maintain state
- Communicate with other agents

#### 4. Integration Layer
Connections to external services:
- LLM providers (Claude, GPT)
- Memory and storage systems
- Databases and caches

---

## Design Principles

### 1. Message-Driven Architecture

> 💡 **Key Principle**: Everything happens through messages

Agents don't call each other directly. They exchange **messages**.

**Why?**
- **Loose coupling**: Agents don't need to know implementation details
- **Async-friendly**: Messages can be queued and processed later
- **Traceable**: Every interaction is a concrete message object
- **Testable**: Easy to mock messages for testing

```python
# NOT THIS (tight coupling):
result = agent_b.some_method(data)

# THIS (message-based):
message = Message(
    type=MessageType.TASK,
    sender="agent_a",
    recipient="agent_b",
    content="Process this data"
)
await orchestrator.send_message(message)
```

### 2. Async-First Design

> 💡 **Key Principle**: All operations are asynchronous

**Why?**
- **Concurrent execution**: Multiple agents work simultaneously
- **Non-blocking**: Agents don't wait for each other
- **Scalable**: Handle many messages efficiently
- **Responsive**: UI doesn't freeze

```python
# All agent methods are async
async def process_message(self, message):
    result = await self.llm_provider.generate(...)
    await self.send_message(response)
```

### 3. Extensible Core

> 💡 **Key Principle**: Easy to extend, hard to break

Framework provides:
- **Abstract base classes**: `Agent`, `LLMProvider`, `StorageBackend`
- **Clear interfaces**: Well-defined methods and contracts
- **Minimal requirements**: Only implement what you need

```python
# Extend the Agent base class
class MyCustomAgent(Agent):
    async def process_message(self, message):
        # Your custom logic
        pass
```

### 4. Explicit Over Implicit

> 💡 **Key Principle**: Clear and obvious behavior

- Message types are explicit (TASK, QUERY, RESPONSE)
- Routing is explicit (sender, recipient)
- State management is explicit (self._state)
- No magic or hidden behaviors

### 5. Opt-In Features

> 💡 **Key Principle**: Features are optional, not mandatory

```python
# Basic usage (no memory)
agent = Agent(config)

# With memory (opt-in)
agent = Agent(config)
agent.set_memory_manager(memory_manager)

# With context management (opt-in)
agent = LLMAgent(config, provider, enable_context_management=True)
```

---

## Core Components

### Component Diagram

```
┌──────────────────────────────────────────────────────────┐
│                      Orchestrator                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │ agents: dict[str, Agent]                           │ │
│  │ message_history: list[Message]                     │ │
│  │ memory_manager: Optional[MemoryManager]            │ │
│  └────────────────────────────────────────────────────┘ │
│  Methods:                                                 │
│  - register_agent(agent)                                  │
│  - send_message_to_agent(id, message)                     │
│  - broadcast_message(message)                             │
│  - start() / stop()                                       │
└──────────────────────────────────────────────────────────┘
                           │
                           │ manages
                           ↓
┌──────────────────────────────────────────────────────────┐
│                         Agent                             │
│  ┌────────────────────────────────────────────────────┐ │
│  │ id: str                                            │ │
│  │ config: AgentConfig                                │ │
│  │ inbox: Queue[Message]                              │ │
│  │ _state: dict                                       │ │
│  │ memory_manager: Optional[MemoryManager]            │ │
│  └────────────────────────────────────────────────────┘ │
│  Methods:                                                 │
│  - process_message(message) [ABSTRACT]                    │
│  - send_message(message)                                  │
│  - save_state() / restore_state()                         │
└──────────────────────────────────────────────────────────┘
                           │
                           │ specializes
                           ↓
┌──────────────────────────────────────────────────────────┐
│                       LLMAgent                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │ llm_provider: LLMProvider                          │ │
│  │ conversation_history: list[LLMMessage]             │ │
│  │ context_manager: Optional[ContextManager]          │ │
│  │ query_engine: Optional[QueryEngine]                │ │
│  └────────────────────────────────────────────────────┘ │
│  Methods:                                                 │
│  - process_message(message) [IMPLEMENTED]                 │
│  - _format_message_for_llm(message)                       │
│  - clear_history()                                        │
└──────────────────────────────────────────────────────────┘
```

### 1. Message

The fundamental communication unit.

```python
@dataclass
class Message:
    type: MessageType       # TASK, QUERY, RESPONSE, etc.
    sender: str            # Who sent it
    recipient: str         # Who receives it
    content: str           # The actual message
    metadata: dict         # Extra information
    id: str                # Unique identifier
    timestamp: datetime    # When it was sent
```

**Message Types:**
- `TASK`: "Do this for me"
- `QUERY`: "I need information about..."
- `RESPONSE`: "Here's the answer"
- `BROADCAST`: "Everyone should know this"
- `SYSTEM`: "System notification"
- `ERROR`: "Something went wrong"
- `STATUS`: "Current state update"

### 2. AgentConfig

Configuration for agent initialization.

```python
class AgentConfig(BaseModel):
    name: str                    # Unique identifier
    role: str                    # Human-readable role
    system_prompt: str          # For LLM agents
    capabilities: list[str]     # What the agent can do
    max_iterations: int         # Safety limit
    metadata: dict              # Custom configuration
```

### 3. Agent (Base Class)

Abstract base that all agents inherit from.

**Key Responsibilities:**
- Message processing (abstract method)
- Message sending (via orchestrator callback)
- State management (dictionary-based)
- Inbox management (async queue)
- Lifecycle (start/stop)

**Key Attributes:**
```python
self.id: str                    # Agent identifier
self.config: AgentConfig        # Configuration
self.inbox: asyncio.Queue       # Message queue
self._state: dict              # Internal state
self.memory_manager: Optional   # Memory system
```

**Key Methods:**
```python
async def process_message(msg) # [ABSTRACT] Process incoming message
async def send_message(msg)    # Send message via orchestrator
async def save_state()         # Persist state to memory
async def restore_state()      # Load state from memory
async def start()              # Begin message processing
async def stop()               # Stop processing
```

### 4. LLMAgent

Agent that uses LLMs for reasoning.

**Adds:**
- LLM provider integration
- Conversation history management
- Context window management
- Memory retrieval
- Automatic prompt formatting

**Processing Flow:**
```
1. Receive message
2. Format for LLM
3. Retrieve relevant memories (if enabled)
4. Prepare context (with pruning if needed)
5. Call LLM
6. Format response
7. Send response
8. Save to memory (if enabled)
```

### 5. Orchestrator

The central coordinator.

**Responsibilities:**
- Agent registration and tracking
- Message routing (direct and broadcast)
- Lifecycle management (start/stop all agents)
- Message history
- Memory system integration

**Message Routing Logic:**
```python
if message.recipient is None:
    # Broadcast to all except sender
    for agent in agents:
        if agent.id != message.sender:
            await agent.receive_message(message)
else:
    # Direct message to recipient
    await agents[message.recipient].receive_message(message)
```

---

## Message Flow

### Detailed Message Journey

```
Step 1: Application sends message
┌──────────────┐
│ Application  │ message = Message(...)
│              │ await orchestrator.send_message_to_agent("bob", message)
└──────────────┘
       ↓
Step 2: Orchestrator routes message
┌──────────────┐
│ Orchestrator │ await agents["bob"].receive_message(message)
│              │ [Also: store in history, persist if memory enabled]
└──────────────┘
       ↓
Step 3: Agent receives message
┌──────────────┐
│  Agent Bob   │ await inbox.put(message)
│   (inbox)    │ [Message queued for processing]
└──────────────┘
       ↓
Step 4: Agent processes message
┌──────────────┐
│  Agent Bob   │ message = await inbox.get()
│  (process)   │ await process_message(message)
└──────────────┘
       ↓
Step 5: Agent generates response
┌──────────────┐
│  Agent Bob   │ response = Message(...)
│  (respond)   │ await self.send_message(response)
└──────────────┘
       ↓
Step 6: Back to orchestrator
┌──────────────┐
│ Orchestrator │ await _handle_message(response)
│              │ [Route to original sender or specified recipient]
└──────────────┘
```

### Example: Three-Agent Conversation

```
User → [Orchestrator] → Coordinator Agent
                            ↓
                    "I need help with task X"
                            ↓
                      [Analyzes task]
                            ↓
         ┌──────────────────┴──────────────────┐
         ↓                                      ↓
    Worker Agent A                         Worker Agent B
    "Handle part 1"                        "Handle part 2"
         ↓                                      ↓
    [Processes]                            [Processes]
         ↓                                      ↓
    "Part 1 done"                          "Part 2 done"
         └──────────────────┬──────────────────┘
                            ↓
                    Coordinator Agent
                      [Combines results]
                            ↓
                       "Task X complete"
                            ↓
                    [Orchestrator] → User
```

---

## Async/Await Patterns

### Why Async?

**Without Async (Blocking):**
```python
def process_three_agents():
    result1 = agent1.process()  # Wait...
    result2 = agent2.process()  # Wait...
    result3 = agent3.process()  # Wait...
    # Total time = sum of all times
```

**With Async (Concurrent):**
```python
async def process_three_agents():
    results = await asyncio.gather(
        agent1.process(),
        agent2.process(),
        agent3.process()
    )
    # Total time = max of all times
```

### Common Patterns

#### Pattern 1: Sequential Processing
```python
async def sequential_workflow():
    msg1 = await step1()
    msg2 = await step2(msg1)
    msg3 = await step3(msg2)
    return msg3
```

#### Pattern 2: Concurrent Processing
```python
async def concurrent_workflow():
    results = await asyncio.gather(
        agent1.process(),
        agent2.process(),
        agent3.process()
    )
    return combine(results)
```

#### Pattern 3: Wait for First
```python
async def race_agents():
    # Get first response
    done, pending = await asyncio.wait(
        [agent1.process(), agent2.process()],
        return_when=asyncio.FIRST_COMPLETED
    )
    # Cancel others
    for task in pending:
        task.cancel()
```

#### Pattern 4: Message Queue
```python
async def process_inbox():
    while self.running:
        try:
            # Wait for message with timeout
            message = await asyncio.wait_for(
                self.inbox.get(),
                timeout=0.1
            )
            await self.process_message(message)
        except asyncio.TimeoutError:
            continue  # Check running flag
```

---

## Component Relationships

### Dependency Graph

```
Application Code
    ↓ uses
Orchestrator
    ↓ manages
Agent (base class)
    ↓ inherits
LLMAgent
    ↓ uses
LLMProvider (interface)
    ↓ implements
├─ AnthropicProvider
└─ OpenAIProvider

Orchestrator + Agent
    ↓ optionally uses
MemoryManager
    ↓ uses
├─ StorageBackend (SQLite)
├─ ContextManager
└─ QueryEngine
```

### Data Flow

```
Configuration (AgentConfig)
    ↓
Agent Initialization
    ↓
Registration with Orchestrator
    ↓
Start Processing Loop
    ↓
Receive Messages (via inbox)
    ↓
Process Messages (custom logic)
    ↓
Generate Responses
    ↓
Send via Orchestrator
    ↓
Route to Recipients
    ↓
[Cycle continues]
```

### State Management

```
Agent Level:
self._state = {}                # In-memory state
    ↓
    ↓ optionally persisted to
    ↓
MemoryManager
    ↓
SQLiteStorage
    ↓
Database (sessions.db)

Session Level:
orchestrator.message_history    # In-memory history
    ↓
    ↓ optionally persisted to
    ↓
MemoryManager.store_message()
    ↓
Database (messages table)
```

---

## Key Design Decisions

### 1. Why Message Queues?

**Decision**: Each agent has an `asyncio.Queue` for messages

**Rationale**:
- Decouples message receipt from processing
- Natural backpressure mechanism
- Async-friendly
- Thread-safe

**Alternative Considered**: Direct method calls
**Why Not**: Tight coupling, synchronous, hard to test

### 2. Why Dictionary-Based State?

**Decision**: `self._state: dict = {}`

**Rationale**:
- Flexible (no predefined schema)
- Easy to serialize
- Simple to understand
- Works with any data type

**Alternative Considered**: Class attributes
**Why Not**: Less flexible, harder to persist

### 3. Why Callback Pattern?

**Decision**: Agents get a callback for sending messages

```python
agent.set_message_callback(orchestrator._handle_message)
```

**Rationale**:
- Agents don't need reference to orchestrator
- Can change routing logic without changing agents
- Easy to intercept/log messages
- Testable with mock callbacks

**Alternative Considered**: Pass orchestrator reference
**Why Not**: Tight coupling, circular dependencies

---

## Performance Considerations

### Memory Usage

- **Message History**: Grows with conversation length
- **Agent State**: One dictionary per agent
- **Inbox Queues**: Bounded by message rate
- **LLM Context**: Managed by ContextManager

**Optimization**: Use memory system with pruning

### Concurrency

- **Agent Tasks**: One task per agent
- **Message Processing**: Sequential per agent, concurrent across agents
- **LLM Calls**: Can be rate-limited by provider

**Optimization**: Batch messages, use multiple agents

### Latency

- **Message Routing**: ~microseconds (in-process)
- **Agent Processing**: Depends on logic
- **LLM Calls**: 1-5 seconds typically

**Optimization**: Cache responses, use faster models

---

## Next Steps

Now that you understand the architecture:

**Learn by Doing**: [Getting Started Tutorial →](03_GETTING_STARTED.md)

**Deep Dive into Components**:
- [Agents & Messaging →](04_AGENTS_AND_MESSAGING.md)
- [LLM Integration →](05_LLM_INTEGRATION.md)
- [Orchestration →](06_ORCHESTRATION.md)

**Reference**: [API Reference →](11_API_REFERENCE.md)

---

*Questions about architecture? See [Troubleshooting Guide](12_TROUBLESHOOTING.md) or open an issue.*
