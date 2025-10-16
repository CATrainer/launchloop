"""
Structured logging utility for production
"""
import logging
import sys
from typing import Any, Dict
from app.config import settings


class StructuredLogger:
    """Custom logger with structured output"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _format_extra(self, extra: Dict[str, Any] = None) -> str:
        """Format extra context data"""
        if not extra:
            return ""
        return " | " + " | ".join(f"{k}={v}" for k, v in extra.items())
    
    def debug(self, message: str, extra: Dict[str, Any] = None):
        """Debug level log"""
        self.logger.debug(message + self._format_extra(extra))
    
    def info(self, message: str, extra: Dict[str, Any] = None):
        """Info level log"""
        self.logger.info(message + self._format_extra(extra))
    
    def warning(self, message: str, extra: Dict[str, Any] = None):
        """Warning level log"""
        self.logger.warning(message + self._format_extra(extra))
    
    def error(self, message: str, extra: Dict[str, Any] = None, exc_info: bool = False):
        """Error level log"""
        self.logger.error(message + self._format_extra(extra), exc_info=exc_info)
    
    def critical(self, message: str, extra: Dict[str, Any] = None, exc_info: bool = False):
        """Critical level log"""
        self.logger.critical(message + self._format_extra(extra), exc_info=exc_info)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)


# Module-level convenience loggers
api_logger = get_logger("api")
task_logger = get_logger("tasks")
service_logger = get_logger("services")
db_logger = get_logger("database")
auth_logger = get_logger("auth")
