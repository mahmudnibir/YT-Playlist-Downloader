"""Error handling and retry logic for YouTube Downloader."""

import time
import random
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
from enum import Enum
import logging
from dataclasses import dataclass


class ErrorType(Enum):
    """Classification of different error types."""
    NETWORK_ERROR = "network"
    QUOTA_EXCEEDED = "quota"
    VIDEO_UNAVAILABLE = "unavailable"
    PERMISSION_ERROR = "permission"
    DISK_FULL = "disk_full"
    FORMAT_ERROR = "format"
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_errors: Tuple[ErrorType, ...] = (
        ErrorType.NETWORK_ERROR,
        ErrorType.QUOTA_EXCEEDED,
        ErrorType.UNKNOWN
    )


class DownloadError(Exception):
    """Base exception for download-related errors."""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN, 
                 url: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.error_type = error_type
        self.url = url
        self.original_error = original_error
        self.timestamp = time.time()


class NetworkError(DownloadError):
    """Network-related download error."""
    
    def __init__(self, message: str, url: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.NETWORK_ERROR, url, original_error)


class QuotaExceededError(DownloadError):
    """API quota exceeded error."""
    
    def __init__(self, message: str, url: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.QUOTA_EXCEEDED, url, original_error)


class VideoUnavailableError(DownloadError):
    """Video is not available for download."""
    
    def __init__(self, message: str, url: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.VIDEO_UNAVAILABLE, url, original_error)


class PermissionError(DownloadError):
    """Permission-related error."""
    
    def __init__(self, message: str, url: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.PERMISSION_ERROR, url, original_error)


class DiskFullError(DownloadError):
    """Disk space insufficient error."""
    
    def __init__(self, message: str, url: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.DISK_FULL, url, original_error)


class FormatError(DownloadError):
    """Video format not available error."""
    
    def __init__(self, message: str, url: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.FORMAT_ERROR, url, original_error)


class ErrorClassifier:
    """Classifies errors from yt-dlp and other sources."""
    
    @staticmethod
    def classify_ytdlp_error(error_msg: str, url: str = "") -> DownloadError:
        """Classify a yt-dlp error message into appropriate exception type."""
        error_msg_lower = error_msg.lower()
        
        # Network-related errors
        if any(keyword in error_msg_lower for keyword in [
            'network', 'connection', 'timeout', 'unreachable', 'http error 5',
            'temporary failure', 'unable to connect', 'connection refused'
        ]):
            return NetworkError(error_msg, url)
        
        # Quota/Rate limiting
        if any(keyword in error_msg_lower for keyword in [
            'quota exceeded', 'rate limit', 'too many requests', 'http error 429'
        ]):
            return QuotaExceededError(error_msg, url)
        
        # Video unavailable
        if any(keyword in error_msg_lower for keyword in [
            'video unavailable', 'private video', 'deleted', 'not available',
            'blocked in your country', 'age-restricted', 'http error 404'
        ]):
            return VideoUnavailableError(error_msg, url)
        
        # Permission errors
        if any(keyword in error_msg_lower for keyword in [
            'permission denied', 'access denied', 'forbidden', 'http error 403'
        ]):
            return PermissionError(error_msg, url)
        
        # Disk space errors
        if any(keyword in error_msg_lower for keyword in [
            'no space left', 'disk full', 'insufficient space'
        ]):
            return DiskFullError(error_msg, url)
        
        # Format errors
        if any(keyword in error_msg_lower for keyword in [
            'no video formats found', 'format not available', 'unsupported format'
        ]):
            return FormatError(error_msg, url)
        
        # Default to unknown error
        return DownloadError(error_msg, ErrorType.UNKNOWN, url)


class RetryManager:
    """Manages retry logic with exponential backoff."""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.logger = logging.getLogger(__name__)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Add random jitter ±25%
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def should_retry(self, error: DownloadError, attempt: int) -> bool:
        """Determine if an error should be retried."""
        if attempt >= self.config.max_attempts:
            return False
        
        return error.error_type in self.config.retryable_errors
    
    def retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with retry logic."""
        last_error = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                return func(*args, **kwargs)
                
            except DownloadError as e:
                last_error = e
                self.logger.warning(
                    f"Attempt {attempt}/{self.config.max_attempts} failed: {e}",
                    extra={'error_type': e.error_type.value, 'url': e.url}
                )
                
                if not self.should_retry(e, attempt):
                    self.logger.error(f"Giving up after {attempt} attempts")
                    raise e
                
                if attempt < self.config.max_attempts:
                    delay = self.calculate_delay(attempt)
                    self.logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    
            except Exception as e:
                # Convert unknown exceptions to DownloadError
                classified_error = ErrorClassifier.classify_ytdlp_error(str(e))
                classified_error.original_error = e
                last_error = classified_error
                
                self.logger.warning(
                    f"Attempt {attempt}/{self.config.max_attempts} failed with unexpected error: {e}",
                    extra={'error_type': classified_error.error_type.value}
                )
                
                if not self.should_retry(classified_error, attempt):
                    raise classified_error
                
                if attempt < self.config.max_attempts:
                    delay = self.calculate_delay(attempt)
                    self.logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
        
        # If we get here, all attempts failed
        raise last_error


def with_retry(retry_config: Optional[RetryConfig] = None):
    """Decorator to add retry functionality to a function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_manager = RetryManager(retry_config)
            return retry_manager.retry(func, *args, **kwargs)
        return wrapper
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for handling repeated failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
        self.logger = logging.getLogger(__name__)
    
    def can_execute(self) -> bool:
        """Check if execution is allowed based on circuit breaker state."""
        if self.state == 'closed':
            return True
        
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'half-open'
                self.logger.info("Circuit breaker transitioning to half-open")
                return True
            return False
        
        # half-open state
        return True
    
    def record_success(self):
        """Record a successful execution."""
        if self.state == 'half-open':
            self.state = 'closed'
            self.failure_count = 0
            self.logger.info("Circuit breaker closed - service recovered")
    
    def record_failure(self):
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != 'open':
                self.state = 'open'
                self.logger.warning(f"Circuit breaker opened due to {self.failure_count} failures")


class GracefulShutdown:
    """Handles graceful shutdown of download operations."""
    
    def __init__(self):
        self.shutdown_requested = False
        self.active_downloads = set()
        self.logger = logging.getLogger(__name__)
    
    def request_shutdown(self):
        """Request a graceful shutdown."""
        self.shutdown_requested = True
        self.logger.info("Graceful shutdown requested")
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self.shutdown_requested
    
    def register_download(self, download_id: str):
        """Register an active download."""
        self.active_downloads.add(download_id)
    
    def unregister_download(self, download_id: str):
        """Unregister a completed download."""
        self.active_downloads.discard(download_id)
    
    def wait_for_completion(self, timeout: int = 300):
        """Wait for all active downloads to complete."""
        start_time = time.time()
        
        while self.active_downloads and (time.time() - start_time) < timeout:
            self.logger.info(f"Waiting for {len(self.active_downloads)} downloads to complete...")
            time.sleep(5)
        
        if self.active_downloads:
            self.logger.warning(f"Timeout reached. {len(self.active_downloads)} downloads still active.")
        else:
            self.logger.info("All downloads completed successfully.")