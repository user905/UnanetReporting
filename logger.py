"""
Logging configuration for Unanet to Dataverse Integration
Logs to both console and file
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from config import PROJECT_DIR


def setup_logger():
    """
    Set up logging to both console and file
    Creates logs directory and dated log files
    """
    # Create logs directory
    logs_dir = PROJECT_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"unanet_sync_{timestamp}.log"

    # Create logger
    logger = logging.getLogger("UnanetSync")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter('%(message)s')

    # File handler (detailed)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Console handler (simple)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Log file: {log_file}")

    return logger


def get_logger():
    """Get the configured logger instance"""
    return logging.getLogger("UnanetSync")
