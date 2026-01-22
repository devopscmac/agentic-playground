"""
Session Restore Demo

Demonstrates how to restore a previous session from persistent storage
and continue a conversation where it left off.
"""

import asyncio
from agentic_playground.core import Orchestrator, AgentConfig, LLMAgent, Message, MessageType
from agentic_playground.llm import AnthropicProvider
from agentic_playground.memory import MemoryManager, SQLiteStorage


async def main():
    print("=" * 60)
    print("Session Restore Demo")
    print("=" * 60)

    # Step 1: Initialize storage
    print("\n1. Initializing storage...")
    storage = SQLiteStorage("./data/demo_sessions.db")
    await storage.initialize()
    print("✓ Storage initialized")

    # Step 2: Create memory manager
    print("\n2. Creating memory manager...")
    memory_manager = MemoryManager(storage)
    print("✓ Memory manager created")

    # Step 3: List available sessions
    print("\n3. Available sessions:")
    sessions = await memory_manager.list_sessions(limit=10)

    if not sessions:
        print("  No sessions found. Run memory_demo.py first to create a session.")
        await storage.close()
        return

    for i, sess in enumerate(sessions, 1):
        msg_count = await memory_manager.get_message_count(sess.session_id)
        print(f"  {i}. {sess.session_id[:16]}... "
              f"({msg_count} messages, {sess.created_at.strftime('%Y-%m-%d %H:%M')})")

    # Use the most recent session
    session_to_restore = sessions[0]
    session_id = session_to_restore.session_id

    print(f"\n4. Restoring session: {session_id[:16]}...")

    # Step 4: Setup orchestrator
    orchestrator = Orchestrator()
    orchestrator.attach_memory_manager(memory_manager, session_id)

    # Step 5: Recreate agents (they will restore their state)
    print("\n5. Recreating agents...")

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
    print("✓ Agent registered")

    # Step 6: Restore session
    print("\n6. Restoring session from storage...")
    await orchestrator.restore_session(session_id)
    print("✓ Session restored!")

    # Step 7: Show restored message history
    print("\n7. Restored Message History:")
    for i, msg in enumerate(orchestrator.message_history[-5:], 1):
        print(f"  {i}. [{msg.type.value}] {msg.sender} → {msg.recipient or 'all'}")
        print(f"     {msg.content[:80]}...")

    # Step 8: Continue the conversation
    print("\n8. Continuing conversation...")
    await orchestrator.start()

    # Send a follow-up message
    followup = Message(
        type=MessageType.TASK,
        sender="user",
        recipient="assistant",
        content="Do you remember what we talked about before?"
    )

    print(f"\n  User: {followup.content}")
    await orchestrator.send_message_to_agent("assistant", followup)

    # Wait for response
    await asyncio.sleep(3)

    # Get response
    recent = orchestrator.get_message_history()[-1]
    if recent.type == MessageType.RESPONSE:
        print(f"  Assistant: {recent.content[:150]}...")

    # Step 9: Save updated session
    print("\n9. Saving updated session...")
    await orchestrator.save_session()
    print("✓ Session saved")

    # Clean up
    print("\n10. Cleaning up...")
    await orchestrator.stop()
    await storage.close()
    print("✓ Demo complete!")

    print("\n" + "=" * 60)
    print("Session successfully restored and updated!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
