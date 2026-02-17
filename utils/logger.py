"""
Centralized logging configuration for the Multi-Agent Document Analysis System.
Provides structured logging with file and console output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from config.settings import settings


class SystemLogger:
    """Centralized logger for the system."""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name.
        
        Args:
            name: Logger name (typically __name__ of the module)
            
        Returns:
            Configured logger instance
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        
        # Only configure if not already configured
        if not logger.handlers:
            # Get configuration
            log_level = settings.get('logging.level', 'INFO')
            log_format = settings.get('logging.format', 
                                     '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            log_file = settings.get('logging.file', 'logs/system.log')
            
            # Set level
            logger.setLevel(getattr(logging, log_level))
            
            # Create formatter
            formatter = logging.Formatter(log_format)
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level))
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, log_level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Prevent propagation to root logger
            logger.propagate = False
        
        cls._loggers[name] = logger
        return logger


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger.
    
    Args:
        name: Logger name (use __name__)
        
    Returns:
        Configured logger instance
    """
    return SystemLogger.get_logger(name)
