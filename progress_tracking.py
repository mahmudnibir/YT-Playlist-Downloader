"""Progress tracking and notifications for YouTube Downloader."""

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import json
import logging
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


@dataclass
class DownloadStats:
    """Statistics for a download operation."""
    url: str
    filename: str = ""
    total_bytes: int = 0
    downloaded_bytes: int = 0
    speed: float = 0.0  # bytes per second
    eta: Optional[int] = None  # seconds
    status: str = "starting"  # starting, downloading, completed, failed, cancelled
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def speed_mbps(self) -> float:
        """Get speed in MB/s."""
        return self.speed / (1024 * 1024) if self.speed else 0.0


class ProgressTracker:
    """Tracks progress of multiple downloads."""
    
    def __init__(self, use_progress_bar: bool = True):
        self.downloads: Dict[str, DownloadStats] = {}
        self.use_progress_bar = use_progress_bar and tqdm is not None
        self.progress_bars: Dict[str, tqdm] = {}
        self.callbacks: list = []
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def add_download(self, download_id: str, url: str) -> DownloadStats:
        """Add a new download to track."""
        with self.lock:
            stats = DownloadStats(url=url)
            self.downloads[download_id] = stats
            
            if self.use_progress_bar:
                pbar = tqdm(
                    total=100,
                    desc=f"Download {download_id[:8]}",
                    unit="%",
                    position=len(self.progress_bars),
                    leave=True
                )
                self.progress_bars[download_id] = pbar
            
            return stats
    
    def update_progress(self, download_id: str, **kwargs):
        """Update progress for a download."""
        with self.lock:
            if download_id not in self.downloads:
                return
            
            stats = self.downloads[download_id]
            
            # Update stats
            for key, value in kwargs.items():
                if hasattr(stats, key):
                    setattr(stats, key, value)
            
            # Update progress bar
            if self.use_progress_bar and download_id in self.progress_bars:
                pbar = self.progress_bars[download_id]
                pbar.n = stats.progress_percentage
                pbar.set_postfix({
                    'Speed': f"{stats.speed_mbps:.1f}MB/s",
                    'ETA': f"{stats.eta}s" if stats.eta else "N/A"
                })
                pbar.refresh()
            
            # Trigger callbacks
            for callback in self.callbacks:
                try:
                    callback(download_id, stats)
                except Exception as e:
                    self.logger.error(f"Progress callback error: {e}")
    
    def complete_download(self, download_id: str, success: bool = True, error: str = None):
        """Mark a download as completed."""
        with self.lock:
            if download_id not in self.downloads:
                return
            
            stats = self.downloads[download_id]
            stats.end_time = time.time()
            stats.status = "completed" if success else "failed"
            
            if error:
                stats.error_message = error
            
            # Close progress bar
            if self.use_progress_bar and download_id in self.progress_bars:
                pbar = self.progress_bars[download_id]
                if success:
                    pbar.n = 100
                    pbar.set_postfix_str("✓ Completed")
                else:
                    pbar.set_postfix_str("✗ Failed")
                pbar.close()
                del self.progress_bars[download_id]
            
            # Trigger callbacks
            for callback in self.callbacks:
                try:
                    callback(download_id, stats)
                except Exception as e:
                    self.logger.error(f"Completion callback error: {e}")
    
    def add_callback(self, callback: Callable[[str, DownloadStats], None]):
        """Add a progress callback function."""
        self.callbacks.append(callback)
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall download statistics."""
        with self.lock:
            total_downloads = len(self.downloads)
            completed = sum(1 for stats in self.downloads.values() if stats.status == "completed")
            failed = sum(1 for stats in self.downloads.values() if stats.status == "failed")
            in_progress = sum(1 for stats in self.downloads.values() if stats.status == "downloading")
            
            total_bytes = sum(stats.total_bytes for stats in self.downloads.values())
            downloaded_bytes = sum(stats.downloaded_bytes for stats in self.downloads.values())
            
            overall_progress = (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
            
            return {
                'total_downloads': total_downloads,
                'completed': completed,
                'failed': failed,
                'in_progress': in_progress,
                'overall_progress': overall_progress,
                'total_bytes': total_bytes,
                'downloaded_bytes': downloaded_bytes
            }
    
    def cleanup(self):
        """Clean up all progress bars."""
        with self.lock:
            for pbar in self.progress_bars.values():
                pbar.close()
            self.progress_bars.clear()


class EmailNotifier:
    """Handles email notifications for download events."""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, from_email: str, to_email: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_email = to_email
        self.logger = logging.getLogger(__name__)
    
    def send_email(self, subject: str, body: str, is_html: bool = False):
        """Send an email notification."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email notification sent: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
    
    def notify_download_started(self, playlist_url: str, video_count: int):
        """Send notification when download starts."""
        subject = "YouTube Download Started"
        body = f"""
        <h2>Download Started</h2>
        <p><strong>Playlist URL:</strong> {playlist_url}</p>
        <p><strong>Video Count:</strong> {video_count}</p>
        <p><strong>Started At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        self.send_email(subject, body, is_html=True)
    
    def notify_download_completed(self, stats: Dict[str, Any]):
        """Send notification when all downloads complete."""
        subject = "YouTube Downloads Completed"
        
        success_rate = (stats['completed'] / stats['total_downloads'] * 100) if stats['total_downloads'] > 0 else 0
        
        body = f"""
        <h2>Downloads Completed</h2>
        <p><strong>Total Downloads:</strong> {stats['total_downloads']}</p>
        <p><strong>Successful:</strong> {stats['completed']}</p>
        <p><strong>Failed:</strong> {stats['failed']}</p>
        <p><strong>Success Rate:</strong> {success_rate:.1f}%</p>
        <p><strong>Total Size:</strong> {stats['total_bytes'] / (1024**3):.2f} GB</p>
        <p><strong>Completed At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        self.send_email(subject, body, is_html=True)
    
    def notify_download_failed(self, error_message: str):
        """Send notification when download fails critically."""
        subject = "YouTube Download Failed"
        body = f"""
        <h2>Download Failed</h2>
        <p><strong>Error:</strong> {error_message}</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        self.send_email(subject, body, is_html=True)


class StatusReporter:
    """Generates status reports and saves them to files."""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, downloads: Dict[str, DownloadStats]) -> Dict[str, Any]:
        """Generate a comprehensive status report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_downloads': len(downloads),
                'completed': 0,
                'failed': 0,
                'in_progress': 0,
                'total_size_bytes': 0,
                'total_duration_seconds': 0
            },
            'downloads': []
        }
        
        for download_id, stats in downloads.items():
            # Update summary
            if stats.status == 'completed':
                report['summary']['completed'] += 1
            elif stats.status == 'failed':
                report['summary']['failed'] += 1
            elif stats.status in ['downloading', 'starting']:
                report['summary']['in_progress'] += 1
            
            report['summary']['total_size_bytes'] += stats.total_bytes
            report['summary']['total_duration_seconds'] += stats.elapsed_time
            
            # Add download details
            download_report = {
                'id': download_id,
                'url': stats.url,
                'filename': stats.filename,
                'status': stats.status,
                'progress_percentage': stats.progress_percentage,
                'total_bytes': stats.total_bytes,
                'downloaded_bytes': stats.downloaded_bytes,
                'speed_mbps': stats.speed_mbps,
                'elapsed_time_seconds': stats.elapsed_time,
                'start_time': datetime.fromtimestamp(stats.start_time).isoformat(),
                'end_time': datetime.fromtimestamp(stats.end_time).isoformat() if stats.end_time else None,
                'error_message': stats.error_message
            }
            report['downloads'].append(download_report)
        
        return report
    
    def save_report(self, downloads: Dict[str, DownloadStats], filename: str = None):
        """Save status report to file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"download_report_{timestamp}.json"
        
        report = self.generate_report(downloads)
        report_path = self.output_dir / filename
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Status report saved to: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Failed to save status report: {e}")
            return None
    
    def generate_html_report(self, downloads: Dict[str, DownloadStats]) -> str:
        """Generate an HTML status report."""
        report = self.generate_report(downloads)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>YouTube Download Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .downloads {{ margin-top: 20px; }}
                .download {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px; }}
                .completed {{ border-left: 5px solid #28a745; }}
                .failed {{ border-left: 5px solid #dc3545; }}
                .in-progress {{ border-left: 5px solid #ffc107; }}
                .progress-bar {{ background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; }}
                .progress-fill {{ background: #007bff; height: 100%; transition: width 0.3s; }}
            </style>
        </head>
        <body>
            <h1>YouTube Download Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Generated:</strong> {report['timestamp']}</p>
                <p><strong>Total Downloads:</strong> {report['summary']['total_downloads']}</p>
                <p><strong>Completed:</strong> {report['summary']['completed']}</p>
                <p><strong>Failed:</strong> {report['summary']['failed']}</p>
                <p><strong>In Progress:</strong> {report['summary']['in_progress']}</p>
                <p><strong>Total Size:</strong> {report['summary']['total_size_bytes'] / (1024**3):.2f} GB</p>
            </div>
            
            <div class="downloads">
                <h2>Download Details</h2>
        """
        
        for download in report['downloads']:
            status_class = download['status'].replace('_', '-')
            html += f"""
                <div class="download {status_class}">
                    <h3>{download['filename'] or download['id']}</h3>
                    <p><strong>Status:</strong> {download['status'].title()}</p>
                    <p><strong>Progress:</strong> {download['progress_percentage']:.1f}%</p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {download['progress_percentage']}%;"></div>
                    </div>
                    <p><strong>Size:</strong> {download['total_bytes'] / (1024**2):.1f} MB</p>
                    <p><strong>Speed:</strong> {download['speed_mbps']:.1f} MB/s</p>
                    <p><strong>Elapsed Time:</strong> {download['elapsed_time_seconds']:.1f}s</p>
                    {f"<p><strong>Error:</strong> {download['error_message']}</p>" if download['error_message'] else ""}
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def save_html_report(self, downloads: Dict[str, DownloadStats], filename: str = None):
        """Save HTML status report to file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"download_report_{timestamp}.html"
        
        html = self.generate_html_report(downloads)
        report_path = self.output_dir / filename
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            self.logger.info(f"HTML report saved to: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Failed to save HTML report: {e}")
            return None