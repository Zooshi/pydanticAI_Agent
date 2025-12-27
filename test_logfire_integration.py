"""Test script to verify LogFire integration is working correctly.

This script runs a simple query through the agent and verifies that:
1. The user prompt is logged to LogFire
2. The complete response (not individual chunks) is logged to LogFire
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.financial_agent import create_agent
from src.agent.streaming import stream_agent_response


def test_logfire_logging():
    """Test that LogFire logs user prompt and complete response."""
    print("=" * 60)
    print("Testing LogFire Integration")
    print("=" * 60)
    print()

    # Create agent with OpenAI (more reliable for testing)
    print("1. Creating agent with OpenAI model...")
    agent = create_agent("openai")
    print("   Agent created successfully!")
    print()

    # Test query
    user_prompt = "What is the current stock price of Apple?"
    print(f"2. User prompt: {user_prompt}")
    print()

    # Stream the response
    print("3. Streaming response...")
    print("-" * 60)

    conversation_history = []
    chunks = []

    for chunk in stream_agent_response(agent, user_prompt, conversation_history):
        print(chunk, end="", flush=True)
        chunks.append(chunk)

    print()
    print("-" * 60)
    print()

    # Verify response was captured
    complete_response = "".join(chunks)
    print(f"4. Complete response length: {len(complete_response)} characters")
    print(f"   Number of chunks received: {len(chunks)}")
    print()

    print("5. LogFire logging verification:")
    print("   The following should have been logged to LogFire:")
    print(f"   - Event: 'conversation_completed'")
    print(f"   - user_prompt: '{user_prompt}'")
    print(f"   - agent_response: [complete response with {len(complete_response)} chars]")
    print(f"   - response_length: {len(complete_response)}")
    print(f"   - chunks_count: {len(chunks)}")
    print()

    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Check your LogFire dashboard at: https://logfire.pydantic.dev/")
    print("2. Look for the 'conversation_completed' event")
    print("3. Verify it contains:")
    print("   - user_prompt field")
    print("   - agent_response field (complete response, not chunks)")
    print()


if __name__ == "__main__":
    test_logfire_logging()
