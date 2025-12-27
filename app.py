"""Streamlit Financial Research Agent - Chat Interface.

This module provides the main Streamlit web application interface for the
Financial Research Agent. It includes a chat interface with model selection
and session management capabilities.

Agent integration provides real-time streaming responses with tool transparency
and comprehensive error handling for a robust user experience.
"""

import streamlit as st

from src.agent.financial_agent import create_agent
from src.agent.streaming import stream_agent_response
from src.utils.exceptions import (
    ConfigurationError,
    RateLimitExceededError,
    ToolExecutionError,
)


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables.

    Creates session state variables for messages and model choice if they
    don't already exist. This ensures consistent state across reruns.
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "model_choice" not in st.session_state:
        st.session_state.model_choice = "ollama"


def clear_chat_history() -> None:
    """Clear all messages from the chat history.

    Resets the messages list in session state to an empty list,
    effectively starting a new conversation session.
    """
    st.session_state.messages = []


def render_sidebar() -> str:
    """Render the sidebar with model selection and controls.

    Displays the application title, model selection dropdown, and
    new session button in the sidebar.

    Returns:
        The selected model choice string ("ollama" or "openai")
    """
    with st.sidebar:
        st.title("Financial Research Agent")

        # Model selection dropdown
        model_option = st.selectbox(
            "Select Model",
            options=[
                "OLLAMA (qwen3:8b)",
                "OpenAI (gpt-4o-mini)"
            ],
            index=0 if st.session_state.model_choice == "ollama" else 1,
            key="model_selector"
        )

        # Convert display name to internal model choice
        if "OLLAMA" in model_option:
            st.session_state.model_choice = "ollama"
        else:
            st.session_state.model_choice = "openai"

        # New Session button
        if st.button("New Session", use_container_width=True):
            clear_chat_history()
            st.rerun()

        return st.session_state.model_choice


def render_chat_history() -> None:
    """Render all messages from the chat history.

    Displays all messages stored in session state using st.chat_message
    with appropriate role indicators (user or assistant).
    """
    for message in st.session_state.messages:
        role = message.get("role", "user")
        content = message.get("content", "")

        with st.chat_message(role):
            st.write(content)


def convert_to_pydantic_history(
    streamlit_messages: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Convert Streamlit message history to PydanticAI format.

    PydanticAI expects conversation history as a list of message dictionaries
    with specific role naming conventions. This function transforms the Streamlit
    message format to the PydanticAI format.

    Args:
        streamlit_messages: List of message dicts with "role" (user/assistant)
            and "content" keys from Streamlit session state.

    Returns:
        List of message dicts for PydanticAI agent. Roles are converted:
        - "user" -> "user" (no change)
        - "assistant" -> "model" (PydanticAI convention)

    Note:
        PydanticAI uses "model" instead of "assistant" for AI responses.
    """
    pydantic_history = []

    for message in streamlit_messages:
        role = message.get("role", "user")
        content = message.get("content", "")

        # Convert assistant role to model role for PydanticAI
        pydantic_role = "model" if role == "assistant" else role

        # Create message dict with converted role
        pydantic_history.append({
            "role": pydantic_role,
            "content": content,
        })

    return pydantic_history


def handle_user_input() -> None:
    """Handle user input from the chat input widget with agent integration.

    Processes user messages by:
    1. Adding user message to session state
    2. Creating PydanticAI agent with selected model
    3. Converting message history to PydanticAI format
    4. Streaming agent response with real-time display
    5. Handling errors gracefully with user-friendly messages

    Error handling covers:
    - ConfigurationError: Missing API keys or invalid config
    - RateLimitExceededError: API rate limits exceeded
    - ToolExecutionError: Tool failures (YFinance, Tavily)
    - Generic exceptions: Unexpected errors with full trace
    """
    # Security: Maximum prompt length to prevent resource exhaustion
    MAX_PROMPT_LENGTH = 2000

    if prompt := st.chat_input("Ask about stocks or companies..."):
        # Security: Validate and sanitize user input
        prompt = prompt.strip()

        if len(prompt) < 1:
            return

        if len(prompt) > MAX_PROMPT_LENGTH:
            st.error(f"Input too long (maximum {MAX_PROMPT_LENGTH} characters)")
            return

        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Display assistant response with streaming
        with st.chat_message("assistant"):
            try:
                # Create agent with selected model
                agent = create_agent(st.session_state.model_choice)

                # Convert Streamlit message history to PydanticAI format
                # Exclude the just-added user message (will be passed separately)
                history_for_agent = convert_to_pydantic_history(
                    st.session_state.messages[:-1]
                )

                # Stream agent response with real-time display
                # st.write_stream() handles generator and displays chunks as they arrive
                response_text = st.write_stream(
                    stream_agent_response(agent, prompt, history_for_agent)
                )

                # Add complete assistant response to history
                st.session_state.messages.append(
                    {"role": "assistant", "content": response_text}
                )

            except ConfigurationError as e:
                # Missing or invalid configuration (API keys, model settings)
                error_msg = (
                    f"Configuration error: {str(e)}. "
                    "Please check your .env file and ensure all required "
                    "API keys are set correctly."
                )
                st.error(error_msg)

                # Add error to history so it persists across reruns
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

            except RateLimitExceededError as e:
                # Rate limit exceeded (YFinance API calls)
                error_msg = f"Rate limit exceeded: {str(e)}"
                st.error(error_msg)

                # Add error to history
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

            except ToolExecutionError as e:
                # Tool execution failures (invalid ticker, API errors)
                error_msg = f"Tool error: {str(e)}"
                st.error(error_msg)

                # Add error to history
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

            except Exception as e:
                # Catch-all for unexpected errors
                error_msg = "An unexpected error occurred. Please try again or contact support."
                st.error(error_msg)

                # Security: Log full details to LogFire instead of exposing to user
                import logfire
                logfire.error("unexpected_ui_error", error=str(e), error_type=type(e).__name__)

                # Add error to history
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )


def main() -> None:
    """Main application entry point.

    Sets up the Streamlit page configuration and orchestrates the
    rendering of all UI components.
    """
    # Page configuration
    st.set_page_config(
        page_title="Financial Research Agent",
        page_icon="📊",
        layout="centered",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    initialize_session_state()

    # Render sidebar and get model choice
    model_choice = render_sidebar()

    # Render chat history
    render_chat_history()

    # Handle user input
    handle_user_input()


if __name__ == "__main__":
    main()
