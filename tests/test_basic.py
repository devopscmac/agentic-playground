"""
Basic tests for the agentic playground framework.
"""

import pytest
from agentic_playground import AgentConfig, Message, MessageType, Orchestrator
from agentic_playground.agents import EchoAgent


class TestMessage:
    """Test the Message class."""

    def test_message_creation(self):
        """Test creating a basic message."""
        msg = Message(
            type=MessageType.QUERY,
            sender="alice",
            recipient="bob",
            content="Hello"
        )

        assert msg.sender == "alice"
        assert msg.recipient == "bob"
        assert msg.content == "Hello"
        assert msg.type == MessageType.QUERY

    def test_message_string_representation(self):
        """Test message string representation."""
        msg = Message(
            type=MessageType.TASK,
            sender="alice",
            recipient="bob",
            content="Do something"
        )

        str_repr = str(msg)
        assert "alice" in str_repr
        assert "bob" in str_repr
        assert "task" in str_repr


class TestAgentConfig:
    """Test the AgentConfig class."""

    def test_agent_config_creation(self):
        """Test creating an agent configuration."""
        config = AgentConfig(
            name="test_agent",
            role="Test Role",
            capabilities=["test"]
        )

        assert config.name == "test_agent"
        assert config.role == "Test Role"
        assert "test" in config.capabilities


class TestOrchestrator:
    """Test the Orchestrator class."""

    def test_orchestrator_creation(self):
        """Test creating an orchestrator."""
        orch = Orchestrator()
        assert len(orch.agents) == 0
        assert len(orch.message_history) == 0

    def test_register_agent(self):
        """Test registering an agent."""
        orch = Orchestrator()
        agent = EchoAgent(name="echo1")

        orch.register_agent(agent)
        assert "echo1" in orch.agents
        assert orch.agents["echo1"] == agent

    def test_duplicate_agent_registration(self):
        """Test that duplicate agent registration raises an error."""
        orch = Orchestrator()
        agent1 = EchoAgent(name="echo1")
        agent2 = EchoAgent(name="echo1")

        orch.register_agent(agent1)

        with pytest.raises(ValueError):
            orch.register_agent(agent2)


class TestEchoAgent:
    """Test the EchoAgent."""

    @pytest.mark.asyncio
    async def test_echo_agent_creation(self):
        """Test creating an echo agent."""
        agent = EchoAgent(name="echo_test")

        assert agent.id == "echo_test"
        assert agent.config.role == "Echo messages back to sender"

    @pytest.mark.asyncio
    async def test_echo_agent_message_handling(self):
        """Test that echo agent responds to messages."""
        orch = Orchestrator()
        agent = EchoAgent(name="echo1")

        orch.register_agent(agent)
        await orch.start()

        # Send a query
        msg = Message(
            type=MessageType.QUERY,
            sender="test",
            recipient="echo1",
            content="Test message"
        )

        await orch.send_message_to_agent("echo1", msg)

        # Give it a moment to process
        import asyncio
        await asyncio.sleep(0.1)

        await orch.stop()

        # Check that a response was generated
        assert len(orch.message_history) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
