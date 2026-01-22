"""
Memory System Demo

Demonstrates basic usage of the memory system with persistent storage,
session management, and conversation history.
"""

import asyncio
from agentic_playground.core import Orchestrator, AgentConfig, LLMAgent, Message, MessageType
from agentic_playground.llm import AnthropicProvider
from agentic_playground.memory import MemoryManager, SQLiteStorage


async def main():
    print("=" * 60)
    print("Memory System Demo")
    print("=" * 60)

    # Step 1: Initialize storage backend
    print("\n1. Initializing SQLite storage...")
    storage = SQLiteStorage("./data/demo_sessions.db")
    await storage.initialize()
    print("✓ Storage initialized")

    # Step 2: Create memory manager
    print("\n2. Creating memory manager...")
    memory_manager = MemoryManager(storage)
    print("✓ Memory manager created")

    # Step 3: Create a new session
    print("\n3. Creating new session...")
    session_id = await memory_manager.create_session(
        metadata={
            "user": "demo_user",
            "purpose": "testing memory system"
        }
    )
    print(f"✓ Created session: {session_id[:12]}...")

    # Step 4: Setup orchestrator with memory
    print("\n4. Setting up orchestrator with memory...")
    orchestrator = Orchestrator()
    orchestrator.attach_memory_manager(memory_manager, session_id)
    print("✓ Orchestrator configured with memory")

    # Step 5: Create and register agents
    print("\n5. Creating agents...")

    # Create LLM agent with memory-aware features
    assistant_config = AgentConfig(
        name="assistant",
        role="Helpful AI assistant",
        system_prompt="You are a helpful assistant. Remember previous conversations."
    )

    assistant = LLMAgent(
        assistant_config,
        AnthropicProvider(model="claude-sonnet-4-20250514"),
        enable_context_management=True,
        enable_memory_retrieval=True
    )

    orchestrator.register_agent(assistant)
    print("✓ Registered assistant agent")

    # Step 6: Start orchestrator
    print("\n6. Starting orchestrator...")
    await orchestrator.start()
    print("✓ Orchestrator started")

    # Step 7: Send some messages
    print("\n7. Sending messages and building conversation history...")

    messages_to_send = [
        "Hello! My name is Alice and I love Python programming.",
        "What's the weather like today?",
        "Can you remind me what my name is?"
    ]

    for msg_content in messages_to_send:
        print(f"\n  User: {msg_content}")

        msg = Message(
            type=MessageType.TASK,
            sender="user",
            recipient="assistant",
            content=msg_content
        )

        await orchestrator.send_message_to_agent("assistant", msg)

        # Wait for response
        await asyncio.sleep(2)

        # Get last response
        recent = orchestrator.get_message_history()[-1]
        if recent.type == MessageType.RESPONSE:
            print(f"  Assistant: {recent.content[:100]}...")

    # Step 8: Save session
    print("\n8. Saving session...")
    await orchestrator.save_session()
    print("✓ Session saved")

    # Step 9: Show session statistics
    print("\n9. Session Statistics:")
    summary = await memory_manager.get_session_summary(session_id)
    print(f"  - Session ID: {summary['session_id'][:12]}...")
    print(f"  - Created: {summary['created_at']}")
    print(f"  - Messages: {summary['message_count']}")
    print(f"  - Metadata: {summary['metadata']}")

    # Step 10: List all sessions
    print("\n10. Available Sessions:")
    sessions = await memory_manager.list_sessions(limit=5)
    for sess in sessions:
        msg_count = await memory_manager.get_message_count(sess.session_id)
        print(f"  - {sess.session_id[:12]}... ({msg_count} messages, "
              f"created {sess.created_at.strftime('%Y-%m-%d %H:%M')})")

    # Clean up
    print("\n11. Cleaning up...")
    await orchestrator.stop()
    await storage.close()
    print("✓ Demo complete!")

    print("\n" + "=" * 60)
    print(f"Session saved at: ./data/demo_sessions.db")
    print(f"Session ID: {session_id}")
    print("Run session_restore_demo.py to restore this session")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
