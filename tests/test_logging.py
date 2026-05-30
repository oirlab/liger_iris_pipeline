"""
Tests for stpipe's logging infrastructure (stpipe.log.LogConfig).
"""
import logging
import pytest

from stpipe.log import LogConfig, STPIPE_ROOT_LOGGER
from liger_iris_pipeline.normalize import NormalizeStep

from .utils import make_imager_model

PIPELINE_ROOT_LOGGER = "liger_iris_pipeline"


@pytest.fixture
def logger():
    """Create a test logger"""
    logger_name = f"{STPIPE_ROOT_LOGGER}.test"
    log = logging.getLogger(logger_name)
    yield log
    # Cleanup
    for handler in log.handlers[:]:
        handler.close()
        log.removeHandler(handler)


class TestHandlerCombinations:
    """Test all 4 handler combinations: stdout/file on/off"""

    def test_stdout_only(self, logger, capsys):
        """Test stdout handler only"""
        config = LogConfig(handler="stdout", level="INFO")
        config.apply([logger.name])

        logger.info("stdout message")
        captured = capsys.readouterr()

        assert "stdout message" in captured.out
        config.undo([logger.name])

    def test_file_only(self, logger, tmp_path):
        """Test file handler only"""
        log_file = tmp_path / "test.log"
        config = LogConfig(handler=f"file:{log_file}", level="INFO")
        config.apply([logger.name])

        logger.info("file message")
        config.undo([logger.name])

        assert "file message" in log_file.read_text()

    def test_both_handlers(self, logger, tmp_path, capsys):
        """Test both stdout and file handlers"""
        log_file = tmp_path / "test.log"
        config = LogConfig(handler=f"stdout,file:{log_file}", level="INFO")
        config.apply([logger.name])

        logger.info("both handlers")
        captured = capsys.readouterr()
        config.undo([logger.name])

        assert "both handlers" in captured.out
        assert "both handlers" in log_file.read_text()

    def test_null_handler(self, logger):
        """Test with null handler"""
        config = LogConfig(handler="null", level="INFO")
        config.apply([logger.name])

        logger.info("no handlers")  # Should not raise error
        config.undo([logger.name])


class TestLogLevels:
    """Test log levels"""

    def test_log_levels(self, logger, tmp_path):
        """Test DEBUG, INFO, WARNING, ERROR levels"""
        log_file = tmp_path / "test.log"
        config = LogConfig(handler=f"file:{log_file}", level="WARNING")
        config.apply([logger.name])

        logger.debug("debug")
        logger.info("info")
        logger.warning("warning")
        logger.error("error")
        config.undo([logger.name])

        content = log_file.read_text()
        assert "debug" not in content
        assert "info" not in content
        assert "warning" in content
        assert "error" in content


class TestContextManager:
    """Test LogConfig context manager"""

    def test_context_cleanup(self, logger, tmp_path):
        """Test context manager cleans up handlers"""
        log_file = tmp_path / "test.log"
        config = LogConfig(handler=f"file:{log_file}", level="INFO")
        initial_handlers = len(logger.handlers)

        with config.context([logger.name]):
            assert len(logger.handlers) > initial_handlers
            logger.info("in context")

        assert len(logger.handlers) == initial_handlers
        assert "in context" in log_file.read_text()


@pytest.fixture
def imager_model():
    return make_imager_model(shape=(10, 10), snr=100)


class TestStepLogging:
    """Test logging behavior when running a Step via .run()"""

    def test_step_logs_to_stdout(self, imager_model, capsys):
        """Step messages appear on stdout when configured"""
        config = LogConfig(handler="stdout", level="INFO")
        with config.context([PIPELINE_ROOT_LOGGER]):
            NormalizeStep().run(imager_model)

        captured = capsys.readouterr()
        assert "NormalizeStep" in captured.out

    def test_step_logs_to_file(self, imager_model, tmp_path):
        """Step messages are written to a log file"""
        log_file = tmp_path / "step.log"
        config = LogConfig(handler=f"file:{log_file}", level="INFO")
        with config.context([PIPELINE_ROOT_LOGGER]):
            NormalizeStep().run(imager_model)

        content = log_file.read_text()
        assert "NormalizeStep" in content

    def test_step_process_message_logged(self, imager_model, tmp_path):
        """The per-step process log message is captured"""
        log_file = tmp_path / "step.log"
        config = LogConfig(handler=f"file:{log_file}", level="INFO")
        with config.context([PIPELINE_ROOT_LOGGER]):
            NormalizeStep().run(imager_model)

        content = log_file.read_text()
        assert "Running normalize with method" in content

    def test_step_debug_suppressed_at_info_level(self, imager_model, tmp_path):
        """DEBUG messages from the step are suppressed when level=INFO"""
        log_file = tmp_path / "step.log"
        config = LogConfig(handler=f"file:{log_file}", level="INFO")
        with config.context([PIPELINE_ROOT_LOGGER]):
            NormalizeStep().run(imager_model)

        content = log_file.read_text()
        # No DEBUG-level records should appear
        assert "DEBUG" not in content
