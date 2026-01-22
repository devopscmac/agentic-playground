# Memory & Context Management Guide

Complete guide to the memory system (from feature branch: feature/memory-and-context-management).

## Overview

The memory system provides:
- **Session Persistence**: Save/restore conversations
- **Context Management**: Automatic token limit handling
- **Memory Retrieval**: Search relevant past interactions
- **Agent State**: Persist agent internal state

## Quick Start

```python
from agentic_playground.memory import MemoryManager, SQLiteStorage

# 1. Initialize storage
storage = SQLiteStorage("./data/sessions.db")
await storage.initialize()

# 2. Create memory manager
memory = MemoryManager(storage)

# 3. Create session
session_id = await memory.create_session(metadata={"user": "alice"})

# 4. Attach to orchestrator
orchestrator.attach_memory_manager(memory, session_id)

# 5. Use normally - messages automatically saved!
```

## Session Management

### Create Session
```python
session_id = await memory.create_session(
    metadata={
        "user": "alice",
        "project": "customer_service",
        "created_via": "api"
    }
)
```

### List Sessions
```python
sessions = await memory.list_sessions(limit=10, order_by="last_active")
for session in sessions:
    print(f"{session.session_id}: {session.metadata}")
```

### Restore Session
```python
# Restore full session state
await orchestrator.restore_session(session_id)
# All messages, agent states restored!
```

### Save Session
```python
await orchestrator.save_session()
```

### Delete Session
```python
await memory.delete_session(session_id)
```

## Context Window Management

### Automatic Pruning

When enabled, prevents context overflow:

```python
agent = LLMAgent(
    config,
    provider,
    enable_context_management=True,
    max_context_tokens=180000  # Claude's limit
)
```

**What it does:**
1. Counts tokens in conversation
2. When approaching limit, prunes low-importance messages
3. Always keeps: system prompt + recent messages
4. Uses importance scoring

### Importance Scoring

Messages scored by:
- **Recency** (30%): Recent messages score higher
- **Content** (40%): Errors, questions, decisions score higher
- **Interaction** (20%): Messages with replies score higher
- **Role** (10%): User messages score higher

### Manual Control

```python
from agentic_playground.memory.context import ContextManager

cm = ContextManager(
    max_tokens=100000,
    buffer_tokens=10000,
    always_keep_recent=10,
    always_keep_system=True
)

context = cm.prepare_context(messages)
print(f"Total tokens: {context.total_tokens}")
print(f"Pruned: {context.pruned_count} messages")
```

## Memory Retrieval

### Store Memories

```python
from agentic_playground.memory.models import MemoryType

# Store semantic memory
memory_id = await memory_manager.store_memory(
    agent_id="assistant",
    session_id=session_id,
    content="User prefers technical explanations",
    memory_type=MemoryType.SEMANTIC,
    importance_score=0.9
)
```

### Search Memories

```python
# Keyword search
memories = await memory_manager.retrieve_memories(
    agent_id="assistant",
    query="technical preferences",
    limit=5,
    min_importance=0.5
)

for mem in memories:
    print(f"[{mem.importance_score}] {mem.content}")
```

### Automatic Retrieval (LLMAgent)

When enabled, LLMAgent automatically:
1. Extracts keywords from incoming message
2. Searches memory
3. Adds relevant memories to context

```python
agent = LLMAgent(
    config,
    provider,
    enable_memory_retrieval=True  # Default
)
```

## Memory Types

### WORKING
Current conversation context (auto-managed)
```python
MemoryType.WORKING
```

### EPISODIC
Specific past interactions
```python
await memory.store_memory(
    content="User asked about pricing on 2024-01-15",
    memory_type=MemoryType.EPISODIC
)
```

### SEMANTIC
Facts and knowledge
```python
await memory.store_memory(
    content="User company: Acme Corp, Industry: Technology",
    memory_type=MemoryType.SEMANTIC
)
```

## Database Schema

SQLite tables:
- `sessions`: Session metadata
- `messages`: All messages with importance scores
- `agent_states`: Agent internal state
- `conversation_history`: LLM conversation format
- `memories`: Stored memories
- `memories_fts`: Full-text search index

## Web UI Integration

Enable memory in Web UI:
1. Go to "Memory Settings" tab
2. Enable persistent memory
3. Configure storage path
4. Create/load sessions
5. Export/import sessions

## Examples

See detailed examples:
- `examples/memory_demo.py`
- `examples/session_restore_demo.py`
- `examples/memory_search_demo.py`

## Performance

- **Storage**: SQLite ~1000 writes/sec
- **Token Counting**: <1ms
- **Context Prep**: <10ms
- **Memory Search**: <1ms (FTS indexed)
- **Session Restore**: ~100ms

## Best Practices

1. **Session per conversation**: Create new session per user interaction
2. **Regular saves**: Call save_session() periodically
3. **Importance scores**: Set appropriately (0.0-1.0)
4. **Memory pruning**: Clean old memories periodically
5. **Backup**: Copy database file for backups

See [Memory System Documentation](../MEMORY_SYSTEM.md) for complete details.
