"""PydanticAI agent for financial research and stock analysis.

This module provides the core agent implementation using the PydanticAI framework.
It supports dual-model configuration (OLLAMA local and OpenAI cloud) and integrates
both finance and research tools for comprehensive financial analysis.

The agent uses intelligent system instructions to convert company names to stock
tickers and explicitly mentions tool usage for full transparency in responses.

Example:
    from src.agent.financial_agent import create_agent

    # Create agent with OLLAMA model
    agent = create_agent("ollama")

    # Create agent with OpenAI model
    agent = create_agent("openai")

    # Run agent with streaming
    async with agent.run_stream("What is Apple's stock price?") as result:
        async for text in result.stream_text():
            print(text)
"""

from typing import Any

import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from src.config import LOGFIRE_TOKEN, OLLAMA_BASE_URL, OLLAMA_MODEL_NAME
from src.tools.finance_tool import get_stock_price
from src.tools.research_tool import search_web
from src.utils.exceptions import ConfigurationError, ToolExecutionError

# System instructions for the financial agent
SYSTEM_INSTRUCTIONS = """You are a financial research assistant with access to real-time stock data and web search capabilities.

CRITICAL INSTRUCTIONS:

1. TICKER CONVERSION:
   - When users mention company names (e.g., "Apple", "Microsoft", "Tesla"), you MUST convert them to stock ticker symbols (e.g., "AAPL", "MSFT", "TSLA") before using the finance tool.
   - Use your knowledge to determine the correct ticker symbol. Do NOT hardcode mappings.
   - If you're unsure about a ticker, use the research tool to verify it first.

2. TOOL USAGE TRANSPARENCY:
   - ALWAYS explicitly mention which tool you're using when you use it.
   - Example: "I'm using the finance tool to fetch the latest stock price for AAPL..."
   - Example: "I'm using the research tool to search for recent news about Tesla..."
   - This transparency is CRITICAL for user trust and debugging.

3. TOOL SELECTION:
   - Use the finance tool (get_stock_price) for stock prices and financial data.
   - Use the research tool (search_web) for news, analysis, company information, and general research.
   - You can use multiple tools in sequence if needed to answer a question comprehensively.

4. ERROR HANDLING:
   - If a tool fails, explain the error clearly to the user.
   - Suggest alternative approaches or ask for clarification if needed.

5. RESPONSE STYLE:
   - Be concise but informative.
   - Always cite your sources when using the research tool.
   - Format financial data clearly (e.g., prices with currency symbols).

Remember: Transparency about tool usage is non-negotiable. Always tell users which tool you're using and why.
"""


def create_agent(model_choice: str) -> Agent:
    """Create and configure a PydanticAI financial agent with dual-model support.

    This function initializes a PydanticAI agent with the specified model (OLLAMA
    local or OpenAI cloud) and registers both finance and research tools. The agent
    is configured with system instructions for intelligent ticker conversion and
    tool usage transparency.

    LogFire observability is integrated for tracking all agent interactions,
    tool calls, and conversation history.

    Args:
        model_choice: Model to use. Must be "ollama" or "openai".
            - "ollama": Uses local OLLAMA model (qwen3:8b) via OLLAMA_BASE_URL
            - "openai": Uses OpenAI's gpt-4o-mini model via OpenAI API

    Returns:
        Configured Agent instance ready for running queries with streaming support.
        The agent has both finance_tool and research_tool registered.

    Raises:
        ConfigurationError: If model_choice is invalid or required configuration
            is missing (LOGFIRE_TOKEN, OLLAMA_BASE_URL for ollama model).

    Example:
        >>> agent = create_agent("ollama")
        >>> result = agent.run_sync("What is the stock price of Apple?")
        >>> print(result.output)
        I'm using the finance tool to fetch the latest stock price for AAPL...
        The current stock price of Apple (AAPL) is $150.25 USD.

        >>> # With streaming
        >>> async with agent.run_stream("Research Tesla news") as result:
        ...     async for text in result.stream_text():
        ...         print(text, end="", flush=True)
    """
    # Validate model_choice parameter
    model_choice_lower = model_choice.lower()
    valid_models = ["ollama", "openai"]

    if model_choice_lower not in valid_models:
        raise ConfigurationError(
            f"Invalid model_choice '{model_choice}'. Must be one of: {', '.join(valid_models)}"
        )

    # Validate LogFire token is configured
    if not LOGFIRE_TOKEN:
        raise ConfigurationError(
            "LOGFIRE_TOKEN is required for agent observability. "
            "Please set it in your .env file or environment variables."
        )

    # Configure LogFire for observability
    logfire.configure(token=LOGFIRE_TOKEN)
    logfire.instrument_pydantic()
    # Determine model based on choice
    if model_choice_lower == "ollama":
        # Validate OLLAMA configuration
        if not OLLAMA_BASE_URL:
            raise ConfigurationError(
                "OLLAMA_BASE_URL is required for OLLAMA model. "
                "Please set it in your .env file (default: http://localhost:11434)."
            )

        if not OLLAMA_MODEL_NAME:
            raise ConfigurationError(
                "OLLAMA_MODEL_NAME is required for OLLAMA model. "
                "Please set it in your .env file (default: qwen3:8b)."
            )

        # OLLAMA uses OpenAI-compatible API via OllamaProvider
        # The base_url must include /v1 suffix for OpenAI compatibility
        ollama_base_url = OLLAMA_BASE_URL
        if not ollama_base_url.endswith('/v1'):
            ollama_base_url = f"{ollama_base_url}/v1"

        model = OpenAIChatModel(
            model_name=OLLAMA_MODEL_NAME,
            provider=OllamaProvider(base_url=ollama_base_url),
        )
        model_string = f"ollama:{OLLAMA_MODEL_NAME}"

    else:  # openai
        # PydanticAI model string format: "openai:<model_name>"
        # Using gpt-4o-mini as specified in requirements
        model_string = "openai:gpt-4o-mini"
        model = model_string  # Agent accepts string for standard providers

        # Note: OPENAI_API_KEY is used via environment variable
        # PydanticAI's openai integration automatically reads this

    # Create agent with system instructions
    agent = Agent(
        model,
        system_prompt=SYSTEM_INSTRUCTIONS,
    )

    # Register finance tool
    @agent.tool
    def finance_tool(ctx: RunContext, ticker: str) -> dict[str, Any]:
        """Fetch current stock price and financial data for a given ticker symbol.

        This tool retrieves real-time stock market data including current price,
        previous close, daily high/low, volume, and currency. It enforces rate
        limiting (10 requests per minute) to prevent API abuse.

        Args:
            ctx: PydanticAI run context (automatically provided).
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL').
                Must be a valid ticker recognized by Yahoo Finance.

        Returns:
            Dictionary containing structured financial data with keys:
            ticker, current_price, previous_close, day_high, day_low,
            volume, currency.

        Raises:
            ToolExecutionError: If ticker is invalid, rate limit exceeded,
                or YFinance API encounters an error.
        """
        return get_stock_price(ticker)

    # Register research tool
    @agent.tool
    def research_tool(
        ctx: RunContext, query: str, max_results: int = 5
    ) -> dict[str, Any]:
        """Perform web search using Tavily API and return structured results.

        This tool executes a web search query and returns structured results
        including titles, URLs, content snippets, and source count. It's ideal
        for news gathering, company research, and fact-finding operations.

        Args:
            ctx: PydanticAI run context (automatically provided).
            query: Search query string describing what information to find.
            max_results: Maximum number of search results to return (1-20).
                Defaults to 5.

        Returns:
            Dictionary containing structured search results with keys:
            query (original query), results (list of dicts with title/url/content),
            source_count (total number of sources).

        Raises:
            ToolExecutionError: If TAVILY_API_KEY is not configured, query is
                invalid, or Tavily API encounters an error.
        """
        return search_web(query, max_results)

    # Log agent creation
    logfire.info(
        "Financial agent created",
        model_choice=model_choice_lower,
        model_string=model_string,
        tools=["finance_tool", "research_tool"],
    )

    return agent
