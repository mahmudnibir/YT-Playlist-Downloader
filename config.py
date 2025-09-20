"""Configuration management for YouTube Downloader."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
from dataclasses import dataclass, asdict


@dataclass
class DownloadConfig:
    """Configuration class for download settings."""
    output_dir: str = "./downloads"
    max_quality: str = "2160"  # 4K by default
    audio_format: str = "best"
    video_format: str = "mp4"
    naming_template: str = "%(playlist_index)03d - %(title)s.%(ext)s"
    concurrent_downloads: int = 3
    retry_attempts: int = 3
    rate_limit: str = "1M"  # 1MB/s default rate limit
    embed_subs: bool = False
    embed_thumbnail: bool = True
    write_metadata: bool = True
    
    # Notification settings
    email_notifications: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_to: str = ""
    
    # Database settings
    use_database: bool = True
    database_path: str = "./downloads.db"
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "./yt_downloader.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 5


class ConfigManager:
    """Manages configuration from multiple sources."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config = DownloadConfig()
        
    def load_config(self) -> DownloadConfig:
        """Load configuration from file, environment, and command line."""
        # 1. Load from config file if it exists
        if self.config_file.exists():
            self._load_from_file()
            
        # 2. Override with environment variables
        self._load_from_env()
        
        return self.config
    
    def _load_from_file(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Update config with file values
            for key, value in config_data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_mappings = {
            'YT_OUTPUT_DIR': 'output_dir',
            'YT_MAX_QUALITY': 'max_quality',
            'YT_RATE_LIMIT': 'rate_limit',
            'YT_CONCURRENT_DOWNLOADS': 'concurrent_downloads',
            'YT_LOG_LEVEL': 'log_level',
            'YT_EMAIL_NOTIFICATIONS': 'email_notifications',
            'YT_EMAIL_SERVER': 'email_smtp_server',
            'YT_EMAIL_USERNAME': 'email_username',
            'YT_EMAIL_PASSWORD': 'email_password',
            'YT_EMAIL_TO': 'email_to',
        }
        
        for env_var, config_attr in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Convert string values to appropriate types
                if config_attr in ['concurrent_downloads', 'email_smtp_port', 'log_max_size', 'log_backup_count']:
                    env_value = int(env_value)
                elif config_attr in ['email_notifications', 'embed_subs', 'embed_thumbnail', 'write_metadata', 'use_database']:
                    env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                
                setattr(self.config, config_attr, env_value)
    
    def save_config(self):
        """Save current configuration to file."""
        config_dict = asdict(self.config)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)
    
    def create_sample_config(self):
        """Create a sample configuration file."""
        sample_config = asdict(DownloadConfig())
        with open('config.sample.json', 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2)
        print("Sample configuration created: config.sample.json")


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Professional YouTube Playlist Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://youtube.com/playlist?list=PLxxxxxx
  %(prog)s --url https://youtube.com/playlist?list=PLxxxxxx --quality 1440 --output ./my_videos
  %(prog)s --config my_config.json --url https://youtube.com/playlist?list=PLxxxxxx
  %(prog)s --create-config  # Create sample configuration file
        """
    )
    
    parser.add_argument('url', nargs='?', help='YouTube playlist URL')
    parser.add_argument('--config', '-c', default='config.json', 
                       help='Configuration file path (default: config.json)')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--quality', '-q', choices=['480', '720', '1080', '1440', '2160'],
                       help='Maximum video quality')
    parser.add_argument('--format', '-f', choices=['mp4', 'mkv', 'webm'],
                       help='Output video format')
    parser.add_argument('--concurrent', '-j', type=int,
                       help='Number of concurrent downloads')
    parser.add_argument('--rate-limit', '-r',
                       help='Download rate limit (e.g., 1M, 500K)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    parser.add_argument('--no-database', action='store_true',
                       help='Disable database tracking')
    parser.add_argument('--create-config', action='store_true',
                       help='Create sample configuration file and exit')
    parser.add_argument('--resume', action='store_true',
                       help='Resume interrupted downloads')
    parser.add_argument('--list-formats', action='store_true',
                       help='List available formats for the playlist')
    
    return parser


def merge_args_with_config(config: DownloadConfig, args: argparse.Namespace) -> DownloadConfig:
    """Merge command line arguments with configuration."""
    if args.output:
        config.output_dir = args.output
    if args.quality:
        config.max_quality = args.quality
    if args.format:
        config.video_format = args.format
    if args.concurrent:
        config.concurrent_downloads = args.concurrent
    if args.rate_limit:
        config.rate_limit = args.rate_limit
    if args.log_level:
        config.log_level = args.log_level
    if args.no_database:
        config.use_database = False
        
    return config