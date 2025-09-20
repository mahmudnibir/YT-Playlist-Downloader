"""Security and validation utilities for YouTube Downloader."""

import re
import time
import hashlib
import hmac
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    max_file_size_gb: float = 10.0
    max_downloads_per_hour: int = 100
    allowed_domains: List[str] = None
    blocked_domains: List[str] = None
    max_concurrent_ips: int = 5
    enable_rate_limiting: bool = True
    enable_url_validation: bool = True
    enable_path_sanitization: bool = True
    quarantine_suspicious_files: bool = True
    
    def __post_init__(self):
        if self.allowed_domains is None:
            self.allowed_domains = [
                'youtube.com', 'youtu.be', 'm.youtube.com',
                'music.youtube.com', 'www.youtube.com'
            ]
        if self.blocked_domains is None:
            self.blocked_domains = []


class URLValidator:
    """Validates and sanitizes YouTube URLs."""
    
    YOUTUBE_URL_PATTERNS = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'^https?://youtu\.be/[\w-]+',
        r'^https?://(www\.)?youtube\.com/c/[\w-]+',
        r'^https?://(www\.)?youtube\.com/channel/[\w-]+',
        r'^https?://(www\.)?youtube\.com/user/[\w-]+',
        r'^https?://music\.youtube\.com/',
    ]
    
    def __init__(self, security_config: SecurityConfig):
        self.config = security_config
        self.logger = logging.getLogger(__name__)
    
    def is_valid_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL."""
        if not self.config.enable_url_validation:
            return True
        
        try:
            parsed = urlparse(url)
            
            # Check domain
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            
            if domain not in self.config.allowed_domains:
                self.logger.warning(f"Domain not in allowed list: {domain}")
                return False
            
            if domain in self.config.blocked_domains:
                self.logger.warning(f"Domain is blocked: {domain}")
                return False
            
            # Check URL pattern
            for pattern in self.YOUTUBE_URL_PATTERNS:
                if re.match(pattern, url, re.IGNORECASE):
                    return True
            
            self.logger.warning(f"URL doesn't match valid YouTube patterns: {url}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating URL {url}: {e}")
            return False
    
    def sanitize_url(self, url: str) -> str:
        """Sanitize and normalize a YouTube URL."""
        try:
            parsed = urlparse(url)
            
            # Remove potentially harmful parameters
            safe_params = ['v', 'list', 't', 'index', 'start', 'end']
            query_params = parse_qs(parsed.query)
            sanitized_params = {k: v for k, v in query_params.items() if k in safe_params}
            
            # Rebuild query string
            query_parts = []
            for key, values in sanitized_params.items():
                for value in values:
                    query_parts.append(f"{key}={value}")
            
            sanitized_query = "&".join(query_parts)
            
            # Rebuild URL
            sanitized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if sanitized_query:
                sanitized_url += f"?{sanitized_query}"
            
            return sanitized_url
            
        except Exception as e:
            self.logger.error(f"Error sanitizing URL {url}: {e}")
            return url
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        try:
            parsed = urlparse(url)
            
            if 'youtu.be' in parsed.netloc:
                return parsed.path[1:]  # Remove leading slash
            
            query_params = parse_qs(parsed.query)
            return query_params.get('v', [None])[0]
            
        except Exception as e:
            self.logger.error(f"Error extracting video ID from {url}: {e}")
            return None
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from YouTube URL."""
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            return query_params.get('list', [None])[0]
            
        except Exception as e:
            self.logger.error(f"Error extracting playlist ID from {url}: {e}")
            return None


class PathSanitizer:
    """Sanitizes file paths and names for security."""
    
    # Characters that are not allowed in filenames
    FORBIDDEN_CHARS = r'<>:"/\\|?*'
    FORBIDDEN_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
        'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
        'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    def __init__(self, security_config: SecurityConfig):
        self.config = security_config
        self.logger = logging.getLogger(__name__)
    
    def sanitize_filename(self, filename: str, max_length: int = 255) -> str:
        """Sanitize a filename for safe filesystem storage."""
        if not self.config.enable_path_sanitization:
            return filename
        
        try:
            # Remove or replace forbidden characters
            sanitized = filename
            for char in self.FORBIDDEN_CHARS:
                sanitized = sanitized.replace(char, '_')
            
            # Remove leading/trailing whitespace and dots
            sanitized = sanitized.strip(' .')
            
            # Check for forbidden names
            name_part = sanitized.split('.')[0].upper()
            if name_part in self.FORBIDDEN_NAMES:
                sanitized = f"file_{sanitized}"
            
            # Truncate if too long
            if len(sanitized) > max_length:
                name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
                max_name_len = max_length - len(ext) - 1 if ext else max_length
                sanitized = name[:max_name_len] + (f".{ext}" if ext else "")
            
            # Ensure it's not empty
            if not sanitized:
                sanitized = "unnamed_file"
            
            return sanitized
            
        except Exception as e:
            self.logger.error(f"Error sanitizing filename {filename}: {e}")
            return "sanitized_file"
    
    def sanitize_path(self, path: str, base_path: Optional[str] = None) -> str:
        """Sanitize a complete file path."""
        try:
            path_obj = Path(path)
            
            # Sanitize each part of the path
            sanitized_parts = []
            for part in path_obj.parts:
                sanitized_parts.append(self.sanitize_filename(part))
            
            sanitized_path = Path(*sanitized_parts)
            
            # Ensure path is within base directory if specified
            if base_path:
                base_path_obj = Path(base_path).resolve()
                try:
                    sanitized_path = base_path_obj / sanitized_path
                    sanitized_path.resolve().relative_to(base_path_obj)
                except ValueError:
                    # Path tries to escape base directory
                    self.logger.warning(f"Path tries to escape base directory: {path}")
                    sanitized_path = base_path_obj / self.sanitize_filename(path_obj.name)
            
            return str(sanitized_path)
            
        except Exception as e:
            self.logger.error(f"Error sanitizing path {path}: {e}")
            return str(Path(base_path or ".") / "sanitized_file")


class RateLimiter:
    """Rate limiting functionality to prevent abuse."""
    
    def __init__(self, security_config: SecurityConfig):
        self.config = security_config
        self.requests = {}  # IP -> list of timestamps
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def is_allowed(self, identifier: str = "default") -> bool:
        """Check if request is allowed based on rate limiting."""
        if not self.config.enable_rate_limiting:
            return True
        
        current_time = time.time()
        hour_ago = current_time - 3600  # 1 hour
        
        with self.lock:
            # Clean old requests
            if identifier in self.requests:
                self.requests[identifier] = [
                    ts for ts in self.requests[identifier] if ts > hour_ago
                ]
            else:
                self.requests[identifier] = []
            
            # Check rate limit
            if len(self.requests[identifier]) >= self.config.max_downloads_per_hour:
                self.logger.warning(f"Rate limit exceeded for {identifier}")
                return False
            
            # Record this request
            self.requests[identifier].append(current_time)
            return True
    
    def get_remaining_requests(self, identifier: str = "default") -> int:
        """Get number of remaining requests for identifier."""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        with self.lock:
            if identifier not in self.requests:
                return self.config.max_downloads_per_hour
            
            # Count recent requests
            recent_requests = [
                ts for ts in self.requests[identifier] if ts > hour_ago
            ]
            
            return max(0, self.config.max_downloads_per_hour - len(recent_requests))
    
    def reset_limits(self, identifier: str = None):
        """Reset rate limits for specific identifier or all."""
        with self.lock:
            if identifier:
                self.requests.pop(identifier, None)
            else:
                self.requests.clear()


class FileSizeValidator:
    """Validates file sizes to prevent storage abuse."""
    
    def __init__(self, security_config: SecurityConfig):
        self.config = security_config
        self.logger = logging.getLogger(__name__)
    
    def is_size_allowed(self, size_bytes: int) -> bool:
        """Check if file size is within allowed limits."""
        max_size = self.config.max_file_size_gb * 1024 * 1024 * 1024  # Convert to bytes
        
        if size_bytes > max_size:
            self.logger.warning(
                f"File size {size_bytes / (1024**3):.2f}GB exceeds limit "
                f"of {self.config.max_file_size_gb}GB"
            )
            return False
        
        return True
    
    def check_disk_space(self, path: str, required_bytes: int) -> bool:
        """Check if there's enough disk space for download."""
        try:
            path_obj = Path(path)
            parent_dir = path_obj.parent if path_obj.is_file() else path_obj
            
            if not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)
            
            # Get available disk space
            statvfs = parent_dir.stat() if hasattr(parent_dir, 'stat') else None
            
            # For Windows, we'll use a simplified check
            import shutil
            free_bytes = shutil.disk_usage(parent_dir).free
            
            # Add 10% buffer for safety
            required_with_buffer = required_bytes * 1.1
            
            if free_bytes < required_with_buffer:
                self.logger.error(
                    f"Insufficient disk space. Required: {required_with_buffer / (1024**3):.2f}GB, "
                    f"Available: {free_bytes / (1024**3):.2f}GB"
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking disk space: {e}")
            return False  # Fail safe


class SecurityManager:
    """Main security manager that coordinates all security features."""
    
    def __init__(self, security_config: SecurityConfig = None):
        self.config = security_config or SecurityConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.url_validator = URLValidator(self.config)
        self.path_sanitizer = PathSanitizer(self.config)
        self.rate_limiter = RateLimiter(self.config)
        self.file_size_validator = FileSizeValidator(self.config)
        
        # Track active connections
        self.active_connections: Dict[str, int] = {}
        self.connection_lock = threading.Lock()
    
    def validate_download_request(self, url: str, output_path: str, 
                                identifier: str = "default") -> Dict[str, Any]:
        """Comprehensive validation of a download request."""
        results = {
            'allowed': True,
            'url_valid': True,
            'path_safe': True,
            'rate_limit_ok': True,
            'sanitized_url': url,
            'sanitized_path': output_path,
            'errors': []
        }
        
        try:
            # Validate URL
            if not self.url_validator.is_valid_youtube_url(url):
                results['url_valid'] = False
                results['allowed'] = False
                results['errors'].append("Invalid or unsafe URL")
            else:
                results['sanitized_url'] = self.url_validator.sanitize_url(url)
            
            # Sanitize path
            results['sanitized_path'] = self.path_sanitizer.sanitize_path(output_path)
            
            # Check rate limits
            if not self.rate_limiter.is_allowed(identifier):
                results['rate_limit_ok'] = False
                results['allowed'] = False
                results['errors'].append("Rate limit exceeded")
            
            # Check concurrent connections
            with self.connection_lock:
                current_connections = self.active_connections.get(identifier, 0)
                if current_connections >= self.config.max_concurrent_ips:
                    results['allowed'] = False
                    results['errors'].append("Too many concurrent connections")
            
        except Exception as e:
            self.logger.error(f"Error validating download request: {e}")
            results['allowed'] = False
            results['errors'].append(f"Validation error: {e}")
        
        return results
    
    def register_connection(self, identifier: str):
        """Register a new connection."""
        with self.connection_lock:
            self.active_connections[identifier] = self.active_connections.get(identifier, 0) + 1
    
    def unregister_connection(self, identifier: str):
        """Unregister a connection."""
        with self.connection_lock:
            if identifier in self.active_connections:
                self.active_connections[identifier] -= 1
                if self.active_connections[identifier] <= 0:
                    del self.active_connections[identifier]
    
    def check_file_size_before_download(self, estimated_size: int, output_path: str) -> bool:
        """Check if file size and disk space are acceptable."""
        if not self.file_size_validator.is_size_allowed(estimated_size):
            return False
        
        if not self.file_size_validator.check_disk_space(output_path, estimated_size):
            return False
        
        return True
    
    def generate_secure_filename(self, original_name: str, video_id: str) -> str:
        """Generate a secure filename with hash verification."""
        sanitized_name = self.path_sanitizer.sanitize_filename(original_name)
        
        # Add hash of video ID for integrity checking
        hash_suffix = hashlib.sha256(video_id.encode()).hexdigest()[:8]
        name_part, ext = sanitized_name.rsplit('.', 1) if '.' in sanitized_name else (sanitized_name, '')
        
        secure_name = f"{name_part}_{hash_suffix}"
        if ext:
            secure_name += f".{ext}"
        
        return secure_name
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events for monitoring."""
        self.logger.warning(f"Security event [{event_type}]: {details}")
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get current security statistics."""
        with self.connection_lock:
            return {
                'active_connections': dict(self.active_connections),
                'total_active': sum(self.active_connections.values()),
                'rate_limits': {
                    identifier: self.rate_limiter.get_remaining_requests(identifier)
                    for identifier in self.rate_limiter.requests.keys()
                },
                'config': {
                    'max_file_size_gb': self.config.max_file_size_gb,
                    'max_downloads_per_hour': self.config.max_downloads_per_hour,
                    'max_concurrent_ips': self.config.max_concurrent_ips,
                    'rate_limiting_enabled': self.config.enable_rate_limiting,
                    'url_validation_enabled': self.config.enable_url_validation,
                }
            }