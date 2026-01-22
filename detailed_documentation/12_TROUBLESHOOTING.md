# Troubleshooting Guide

Common issues and solutions.

## Installation Issues

### Module Not Found
```
Error: ModuleNotFoundError: No module named 'agentic_playground'
```
**Solution:**
```bash
pip install -e .
```

### Import Errors
```
Error: cannot import name 'Agent'
```
**Solution:**
```bash
# Reinstall
pip uninstall agentic-playground
pip install -e .
```

## API Key Issues

### Anthropic API Key Error
```
Error: anthropic.APIKeyError: Missing API key
```
**Solution:**
```bash
# Check .env file
cat .env | grep ANTHROPIC_API_KEY

# Or set directly
export ANTHROPIC_API_KEY="your-key-here"
```

### OpenAI API Key Error
```
Error: openai.error.AuthenticationError
```
**Solution:**
```bash
export OPENAI_API_KEY="your-key-here"
```

## Async/Await Issues

### Coroutine Never Awaited
```
RuntimeWarning: coroutine 'my_function' was never awaited
```
**Solution:**
```python
# Wrong:
result = my_async_function()

# Right:
result = await my_async_function()
```

### Event Loop Issues
```
Error: RuntimeError: This event loop is already running
```
**Solution:**
```python
# Don't nest asyncio.run()
# Wrong:
async def main():
    asyncio.run(other_function())  # ❌

# Right:
async def main():
    await other_function()  # ✓
```

## Agent Issues

### Agent Not Responding
**Symptoms:** Agent receives messages but doesn't respond

**Check:**
1. Agent is registered: `agent_id in orchestrator.agents`
2. Orchestrator is started: `await orchestrator.start()`
3. Agent's process_message() is implemented
4. No exceptions in processing

**Debug:**
```python
# Add logging
async def process_message(self, message):
    print(f"Processing: {message}")
    # ... your code
```

### Messages Not Routed
**Symptoms:** Messages sent but never received

**Check:**
1. Recipient ID is correct
2. Recipient is registered
3. Message callback is set (automatically by orchestrator)

**Debug:**
```python
print(f"Registered agents: {list(orchestrator.agents.keys())}")
print(f"Sending to: {message.recipient}")
```

## Memory Issues

### Database Locked
```
Error: sqlite3.OperationalError: database is locked
```
**Solution:**
```python
# Close existing connections
await storage.close()

# Or use different database file
storage = SQLiteStorage("./data/sessions_v2.db")
```

### Session Not Found
```
Error: Session xyz not found
```
**Solution:**
```python
# List available sessions
sessions = await memory_manager.list_sessions()
for s in sessions:
    print(s.session_id)
```

### Memory Not Persisting
**Check:**
1. Memory manager is attached: `orchestrator.attach_memory_manager()`
2. Session ID is set
3. Storage is initialized: `await storage.initialize()`

## LLM Issues

### Rate Limiting
```
Error: RateLimitError: Rate limit exceeded
```
**Solution:**
```python
import asyncio

async def with_retry(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await func()
        except RateLimitError:
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise
```

### Context Too Long
```
Error: Context length exceeded
```
**Solution:**
```python
# Enable context management
agent = LLMAgent(
    config,
    provider,
    enable_context_management=True,
    max_context_tokens=180000
)

# Or clear history
agent.clear_history(keep_system_prompt=True)
```

### Timeout Errors
```
Error: asyncio.TimeoutError
```
**Solution:**
```python
provider = AnthropicProvider(timeout=60.0)  # Increase timeout
```

## Web UI Issues

### Port Already in Use
```
Error: OSError: Address already in use
```
**Solution:**
```python
# Use different port
interface.launch(server_port=7861)
```

### Gradio Import Error
```
Error: ModuleNotFoundError: No module named 'gradio'
```
**Solution:**
```bash
pip install -e ".[webui]"
```

## Performance Issues

### Slow Message Processing
**Solutions:**
1. Run agents concurrently (they do by default)
2. Use faster LLM models
3. Reduce max_tokens
4. Enable context management

### High Memory Usage
**Solutions:**
1. Clear conversation history periodically
2. Enable context pruning
3. Limit message history size
4. Use memory system with pruning

### Too Many Tokens
**Solutions:**
1. Enable context management
2. Reduce max_context_tokens
3. Increase always_keep_recent limit
4. Clear old sessions

## Debugging Tips

### Enable Detailed Logging
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("agentic_playground")
logger.setLevel(logging.DEBUG)
```

### Print Message History
```python
for msg in orchestrator.message_history:
    print(f"[{msg.timestamp}] {msg.sender} → {msg.recipient}: {msg.content[:50]}")
```

### Check Agent State
```python
for agent_id, agent in orchestrator.agents.items():
    print(f"{agent_id}: {agent._state}")
```

### Monitor Token Usage
```python
if agent.context_manager:
    usage = agent.context_manager.get_token_usage(messages)
    print(f"Tokens: {usage['total_tokens']}/{usage['max_tokens']}")
```

## Getting Help

1. **Check Examples**: See `examples/` folder
2. **Read Docs**: Review relevant documentation
3. **GitHub Issues**: Search existing issues
4. **Create Issue**: Provide:
   - Python version
   - Framework version
   - Full error traceback
   - Minimal reproduction code

## Common Error Messages

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| Agent not registered | Agent not added to orchestrator | `orchestrator.register_agent(agent)` |
| Callback not set | Agent created but not registered | Register with orchestrator |
| Session not found | Invalid session ID | Check `list_sessions()` |
| API key missing | .env not loaded | Check environment variables |
| Context too long | Too many messages | Enable context management |
| Database locked | Multiple connections | Close connections, use one instance |

For more help, see other documentation guides.
