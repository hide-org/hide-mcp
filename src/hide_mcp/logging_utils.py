import os
import sys
import logging
from pathlib import Path
from datetime import datetime


def get_log_directory() -> Path:
    """
    Get the appropriate log directory based on the operating system.
    Returns a Path object pointing to the log directory.
    """
    if sys.platform == "darwin":  # macOS
        base_dir = Path.home() / "Library/Application Support/hide-mcp"
    elif sys.platform == "win32":  # Windows
        base_dir = Path(os.getenv("APPDATA")) / "hide-mcp"
    else:  # Linux and others
        base_dir = Path.home() / ".local/share/hide-mcp"

    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(level=None):
    """
    Setup logging configuration with both console and file handlers.
    The file handler creates a new log file for each day.

    Args:
        level: Optional logging level. If not provided, will check HIDE_MCP_LOG_LEVEL
              environment variable and default to INFO if not set
    """
    # Get log level from env if not explicitly provided
    if level is None:
        level_name = os.getenv("HIDE_MCP_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)

    log_dir = get_log_directory()
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"hide-mcp-{today}.log"

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Setup file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log startup message
    root_logger.info(f"Logging initialized. Log file: {log_file}")

