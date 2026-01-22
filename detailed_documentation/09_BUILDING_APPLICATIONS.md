# Building Agent Applications

Practical guide to building real applications.

## Design Process

### 1. Define Requirements
- What problem are we solving?
- What inputs/outputs?
- What agents do we need?

### 2. Design Agent Roles
- What is each agent responsible for?
- How do they communicate?
- What state do they maintain?

### 3. Implement Agents
- Create agent classes
- Implement process_message()
- Add error handling

### 4. Wire Together
- Create orchestrator
- Register agents
- Set up routing

### 5. Test & Iterate
- Test with examples
- Handle edge cases
- Optimize performance

## Example: Customer Service System

### Requirements
- Answer FAQs
- Check order status
- Escalate complex issues
- Track conversation history

### Agent Design

```python
# 1. Triage Agent
class TriageAgent(LLMAgent):
    """Routes customer queries to appropriate handlers."""
    async def process_message(self, message):
        # Analyze query
        category = await self.classify(message.content)
        
        # Route to specialist
        if category == "faq":
            await self.forward_to("faq_agent", message)
        elif category == "order":
            await self.forward_to("order_agent", message)
        else:
            await self.forward_to("escalation_agent", message)

# 2. FAQ Agent
class FAQAgent(LLMAgent):
    """Answers frequently asked questions."""
    async def process_message(self, message):
        # Search FAQ database
        answer = await self.search_faqs(message.content)
        
        if answer:
            await self.send_response(message.sender, answer)
        else:
            await self.escalate(message)

# 3. Order Agent
class OrderAgent(Agent):
    """Checks order status."""
    async def process_message(self, message):
        # Extract order number
        order_id = self.extract_order_id(message.content)
        
        # Query database
        status = await self.get_order_status(order_id)
        
        await self.send_response(message.sender, status)

# 4. Escalation Agent
class EscalationAgent(Agent):
    """Escalates to human support."""
    async def process_message(self, message):
        # Notify human support
        await self.notify_support(message)
        
        # Inform customer
        response = "Escalated to human support. ETA: 5 minutes"
        await self.send_response(message.sender, response)
```

### Wiring

```python
async def main():
    orch = Orchestrator()
    
    # Create agents
    triage = TriageAgent(config1, provider)
    faq = FAQAgent(config2, provider)
    order = OrderAgent(config3)
    escalation = EscalationAgent(config4)
    
    # Register
    for agent in [triage, faq, order, escalation]:
        orch.register_agent(agent)
    
    # Start
    await orch.start()
    
    # Handle customer queries
    customer_query = Message(
        type=MessageType.QUERY,
        sender="customer",
        recipient="triage",
        content="Where is my order #12345?"
    )
    await orch.send_message_to_agent("triage", customer_query)
```

## Common Patterns

### Coordinator Pattern
One agent delegates to workers:
```python
class Coordinator(Agent):
    async def process_message(self, message):
        subtasks = self.break_down(message.content)
        for task, worker in subtasks:
            await self.delegate(worker, task)
```

### Pipeline Pattern
Sequential processing:
```python
# Step 1 → Step 2 → Step 3
agent1 → agent2 → agent3
```

### Voting Pattern
Multiple agents decide together:
```python
class VotingCoordinator(Agent):
    async def process_message(self, message):
        # Ask all voters
        votes = await self.collect_votes(message)
        # Decide based on majority
        result = self.decide(votes)
        await self.send_response(message.sender, result)
```

## Error Handling

### Retry Logic
```python
async def process_with_retry(self, message, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await self.process(message)
        except TemporaryError:
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise
```

### Fallback
```python
async def process_message(self, message):
    try:
        result = await self.primary_method(message)
    except Exception:
        result = await self.fallback_method(message)
    await self.send_response(message.sender, result)
```

## Testing

### Unit Testing Agents
```python
import pytest

@pytest.mark.asyncio
async def test_agent():
    agent = MyAgent(config)
    message = Message(type=MessageType.QUERY, sender="test", content="Hello")
    
    # Mock callback
    responses = []
    agent.set_message_callback(lambda msg: responses.append(msg))
    
    await agent.process_message(message)
    
    assert len(responses) == 1
    assert responses[0].type == MessageType.RESPONSE
```

### Integration Testing
```python
@pytest.mark.asyncio
async def test_multi_agent_system():
    orch = Orchestrator()
    orch.register_agent(agent1)
    orch.register_agent(agent2)
    
    await orch.start()
    await orch.send_message_to_agent("agent1", test_message)
    await asyncio.sleep(1)
    await orch.stop()
    
    assert len(orch.message_history) > 0
```

## Deployment

### Production Checklist
- [ ] Error handling in all agents
- [ ] Logging configured
- [ ] Memory/storage set up
- [ ] API keys secured
- [ ] Rate limiting handled
- [ ] Monitoring in place
- [ ] Tests passing

### Performance Tips
1. Use appropriate LLM models
2. Enable context management
3. Cache common responses
4. Monitor token usage
5. Use async throughout
6. Limit conversation history

See [Advanced Patterns](10_ADVANCED_PATTERNS.md) for more techniques.
