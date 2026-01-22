"""
LLM-powered agent implementation.
"""

from typing import Optional
from .agent import Agent, AgentConfig
from .message import Message, MessageType
from ..llm import LLMProvider, LLMMessage


class LLMAgent(Agent):
    """
    An agent that uses an LLM for reasoning and generating responses.
    """

    def __init__(
        self,
        config: AgentConfig,
        llm_provider: LLMProvider,
        enable_context_management: bool = True,
        max_context_tokens: int = 180000,
        enable_memory_retrieval: bool = True,
    ):
        super().__init__(config)
        self.llm_provider = llm_provider
        self.conversation_history: list[LLMMessage] = []
        self.enable_context_management = enable_context_management
        self.enable_memory_retrieval = enable_memory_retrieval
        self.context_manager = None
        self.query_engine = None
        self.memory_retriever = None

        # Initialize context manager if enabled
        if enable_context_management:
            from agentic_playground.memory.context import ContextManager
            self.context_manager = ContextManager(max_tokens=max_context_tokens)

        # Initialize with system prompt if provided
        if config.system_prompt:
            self.conversation_history.append(
                LLMMessage(role="system", content=config.system_prompt)
            )

    async def process_message(self, message: Message) -> None:
        """
        Process an incoming message using the LLM.

        The agent will:
        1. Add the message to its conversation history
        2. Generate a response using the LLM
        3. Send the response back to the sender or as specified
        4. Persist conversation to memory if enabled
        """

        # Format the incoming message for the LLM
        user_message = self._format_message_for_llm(message)
        self.conversation_history.append(user_message)

        # Persist user message to memory if enabled
        if self.memory_manager and self.session_id:
            await self.memory_manager.store_conversation_entry(
                agent_id=self.id,
                session_id=self.session_id,
                role="user",
                content=user_message.content,
                importance_score=0.5,
            )

        try:
            # Retrieve relevant memories if enabled
            retrieved_memories = []
            if (self.memory_retriever and self.enable_memory_retrieval and
                self.memory_manager and self.session_id):
                try:
                    retrieved_memories = await self.memory_retriever.retrieve_for_message(
                        agent_id=self.id,
                        message_content=message.content,
                        session_id=self.session_id,
                        limit=3,
                    )
                    if retrieved_memories:
                        print(f"[{self.id}] Retrieved {len(retrieved_memories)} relevant memories")
                except Exception as e:
                    print(f"[{self.id}] Warning: Memory retrieval failed: {e}")

            # Prepare context with pruning if needed
            messages_to_send = self.conversation_history

            if self.context_manager and self.enable_context_management:
                # Convert to dict format for context manager
                messages_dict = [
                    {"role": msg.role, "content": msg.content}
                    for msg in self.conversation_history
                ]

                # Convert memories to dict format
                memories_dict = None
                if retrieved_memories:
                    memories_dict = [
                        {
                            "role": "system",
                            "content": f"[Memory] {mem.content}"
                        }
                        for mem in retrieved_memories
                    ]

                # Check if pruning is needed
                if self.context_manager.should_prune(messages_dict):
                    context_window = self.context_manager.prepare_context(
                        messages_dict,
                        memories=memories_dict
                    )

                    # Convert back to LLMMessage format
                    messages_to_send = [
                        LLMMessage(role=msg["role"], content=msg["content"])
                        for msg in context_window.messages
                    ]

                    if context_window.pruned_count > 0:
                        print(f"[{self.id}] Pruned {context_window.pruned_count} messages "
                              f"to fit context window ({context_window.total_tokens} tokens)")
                elif memories_dict:
                    # Add memories without pruning
                    # Insert memories after system messages
                    system_count = sum(1 for msg in messages_to_send if msg.role == "system")
                    memory_messages = [
                        LLMMessage(role=mem["role"], content=mem["content"])
                        for mem in memories_dict
                    ]
                    messages_to_send = (
                        messages_to_send[:system_count] +
                        memory_messages +
                        messages_to_send[system_count:]
                    )

            # Generate response using LLM
            response = await self.llm_provider.generate(
                messages=messages_to_send,
                temperature=0.7,
                max_tokens=1024
            )

            # Add assistant response to history
            assistant_message = LLMMessage(role="assistant", content=response.content)
            self.conversation_history.append(assistant_message)

            # Persist assistant response to memory if enabled
            if self.memory_manager and self.session_id:
                await self.memory_manager.store_conversation_entry(
                    agent_id=self.id,
                    session_id=self.session_id,
                    role="assistant",
                    content=response.content,
                    importance_score=0.5,
                )

            # Send response back
            response_message = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                content=response.content,
                metadata={
                    "model": response.model,
                    "usage": response.usage,
                    "in_reply_to": message.id
                }
            )

            await self.send_message(response_message)

        except Exception as e:
            error_message = Message(
                type=MessageType.ERROR,
                sender=self.id,
                recipient=message.sender,
                content=f"Error generating response: {str(e)}",
                metadata={"error": str(e)}
            )
            await self.send_message(error_message)

    def _format_message_for_llm(self, message: Message) -> LLMMessage:
        """
        Format an incoming message for the LLM.

        Converts the agent message into a format the LLM understands.
        """
        content = f"Message from {message.sender} ({message.type.value}): {message.content}"

        if message.metadata:
            content += f"\nMetadata: {message.metadata}"

        return LLMMessage(role="user", content=content)

    def clear_history(self, keep_system_prompt: bool = True) -> None:
        """
        Clear the conversation history.

        Args:
            keep_system_prompt: If True, keep the system prompt in history
        """
        if keep_system_prompt and self.conversation_history:
            system_messages = [
                msg for msg in self.conversation_history
                if msg.role == "system"
            ]
            self.conversation_history = system_messages
        else:
            self.conversation_history = []
