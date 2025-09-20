"""Logging configuration for YouTube Downloader."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
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
        
        # Add extra fields
        if hasattr(record, 'url'):
            log_entry['url'] = record.url
        if hasattr(record, 'filename'):
            log_entry['filename'] = record.filename
        if hasattr(record, 'progress'):
            log_entry['progress'] = record.progress
        if hasattr(record, 'download_id'):
            log_entry['download_id'] = record.download_id
            
        return json.dumps(log_entry)


class DownloadLogger:
    """Centralized logging management for the downloader."""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None, 
                 max_size: int = 10485760, backup_count: int = 5):
        """
        Initialize the logging system.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (None for console only)
            max_size: Maximum log file size in bytes
            backup_count: Number of backup files to keep
        """
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = Path(log_file) if log_file else None
        self.max_size = max_size
        self.backup_count = backup_count
        
        self.setup_logging()
    
    def setup_logging(self):
        """Set up the logging configuration."""
        # Create root logger
        self.logger = logging.getLogger('yt_downloader')
        self.logger.setLevel(self.log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation (if log_file is specified)
        if self.log_file:
            # Create log directory if it doesn't exist
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            
            file_formatter = JSONFormatter()
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # Set up yt-dlp logger to use our system
        ytdl_logger = logging.getLogger('yt-dlp')
        ytdl_logger.setLevel(logging.WARNING)  # Reduce yt-dlp verbosity
        ytdl_logger.handlers = self.logger.handlers
        
    def get_logger(self, name: str = 'yt_downloader') -> logging.Logger:
        """Get a logger instance."""
        return logging.getLogger(name)
    
    def log_download_start(self, url: str, output_dir: str):
        """Log the start of a download."""
        logger = self.get_logger()
        logger.info("Download started", extra={
            'url': url,
            'output_dir': output_dir,
            'download_id': self._generate_download_id(url)
        })
    
    def log_download_progress(self, filename: str, progress: float, speed: str):
        """Log download progress."""
        logger = self.get_logger()
        logger.debug("Download progress", extra={
            'filename': filename,
            'progress': progress,
            'speed': speed
        })
    
    def log_download_complete(self, filename: str, file_size: int):
        """Log download completion."""
        logger = self.get_logger()
        logger.info("Download completed", extra={
            'filename': filename,
            'file_size': file_size
        })
    
    def log_download_error(self, url: str, error: str):
        """Log download error."""
        logger = self.get_logger()
        logger.error("Download failed", extra={
            'url': url,
            'error': error
        })
    
    def log_playlist_info(self, playlist_title: str, video_count: int):
        """Log playlist information."""
        logger = self.get_logger()
        logger.info("Playlist information", extra={
            'playlist_title': playlist_title,
            'video_count': video_count
        })
    
    def _generate_download_id(self, url: str) -> str:
        """Generate a unique download ID."""
        import hashlib
        timestamp = str(datetime.now().timestamp())
        return hashlib.md5(f"{url}{timestamp}".encode()).hexdigest()[:8]


class YTDLPLogger:
    """Custom logger for yt-dlp integration."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def debug(self, msg):
        self.logger.debug(f"[yt-dlp] {msg}")
    
    def info(self, msg):
        self.logger.info(f"[yt-dlp] {msg}")
    
    def warning(self, msg):
        self.logger.warning(f"[yt-dlp] {msg}")
    
    def error(self, msg):
        self.logger.error(f"[yt-dlp] {msg}")


# Global logger instance
_global_logger: Optional[DownloadLogger] = None


def setup_global_logger(log_level: str = "INFO", log_file: Optional[str] = None,
                       max_size: int = 10485760, backup_count: int = 5):
    """Set up the global logger instance."""
    global _global_logger
    _global_logger = DownloadLogger(log_level, log_file, max_size, backup_count)
    return _global_logger


def get_logger(name: str = 'yt_downloader') -> logging.Logger:
    """Get a logger instance from the global logger."""
    if _global_logger is None:
        setup_global_logger()
    return _global_logger.get_logger(name)