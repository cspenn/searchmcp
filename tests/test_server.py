"""Tests for the Web Search MCP Server."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from ddgs.exceptions import DDGSException

from searchmcp.params import SearchParams
from searchmcp.server import (
    SearchError,
    TorConfig,
    check_privileges,
    do_books_search,
    do_image_search,
    do_news_search,
    do_videos_search,
    do_web_search,
    books_search,
    image_search,
    news_search,
    verify_tor_exit,
    verify_tor_proxy,
    videos_search,
    web_search,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_httpx_mock(json_data: dict) -> MagicMock:
    """Build a context-manager-compatible httpx.Client mock."""
    mock_response = MagicMock()
    mock_response.json.return_value = json_data
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)
    mock_client.get.return_value = mock_response
    return mock_client


# ---------------------------------------------------------------------------
# TorConfig
# ---------------------------------------------------------------------------


class TestTorConfig:
    """Tests for Tor configuration."""

    def test_tor_enabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that Tor is ENABLED by default (privacy-first)."""
        monkeypatch.delenv("SEARCHMCP_USE_TOR", raising=False)
        monkeypatch.delenv("SEARCHMCP_TOR_PROXY", raising=False)
        monkeypatch.delenv("SEARCHMCP_TOR_TIMEOUT", raising=False)
        config = TorConfig.from_environment()
        assert config.enabled

    def test_tor_disabled_via_env_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SEARCHMCP_USE_TOR", "false")
        config = TorConfig.from_environment()
        assert not config.enabled

    def test_tor_disabled_via_env_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SEARCHMCP_USE_TOR", "0")
        config = TorConfig.from_environment()
        assert not config.enabled

    def test_tor_disabled_via_env_no(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SEARCHMCP_USE_TOR", "no")
        config = TorConfig.from_environment()
        assert not config.enabled

    def test_tor_enabled_explicit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SEARCHMCP_USE_TOR", "true")
        config = TorConfig.from_environment()
        assert config.enabled

    def test_tor_disabled_case_insensitive(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SEARCHMCP_USE_TOR", "FALSE")
        config = TorConfig.from_environment()
        assert not config.enabled

    def test_default_proxy_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SEARCHMCP_TOR_PROXY", raising=False)
        config = TorConfig.from_environment()
        assert config.proxy == "socks5h://127.0.0.1:9050"

    def test_custom_tor_proxy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SEARCHMCP_TOR_PROXY", "socks5h://127.0.0.1:9150")
        config = TorConfig.from_environment()
        assert config.proxy == "socks5h://127.0.0.1:9150"

    def test_default_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SEARCHMCP_TOR_TIMEOUT", raising=False)
        config = TorConfig.from_environment()
        assert config.timeout == 30

    def test_custom_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SEARCHMCP_TOR_TIMEOUT", "60")
        config = TorConfig.from_environment()
        assert config.timeout == 60


# ---------------------------------------------------------------------------
# verify_tor_proxy
# ---------------------------------------------------------------------------


class TestVerifyTorProxy:
    """Tests for Tor proxy verification."""

    def test_verify_tor_proxy_success(self) -> None:
        """Test successful proxy connection."""
        with patch("socket.socket") as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_instance

            result = verify_tor_proxy("socks5h://127.0.0.1:9050")

            assert result
            mock_instance.connect_ex.assert_called_once_with(("127.0.0.1", 9050))

    def test_verify_tor_proxy_failure(self) -> None:
        """Test failed proxy connection."""
        with patch("socket.socket") as mock_socket:
            mock_instance = MagicMock()
            mock_instance.connect_ex.return_value = 111  # Connection refused
            mock_socket.return_value = mock_instance

            result = verify_tor_proxy("socks5h://127.0.0.1:9050")

            assert not result

    def test_verify_tor_proxy_invalid_url(self) -> None:
        """Test handling of invalid proxy URL."""
        result = verify_tor_proxy("not-a-valid-url")
        assert isinstance(result, bool)


class TestVerifyTorProxyException:
    """Tests for verify_tor_proxy error handling."""

    def test_verify_tor_proxy_oserror(self) -> None:
        """Test that OSError during socket connect returns False."""
        with patch("socket.socket") as mock_socket:
            mock_socket.side_effect = OSError("Connection refused")
            result = verify_tor_proxy("socks5h://127.0.0.1:9050")
            assert result is False


# ---------------------------------------------------------------------------
# verify_tor_exit (httpx-based)
# ---------------------------------------------------------------------------


class TestVerifyTorExit:
    """Tests for verify_tor_exit function."""

    def test_verify_tor_exit_success(self) -> None:
        """Test successful Tor exit verification returns IP."""
        mock_client = make_httpx_mock({"IsTor": True, "IP": "185.220.101.1"})
        with patch("searchmcp.server.httpx.Client", return_value=mock_client):
            result = verify_tor_exit("socks5h://127.0.0.1:9050", 30)
            assert result == "185.220.101.1"

    def test_verify_tor_exit_not_tor_exits(self) -> None:
        """Test that non-Tor traffic triggers SystemExit."""
        mock_client = make_httpx_mock({"IsTor": False, "IP": "1.2.3.4"})
        with patch("searchmcp.server.httpx.Client", return_value=mock_client):
            with pytest.raises(SystemExit, match="Tor verification failed"):
                verify_tor_exit("socks5h://127.0.0.1:9050", 30)

    def test_verify_tor_exit_request_exception(self) -> None:
        """Test that network errors trigger SystemExit."""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.side_effect = httpx.RequestError("Connection refused")
        with patch("searchmcp.server.httpx.Client", return_value=mock_client):
            with pytest.raises(SystemExit, match="Could not verify Tor connection"):
                verify_tor_exit("socks5h://127.0.0.1:9050", 30)

    def test_verify_tor_exit_unknown_ip_fallback(self) -> None:
        """Test that missing IP field returns 'unknown'."""
        mock_client = make_httpx_mock({"IsTor": True})
        with patch("searchmcp.server.httpx.Client", return_value=mock_client):
            result = verify_tor_exit("socks5h://127.0.0.1:9050", 30)
            assert result == "unknown"


# ---------------------------------------------------------------------------
# check_privileges
# ---------------------------------------------------------------------------


class TestCheckPrivileges:
    """Tests for privilege checking."""

    def test_root_warning_on_unix(self) -> None:
        """Test warning when running as root on Unix."""
        with patch("os.name", "posix"):
            with patch("os.getuid", return_value=0):
                with patch("searchmcp.server.log") as mock_log:
                    check_privileges()
                    mock_log.warning.assert_called()

    def test_no_warning_for_regular_user(self) -> None:
        """Test no warning for regular user."""
        with patch("os.name", "posix"):
            with patch("os.getuid", return_value=1000):
                with patch("searchmcp.server.log") as mock_log:
                    check_privileges()
                    mock_log.warning.assert_not_called()


# ---------------------------------------------------------------------------
# DDGS client factory
# ---------------------------------------------------------------------------


class TestDdgsClientFactory:
    """Tests for the DDGS client factory function."""

    def test_ddgs_client_without_tor(self) -> None:
        """Test that DDGS client is created without proxy when Tor is disabled."""
        with patch("searchmcp.server._tor_config") as mock_config:
            mock_config.enabled = False
            with patch("searchmcp.server.DDGS") as mock_ddgs:
                from searchmcp.server import _get_ddgs_client

                _get_ddgs_client()
                mock_ddgs.assert_called_once_with()

    def test_ddgs_client_with_tor(self) -> None:
        """Test that DDGS client is created with proxy when Tor is enabled."""
        with patch("searchmcp.server._tor_config") as mock_config:
            mock_config.enabled = True
            mock_config.proxy = "socks5h://127.0.0.1:9050"
            mock_config.timeout = 30
            with patch("searchmcp.server.DDGS") as mock_ddgs:
                from searchmcp.server import _get_ddgs_client

                _get_ddgs_client()
                mock_ddgs.assert_called_once_with(
                    proxy="socks5h://127.0.0.1:9050", timeout=30
                )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Web Search
# ---------------------------------------------------------------------------


class TestWebSearch:
    """Tests for do_web_search function."""

    def test_web_search_valid_query(self) -> None:
        """Test web search with valid parameters returns results."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
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
                timelimit=None,
                backend="auto",
                page=1,
            )

    def test_web_search_custom_params(self) -> None:
        """Test web search with custom SearchParams."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = []
            mock_ddgs.return_value = mock_instance

            do_web_search(
                "test", SearchParams(max_results=5, region="us-en", safesearch="strict")
            )

            mock_instance.text.assert_called_once_with(
                "test",
                max_results=5,
                region="us-en",
                safesearch="strict",
                timelimit=None,
                backend="auto",
                page=1,
            )

    def test_web_search_api_error_raises_search_error(self) -> None:
        """Test that API errors are wrapped in SearchError with correct message."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.side_effect = RuntimeError("API error")
            mock_ddgs.return_value = mock_instance

            with pytest.raises(SearchError, match="text search failed"):
                do_web_search("test query")

    def test_web_search_with_timelimit(self) -> None:
        """Test web search passes timelimit through correctly."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = []
            mock_ddgs.return_value = mock_instance

            do_web_search("test", SearchParams(timelimit="w"))

            mock_instance.text.assert_called_once_with(
                "test",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
                timelimit="w",
                backend="auto",
                page=1,
            )


# ---------------------------------------------------------------------------
# Image Search
# ---------------------------------------------------------------------------


class TestImageSearch:
    """Tests for do_image_search function."""

    def test_image_search_valid_query(self) -> None:
        """Test image search with valid parameters."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.images.return_value = [
                {"title": "Image", "image": "https://example.com/img.jpg"}
            ]
            mock_ddgs.return_value = mock_instance

            results = do_image_search("test image")

            assert len(results) == 1
            mock_instance.images.assert_called_once_with(
                "test image",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
                timelimit=None,
                backend="auto",
                page=1,
            )

    def test_image_search_api_error_raises_search_error(self) -> None:
        """Test that API errors are wrapped in SearchError."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.images.side_effect = RuntimeError("API error")
            mock_ddgs.return_value = mock_instance

            with pytest.raises(SearchError, match="images search failed"):
                do_image_search("test image")

    def test_image_search_custom_params(self) -> None:
        """Test image search with custom params."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.images.return_value = []
            mock_ddgs.return_value = mock_instance

            do_image_search("cats", SearchParams(max_results=20, safesearch="off"))

            mock_instance.images.assert_called_once_with(
                "cats",
                max_results=20,
                region="wt-wt",
                safesearch="off",
                timelimit=None,
                backend="auto",
                page=1,
            )


# ---------------------------------------------------------------------------
# News Search
# ---------------------------------------------------------------------------


class TestNewsSearch:
    """Tests for do_news_search function."""

    def test_news_search_valid_query(self) -> None:
        """Test news search with valid parameters."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.news.return_value = [
                {"title": "News", "url": "https://example.com/news"}
            ]
            mock_ddgs.return_value = mock_instance

            results = do_news_search("test news")

            assert len(results) == 1
            mock_instance.news.assert_called_once_with(
                "test news",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
                timelimit=None,
                backend="auto",
                page=1,
            )

    def test_news_search_api_error_raises_search_error(self) -> None:
        """Test that API errors are wrapped in SearchError."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.news.side_effect = RuntimeError("API error")
            mock_ddgs.return_value = mock_instance

            with pytest.raises(SearchError, match="news search failed"):
                do_news_search("test news")


class TestNewsSafesearch:
    """Assert safesearch IS now passed to news search (behaviour inverted from old code)."""

    def test_news_search_passes_safesearch(self) -> None:
        """Test that news_search now passes safesearch to DDGS."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.news.return_value = []
            mock_ddgs.return_value = mock_instance

            do_news_search(
                "test", SearchParams(max_results=5, region="us-en", safesearch="strict")
            )

            call_kwargs = mock_instance.news.call_args[1]
            assert "safesearch" in call_kwargs
            assert call_kwargs["safesearch"] == "strict"

    def test_news_search_default_safesearch_moderate(self) -> None:
        """Test that news search uses moderate safesearch by default."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.news.return_value = []
            mock_ddgs.return_value = mock_instance

            do_news_search("test news")

            call_kwargs = mock_instance.news.call_args[1]
            assert call_kwargs["safesearch"] == "moderate"


# ---------------------------------------------------------------------------
# Video Search
# ---------------------------------------------------------------------------


class TestVideoSearch:
    """Tests for do_videos_search function."""

    def test_videos_search_valid_query(self) -> None:
        """Test video search with valid parameters."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.videos.return_value = [
                {"title": "Video", "content": "https://example.com/video"}
            ]
            mock_ddgs.return_value = mock_instance

            results = do_videos_search("test video")

            assert len(results) == 1
            mock_instance.videos.assert_called_once_with(
                "test video",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
                timelimit=None,
                backend="auto",
                page=1,
            )

    def test_videos_search_api_error_raises_search_error(self) -> None:
        """Test that API errors are wrapped in SearchError."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.videos.side_effect = RuntimeError("API error")
            mock_ddgs.return_value = mock_instance

            with pytest.raises(SearchError, match="videos search failed"):
                do_videos_search("test video")

    def test_videos_search_value_error_propagates(self) -> None:
        """Test ValueError from DDGS propagates unwrapped."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.videos.side_effect = ValueError("bad param")
            mock_ddgs.return_value = mock_instance

            with pytest.raises(ValueError, match="bad param"):
                do_videos_search("test video")

    def test_videos_search_custom_params(self) -> None:
        """Test video search with custom SearchParams."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.videos.return_value = []
            mock_ddgs.return_value = mock_instance

            do_videos_search("tutorial", SearchParams(max_results=5, timelimit="m"))

            mock_instance.videos.assert_called_once_with(
                "tutorial",
                max_results=5,
                region="wt-wt",
                safesearch="moderate",
                timelimit="m",
                backend="auto",
                page=1,
            )


# ---------------------------------------------------------------------------
# Book Search
# ---------------------------------------------------------------------------


class TestBookSearch:
    """Tests for do_books_search function."""

    def test_books_search_valid_query(self) -> None:
        """Test book search with valid parameters."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.books.return_value = [
                {"title": "Book", "author": "Author", "url": "https://example.com/book"}
            ]
            mock_ddgs.return_value = mock_instance

            results = do_books_search("python programming")

            assert len(results) == 1
            mock_instance.books.assert_called_once_with(
                "python programming",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
                timelimit=None,
                backend="auto",
                page=1,
            )

    def test_books_search_api_error_raises_search_error(self) -> None:
        """Test that API errors are wrapped in SearchError."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.books.side_effect = RuntimeError("API error")
            mock_ddgs.return_value = mock_instance

            with pytest.raises(SearchError, match="books search failed"):
                do_books_search("python programming")

    def test_books_search_value_error_propagates(self) -> None:
        """Test ValueError from DDGS propagates unwrapped."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.books.side_effect = ValueError("bad param")
            mock_ddgs.return_value = mock_instance

            with pytest.raises(ValueError, match="bad param"):
                do_books_search("python programming")

    def test_books_search_custom_params(self) -> None:
        """Test book search with custom SearchParams."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.books.return_value = []
            mock_ddgs.return_value = mock_instance

            do_books_search("history", SearchParams(max_results=3))

            mock_instance.books.assert_called_once_with(
                "history",
                max_results=3,
                region="wt-wt",
                safesearch="moderate",
                timelimit=None,
                backend="auto",
                page=1,
            )


# ---------------------------------------------------------------------------
# ValueError propagation
# ---------------------------------------------------------------------------


class TestSearchValueErrorPropagation:
    """Tests that ValueError from DDGS propagates without wrapping in SearchError."""

    def test_web_search_ddgs_value_error_propagates(self) -> None:
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.side_effect = ValueError("bad ddgs param")
            mock_ddgs.return_value = mock_instance
            with pytest.raises(ValueError, match="bad ddgs param"):
                do_web_search("test query")

    def test_image_search_ddgs_value_error_propagates(self) -> None:
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.images.side_effect = ValueError("bad ddgs param")
            mock_ddgs.return_value = mock_instance
            with pytest.raises(ValueError, match="bad ddgs param"):
                do_image_search("test query")

    def test_news_search_ddgs_value_error_propagates(self) -> None:
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.news.side_effect = ValueError("bad ddgs param")
            mock_ddgs.return_value = mock_instance
            with pytest.raises(ValueError, match="bad ddgs param"):
                do_news_search("test query")


# ---------------------------------------------------------------------------
# Query logging
# ---------------------------------------------------------------------------


class TestQueryLogging:
    """Tests for query logging behavior."""

    def test_query_hidden_by_default(self) -> None:
        """Test that query content is hidden when _with_logging is False."""
        import searchmcp.server as server

        original_value = server._with_logging
        try:
            server._with_logging = False
            with patch("searchmcp.server.DDGS") as mock_ddgs:
                mock_instance = MagicMock()
                mock_instance.text.return_value = []
                mock_ddgs.return_value = mock_instance
                with patch("searchmcp.server.log") as mock_log:
                    do_web_search("secret query")
                    mock_log.info.assert_any_call("text_search_performed")
                    # Query must NOT appear in log calls
                    log_calls = str(mock_log.info.call_args_list)
                    assert "secret query" not in log_calls
        finally:
            server._with_logging = original_value

    def test_query_logged_with_flag(self) -> None:
        """Test that query content is logged when _with_logging is True."""
        import searchmcp.server as server

        original_value = server._with_logging
        try:
            server._with_logging = True
            with patch("searchmcp.server.DDGS") as mock_ddgs:
                mock_instance = MagicMock()
                mock_instance.text.return_value = []
                mock_ddgs.return_value = mock_instance
                with patch("searchmcp.server.log") as mock_log:
                    do_web_search("visible query")
                    mock_log.info.assert_any_call(
                        "text_search_started", query="visible query"
                    )
        finally:
            server._with_logging = original_value


class TestSearchLoggingImageNews:
    """Tests for _with_logging=True path in image and news search."""

    def test_image_search_logging_enabled(self) -> None:
        """Test that image query is logged when _with_logging is True."""
        import searchmcp.server as server

        original = server._with_logging
        try:
            server._with_logging = True
            with patch("searchmcp.server.DDGS") as mock_ddgs:
                mock_instance = MagicMock()
                mock_instance.images.return_value = []
                mock_ddgs.return_value = mock_instance
                with patch("searchmcp.server.log") as mock_log:
                    do_image_search("secret image query")
                    mock_log.info.assert_any_call(
                        "images_search_started", query="secret image query"
                    )
        finally:
            server._with_logging = original

    def test_news_search_logging_enabled(self) -> None:
        """Test that news query is logged when _with_logging is True."""
        import searchmcp.server as server

        original = server._with_logging
        try:
            server._with_logging = True
            with patch("searchmcp.server.DDGS") as mock_ddgs:
                mock_instance = MagicMock()
                mock_instance.news.return_value = []
                mock_ddgs.return_value = mock_instance
                with patch("searchmcp.server.log") as mock_log:
                    do_news_search("secret news query")
                    mock_log.info.assert_any_call(
                        "news_search_started", query="secret news query"
                    )
        finally:
            server._with_logging = original

    def test_videos_search_logging_enabled(self) -> None:
        """Test that video query is logged when _with_logging is True."""
        import searchmcp.server as server

        original = server._with_logging
        try:
            server._with_logging = True
            with patch("searchmcp.server.DDGS") as mock_ddgs:
                mock_instance = MagicMock()
                mock_instance.videos.return_value = []
                mock_ddgs.return_value = mock_instance
                with patch("searchmcp.server.log") as mock_log:
                    do_videos_search("secret video query")
                    mock_log.info.assert_any_call(
                        "videos_search_started", query="secret video query"
                    )
        finally:
            server._with_logging = original

    def test_books_search_logging_enabled(self) -> None:
        """Test that book query is logged when _with_logging is True."""
        import searchmcp.server as server

        original = server._with_logging
        try:
            server._with_logging = True
            with patch("searchmcp.server.DDGS") as mock_ddgs:
                mock_instance = MagicMock()
                mock_instance.books.return_value = []
                mock_ddgs.return_value = mock_instance
                with patch("searchmcp.server.log") as mock_log:
                    do_books_search("secret book query")
                    mock_log.info.assert_any_call(
                        "books_search_started", query="secret book query"
                    )
        finally:
            server._with_logging = original

    def test_search_logging_disabled_shows_performed(self) -> None:
        """Test that _with_logging=False logs *_search_performed (no query)."""
        import searchmcp.server as server

        original = server._with_logging
        try:
            server._with_logging = False
            with patch("searchmcp.server.DDGS") as mock_ddgs:
                mock_instance = MagicMock()
                mock_instance.images.return_value = []
                mock_ddgs.return_value = mock_instance
                with patch("searchmcp.server.log") as mock_log:
                    do_image_search("cats")
                    mock_log.info.assert_any_call("images_search_performed")
        finally:
            server._with_logging = original


# ---------------------------------------------------------------------------
# Tool functions callable directly (FastMCP v3)
# ---------------------------------------------------------------------------


class TestToolFunctionsDirectly:
    """Tests leveraging FastMCP v3's callable decorators."""

    def test_web_search_tool_is_callable(self, mock_ddgs_web_results) -> None:
        """Verify decorated function is directly callable (v3 feature)."""
        results = web_search("test query")  # pyright: ignore[reportCallIssue]
        assert len(results) == 1
        assert results[0]["title"] == "Result 1"

    def test_image_search_tool_is_callable(self, mock_ddgs_image_results) -> None:
        """Verify image_search tool is callable."""
        results = image_search("test image")  # pyright: ignore[reportCallIssue]
        assert len(results) == 1
        assert results[0]["title"] == "Image 1"

    def test_news_search_tool_is_callable(self, mock_ddgs_news_results) -> None:
        """Verify news_search tool is callable."""
        results = news_search("test news")  # pyright: ignore[reportCallIssue]
        assert len(results) == 1
        assert results[0]["title"] == "News 1"

    def test_web_search_tool_with_custom_params(self, mock_ddgs_web_results) -> None:
        """Verify tool accepts custom parameters and passes them through."""
        results = web_search(  # pyright: ignore[reportCallIssue]
            "test query",
            max_results=5,
            region="us-en",
            safe_search="strict",
        )
        assert len(results) == 1
        mock_ddgs_web_results.text.assert_called_once_with(
            "test query",
            max_results=5,
            region="us-en",
            safesearch="strict",
            timelimit=None,
            backend="auto",
            page=1,
        )

    def test_videos_search_tool_is_callable(self) -> None:
        """Verify videos_search tool is callable."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.videos.return_value = [
                {"title": "Video 1", "content": "https://example.com/v1"}
            ]
            mock_ddgs.return_value = mock_instance

            results = videos_search("python tutorial")  # pyright: ignore[reportCallIssue]
            assert len(results) == 1
            assert results[0]["title"] == "Video 1"
            mock_instance.videos.assert_called_once_with(
                "python tutorial",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
                timelimit=None,
                backend="auto",
                page=1,
            )

    def test_books_search_tool_is_callable(self) -> None:
        """Verify books_search tool is callable."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.books.return_value = [
                {"title": "Book 1", "author": "Author 1"}
            ]
            mock_ddgs.return_value = mock_instance

            results = books_search("machine learning")  # pyright: ignore[reportCallIssue]
            assert len(results) == 1
            assert results[0]["title"] == "Book 1"
            mock_instance.books.assert_called_once_with(
                "machine learning",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
                timelimit=None,
                backend="auto",
                page=1,
            )


# ---------------------------------------------------------------------------
# SearchParams integration
# ---------------------------------------------------------------------------


class TestSearchParamsIntegration:
    """Tests that timelimit, backend, page wire through do_web_search."""

    def test_timelimit_wired_through(self) -> None:
        """Test timelimit parameter passes through to DDGS."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = []
            mock_ddgs.return_value = mock_instance

            do_web_search("test", SearchParams(timelimit="d"))

            mock_instance.text.assert_called_once_with(
                "test",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
                timelimit="d",
                backend="auto",
                page=1,
            )

    def test_backend_wired_through(self) -> None:
        """Test backend parameter passes through to DDGS."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = []
            mock_ddgs.return_value = mock_instance

            do_web_search("test", SearchParams(backend="google"))

            mock_instance.text.assert_called_once_with(
                "test",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
                timelimit=None,
                backend="google",
                page=1,
            )

    def test_page_wired_through(self) -> None:
        """Test page parameter passes through to DDGS."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = []
            mock_ddgs.return_value = mock_instance

            do_web_search("test", SearchParams(page=3))

            mock_instance.text.assert_called_once_with(
                "test",
                max_results=10,
                region="wt-wt",
                safesearch="moderate",
                timelimit=None,
                backend="auto",
                page=3,
            )

    def test_all_custom_params(self) -> None:
        """Test all custom params wire through together."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = []
            mock_ddgs.return_value = mock_instance

            do_web_search(
                "test",
                SearchParams(
                    max_results=25,
                    region="us-en",
                    safesearch="strict",
                    timelimit="w",
                    backend="brave",
                    page=2,
                ),
            )

            mock_instance.text.assert_called_once_with(
                "test",
                max_results=25,
                region="us-en",
                safesearch="strict",
                timelimit="w",
                backend="brave",
                page=2,
            )


# ---------------------------------------------------------------------------
# Backend validation before DDGS
# ---------------------------------------------------------------------------


class TestBackendValidationInTools:
    """Tests that invalid backends raise ValueError before DDGS is called."""

    def test_invalid_backend_for_text_raises_before_ddgs(self) -> None:
        """bing is only valid for news, not text."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            with pytest.raises(ValueError, match="bing"):
                do_web_search("test", SearchParams(backend="bing"))
            mock_ddgs.return_value.text.assert_not_called()

    def test_invalid_backend_for_images_raises_before_ddgs(self) -> None:
        """google is not valid for images."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            with pytest.raises(ValueError, match="google"):
                do_image_search("test", SearchParams(backend="google"))
            mock_ddgs.return_value.images.assert_not_called()

    def test_valid_backend_for_news(self) -> None:
        """bing is valid for news and should not raise."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.news.return_value = []
            mock_ddgs.return_value = mock_instance

            do_news_search("test", SearchParams(backend="bing"))

            mock_instance.news.assert_called_once()

    def test_invalid_backend_for_videos_raises(self) -> None:
        """google is not valid for videos."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            with pytest.raises(ValueError, match="google"):
                do_videos_search("test", SearchParams(backend="google"))
            mock_ddgs.return_value.videos.assert_not_called()

    def test_auto_backend_always_valid(self) -> None:
        """auto is always valid for any category."""
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = []
            mock_instance.news.return_value = []
            mock_instance.images.return_value = []
            mock_ddgs.return_value = mock_instance

            do_web_search("test", SearchParams(backend="auto"))
            do_news_search("test", SearchParams(backend="auto"))
            do_image_search("test", SearchParams(backend="auto"))


# ---------------------------------------------------------------------------
# DDGSException handling
# ---------------------------------------------------------------------------


class TestDDGSExceptionHandling:
    """Tests that DDGSException is wrapped in SearchError."""

    def test_ddgs_exception_wrapped_in_search_error_for_text(self) -> None:
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.side_effect = DDGSException("rate limited")
            mock_ddgs.return_value = mock_instance
            with pytest.raises(SearchError, match="text search failed"):
                do_web_search("test")

    def test_ddgs_exception_wrapped_in_search_error_for_images(self) -> None:
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.images.side_effect = DDGSException("rate limited")
            mock_ddgs.return_value = mock_instance
            with pytest.raises(SearchError, match="images search failed"):
                do_image_search("test")

    def test_ddgs_exception_wrapped_in_search_error_for_news(self) -> None:
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.news.side_effect = DDGSException("rate limited")
            mock_ddgs.return_value = mock_instance
            with pytest.raises(SearchError, match="news search failed"):
                do_news_search("test")

    def test_ddgs_exception_wrapped_in_search_error_for_videos(self) -> None:
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.videos.side_effect = DDGSException("rate limited")
            mock_ddgs.return_value = mock_instance
            with pytest.raises(SearchError, match="videos search failed"):
                do_videos_search("test")

    def test_ddgs_exception_wrapped_in_search_error_for_books(self) -> None:
        with patch("searchmcp.server.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.books.side_effect = DDGSException("rate limited")
            mock_ddgs.return_value = mock_instance
            with pytest.raises(SearchError, match="books search failed"):
                do_books_search("test")


# ---------------------------------------------------------------------------
# Integration tests - require actual Tor running
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestTorIntegration:
    """Integration tests requiring actual Tor service."""

    def test_real_tor_proxy_connection(self) -> None:
        """Test actual connection to Tor proxy."""
        result = verify_tor_proxy("socks5h://127.0.0.1:9050")
        if not result:
            pytest.skip("Tor service not available")
        assert result

    def test_real_tor_verification(self) -> None:
        """Test actual Tor exit verification."""
        if not verify_tor_proxy("socks5h://127.0.0.1:9050"):
            pytest.skip("Tor service not available")

        exit_ip = verify_tor_exit("socks5h://127.0.0.1:9050", 30)
        assert exit_ip is not None
        assert exit_ip != "unknown"


# ---------------------------------------------------------------------------
# configure() function
# ---------------------------------------------------------------------------


class TestConfigure:
    """Tests for the configure() server function."""

    def test_configure_sets_with_logging(self) -> None:
        import searchmcp.server as server

        original_logging = server._with_logging
        original_config = server._tor_config
        try:
            from searchmcp.server import configure

            configure(with_logging=True)
            assert server._with_logging is True
        finally:
            server._with_logging = original_logging
            server._tor_config = original_config
            server._ddgs_client = None

    def test_configure_with_tor_config_replaces_config(self) -> None:
        import searchmcp.server as server

        original_logging = server._with_logging
        original_config = server._tor_config
        try:
            from searchmcp.server import configure

            new_config = TorConfig(enabled=False, proxy="", timeout=10)
            result = configure(with_logging=False, tor_config=new_config)
            assert server._tor_config.enabled is False
            assert result is server._tor_config
        finally:
            server._with_logging = original_logging
            server._tor_config = original_config
            server._ddgs_client = None

    def test_configure_without_tor_config_preserves_existing(self) -> None:
        import searchmcp.server as server

        original_logging = server._with_logging
        original_config = server._tor_config
        try:
            from searchmcp.server import configure

            configure(with_logging=False, tor_config=None)
            assert server._tor_config is original_config
        finally:
            server._with_logging = original_logging
            server._tor_config = original_config
            server._ddgs_client = None

    def test_configure_invalidates_ddgs_client(self) -> None:
        import searchmcp.server as server

        original_logging = server._with_logging
        original_config = server._tor_config
        original_client = server._ddgs_client
        try:
            server._ddgs_client = MagicMock()
            from searchmcp.server import configure

            configure(with_logging=False)
            assert server._ddgs_client is None
        finally:
            server._with_logging = original_logging
            server._tor_config = original_config
            server._ddgs_client = original_client


# ---------------------------------------------------------------------------
# print_privacy_status
# ---------------------------------------------------------------------------


class TestPrintPrivacyStatus:
    """Tests for print_privacy_status output."""

    def test_print_privacy_status_output(self, capsys: pytest.CaptureFixture) -> None:
        from searchmcp.server import print_privacy_status

        print_privacy_status("socks5h://127.0.0.1:9050", "185.220.101.1")
        captured = capsys.readouterr()
        assert "Privacy Mode ENABLED" in captured.out
        assert "185.220.101.1" in captured.out
        assert "socks5h://127.0.0.1:9050" in captured.out
        assert "ISP surveillance: PROTECTED" in captured.out
