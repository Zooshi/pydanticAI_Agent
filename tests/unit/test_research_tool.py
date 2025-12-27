"""Unit tests for Tavily research tool.

This module contains comprehensive unit tests for the search_web function
in src/tools/research_tool.py. All tests mock the Tavily API to avoid
making real API calls.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.tools.research_tool import search_web
from src.utils.exceptions import ToolExecutionError


class TestSearchWebSuccess(unittest.TestCase):
    """Test cases for successful web search operations."""

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_valid_query_returns_results(self, mock_tavily_class):
        """Test that a valid query returns structured results."""
        # Setup mock
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "Apple announces new iPhone",
                    "url": "https://example.com/article1",
                    "content": "Apple has announced the latest iPhone model..."
                },
                {
                    "title": "iPhone release date confirmed",
                    "url": "https://example.com/article2",
                    "content": "The new iPhone will be released next month..."
                }
            ]
        }

        # Execute
        result = search_web("latest Apple iPhone news")

        # Assert
        self.assertEqual(result["query"], "latest Apple iPhone news")
        self.assertEqual(result["source_count"], 2)
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["title"], "Apple announces new iPhone")
        self.assertEqual(result["results"][0]["url"], "https://example.com/article1")
        self.assertIn("Apple has announced", result["results"][0]["content"])
        mock_client.search.assert_called_once_with(
            query="latest Apple iPhone news",
            max_results=5,
            search_depth="basic"
        )

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_custom_max_results(self, mock_tavily_class):
        """Test that custom max_results parameter is respected."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = {
            "results": [
                {"title": "Result 1", "url": "https://example.com/1", "content": "Content 1"},
                {"title": "Result 2", "url": "https://example.com/2", "content": "Content 2"},
                {"title": "Result 3", "url": "https://example.com/3", "content": "Content 3"}
            ]
        }

        result = search_web("test query", max_results=3)

        self.assertEqual(result["source_count"], 3)
        mock_client.search.assert_called_once_with(
            query="test query",
            max_results=3,
            search_depth="basic"
        )

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_empty_results_list(self, mock_tavily_class):
        """Test handling of empty results list from API."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = {"results": []}

        result = search_web("query with no results")

        self.assertEqual(result["query"], "query with no results")
        self.assertEqual(result["source_count"], 0)
        self.assertEqual(len(result["results"]), 0)

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_handles_missing_fields(self, mock_tavily_class):
        """Test that missing fields in results use default values."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = {
            "results": [
                {
                    "url": "https://example.com/partial"
                    # Missing title and content
                }
            ]
        }

        result = search_web("test query")

        self.assertEqual(result["source_count"], 1)
        self.assertEqual(result["results"][0]["title"], "No title")
        self.assertEqual(result["results"][0]["url"], "https://example.com/partial")
        self.assertEqual(result["results"][0]["content"], "No content available")

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_query_whitespace_trimmed(self, mock_tavily_class):
        """Test that query with leading/trailing whitespace is trimmed."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = {"results": []}

        result = search_web("  test query  ")

        self.assertEqual(result["query"], "test query")
        mock_client.search.assert_called_once_with(
            query="test query",
            max_results=5,
            search_depth="basic"
        )

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_skips_malformed_results(self, mock_tavily_class):
        """Test that malformed results are skipped gracefully."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = {
            "results": [
                {"title": "Good Result", "url": "https://example.com", "content": "Valid"},
                "not a dict",  # Malformed result
                {"title": "Another Good Result", "url": "https://example2.com", "content": "Also valid"}
            ]
        }

        result = search_web("test query")

        # Should only include the 2 valid results
        self.assertEqual(result["source_count"], 2)
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["title"], "Good Result")
        self.assertEqual(result["results"][1]["title"], "Another Good Result")


class TestSearchWebMissingAPIKey(unittest.TestCase):
    """Test cases for missing API key scenario."""

    @patch("src.tools.research_tool.TAVILY_API_KEY", None)
    def test_search_web_missing_api_key_raises_error(self):
        """Test that missing API key raises ToolExecutionError."""
        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query")

        self.assertIn("TAVILY_API_KEY is not configured", str(context.exception))
        self.assertIn("tavily.com", str(context.exception).lower())

    @patch("src.tools.research_tool.TAVILY_API_KEY", "")
    def test_search_web_empty_api_key_raises_error(self):
        """Test that empty API key raises ToolExecutionError."""
        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query")

        self.assertIn("TAVILY_API_KEY is not configured", str(context.exception))


class TestSearchWebInvalidInput(unittest.TestCase):
    """Test cases for invalid input validation."""

    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_empty_query_raises_error(self):
        """Test that empty query raises ToolExecutionError."""
        with self.assertRaises(ToolExecutionError) as context:
            search_web("")

        self.assertIn("query cannot be empty", str(context.exception))

    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_whitespace_only_query_raises_error(self):
        """Test that whitespace-only query raises ToolExecutionError."""
        with self.assertRaises(ToolExecutionError) as context:
            search_web("   ")

        self.assertIn("query cannot be empty", str(context.exception))

    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_none_query_raises_error(self):
        """Test that None query raises ToolExecutionError."""
        with self.assertRaises(ToolExecutionError) as context:
            search_web(None)

        self.assertIn("query must be a non-empty string", str(context.exception))
        self.assertIn("NoneType", str(context.exception))

    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_integer_query_raises_error(self):
        """Test that integer query raises ToolExecutionError."""
        with self.assertRaises(ToolExecutionError) as context:
            search_web(123)

        self.assertIn("query must be a non-empty string", str(context.exception))
        self.assertIn("int", str(context.exception))

    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_max_results_too_small_raises_error(self):
        """Test that max_results < 1 raises ToolExecutionError."""
        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query", max_results=0)

        self.assertIn("max_results value", str(context.exception))
        self.assertIn("between 1 and 20", str(context.exception))

    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_max_results_too_large_raises_error(self):
        """Test that max_results > 20 raises ToolExecutionError."""
        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query", max_results=21)

        self.assertIn("max_results value", str(context.exception))
        self.assertIn("between 1 and 20", str(context.exception))

    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_max_results_not_integer_raises_error(self):
        """Test that non-integer max_results raises ToolExecutionError."""
        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query", max_results="5")

        self.assertIn("max_results format", str(context.exception))
        self.assertIn("must be an integer", str(context.exception))


class TestSearchWebAPIErrors(unittest.TestCase):
    """Test cases for API error scenarios."""

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_api_authentication_error(self, mock_tavily_class):
        """Test that API authentication errors are wrapped in ToolExecutionError."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.side_effect = Exception("Invalid API key provided")

        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query")

        error_message = str(context.exception)
        self.assertIn("authentication failed", error_message)
        self.assertIn("TAVILY_API_KEY is valid", error_message)

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_network_error(self, mock_tavily_class):
        """Test that network errors are wrapped in ToolExecutionError."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.side_effect = Exception("Connection timeout after 30s")

        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query")

        error_message = str(context.exception)
        self.assertIn("network error", error_message)
        self.assertIn("internet connection", error_message)

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_rate_limit_error(self, mock_tavily_class):
        """Test that rate limit errors are wrapped in ToolExecutionError."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.side_effect = Exception("Rate limit exceeded for your plan")

        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query")

        error_message = str(context.exception)
        self.assertIn("rate limit exceeded", error_message)
        self.assertIn("wait before making more requests", error_message)

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_generic_api_error(self, mock_tavily_class):
        """Test that generic API errors are wrapped in ToolExecutionError."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.side_effect = ValueError("Unexpected API error")

        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query")

        error_message = str(context.exception)
        self.assertIn("Tavily API error", error_message)
        self.assertIn("test query", error_message)
        self.assertIn("ValueError", error_message)
        self.assertIn("Unexpected API error", error_message)

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_invalid_response_format(self, mock_tavily_class):
        """Test that invalid response format raises ToolExecutionError."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = "not a dict"

        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query")

        self.assertIn("Invalid API response format", str(context.exception))
        self.assertIn("expected dict", str(context.exception))

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_invalid_results_format(self, mock_tavily_class):
        """Test that invalid results format raises ToolExecutionError."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = {"results": "not a list"}

        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query")

        self.assertIn("Invalid results format", str(context.exception))
        self.assertIn("expected list", str(context.exception))

    @patch("src.tools.research_tool.TavilyClient")
    @patch("src.tools.research_tool.TAVILY_API_KEY", "test-api-key")
    def test_search_web_none_response(self, mock_tavily_class):
        """Test that None response raises ToolExecutionError."""
        mock_client = MagicMock()
        mock_tavily_class.return_value = mock_client
        mock_client.search.return_value = None

        with self.assertRaises(ToolExecutionError) as context:
            search_web("test query")

        self.assertIn("Invalid API response format", str(context.exception))


if __name__ == "__main__":
    unittest.main()
