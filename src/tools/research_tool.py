"""Research tool for web search using Tavily API.

This module provides a tool function for performing web research using the
Tavily search API. It retrieves up-to-date information from the internet
and returns structured results with sources.

The tool is designed to be called by PydanticAI agents for general web
research tasks, news gathering, and fact-finding operations.
"""

from typing import Any

from tavily import TavilyClient

from src.config import TAVILY_API_KEY
from src.utils.exceptions import ToolExecutionError


def search_web(query: str, max_results: int = 5) -> dict[str, Any]:
    """Perform web search using Tavily API and return structured results.

    This function executes a web search query using the Tavily API and returns
    structured results including titles, URLs, content snippets, and source count.
    It handles API authentication, network errors, and result formatting.

    Args:
        query: Search query string. Must be a non-empty string describing
            what information to search for on the web.
        max_results: Maximum number of search results to return. Must be
            between 1 and 20. Defaults to 5.

    Returns:
        Dictionary containing structured search results:
        {
            "query": str,              # The original search query
            "results": [               # List of search results
                {
                    "title": str,      # Result title
                    "url": str,        # Source URL
                    "content": str     # Content snippet/summary
                },
                # ... more results
            ],
            "source_count": int        # Total number of sources returned
        }

    Raises:
        ToolExecutionError: If TAVILY_API_KEY is not configured, query is
            invalid, max_results is out of range, API request fails, or
            network errors occur. Error messages include specific failure
            context for debugging.

    Example:
        >>> results = search_web("latest Apple iPhone news", max_results=3)
        >>> print(f"Found {results['source_count']} sources")
        Found 3 sources
        >>> for result in results['results']:
        ...     print(f"{result['title']}: {result['url']}")
    """
    # Validate API key is configured
    if not TAVILY_API_KEY:
        raise ToolExecutionError(
            "TAVILY_API_KEY is not configured. Please set the API key in your "
            ".env file or environment variables. Get your API key from https://tavily.com"
        )

    # Validate query format - type check first
    if not isinstance(query, str):
        raise ToolExecutionError(
            f"Invalid query format: query must be a non-empty string, got {type(query).__name__}"
        )

    # Trim whitespace
    query = query.strip()

    # Check for empty/whitespace-only after trimming
    if not query:
        raise ToolExecutionError(
            "Invalid query format: query cannot be empty or whitespace"
        )

    # Validate max_results parameter
    if not isinstance(max_results, int):
        raise ToolExecutionError(
            f"Invalid max_results format: must be an integer, got {type(max_results).__name__}"
        )

    if max_results < 1 or max_results > 20:
        raise ToolExecutionError(
            f"Invalid max_results value: must be between 1 and 20, got {max_results}"
        )

    try:
        # Initialize Tavily client with API key
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

        # Execute search with basic parameters
        response = tavily_client.search(
            query=query,
            max_results=max_results,
            search_depth="basic"  # Use basic search for faster responses
        )

        # Validate response structure
        if not response or not isinstance(response, dict):
            raise ToolExecutionError(
                f"Invalid API response format: expected dict, got {type(response).__name__}"
            )

        # Extract results from response
        results_list = response.get("results", [])

        if not isinstance(results_list, list):
            raise ToolExecutionError(
                f"Invalid results format in API response: expected list, got {type(results_list).__name__}"
            )

        # Build structured results list
        structured_results = []
        for result in results_list:
            if not isinstance(result, dict):
                continue  # Skip malformed results

            structured_results.append({
                "title": str(result.get("title", "No title")),
                "url": str(result.get("url", "")),
                "content": str(result.get("content", "No content available"))
            })

        # Build response dictionary
        return {
            "query": query,
            "results": structured_results,
            "source_count": len(structured_results)
        }

    except ToolExecutionError:
        # Re-raise our custom errors without wrapping
        raise

    except Exception as e:
        # Wrap unexpected errors with context
        error_type = type(e).__name__
        error_message = str(e)

        # Provide helpful error messages for common issues
        if "api key" in error_message.lower() or "authentication" in error_message.lower():
            raise ToolExecutionError(
                f"Tavily API authentication failed: {error_type}: {error_message}. "
                "Please verify your TAVILY_API_KEY is valid."
            )
        elif "timeout" in error_message.lower() or "connection" in error_message.lower():
            raise ToolExecutionError(
                f"Tavily API network error: {error_type}: {error_message}. "
                "Please check your internet connection and try again."
            )
        elif "rate limit" in error_message.lower() or "quota" in error_message.lower():
            raise ToolExecutionError(
                f"Tavily API rate limit exceeded: {error_type}: {error_message}. "
                "Please wait before making more requests or upgrade your plan."
            )
        else:
            raise ToolExecutionError(
                f"Tavily API error for query '{query}': {error_type}: {error_message}"
            )
