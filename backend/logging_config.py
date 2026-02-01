"""
DisasterAI Backend - Logging Configuration
Sets up comprehensive logging for the application
"""

import logging
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path
import json

from config import settings


class JSONFormatter(logging.Formatter):
    """Custom formatter to output logs in JSON format"""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'task_id'):
            log_entry['task_id'] = record.task_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id

        return json.dumps(log_entry)


def setup_logging():
    """Setup logging configuration for the application"""

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    if settings.ENVIRONMENT == "production":
        # In production, use JSON format
        console_handler.setFormatter(JSONFormatter())
    else:
        # In development, use readable format
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

    root_logger.addHandler(console_handler)

    # File handler for all logs
    file_handler = logging.FileHandler(logs_dir / "app.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Separate error file handler
    error_handler = logging.FileHandler(logs_dir / "errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)

    # Set specific loggers to appropriate levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)


def log_task_event(
    logger: logging.Logger,
    task_id: str,
    event: str,
    level: str = "INFO",
    extra_data: Optional[dict] = None
):
    """Log a task-specific event"""
    extra = {'task_id': task_id}
    if extra_data:
        extra.update(extra_data)

    log_method = getattr(logger, level.lower())
    log_method(event, extra=extra)


def log_api_call(
    logger: logging.Logger,
    endpoint: str,
    method: str,
    duration_ms: float,
    status_code: int,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Log an API call"""
    extra = {
        'endpoint': endpoint,
        'method': method,
        'duration_ms': duration_ms,
        'status_code': status_code
    }
    if user_agent:
        extra['user_agent'] = user_agent
    if ip_address:
        extra['ip_address'] = ip_address

    logger.info(f"API call to {endpoint}", extra=extra)


# Initialize logging when module is imported
setup_logging()