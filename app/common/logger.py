import logging
import sys
from pathlib import Path
from typing import Optional


class AppLogger:
    """Centralized logging configuration for the application."""
    
    _instance: Optional['AppLogger'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'AppLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_default_logging()
            AppLogger._initialized = True
    
    def _setup_default_logging(self):
        """Setup default logging configuration."""
        self.setup_logging(verbose=False, log_file="app.log")
    
    def setup_logging(self, verbose: bool = False, log_file: str = "app.log") -> logging.Logger:
        """
        Configure centralized logging for the application.
        
        Args:
            verbose: Enable debug level logging
            log_file: Name of the log file
        
        Returns:
            Configured root logger instance
        """
        log_level = logging.DEBUG if verbose else logging.INFO
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_path = log_dir / log_file
        
        # Configure logging format
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Clear existing handlers to avoid duplicates
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # File handler
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always log debug to file
        file_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        return root_logger
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger instance for the specified module.
        
        Args:
            name: Module name (typically __name__)
        
        Returns:
            Logger instance
        """
        # Ensure AppLogger is initialized
        AppLogger()
        return logging.getLogger(name)