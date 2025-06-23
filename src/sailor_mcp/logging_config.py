"""Logging configuration for Sailor MCP"""
import logging
import os
import sys
from typing import Optional


def setup_logging(
    name: Optional[str] = None,
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration
    
    Args:
        name: Logger name (defaults to 'sailor_mcp')
        level: Logging level (defaults to env var SAILOR_LOG_LEVEL or INFO)
        log_file: Optional log file path (defaults to env var SAILOR_LOG_FILE)
    
    Returns:
        Configured logger instance
    """
    # Get configuration from environment or parameters
    logger_name = name or "sailor_mcp"
    log_level = level or os.getenv("SAILOR_LOG_LEVEL", "INFO")
    log_file_path = log_file or os.getenv("SAILOR_LOG_FILE")
    
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file_path:
        try:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.info(f"Logging to file: {log_file_path}")
        except Exception as e:
            logger.error(f"Failed to create log file handler: {e}")
    
    # Log initial configuration
    logger.info(f"Sailor MCP logging initialized - Level: {log_level}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the module name
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"sailor_mcp.{name}")


# Configure default logging on import
setup_logging()