"""Streamlit Financial Research Agent - Chat Interface.

This module provides the main Streamlit web application interface for the
Financial Research Agent. It includes a chat interface with model selection
and session management capabilities.

Note: This is the UI layer only. Agent integration is handled separately.
"""

import streamlit as st


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
                "OLLAMA (qwen2.5:3b)",
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


def handle_user_input() -> None:
    """Handle user input from the chat input widget.

    Processes user messages by adding them to the session state and
    displaying them immediately. In this UI-only version, a placeholder
    assistant response is shown.

    Note: Actual agent integration will be added in a future task.
    """
    if prompt := st.chat_input("Ask about stocks or companies..."):
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Placeholder for assistant response (agent integration comes later)
        # This is just for UI testing purposes
        placeholder_response = (
            f"[UI Mode] You selected {st.session_state.model_choice.upper()} model. "
            "Agent integration will be added in the next task."
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": placeholder_response
        })

        # Display assistant message
        with st.chat_message("assistant"):
            st.write(placeholder_response)


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
