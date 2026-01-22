#!/usr/bin/env python3
"""
Verify that the agentic playground is set up correctly.

This script checks:
1. Python version
2. Dependencies are installed
3. API keys are configured
4. Basic functionality works
"""

import sys
import os


def check_python_version():
    """Check Python version."""
    print("Checking Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro}")
        print("  Error: Python 3.10 or higher required")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\nChecking dependencies...")
    required = {
        "anthropic": "Anthropic SDK",
        "openai": "OpenAI SDK",
        "pydantic": "Pydantic",
        "dotenv": "python-dotenv",
    }

    all_ok = True
    for module, name in required.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} not found")
            all_ok = False

    return all_ok


def check_environment():
    """Check environment variables."""
    print("\nChecking API keys...")

    from dotenv import load_dotenv
    load_dotenv()

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    has_key = False

    if anthropic_key:
        print(f"  ✓ ANTHROPIC_API_KEY found")
        has_key = True
    else:
        print(f"  ✗ ANTHROPIC_API_KEY not found")

    if openai_key:
        print(f"  ✓ OPENAI_API_KEY found")
        has_key = True
    else:
        print(f"  ✗ OPENAI_API_KEY not found")

    if not has_key:
        print("\n  Warning: No API keys found. You need at least one.")
        print("  Copy .env.example to .env and add your API keys.")
        return False

    return True


def check_basic_functionality():
    """Test basic functionality."""
    print("\nTesting basic functionality...")

    try:
        from agentic_playground import AgentConfig, Message, MessageType, Orchestrator
        from agentic_playground.agents import EchoAgent

        print("  ✓ Imports work")

        # Create basic components
        config = AgentConfig(name="test", role="Test")
        print("  ✓ AgentConfig creation")

        message = Message(
            type=MessageType.QUERY,
            sender="test",
            content="test"
        )
        print("  ✓ Message creation")

        agent = EchoAgent()
        print("  ✓ Agent creation")

        orchestrator = Orchestrator()
        print("  ✓ Orchestrator creation")

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("Agentic Playground Setup Verification")
    print("=" * 60)

    checks = [
        check_python_version(),
        check_dependencies(),
        check_environment(),
        check_basic_functionality(),
    ]

    print("\n" + "=" * 60)

    if all(checks):
        print("✓ All checks passed! Your setup is ready.")
        print("\nNext steps:")
        print("  1. Check out GETTING_STARTED.md")
        print("  2. Run an example: python -m agentic_playground.examples.simple_conversation")
        print("  3. Build your own agents!")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nTroubleshooting:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Set up API keys: cp .env.example .env (then edit .env)")
        print("  - Check Python version: python --version")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()
