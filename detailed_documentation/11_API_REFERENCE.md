# API Reference

Complete API reference for all public classes and methods.

## Core Module (`agentic_playground.core`)

### Agent

**Base class for all agents.**

```python
class Agent(ABC):
    def __init__(self, config: AgentConfig)
```

**Attributes:**
- `id: str` - Agent identifier (from config.name)
- `config: AgentConfig` - Agent configuration
- `inbox: asyncio.Queue[Message]` - Message queue
- `running: bool` - Whether agent is running
- `_state: dict` - Internal state dictionary
- `memory_manager: Optional[MemoryManager]` - Memory system (if attached)
- `session_id: Optional[str]` - Current session (if using memory)

**Methods:**
- `async process_message(message: Message) -> None` [ABSTRACT]
  - Process an incoming message (must implement)
- `async send_message(message: Message) -> None`
  - Send a message via orchestrator
- `async start() -> None`
  - Start the agent's message processing loop
- `async stop() -> None`
  - Stop the agent
- `set_message_callback(callback) -> None`
  - Set orchestrator callback (called by orchestrator)
- `set_memory_manager(manager, session_id) -> None`
  - Attach memory manager
- `async save_state() -> None`
  - Persist state to memory
- `async restore_state() -> None`
  - Load state from memory

### AgentConfig

**Configuration for agents.**

```python
class AgentConfig(BaseModel):
    name: str                      # Unique identifier
    role: str                      # Human-readable role description
    system_prompt: Optional[str]   # System prompt for LLM agents
    capabilities: list[str]        # List of capabilities
    max_iterations: int = 10       # Safety limit
    metadata: dict                 # Custom configuration
```

### LLMAgent

**Agent powered by Large Language Models.**

```python
class LLMAgent(Agent):
    def __init__(
        self,
        config: AgentConfig,
        llm_provider: LLMProvider,
        enable_context_management: bool = True,
        max_context_tokens: int = 180000,
        enable_memory_retrieval: bool = True
    )
```

**Additional Attributes:**
- `llm_provider: LLMProvider` - LLM provider instance
- `conversation_history: list[LLMMessage]` - Full conversation
- `context_manager: Optional[ContextManager]` - Context management
- `query_engine: Optional[QueryEngine]` - Memory retrieval

**Additional Methods:**
- `clear_history(keep_system_prompt: bool = True) -> None`
  - Clear conversation history

### Message

**Communication between agents.**

```python
@dataclass
class Message:
    type: MessageType              # Message type
    sender: str                    # Sender agent ID
    recipient: Optional[str]       # Recipient agent ID (None = broadcast)
    content: str                   # Message content
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=generate_id)
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

### MessageType

**Enumeration of message types.**

```python
class MessageType(Enum):
    TASK = "task"           # Task to perform
    QUERY = "query"         # Information request
    RESPONSE = "response"   # Response to task/query
    BROADCAST = "broadcast" # Announcement to all
    SYSTEM = "system"       # System message
    ERROR = "error"         # Error notification
    STATUS = "status"       # Status update
```

### Orchestrator

**Manages agents and routes messages.**

```python
class Orchestrator:
    def __init__(self)
```

**Attributes:**
- `agents: dict[str, Agent]` - Registered agents
- `message_history: list[Message]` - All messages
- `running: bool` - Whether orchestrator is running
- `memory_manager: Optional[MemoryManager]` - Memory system
- `session_id: Optional[str]` - Current session

**Methods:**
- `register_agent(agent: Agent) -> None`
  - Register an agent
- `unregister_agent(agent_id: str) -> None`
  - Remove an agent
- `async start() -> None`
  - Start all agents
- `async stop() -> None`
  - Stop all agents
- `async send_message_to_agent(agent_id: str, message: Message) -> None`
  - Send message to specific agent
- `async broadcast_message(message: Message) -> None`
  - Broadcast message to all agents
- `get_message_history(agent_id=None, message_type=None) -> list[Message]`
  - Get filtered message history
- `attach_memory_manager(manager, session_id=None) -> str`
  - Attach memory system
- `async restore_session(session_id: str) -> None`
  - Restore previous session
- `async save_session() -> None`
  - Save current session

## LLM Module (`agentic_playground.llm`)

### LLMProvider (Base)

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse
```

### AnthropicProvider

```python
class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    )
```

### OpenAIProvider

```python
class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    )
```

### LLMResponse

```python
@dataclass
class LLMResponse:
    content: str              # Generated text
    model: str                # Model used
    usage: dict              # Token usage
    finish_reason: Optional[str]
```

### LLMMessage

```python
@dataclass
class LLMMessage:
    role: str                # "system", "user", or "assistant"
    content: str             # Message content
```

## Memory Module (`agentic_playground.memory`)

### MemoryManager

```python
class MemoryManager:
    def __init__(self, storage: StorageBackend)
```

**Session Methods:**
- `async create_session(session_id=None, metadata=None) -> str`
- `async get_session(session_id: str) -> Optional[Session]`
- `async list_sessions(limit=100, offset=0, order_by="last_active") -> list[Session]`
- `async update_session_metadata(session_id, metadata) -> None`
- `async delete_session(session_id) -> None`

**Message Methods:**
- `async store_message(...) -> str`
- `async get_messages(session_id, limit=None, offset=0, sender=None) -> list[StoredMessage]`
- `async get_message_count(session_id) -> int`

**Agent State Methods:**
- `async save_agent_state(agent_id, session_id, state_data) -> None`
- `async load_agent_state(agent_id, session_id) -> Optional[dict]`

**Memory Methods:**
- `async store_memory(...) -> int`
- `async retrieve_memories(agent_id, query, memory_type=None, limit=10) -> list[Memory]`
- `async delete_memories(agent_id, memory_ids) -> None`

### SQLiteStorage

```python
class SQLiteStorage(StorageBackend):
    def __init__(self, db_path: str = "./data/sessions.db")
    
    async def initialize() -> None
    async def close() -> None
```

### ContextManager

```python
class ContextManager:
    def __init__(
        self,
        max_tokens: int = 180000,
        buffer_tokens: int = 20000,
        always_keep_recent: int = 10,
        always_keep_system: bool = True
    )
    
    def prepare_context(messages, memories=None) -> ContextWindow
    def should_prune(messages) -> bool
    def get_token_usage(messages) -> dict
```

### Memory Types

```python
class MemoryType(Enum):
    WORKING = "working"      # Current context
    EPISODIC = "episodic"    # Past interactions
    SEMANTIC = "semantic"    # Facts and knowledge
```

## Example Agents Module (`agentic_playground.agents`)

### EchoAgent

```python
class EchoAgent(Agent):
    def __init__(self, name: str)
```

Echoes messages back to sender.

## Type Hints

All classes and methods use Python type hints:

```python
async def process_message(self, message: Message) -> None:
    response: Message = await self.generate_response(message)
    await self.send_message(response)
```

## Error Handling

All async methods may raise:
- `RuntimeError`: Configuration or state errors
- `ValueError`: Invalid parameters
- `asyncio.TimeoutError`: Operation timeout
- Provider-specific errors (API errors, rate limits)

Always wrap in try/except:

```python
try:
    await agent.process_message(message)
except Exception as e:
    logger.error(f"Processing error: {e}")
```

## Complete Example

```python
from agentic_playground.core import Agent, AgentConfig, Message, MessageType, Orchestrator, LLMAgent
from agentic_playground.llm import AnthropicProvider
from agentic_playground.memory import MemoryManager, SQLiteStorage

# Setup
async def main():
    # Memory
    storage = SQLiteStorage("./data/sessions.db")
    await storage.initialize()
    memory = MemoryManager(storage)
    session_id = await memory.create_session()
    
    # Orchestrator
    orch = Orchestrator()
    orch.attach_memory_manager(memory, session_id)
    
    # Agent
    config = AgentConfig(name="assistant", role="Helper")
    agent = LLMAgent(config, AnthropicProvider())
    orch.register_agent(agent)
    
    # Run
    await orch.start()
    msg = Message(type=MessageType.QUERY, sender="user", recipient="assistant", content="Hello")
    await orch.send_message_to_agent("assistant", msg)
    await asyncio.sleep(2)
    await orch.stop()
    await storage.close()
```

For implementation details, see source code in `agentic_playground/` directory.
