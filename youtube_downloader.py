"""
Professional YouTube Downloader - Main Application Class
"""

import os
import sys
import signal
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs
import hashlib

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YTDLPDownloadError

# Import our custom modules
from config import DownloadConfig, ConfigManager, setup_argument_parser, merge_args_with_config
from logging_config import setup_global_logger, get_logger, YTDLPLogger
from error_handling import (
    RetryManager, RetryConfig, ErrorClassifier, DownloadError,
    CircuitBreaker, GracefulShutdown, with_retry
)
from progress_tracking import ProgressTracker, EmailNotifier, StatusReporter
from database import DownloadDatabase, DownloadRecord, ResumeManager


class YouTubeDownloader:
    """Professional YouTube playlist downloader with all production features."""
    
    def __init__(self, config: DownloadConfig):
        """Initialize the downloader with configuration."""
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.database = DownloadDatabase(config.database_path) if config.use_database else None
        self.resume_manager = ResumeManager(self.database) if self.database else None
        self.progress_tracker = ProgressTracker(use_progress_bar=True)
        self.status_reporter = StatusReporter(config.output_dir)
        self.retry_manager = RetryManager(RetryConfig(max_attempts=config.retry_attempts))
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=300)
        self.graceful_shutdown = GracefulShutdown()
        
        # Email notifications
        self.email_notifier = None
        if config.email_notifications and config.email_smtp_server:
            self.email_notifier = EmailNotifier(
                config.email_smtp_server,
                config.email_smtp_port,
                config.email_username,
                config.email_password,
                config.email_username,
                config.email_to
            )
        
        # Thread pool for concurrent downloads
        self.executor = ThreadPoolExecutor(max_workers=config.concurrent_downloads)
        self.active_downloads = {}
        self.session_id = None
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Setup progress callbacks
        self._setup_progress_callbacks()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.graceful_shutdown.request_shutdown()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _setup_progress_callbacks(self):
        """Setup progress tracking callbacks."""
        def progress_callback(download_id: str, stats):
            if stats.status == 'completed' and self.email_notifier:
                # Could send individual completion emails here if desired
                pass
        
        self.progress_tracker.add_callback(progress_callback)
    
    def _create_ytdl_opts(self) -> Dict[str, Any]:
        """Create yt-dlp options from configuration."""
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        opts = {
            'outtmpl': str(output_path / self.config.naming_template),
            'format': self._get_format_selector(),
            'merge_output_format': self.config.video_format,
            'writeinfojson': self.config.write_metadata,
            'writesubtitles': self.config.embed_subs,
            'writeautomaticsub': self.config.embed_subs,
            'writethumbnail': self.config.embed_thumbnail,
            'embedthumbnail': self.config.embed_thumbnail,
            'embedsubs': self.config.embed_subs,
            'noplaylist': False,
            'ignoreerrors': True,
            'continuedl': True,  # Resume partial downloads
            'retries': 0,  # We handle retries ourselves
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'logger': YTDLPLogger(self.logger),
            'progress_hooks': [self._progress_hook],
            'postprocessor_hooks': [self._postprocessor_hook],
            'prefer_ffmpeg': True,  # Prefer ffmpeg for better audio handling
            'keepvideo': False,  # Don't keep separate video files
        }
        
        # Rate limiting
        if self.config.rate_limit:
            opts['ratelimit'] = self._parse_rate_limit(self.config.rate_limit)
        
        return opts
    
    def _get_format_selector(self) -> str:
        """Generate format selector based on configuration."""
        max_height = self.config.max_quality
        
        # Simplified format selector that ensures audio is included
        # This prioritizes complete videos with audio over separate streams
        format_selector = f"best[height<={max_height}][acodec!=none]/"
        format_selector += f"best[height<={max_height}]/"
        format_selector += "best"
        
        return format_selector
    
    def _parse_rate_limit(self, rate_limit: str) -> int:
        """Parse rate limit string to bytes per second."""
        rate_limit = rate_limit.upper()
        if rate_limit.endswith('K'):
            return int(float(rate_limit[:-1]) * 1024)
        elif rate_limit.endswith('M'):
            return int(float(rate_limit[:-1]) * 1024 * 1024)
        elif rate_limit.endswith('G'):
            return int(float(rate_limit[:-1]) * 1024 * 1024 * 1024)
        else:
            return int(rate_limit)
    
    def _progress_hook(self, d: Dict[str, Any]):
        """Handle yt-dlp progress updates."""
        if d['status'] == 'downloading':
            filename = d.get('filename', 'unknown')
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta')
            
            # Find the download ID for this filename
            download_id = self._get_download_id_by_filename(filename)
            if download_id:
                self.progress_tracker.update_progress(
                    download_id,
                    filename=filename,
                    total_bytes=total_bytes,
                    downloaded_bytes=downloaded_bytes,
                    speed=speed or 0,
                    eta=eta,
                    status='downloading'
                )
                
                # Update database
                if self.database:
                    self.database.update_download_status(
                        download_id, 'downloading', downloaded_bytes
                    )
        
        elif d['status'] == 'finished':
            filename = d.get('filename', 'unknown')
            download_id = self._get_download_id_by_filename(filename)
            
            if download_id:
                file_size = Path(filename).stat().st_size if Path(filename).exists() else 0
                
                self.progress_tracker.complete_download(download_id, success=True)
                
                # Update database
                if self.database:
                    self.database.update_download_status(download_id, 'completed')
                
                self.logger.info(f"Successfully downloaded: {Path(filename).name}")
    
    def _postprocessor_hook(self, d: Dict[str, Any]):
        """Handle yt-dlp post-processor updates."""
        if d['status'] == 'finished':
            self.logger.debug(f"Post-processing completed: {d.get('filepath', 'unknown')}")
    
    def _get_download_id_by_filename(self, filename: str) -> Optional[str]:
        """Get download ID by matching filename pattern."""
        # This is a simplified approach - in production you might want a more robust mapping
        for download_id, info in self.active_downloads.items():
            if info.get('filename') and info['filename'] in filename:
                return download_id
        return None
    
    def _extract_playlist_info(self, playlist_url: str) -> Dict[str, Any]:
        """Extract playlist information without downloading."""
        opts = self._create_ytdl_opts()
        opts.update({
            'extract_flat': True,  # Only extract metadata
            'quiet': True
        })
        
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                return info
        except Exception as e:
            error = ErrorClassifier.classify_ytdlp_error(str(e), playlist_url)
            self.logger.error(f"Failed to extract playlist info: {error}")
            raise error
    
    def _create_download_records(self, playlist_info: Dict[str, Any]) -> List[DownloadRecord]:
        """Create download records from playlist information."""
        records = []
        playlist_url = playlist_info.get('webpage_url', '')
        
        for entry in playlist_info.get('entries', []):
            if not entry:
                continue
            
            video_id = entry.get('id', '')
            video_url = entry.get('url', f"https://youtube.com/watch?v={video_id}")
            title = entry.get('title', 'Unknown Title')
            
            # Generate filename
            filename = self.config.naming_template.replace('%(title)s', title)
            filename = filename.replace('%(ext)s', self.config.video_format)
            filename = filename.replace('%(playlist_index)03d', f"{len(records) + 1:03d}")
            
            # Create download record
            download_id = self._generate_download_id(playlist_url, video_id)
            record = DownloadRecord(
                id=download_id,
                playlist_url=playlist_url,
                video_url=video_url,
                video_id=video_id,
                title=title,
                filename=filename,
                status='pending',
                quality=self.config.max_quality,
                format=self.config.video_format
            )
            
            records.append(record)
        
        return records
    
    def _generate_download_id(self, playlist_url: str, video_id: str) -> str:
        """Generate a unique download ID."""
        return hashlib.md5(f"{playlist_url}:{video_id}".encode()).hexdigest()[:16]
    
    @with_retry()
    def _download_single_video(self, record: DownloadRecord) -> bool:
        """Download a single video with retry logic."""
        if not self.circuit_breaker.can_execute():
            raise DownloadError("Circuit breaker is open - too many failures")
        
        if self.graceful_shutdown.is_shutdown_requested():
            raise DownloadError("Shutdown requested")
        
        try:
            # Register with graceful shutdown
            self.graceful_shutdown.register_download(record.id)
            
            # Add to progress tracker
            self.progress_tracker.add_download(record.id, record.video_url)
            self.active_downloads[record.id] = {'filename': record.filename}
            
            # Update database status
            if self.database:
                self.database.update_download_status(record.id, 'downloading')
            
            # Check if already downloaded
            output_path = Path(self.config.output_dir) / record.filename
            if output_path.exists() and self.database:
                if self.database.is_video_downloaded(record.playlist_url, record.video_id):
                    self.logger.info(f"Skipping already downloaded: {record.title}")
                    self.progress_tracker.complete_download(record.id, success=True)
                    return True
            
            # Perform download
            opts = self._create_ytdl_opts()
            with YoutubeDL(opts) as ydl:
                ydl.download([record.video_url])
            
            # Record success
            self.circuit_breaker.record_success()
            return True
            
        except Exception as e:
            # Classify and handle error
            error = ErrorClassifier.classify_ytdlp_error(str(e), record.video_url)
            self.circuit_breaker.record_failure()
            
            # Update progress tracker and database
            self.progress_tracker.complete_download(record.id, success=False, error=str(error))
            if self.database:
                self.database.update_download_status(record.id, 'failed', error_message=str(error))
            
            self.logger.error(f"Failed to download {record.title}: {error}")
            raise error
            
        finally:
            # Cleanup
            self.graceful_shutdown.unregister_download(record.id)
            self.active_downloads.pop(record.id, None)
    
    def download_playlist(self, playlist_url: str, resume: bool = False) -> bool:
        """Download an entire playlist with all production features."""
        try:
            self.logger.info(f"Starting playlist download: {playlist_url}")
            
            # Check for resume
            if resume and self.resume_manager:
                resume_info = self.resume_manager.get_resume_info(playlist_url)
                if resume_info['can_resume']:
                    self.logger.info(f"Resuming download with {resume_info['incomplete_count']} remaining videos")
                    return self._resume_playlist_download(playlist_url, resume_info)
            
            # Extract playlist information
            playlist_info = self._extract_playlist_info(playlist_url)
            playlist_title = playlist_info.get('title', 'Unknown Playlist')
            video_count = len(playlist_info.get('entries', []))
            
            self.logger.info(f"Playlist: {playlist_title} ({video_count} videos)")
            
            # Create download records
            download_records = self._create_download_records(playlist_info)
            
            # Add to database
            if self.database:
                self.database.add_playlist(
                    playlist_url, playlist_title, 
                    playlist_info.get('description', ''), video_count
                )
                
                self.session_id = self.database.create_download_session(
                    playlist_url, video_count, self.config.__dict__
                )
                
                # Add download records to database
                for record in download_records:
                    self.database.add_download(record)
            
            # Send start notification
            if self.email_notifier:
                self.email_notifier.notify_download_started(playlist_url, video_count)
            
            # Download videos concurrently
            success_count = 0
            failed_count = 0
            
            with ThreadPoolExecutor(max_workers=self.config.concurrent_downloads) as executor:
                # Submit all download tasks
                future_to_record = {
                    executor.submit(self._download_single_video, record): record
                    for record in download_records
                }
                
                # Process completed downloads
                for future in as_completed(future_to_record):
                    if self.graceful_shutdown.is_shutdown_requested():
                        self.logger.info("Cancelling remaining downloads due to shutdown request")
                        break
                    
                    record = future_to_record[future]
                    try:
                        success = future.result()
                        if success:
                            success_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        failed_count += 1
                        self.logger.error(f"Download failed for {record.title}: {e}")
                    
                    # Update session stats
                    if self.database and self.session_id:
                        self.database.update_session_stats(
                            self.session_id, success_count, failed_count
                        )
            
            # Generate final report
            overall_stats = self.progress_tracker.get_overall_stats()
            self.status_reporter.save_report(self.progress_tracker.downloads)
            self.status_reporter.save_html_report(self.progress_tracker.downloads)
            
            # Complete session
            if self.database and self.session_id:
                self.database.complete_session(self.session_id)
            
            # Send completion notification
            if self.email_notifier:
                self.email_notifier.notify_download_completed(overall_stats)
            
            # Log summary
            self.logger.info(
                f"Playlist download completed: {success_count} successful, "
                f"{failed_count} failed out of {video_count} total videos"
            )
            
            return failed_count == 0
            
        except Exception as e:
            self.logger.error(f"Playlist download failed: {e}")
            
            if self.email_notifier:
                self.email_notifier.notify_download_failed(str(e))
            
            if self.database and self.session_id:
                self.database.complete_session(self.session_id, "failed")
            
            return False
        
        finally:
            self.cleanup()
    
    def _resume_playlist_download(self, playlist_url: str, resume_info: Dict[str, Any]) -> bool:
        """Resume an interrupted playlist download."""
        self.logger.info(f"Resuming playlist download for {resume_info['incomplete_count']} videos")
        
        # Get incomplete downloads
        incomplete_records = resume_info['incomplete_downloads']
        
        # Create session
        if self.database:
            self.session_id = self.database.create_download_session(
                playlist_url, len(incomplete_records), self.config.__dict__
            )
        
        success_count = 0
        failed_count = 0
        
        # Download remaining videos
        with ThreadPoolExecutor(max_workers=self.config.concurrent_downloads) as executor:
            future_to_record = {
                executor.submit(self._download_single_video, record): record
                for record in incomplete_records
            }
            
            for future in as_completed(future_to_record):
                if self.graceful_shutdown.is_shutdown_requested():
                    break
                
                record = future_to_record[future]
                try:
                    success = future.result()
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
        
        # Complete session
        if self.database and self.session_id:
            self.database.update_session_stats(self.session_id, success_count, failed_count)
            self.database.complete_session(self.session_id)
        
        self.logger.info(f"Resume completed: {success_count} successful, {failed_count} failed")
        return failed_count == 0
    
    def list_formats(self, url: str) -> List[Dict[str, Any]]:
        """List available formats for a video or playlist."""
        opts = self._create_ytdl_opts()
        opts.update({
            'listformats': True,
            'quiet': True
        })
        
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('formats', [])
        except Exception as e:
            self.logger.error(f"Failed to list formats: {e}")
            return []
    
    def cleanup(self):
        """Clean up resources."""
        self.progress_tracker.cleanup()
        
        if self.executor:
            self.executor.shutdown(wait=True)
        
        # Wait for graceful shutdown
        if self.graceful_shutdown.is_shutdown_requested():
            self.graceful_shutdown.wait_for_completion()


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Handle special commands
    if args.create_config:
        ConfigManager().create_sample_config()
        return 0
    
    if not args.url:
        parser.error("URL is required (or use --create-config)")
    
    try:
        # Load configuration
        config_manager = ConfigManager(args.config)
        config = config_manager.load_config()
        config = merge_args_with_config(config, args)
        
        # Setup logging
        setup_global_logger(
            config.log_level,
            config.log_file,
            config.log_max_size,
            config.log_backup_count
        )
        
        logger = get_logger(__name__)
        logger.info("Professional YouTube Downloader started")
        logger.info(f"Configuration: {config}")
        
        # Create downloader instance
        downloader = YouTubeDownloader(config)
        
        # Handle special commands
        if args.list_formats:
            formats = downloader.list_formats(args.url)
            for fmt in formats[:10]:  # Show first 10 formats
                print(f"Format ID: {fmt.get('format_id')}, "
                      f"Extension: {fmt.get('ext')}, "
                      f"Resolution: {fmt.get('resolution', 'N/A')}, "
                      f"Note: {fmt.get('format_note', 'N/A')}")
            return 0
        
        # Start download
        success = downloader.download_playlist(args.url, resume=args.resume)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())