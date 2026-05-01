"""Pytest fixtures for searchmcp tests."""

import pytest
import searchmcp.server as _server
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def reset_server_state():
    """Reset server module state before each test so patches take effect."""
    _server._ddgs_client = None
    original_logging = _server._with_logging
    yield
    _server._ddgs_client = None
    _server._with_logging = original_logging


@pytest.fixture
def mock_ddgs():
    """Fixture that provides a mocked DDGS client."""
    with patch("searchmcp.server.DDGS") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_ddgs_web_results(mock_ddgs):
    """Fixture with pre-configured web search results."""
    mock_ddgs.text.return_value = [
        {"title": "Result 1", "href": "https://example.com/1", "body": "Body 1"},
    ]
    return mock_ddgs


@pytest.fixture
def mock_ddgs_image_results(mock_ddgs):
    """Fixture with pre-configured image search results."""
    mock_ddgs.images.return_value = [
        {"title": "Image 1", "image": "https://example.com/img1.jpg"},
    ]
    return mock_ddgs


@pytest.fixture
def mock_ddgs_news_results(mock_ddgs):
    """Fixture with pre-configured news search results."""
    mock_ddgs.news.return_value = [
        {"title": "News 1", "url": "https://example.com/news1"},
    ]
    return mock_ddgs


@pytest.fixture
def mock_ddgs_videos_results(mock_ddgs):
    """Fixture with pre-configured video search results."""
    mock_ddgs.videos.return_value = [
        {
            "title": "Video 1",
            "content": "https://example.com/v1",
            "description": "Test video",
        },
    ]
    return mock_ddgs


@pytest.fixture
def mock_ddgs_books_results(mock_ddgs):
    """Fixture with pre-configured book search results."""
    mock_ddgs.books.return_value = [
        {"title": "Book 1", "author": "Author 1", "url": "https://example.com/book1"},
    ]
    return mock_ddgs
