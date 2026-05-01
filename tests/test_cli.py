"""Tests for the Typer CLI in searchmcp.cli."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from searchmcp.cli import app, startup_privacy_check, _apply_config, _display_results
from searchmcp.server import TorConfig


# ---------------------------------------------------------------------------
# 1. TestCLIHelp
# ---------------------------------------------------------------------------


class TestCLIHelp:
    """Tests for CLI help output and subcommand discovery."""

    def test_help_shows_subcommands(self):
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "serve" in result.output
        assert "web" in result.output
        assert "news" in result.output
        assert "images" in result.output
        assert "videos" in result.output
        assert "books" in result.output

    @pytest.mark.parametrize(
        "subcommand", ["serve", "web", "news", "images", "videos", "books"]
    )
    def test_subcommand_help(self, subcommand):
        runner = CliRunner()
        result = runner.invoke(app, [subcommand, "--help"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# 2. TestServeSubcommand
# ---------------------------------------------------------------------------


class TestServeSubcommand:
    """Tests for the 'serve' subcommand."""

    def test_serve_runs_mcp(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_serve") as mock_run_serve:
            result = runner.invoke(app, ["serve"])
            assert result.exit_code == 0
            mock_run_serve.assert_called_once_with(
                disable_privacy=False, with_logging=False
            )

    def test_serve_disable_privacy(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_serve") as mock_run_serve:
            result = runner.invoke(app, ["serve", "--disable-privacy"])
            assert result.exit_code == 0
            mock_run_serve.assert_called_once_with(
                disable_privacy=True, with_logging=False
            )

    def test_serve_with_logging(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_serve") as mock_run_serve:
            result = runner.invoke(app, ["serve", "--with-logging"])
            assert result.exit_code == 0
            mock_run_serve.assert_called_once_with(
                disable_privacy=False, with_logging=True
            )

    def test_serve_both_flags(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_serve") as mock_run_serve:
            result = runner.invoke(
                app, ["serve", "--disable-privacy", "--with-logging"]
            )
            assert result.exit_code == 0
            mock_run_serve.assert_called_once_with(
                disable_privacy=True, with_logging=True
            )


# ---------------------------------------------------------------------------
# 3. TestNoSubcommand
# ---------------------------------------------------------------------------


class TestNoSubcommand:
    """Tests for running searchmcp with no subcommand (defaults to serve)."""

    def test_no_subcommand_defaults_to_serve(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_serve") as mock_run_serve:
            runner.invoke(app, [])
            mock_run_serve.assert_called_once_with(
                disable_privacy=False, with_logging=False
            )

    def test_no_subcommand_disable_privacy(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_serve") as mock_run_serve:
            runner.invoke(app, ["--disable-privacy"])
            mock_run_serve.assert_called_once_with(
                disable_privacy=True, with_logging=False
            )

    def test_no_subcommand_with_logging(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_serve") as mock_run_serve:
            runner.invoke(app, ["--with-logging"])
            mock_run_serve.assert_called_once_with(
                disable_privacy=False, with_logging=True
            )


# ---------------------------------------------------------------------------
# 4. TestWebSubcommand
# ---------------------------------------------------------------------------


class TestWebSubcommand:
    """Tests for the 'web' subcommand."""

    def test_web_search_basic(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_search") as mock_run:
            result = runner.invoke(app, ["web", "test query"])
            assert result.exit_code == 0
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args.args[0] == "web"
            assert call_args.args[1] == "test query"

    def test_web_search_json_output(self):
        runner = CliRunner()
        mock_results = [
            {"title": "Test", "href": "https://example.com", "body": "body"}
        ]
        with patch("searchmcp.cli.startup_privacy_check"):
            with patch("searchmcp.cli._apply_config") as mock_config:
                mock_config.return_value = TorConfig(
                    enabled=False, proxy="", timeout=30
                )
                with patch("searchmcp.server.DDGS") as mock_ddgs:
                    mock_instance = MagicMock()
                    mock_instance.text.return_value = mock_results
                    mock_ddgs.return_value = mock_instance
                    result = runner.invoke(
                        app, ["web", "test query", "--json", "--disable-privacy"]
                    )
                    assert result.exit_code == 0
                    data = json.loads(result.output)
                    assert data[0]["title"] == "Test"

    def test_web_empty_query_exits_with_error(self):
        runner = CliRunner()
        with patch("searchmcp.cli.startup_privacy_check"):
            with patch("searchmcp.cli._apply_config") as mock_config:
                mock_config.return_value = TorConfig(
                    enabled=False, proxy="", timeout=30
                )
                result = runner.invoke(app, ["web", "", "--disable-privacy"])
                assert result.exit_code == 1

    def test_web_search_max_results_and_safesearch(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_search") as mock_run:
            result = runner.invoke(
                app, ["web", "test", "--max-results", "5", "--safesearch", "strict"]
            )
            assert result.exit_code == 0
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            # Positional args: category, query, disable_privacy, with_logging,
            #                  max_results, region, safe_search, timelimit, backend, page, as_json
            assert call_args.args[4] == 5  # max_results
            assert call_args.args[6] == "strict"  # safe_search

    def test_web_search_disable_privacy_flag(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_search") as mock_run:
            result = runner.invoke(app, ["web", "test", "--disable-privacy"])
            assert result.exit_code == 0
            call_args = mock_run.call_args
            # disable_privacy is args[2]
            assert call_args.args[2] is True

    def test_web_search_with_logging_flag(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_search") as mock_run:
            result = runner.invoke(app, ["web", "test", "--with-logging"])
            assert result.exit_code == 0
            call_args = mock_run.call_args
            # with_logging is args[3]
            assert call_args.args[3] is True


# ---------------------------------------------------------------------------
# 5. TestNewsSubcommand
# ---------------------------------------------------------------------------


class TestNewsSubcommand:
    """Tests for the 'news' subcommand."""

    def test_news_search_basic(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_search") as mock_run:
            result = runner.invoke(app, ["news", "breaking news"])
            assert result.exit_code == 0
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args.args[0] == "news"
            assert call_args.args[1] == "breaking news"

    def test_news_empty_query_exits_with_error(self):
        runner = CliRunner()
        with patch("searchmcp.cli.startup_privacy_check"):
            with patch("searchmcp.cli._apply_config") as mock_config:
                mock_config.return_value = TorConfig(
                    enabled=False, proxy="", timeout=30
                )
                result = runner.invoke(app, ["news", "", "--disable-privacy"])
                assert result.exit_code == 1

    def test_news_search_json_output(self):
        runner = CliRunner()
        mock_results = [
            {
                "title": "News Title",
                "url": "https://example.com/news",
                "body": "news body",
            }
        ]
        with patch("searchmcp.cli.startup_privacy_check"):
            with patch("searchmcp.cli._apply_config") as mock_config:
                mock_config.return_value = TorConfig(
                    enabled=False, proxy="", timeout=30
                )
                with patch("searchmcp.server.DDGS") as mock_ddgs:
                    mock_instance = MagicMock()
                    mock_instance.news.return_value = mock_results
                    mock_ddgs.return_value = mock_instance
                    result = runner.invoke(
                        app, ["news", "test", "--json", "--disable-privacy"]
                    )
                    assert result.exit_code == 0
                    data = json.loads(result.output)
                    assert data[0]["title"] == "News Title"


# ---------------------------------------------------------------------------
# 6. TestImagesSubcommand
# ---------------------------------------------------------------------------


class TestImagesSubcommand:
    """Tests for the 'images' subcommand."""

    def test_images_search_basic(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_search") as mock_run:
            result = runner.invoke(app, ["images", "cute cats"])
            assert result.exit_code == 0
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args.args[0] == "images"
            assert call_args.args[1] == "cute cats"

    def test_images_empty_query_exits_with_error(self):
        runner = CliRunner()
        with patch("searchmcp.cli.startup_privacy_check"):
            with patch("searchmcp.cli._apply_config") as mock_config:
                mock_config.return_value = TorConfig(
                    enabled=False, proxy="", timeout=30
                )
                result = runner.invoke(app, ["images", "", "--disable-privacy"])
                assert result.exit_code == 1

    def test_images_search_json_output(self):
        runner = CliRunner()
        mock_results = [
            {
                "title": "Image 1",
                "image": "https://example.com/img.jpg",
                "thumbnail": "https://example.com/thumb.jpg",
            }
        ]
        with patch("searchmcp.cli.startup_privacy_check"):
            with patch("searchmcp.cli._apply_config") as mock_config:
                mock_config.return_value = TorConfig(
                    enabled=False, proxy="", timeout=30
                )
                with patch("searchmcp.server.DDGS") as mock_ddgs:
                    mock_instance = MagicMock()
                    mock_instance.images.return_value = mock_results
                    mock_ddgs.return_value = mock_instance
                    result = runner.invoke(
                        app, ["images", "test", "--json", "--disable-privacy"]
                    )
                    assert result.exit_code == 0
                    data = json.loads(result.output)
                    assert data[0]["title"] == "Image 1"


# ---------------------------------------------------------------------------
# 7. TestVideosSubcommand
# ---------------------------------------------------------------------------


class TestVideosSubcommand:
    """Tests for the 'videos' subcommand."""

    def test_videos_search_basic(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_search") as mock_run:
            result = runner.invoke(app, ["videos", "python tutorial"])
            assert result.exit_code == 0
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args.args[0] == "videos"
            assert call_args.args[1] == "python tutorial"

    def test_videos_empty_query_exits_with_error(self):
        runner = CliRunner()
        with patch("searchmcp.cli.startup_privacy_check"):
            with patch("searchmcp.cli._apply_config") as mock_config:
                mock_config.return_value = TorConfig(
                    enabled=False, proxy="", timeout=30
                )
                result = runner.invoke(app, ["videos", "", "--disable-privacy"])
                assert result.exit_code == 1

    def test_videos_search_json_output(self):
        runner = CliRunner()
        mock_results = [
            {
                "title": "Video 1",
                "content": "https://example.com/v1",
                "description": "Test video",
            }
        ]
        with patch("searchmcp.cli.startup_privacy_check"):
            with patch("searchmcp.cli._apply_config") as mock_config:
                mock_config.return_value = TorConfig(
                    enabled=False, proxy="", timeout=30
                )
                with patch("searchmcp.server.DDGS") as mock_ddgs:
                    mock_instance = MagicMock()
                    mock_instance.videos.return_value = mock_results
                    mock_ddgs.return_value = mock_instance
                    result = runner.invoke(
                        app, ["videos", "test", "--json", "--disable-privacy"]
                    )
                    assert result.exit_code == 0
                    data = json.loads(result.output)
                    assert data[0]["title"] == "Video 1"


# ---------------------------------------------------------------------------
# 8. TestBooksSubcommand
# ---------------------------------------------------------------------------


class TestBooksSubcommand:
    """Tests for the 'books' subcommand."""

    def test_books_search_basic(self):
        runner = CliRunner()
        with patch("searchmcp.cli._run_search") as mock_run:
            result = runner.invoke(app, ["books", "python programming"])
            assert result.exit_code == 0
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args.args[0] == "books"
            assert call_args.args[1] == "python programming"

    def test_books_empty_query_exits_with_error(self):
        runner = CliRunner()
        with patch("searchmcp.cli.startup_privacy_check"):
            with patch("searchmcp.cli._apply_config") as mock_config:
                mock_config.return_value = TorConfig(
                    enabled=False, proxy="", timeout=30
                )
                result = runner.invoke(app, ["books", "", "--disable-privacy"])
                assert result.exit_code == 1

    def test_books_search_json_output(self):
        runner = CliRunner()
        mock_results = [
            {
                "title": "Book 1",
                "author": "Author 1",
                "url": "https://example.com/book1",
            }
        ]
        with patch("searchmcp.cli.startup_privacy_check"):
            with patch("searchmcp.cli._apply_config") as mock_config:
                mock_config.return_value = TorConfig(
                    enabled=False, proxy="", timeout=30
                )
                with patch("searchmcp.server.DDGS") as mock_ddgs:
                    mock_instance = MagicMock()
                    mock_instance.books.return_value = mock_results
                    mock_ddgs.return_value = mock_instance
                    result = runner.invoke(
                        app, ["books", "test", "--json", "--disable-privacy"]
                    )
                    assert result.exit_code == 0
                    data = json.loads(result.output)
                    assert data[0]["title"] == "Book 1"


# ---------------------------------------------------------------------------
# 9. TestStartupPrivacyCheck
# ---------------------------------------------------------------------------


class TestStartupPrivacyCheck:
    """Tests for the startup_privacy_check() function."""

    def test_disable_privacy_warns_on_stderr(self, capfd):
        config = TorConfig(enabled=False, proxy="", timeout=30)
        with patch("searchmcp.cli.check_privileges"):
            startup_privacy_check(True, config)
        captured = capfd.readouterr()
        assert (
            "Privacy mode disabled" in captured.err
            or "Privacy mode disabled" in captured.out
        )

    def test_disable_privacy_returns_early(self):
        """When disable_privacy=True, verify_tor_proxy is never called."""
        config = TorConfig(enabled=False, proxy="", timeout=30)
        with patch("searchmcp.cli.check_privileges"):
            with patch("searchmcp.cli.verify_tor_proxy") as mock_verify:
                startup_privacy_check(True, config)
                mock_verify.assert_not_called()

    def test_tor_proxy_unavailable_exits(self):
        config = TorConfig(enabled=True, proxy="socks5h://127.0.0.1:9050", timeout=30)
        with patch("searchmcp.cli.check_privileges"):
            with patch("searchmcp.cli.verify_tor_proxy", return_value=False):
                with pytest.raises(SystemExit) as exc_info:
                    startup_privacy_check(False, config)
                assert "Cannot connect to Tor proxy" in str(exc_info.value)

    def test_successful_tor_verification(self):
        config = TorConfig(enabled=True, proxy="socks5h://127.0.0.1:9050", timeout=30)
        with patch("searchmcp.cli.check_privileges"):
            with patch("searchmcp.cli.verify_tor_proxy", return_value=True):
                with patch(
                    "searchmcp.cli.verify_tor_exit", return_value="185.220.101.1"
                ):
                    with patch("searchmcp.cli.print_privacy_status") as mock_status:
                        startup_privacy_check(False, config)
                        mock_status.assert_called_once_with(
                            "socks5h://127.0.0.1:9050", "185.220.101.1"
                        )

    def test_check_privileges_always_called(self):
        """check_privileges() is called regardless of disable_privacy value."""
        config = TorConfig(enabled=False, proxy="", timeout=30)
        with patch("searchmcp.cli.check_privileges") as mock_priv:
            startup_privacy_check(True, config)
            mock_priv.assert_called_once()


# ---------------------------------------------------------------------------
# 10. TestApplyConfig
# ---------------------------------------------------------------------------


class TestApplyConfig:
    """Tests for _apply_config()."""

    def test_apply_config_with_privacy_disabled(self):
        with patch("searchmcp.cli.configure") as mock_configure:
            mock_configure.return_value = TorConfig(enabled=False, proxy="", timeout=30)
            _apply_config(disable_privacy=True, with_logging=False)
            call_args = mock_configure.call_args
            assert call_args.kwargs["tor_config"].enabled is False
            assert call_args.kwargs["with_logging"] is False

    def test_apply_config_with_privacy_enabled(self):
        with patch("searchmcp.cli.configure") as mock_configure:
            mock_configure.return_value = TorConfig(
                enabled=True, proxy="socks5h://127.0.0.1:9050", timeout=30
            )
            _apply_config(disable_privacy=False, with_logging=True)
            call_args = mock_configure.call_args
            assert call_args.kwargs["tor_config"] is None
            assert call_args.kwargs["with_logging"] is True

    def test_apply_config_returns_tor_config(self):
        expected = TorConfig(enabled=False, proxy="", timeout=30)
        with patch("searchmcp.cli.configure") as mock_configure:
            mock_configure.return_value = expected
            result = _apply_config(disable_privacy=True, with_logging=False)
            assert result is expected

    def test_apply_config_privacy_disabled_passes_disabled_tor_config(self):
        """When disable_privacy=True, tor_config.enabled must be False."""
        with patch("searchmcp.cli.configure") as mock_configure:
            mock_configure.return_value = TorConfig(enabled=False, proxy="", timeout=30)
            _apply_config(disable_privacy=True, with_logging=False)
            call_args = mock_configure.call_args
            assert call_args.kwargs["tor_config"] is not None
            assert call_args.kwargs["tor_config"].enabled is False
            assert call_args.kwargs["tor_config"].proxy == ""


# ---------------------------------------------------------------------------
# 11. TestDisplayResults
# ---------------------------------------------------------------------------


class TestDisplayResults:
    """Tests for _display_results()."""

    def test_display_json(self, capsys):
        _display_results([{"key": "value"}], as_json=True)
        out = capsys.readouterr().out
        assert json.loads(out) == [{"key": "value"}]

    def test_display_no_results(self, capsys):
        _display_results([], as_json=False)
        assert "No results" in capsys.readouterr().out

    def test_display_table_does_not_crash(self):
        # Just verify it doesn't raise
        _display_results(
            [{"title": "Test", "url": "http://example.com"}], as_json=False
        )

    def test_display_json_empty_list(self, capsys):
        _display_results([], as_json=True)
        out = capsys.readouterr().out
        assert json.loads(out) == []

    def test_display_json_multiple_results(self, capsys):
        results = [
            {"title": "A", "href": "https://a.com"},
            {"title": "B", "href": "https://b.com"},
        ]
        _display_results(results, as_json=True)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert len(parsed) == 2
        assert parsed[1]["title"] == "B"


# ---------------------------------------------------------------------------
# 12. TestMain
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for the main() entry point shim."""

    def test_main_calls_app(self):
        from searchmcp.main import main

        with patch("searchmcp.main.app") as mock_app:
            main()
            mock_app.assert_called_once()


# ---------------------------------------------------------------------------
# 13. TestRunServeBody — covers _run_serve actual body (lines 125-127)
# ---------------------------------------------------------------------------


class TestRunServeBody:
    """Tests for the _run_serve helper body (not mocked out)."""

    def test_run_serve_calls_mcp_run(self) -> None:
        from searchmcp.cli import _run_serve

        with patch("searchmcp.cli._apply_config") as mock_config:
            mock_config.return_value = MagicMock()
            with patch("searchmcp.cli.startup_privacy_check"):
                with patch("searchmcp.cli.mcp") as mock_mcp:
                    _run_serve(disable_privacy=True, with_logging=False)
                    mock_mcp.run.assert_called_once()


# ---------------------------------------------------------------------------
# 14. TestSearchErrorBranch — covers SearchError handler in _run_search (lines 193-195)
# ---------------------------------------------------------------------------


class TestSearchErrorBranch:
    """Tests that SearchError from do_*_search is caught and returns exit code 1."""

    def test_web_search_error_exits_1(self) -> None:
        from typer.testing import CliRunner
        from searchmcp.cli import app

        runner = CliRunner()
        with patch("searchmcp.cli._apply_config") as mock_cfg:
            mock_cfg.return_value = MagicMock()
            with patch("searchmcp.cli.startup_privacy_check"):
                with patch("searchmcp.server.DDGS") as mock_ddgs:
                    from searchmcp.server import SearchError

                    mock_instance = MagicMock()
                    mock_instance.text.side_effect = SearchError("backend down")
                    mock_ddgs.return_value = mock_instance
                    result = runner.invoke(
                        app, ["web", "test query", "--disable-privacy"]
                    )
                    assert result.exit_code == 1
