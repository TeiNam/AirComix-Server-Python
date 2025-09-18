"""Logging configuration for the comix server."""

import logging
import sys
from typing import Dict, Any

from app.models.config import settings


def setup_logging() -> None:
    """Configure logging for the application."""
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, settings.log_level))
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    configure_logger_levels()
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.log_level}")
    if settings.debug_mode:
        logger.debug("Debug mode enabled")


def configure_logger_levels() -> None:
    """Configure specific logger levels."""
    
    # Application loggers
    logging.getLogger("app").setLevel(getattr(logging, settings.log_level))
    
    # Third-party library loggers
    if settings.debug_mode:
        # In debug mode, show more details from libraries
        logging.getLogger("uvicorn").setLevel(logging.DEBUG)
        logging.getLogger("fastapi").setLevel(logging.DEBUG)
    else:
        # In production, reduce noise from libraries
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.INFO)
        logging.getLogger("fastapi").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def log_request_info(method: str, path: str, **kwargs: Any) -> None:
    """Log request information."""
    logger = get_logger("app.requests")
    extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"{method} {path} {extra_info}".strip())


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """Log error with context information."""
    logger = get_logger("app.errors")
    context_str = ""
    if context:
        context_str = " - " + " ".join(f"{k}={v}" for k, v in context.items())
    
    if settings.debug_mode:
        logger.exception(f"Error occurred{context_str}: {error}")
    else:
        logger.error(f"Error occurred{context_str}: {error}")


def log_performance(operation: str, duration: float, **kwargs: Any) -> None:
    """Log performance metrics."""
    logger = get_logger("app.performance")
    extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"Performance: {operation} took {duration:.3f}s {extra_info}".strip())