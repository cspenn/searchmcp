"""Tests for src/searchmcp/logging_config.py — configure_logging and get_logger."""

import logging

import pytest

from searchmcp.logging_config import configure_logging, get_logger


class TestConfigureLogging:
    """Tests for configure_logging() and get_logger()."""

    # ------------------------------------------------------------------
    # 1. configure_logging() with default level runs without error
    # ------------------------------------------------------------------

    def test_configure_logging_default_level(self) -> None:
        """configure_logging() with no arguments completes without raising."""
        configure_logging()  # must not raise

    # ------------------------------------------------------------------
    # 2. configure_logging() with DEBUG level runs without error
    # ------------------------------------------------------------------

    def test_configure_logging_debug_level(self) -> None:
        """configure_logging(level=logging.DEBUG) completes without raising."""
        configure_logging(level=logging.DEBUG)  # must not raise

    # ------------------------------------------------------------------
    # 3. get_logger() returns a logger after configure_logging()
    # ------------------------------------------------------------------

    def test_get_logger_returns_object(self) -> None:
        """get_logger() returns a non-None object after configure_logging()."""
        configure_logging()
        logger = get_logger("test")
        assert logger is not None

    # ------------------------------------------------------------------
    # 4. Returned logger has required logging methods
    # ------------------------------------------------------------------

    def test_logger_has_info_method(self) -> None:
        """The returned logger exposes an 'info' method."""
        configure_logging()
        logger = get_logger("test.info")
        assert callable(getattr(logger, "info", None))

    def test_logger_has_debug_method(self) -> None:
        """The returned logger exposes a 'debug' method."""
        configure_logging()
        logger = get_logger("test.debug")
        assert callable(getattr(logger, "debug", None))

    def test_logger_has_warning_method(self) -> None:
        """The returned logger exposes a 'warning' method."""
        configure_logging()
        logger = get_logger("test.warning")
        assert callable(getattr(logger, "warning", None))

    def test_logger_has_error_method(self) -> None:
        """The returned logger exposes an 'error' method."""
        configure_logging()
        logger = get_logger("test.error")
        assert callable(getattr(logger, "error", None))

    # ------------------------------------------------------------------
    # 5. Calling log.info() with kwargs does not raise
    # ------------------------------------------------------------------

    def test_log_info_does_not_raise(self, capsys: pytest.CaptureFixture) -> None:
        """Calling logger.info('event', key='value') does not raise an exception."""
        configure_logging()
        logger = get_logger("test.call")
        logger.info("test_event", key="value")  # must not raise

    def test_log_debug_does_not_raise(self, capsys: pytest.CaptureFixture) -> None:
        """Calling logger.debug() does not raise an exception."""
        configure_logging(level=logging.DEBUG)
        logger = get_logger("test.debug_call")
        logger.debug("debug_event", extra_key=123)  # must not raise

    def test_log_warning_does_not_raise(self, capsys: pytest.CaptureFixture) -> None:
        """Calling logger.warning() does not raise an exception."""
        configure_logging()
        logger = get_logger("test.warn_call")
        logger.warning("warn_event")  # must not raise

    def test_log_error_does_not_raise(self, capsys: pytest.CaptureFixture) -> None:
        """Calling logger.error() does not raise an exception."""
        configure_logging()
        logger = get_logger("test.error_call")
        logger.error("error_event", code=500)  # must not raise

    # ------------------------------------------------------------------
    # 6. configure_logging() is idempotent (can be called multiple times)
    # ------------------------------------------------------------------

    def test_configure_logging_idempotent(self) -> None:
        """Calling configure_logging() multiple times does not raise."""
        configure_logging(level=logging.INFO)
        configure_logging(level=logging.WARNING)
        configure_logging(level=logging.DEBUG)

    # ------------------------------------------------------------------
    # 7. get_logger() with different names returns valid loggers
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "name", ["module.a", "module.b", "__main__", "searchmcp.server"]
    )
    def test_get_logger_accepts_various_names(self, name: str) -> None:
        """get_logger() accepts various name strings and returns a usable logger."""
        configure_logging()
        logger = get_logger(name)
        assert logger is not None
        assert callable(getattr(logger, "info", None))

    # ------------------------------------------------------------------
    # 8. configure_logging() accepts named logging level constants
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "level",
        [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL],
    )
    def test_configure_logging_all_standard_levels(self, level: int) -> None:
        """configure_logging() accepts all standard Python logging levels without error."""
        configure_logging(level=level)
