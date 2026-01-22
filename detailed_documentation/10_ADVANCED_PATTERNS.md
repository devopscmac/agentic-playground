# Advanced Patterns

Advanced techniques for building sophisticated multi-agent systems.

## Agent Hierarchies

### Manager-Worker Pattern
```python
class ManagerAgent(LLMAgent):
    def __init__(self, worker_ids):
        super().__init__(config, provider)
        self.workers = worker_ids
        self.pending_tasks = {}
    
    async def process_message(self, message):
        if message.type == MessageType.TASK:
            # Delegate to workers
            task_id = self.create_task_id()
            worker = self.select_worker()
            
            self.pending_tasks[task_id] = message.sender
            
            await self.send_message(Message(
                type=MessageType.TASK,
                sender=self.id,
                recipient=worker,
                content=message.content,
                metadata={"task_id": task_id}
            ))
        elif message.type == MessageType.RESPONSE:
            # Aggregate worker responses
            task_id = message.metadata.get("task_id")
            original_sender = self.pending_tasks.pop(task_id)
            
            await self.send_message(Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=original_sender,
                content=message.content
            ))
```

## Consensus Mechanisms

### Voting System
```python
class VotingOrchestrator(Agent):
    async def get_consensus(self, question, voters):
        votes = {}
        
        # Collect votes
        for voter_id in voters:
            vote_msg = Message(
                type=MessageType.QUERY,
                sender=self.id,
                recipient=voter_id,
                content=question
            )
            await self.send_message(vote_msg)
            
            # Wait for response
            response = await self.wait_for_response(voter_id)
            votes[voter_id] = response.content
        
        # Determine consensus
        return self.calculate_consensus(votes)
    
    def calculate_consensus(self, votes):
        # Majority voting
        from collections import Counter
        vote_counts = Counter(votes.values())
        return vote_counts.most_common(1)[0][0]
```

## Specialized Agent Types

### Caching Agent
```python
class CachingAgent(LLMAgent):
    def __init__(self, config, provider):
        super().__init__(config, provider)
        self._cache = {}
    
    async def process_message(self, message):
        # Check cache
        cache_key = self.get_cache_key(message)
        if cache_key in self._cache:
            cached_response = self._cache[cache_key]
            await self.send_cached_response(message.sender, cached_response)
            return
        
        # Process normally
        await super().process_message(message)
        
        # Cache response
        response = self.conversation_history[-1].content
        self._cache[cache_key] = response
```

### Rate-Limited Agent
```python
from asyncio import Semaphore

class RateLimitedAgent(LLMAgent):
    def __init__(self, config, provider, max_concurrent=3):
        super().__init__(config, provider)
        self.semaphore = Semaphore(max_concurrent)
    
    async def process_message(self, message):
        async with self.semaphore:
            await super().process_message(message)
            await asyncio.sleep(0.5)  # Rate limit
```

## Agent Collaboration Patterns

### Peer Review
```python
class ReviewerAgent(LLMAgent):
    async def review_work(self, work, reviewer_id):
        review_request = Message(
            type=MessageType.QUERY,
            sender=self.id,
            recipient=reviewer_id,
            content=f"Please review: {work}"
        )
        await self.send_message(review_request)
        
        # Wait for feedback
        feedback = await self.wait_for_response(reviewer_id)
        
        if self.is_approved(feedback):
            return work
        else:
            return await self.revise(work, feedback)
```

### Debate System
```python
class DebateAgent(LLMAgent):
    async def participate_in_debate(self, topic, other_debaters):
        # Initial position
        position = await self.form_position(topic)
        await self.broadcast_position(position)
        
        # Listen to counter-arguments
        for debater in other_debaters:
            counter = await self.wait_for_position(debater)
            
            # Refine position
            position = await self.refine_position(position, counter)
            await self.broadcast_position(position)
        
        # Final argument
        return await self.make_final_argument(position)
```

## Performance Optimization

### Batch Processing
```python
class BatchProcessor(Agent):
    def __init__(self, batch_size=10, timeout=1.0):
        super().__init__(config)
        self.batch = []
        self.batch_size = batch_size
        self.timeout = timeout
    
    async def process_message(self, message):
        self.batch.append(message)
        
        if len(self.batch) >= self.batch_size:
            await self.process_batch()
    
    async def process_batch(self):
        # Process all messages at once
        results = await self.batch_process(self.batch)
        
        # Send responses
        for msg, result in zip(self.batch, results):
            await self.send_response(msg.sender, result)
        
        self.batch.clear()
```

### Parallel Execution
```python
async def parallel_agent_execution(agents, message):
    # Execute all agents concurrently
    tasks = [agent.process_message(message) for agent in agents]
    results = await asyncio.gather(*tasks)
    return results
```

## State Machines

### Stateful Conversation Agent
```python
from enum import Enum

class ConversationState(Enum):
    GREETING = "greeting"
    COLLECTING_INFO = "collecting"
    PROCESSING = "processing"
    DONE = "done"

class StatefulAgent(LLMAgent):
    async def process_message(self, message):
        state = self._state.get("conversation_state", ConversationState.GREETING)
        
        if state == ConversationState.GREETING:
            await self.handle_greeting(message)
            self._state["conversation_state"] = ConversationState.COLLECTING_INFO
        
        elif state == ConversationState.COLLECTING_INFO:
            if self.has_all_info():
                self._state["conversation_state"] = ConversationState.PROCESSING
                await self.process_request(message)
            else:
                await self.request_more_info(message)
        
        elif state == ConversationState.PROCESSING:
            await self.send_result(message)
            self._state["conversation_state"] = ConversationState.DONE
```

## Error Recovery

### Circuit Breaker
```python
class CircuitBreaker:
    def __init__(self, threshold=5, timeout=60):
        self.failure_count = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func):
        if self.state == "open":
            if (datetime.now() - self.last_failure).seconds > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure = datetime.now()
        if self.failure_count >= self.threshold:
            self.state = "open"

class ResilientAgent(LLMAgent):
    def __init__(self, config, provider):
        super().__init__(config, provider)
        self.circuit_breaker = CircuitBreaker()
    
    async def process_message(self, message):
        try:
            await self.circuit_breaker.call(
                lambda: super().process_message(message)
            )
        except Exception as e:
            await self.send_error(message.sender, str(e))
```

## Monitoring and Observability

### Instrumented Agent
```python
class InstrumentedAgent(LLMAgent):
    def __init__(self, config, provider):
        super().__init__(config, provider)
        self.metrics = {
            "messages_processed": 0,
            "errors": 0,
            "avg_response_time": 0
        }
    
    async def process_message(self, message):
        start_time = time.time()
        
        try:
            await super().process_message(message)
            self.metrics["messages_processed"] += 1
        except Exception as e:
            self.metrics["errors"] += 1
            raise
        finally:
            elapsed = time.time() - start_time
            self.update_avg_response_time(elapsed)
    
    def update_avg_response_time(self, elapsed):
        count = self.metrics["messages_processed"]
        current_avg = self.metrics["avg_response_time"]
        self.metrics["avg_response_time"] = (
            (current_avg * (count - 1) + elapsed) / count
        )
```

## Best Practices

1. **Keep agents focused**: One responsibility per agent
2. **Use appropriate patterns**: Match pattern to problem
3. **Handle failures gracefully**: Implement retry and fallback
4. **Monitor performance**: Track metrics and errors
5. **Test thoroughly**: Unit and integration tests
6. **Document behavior**: Clear role and responsibilities
7. **Version agents**: Track changes to agent logic

See [Building Applications](09_BUILDING_APPLICATIONS.md) for practical examples.
