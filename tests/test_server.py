# start tests/test_server.py
"""Tests for the Web Search MCP Server."""

from unittest.mock import MagicMock, patch

import pytest

from server import SearchError, do_image_search, do_news_search, do_web_search


class TestValidation:
    """Tests for input validation."""

    def test_empty_query_raises_error(self) -> None:
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            do_web_search("")

    def test_whitespace_query_raises_error(self) -> None:
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            do_web_search("   ")

    def test_max_results_too_low_raises_error(self) -> None:
        """Test that max_results < 1 raises ValueError."""
        with pytest.raises(ValueError, match="max_results must be between"):
            do_web_search("test", max_results=0)

    def test_max_results_too_high_raises_error(self) -> None:
        """Test that max_results > 100 raises ValueError."""
        with pytest.raises(ValueError, match="max_results must be between"):
            do_web_search("test", max_results=101)

    def test_invalid_safe_search_raises_error(self) -> None:
        """Test that invalid safe_search raises ValueError."""
        with pytest.raises(ValueError, match="safe_search must be"):
            do_web_search("test", safe_search="invalid")


class TestWebSearch:
    """Tests for do_web_search function."""

    def test_web_search_valid_query(self) -> None:
        """Test web search with valid parameters."""
        with patch("server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = [
                {"title": "Test", "href": "https://example.com", "body": "Test body"}
            ]
            mock_ddgs.return_value = mock_instance

            results = do_web_search("test query")

            assert len(results) == 1
            assert results[0]["title"] == "Test"
            mock_instance.text.assert_called_once_with(
                "test query",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
            )

    def test_web_search_custom_params(self) -> None:
        """Test web search with custom parameters."""
        with patch("server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = []
            mock_ddgs.return_value = mock_instance

            do_web_search("test", max_results=5, region="us-en", safe_search="strict")

            mock_instance.text.assert_called_once_with(
                "test",
                max_results=5,
                region="us-en",
                safesearch="strict",
            )

    def test_web_search_api_error_raises_search_error(self) -> None:
        """Test that API errors are wrapped in SearchError."""
        with patch("server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.side_effect = RuntimeError("API error")
            mock_ddgs.return_value = mock_instance

            with pytest.raises(SearchError, match="Web search failed"):
                do_web_search("test query")


class TestImageSearch:
    """Tests for do_image_search function."""

    def test_image_search_valid_query(self) -> None:
        """Test image search with valid parameters."""
        with patch("server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.images.return_value = [
                {"title": "Image", "image": "https://example.com/img.jpg"}
            ]
            mock_ddgs.return_value = mock_instance

            results = do_image_search("test image")

            assert len(results) == 1
            mock_instance.images.assert_called_once()

    def test_image_search_api_error_raises_search_error(self) -> None:
        """Test that API errors are wrapped in SearchError."""
        with patch("server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.images.side_effect = RuntimeError("API error")
            mock_ddgs.return_value = mock_instance

            with pytest.raises(SearchError, match="Image search failed"):
                do_image_search("test image")


class TestNewsSearch:
    """Tests for do_news_search function."""

    def test_news_search_valid_query(self) -> None:
        """Test news search with valid parameters."""
        with patch("server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.news.return_value = [
                {"title": "News", "url": "https://example.com/news"}
            ]
            mock_ddgs.return_value = mock_instance

            results = do_news_search("test news")

            assert len(results) == 1
            mock_instance.news.assert_called_once()

    def test_news_search_api_error_raises_search_error(self) -> None:
        """Test that API errors are wrapped in SearchError."""
        with patch("server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.news.side_effect = RuntimeError("API error")
            mock_ddgs.return_value = mock_instance

            with pytest.raises(SearchError, match="News search failed"):
                do_news_search("test news")

    def test_news_search_no_safe_search_param(self) -> None:
        """Test that news_search doesn't use safe_search parameter."""
        with patch("server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.news.return_value = []
            mock_ddgs.return_value = mock_instance

            do_news_search("test", max_results=5, region="us-en")

            mock_instance.news.assert_called_once_with(
                "test",
                max_results=5,
                region="us-en",
            )


# end tests/test_server.py
