"""
Memory Search Demo

Demonstrates semantic memory storage and retrieval using the query engine.
Shows how to store facts and retrieve them later based on context.
"""

import asyncio
from agentic_playground.memory import MemoryManager, SQLiteStorage, MemoryType
from agentic_playground.memory.query import QueryEngine, MemoryRetriever


async def main():
    print("=" * 60)
    print("Memory Search Demo")
    print("=" * 60)

    # Step 1: Setup
    print("\n1. Initializing storage and memory manager...")
    storage = SQLiteStorage("./data/memory_search_demo.db")
    await storage.initialize()
    memory_manager = MemoryManager(storage)
    print("✓ Setup complete")

    # Step 2: Create session
    print("\n2. Creating session...")
    session_id = await memory_manager.create_session(
        metadata={"demo": "memory_search"}
    )
    print(f"✓ Session: {session_id[:12]}...")

    # Step 3: Store some semantic memories
    print("\n3. Storing semantic memories...")

    facts = [
        ("Python is a high-level programming language known for its simplicity", 0.9),
        ("Machine learning involves training models on data to make predictions", 0.9),
        ("SQLite is a lightweight embedded database that stores data in files", 0.8),
        ("REST APIs use HTTP methods like GET, POST, PUT, DELETE", 0.7),
        ("Neural networks are inspired by biological neurons in the brain", 0.9),
        ("Docker containers provide isolated environments for applications", 0.7),
        ("Git is a distributed version control system for tracking changes", 0.8),
        ("The user prefers Python over JavaScript for backend development", 0.6),
    ]

    agent_id = "knowledge_agent"

    for content, importance in facts:
        await memory_manager.store_memory(
            agent_id=agent_id,
            session_id=session_id,
            content=content,
            memory_type=MemoryType.SEMANTIC,
            importance_score=importance
        )
        print(f"  ✓ Stored: {content[:50]}...")

    print(f"\n✓ Stored {len(facts)} semantic memories")

    # Step 4: Create query engine
    print("\n4. Creating query engine...")
    query_engine = QueryEngine(memory_manager)
    memory_retriever = MemoryRetriever(query_engine)
    print("✓ Query engine ready")

    # Step 5: Perform searches
    print("\n5. Performing searches...")

    queries = [
        "Tell me about Python programming",
        "What is machine learning?",
        "How do databases work?",
        "Explain REST APIs",
        "What does the user prefer for backend?",
    ]

    for query in queries:
        print(f"\n  Query: '{query}'")

        # Search for relevant memories
        results = await query_engine.search(
            agent_id=agent_id,
            query=query,
            memory_type=MemoryType.SEMANTIC,
            limit=2,
            min_importance=0.5
        )

        if results:
            print(f"  Found {len(results)} relevant memories:")
            for i, memory in enumerate(results, 1):
                print(f"    {i}. [Score: {memory.importance_score:.2f}] {memory.content[:60]}...")
                print(f"       (Accessed {memory.access_count} times)")
        else:
            print("  No relevant memories found")

    # Step 6: Keyword extraction
    print("\n6. Testing keyword extraction...")

    test_text = "I'm working on a Python project that uses SQLite database and needs REST API endpoints"
    keywords = await query_engine.extract_keywords(test_text, top_k=5)
    print(f"  Text: '{test_text}'")
    print(f"  Keywords: {', '.join(keywords)}")

    # Search using extracted keywords
    print("\n  Searching using extracted keywords...")
    results = await query_engine.search_by_keywords(
        agent_id=agent_id,
        keywords=keywords,
        limit=3
    )

    print(f"  Found {len(results)} relevant memories:")
    for i, memory in enumerate(results, 1):
        print(f"    {i}. {memory.content[:60]}...")

    # Step 7: Retrieve for message context
    print("\n7. Testing message-based retrieval...")

    message = "Can you help me set up a Python REST API with a database?"
    print(f"  Message: '{message}'")

    memories = await memory_retriever.retrieve_for_message(
        agent_id=agent_id,
        message_content=message,
        session_id=session_id,
        limit=3
    )

    print(f"  Retrieved {len(memories)} contextually relevant memories:")
    for i, memory in enumerate(memories, 1):
        print(f"    {i}. {memory.content[:60]}...")

    # Step 8: Show memory access statistics
    print("\n8. Memory Access Statistics:")
    all_memories = await query_engine.search(
        agent_id=agent_id,
        query="*",  # Match all
        limit=100
    )

    if all_memories:
        total_accesses = sum(m.access_count for m in all_memories)
        avg_importance = sum(m.importance_score for m in all_memories) / len(all_memories)
        print(f"  - Total memories: {len(all_memories)}")
        print(f"  - Total accesses: {total_accesses}")
        print(f"  - Average importance: {avg_importance:.2f}")

        # Most accessed
        most_accessed = max(all_memories, key=lambda m: m.access_count)
        print(f"  - Most accessed: {most_accessed.content[:50]}... ({most_accessed.access_count} times)")

    # Clean up
    print("\n9. Cleaning up...")
    await storage.close()
    print("✓ Demo complete!")

    print("\n" + "=" * 60)
    print("Memory search demo completed successfully!")
    print(f"Database saved at: ./data/memory_search_demo.db")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
