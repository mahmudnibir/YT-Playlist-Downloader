"""Database management and resume functionality for YouTube Downloader."""

import sqlite3
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
from contextlib import contextmanager


@dataclass
class DownloadRecord:
    """Database record for a download."""
    id: str
    playlist_url: str
    video_url: str
    video_id: str
    title: str
    filename: str
    status: str  # pending, downloading, completed, failed, skipped
    file_size: int = 0
    downloaded_bytes: int = 0
    quality: str = ""
    format: str = ""
    error_message: str = ""
    created_at: float = 0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: str = "{}"  # JSON string for additional metadata
    
    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()


class DownloadDatabase:
    """SQLite database for tracking downloads."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Downloads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id TEXT PRIMARY KEY,
                    playlist_url TEXT NOT NULL,
                    video_url TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    file_size INTEGER DEFAULT 0,
                    downloaded_bytes INTEGER DEFAULT 0,
                    quality TEXT DEFAULT '',
                    format TEXT DEFAULT '',
                    error_message TEXT DEFAULT '',
                    created_at REAL NOT NULL,
                    started_at REAL,
                    completed_at REAL,
                    metadata TEXT DEFAULT '{}',
                    UNIQUE(playlist_url, video_id)
                )
            """)
            
            # Playlists table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    url TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    video_count INTEGER,
                    created_at REAL NOT NULL,
                    last_updated REAL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Download sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_sessions (
                    id TEXT PRIMARY KEY,
                    playlist_url TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    completed_at REAL,
                    status TEXT NOT NULL DEFAULT 'active',
                    total_videos INTEGER DEFAULT 0,
                    completed_videos INTEGER DEFAULT 0,
                    failed_videos INTEGER DEFAULT 0,
                    config TEXT DEFAULT '{}',
                    FOREIGN KEY (playlist_url) REFERENCES playlists (url)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_playlist ON downloads(playlist_url)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_video_id ON downloads(video_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON download_sessions(status)")
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def add_playlist(self, url: str, title: str, description: str = "", video_count: int = 0, 
                    metadata: Dict[str, Any] = None) -> bool:
        """Add or update a playlist in the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO playlists 
                    (url, title, description, video_count, created_at, last_updated, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    url, title, description, video_count, 
                    time.time(), time.time(), json.dumps(metadata or {})
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add playlist: {e}")
            return False
    
    def add_download(self, record: DownloadRecord) -> bool:
        """Add a download record to the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO downloads 
                    (id, playlist_url, video_url, video_id, title, filename, status, 
                     file_size, downloaded_bytes, quality, format, error_message,
                     created_at, started_at, completed_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.id, record.playlist_url, record.video_url, record.video_id,
                    record.title, record.filename, record.status, record.file_size,
                    record.downloaded_bytes, record.quality, record.format,
                    record.error_message, record.created_at, record.started_at,
                    record.completed_at, record.metadata
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add download record: {e}")
            return False
    
    def update_download_status(self, download_id: str, status: str, 
                             downloaded_bytes: int = None, error_message: str = None) -> bool:
        """Update the status of a download."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                updates = ["status = ?"]
                params = [status]
                
                if status == "downloading" and downloaded_bytes is not None:
                    updates.append("downloaded_bytes = ?")
                    updates.append("started_at = ?")
                    params.extend([downloaded_bytes, time.time()])
                elif status == "completed":
                    updates.append("completed_at = ?")
                    params.append(time.time())
                elif status == "failed" and error_message:
                    updates.append("error_message = ?")
                    params.append(error_message)
                
                params.append(download_id)
                
                cursor.execute(f"""
                    UPDATE downloads 
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Failed to update download status: {e}")
            return False
    
    def get_download(self, download_id: str) -> Optional[DownloadRecord]:
        """Get a download record by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM downloads WHERE id = ?", (download_id,))
                row = cursor.fetchone()
                
                if row:
                    return DownloadRecord(**dict(row))
                return None
        except Exception as e:
            self.logger.error(f"Failed to get download record: {e}")
            return None
    
    def get_downloads_by_playlist(self, playlist_url: str, status: str = None) -> List[DownloadRecord]:
        """Get all downloads for a playlist, optionally filtered by status."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute(
                        "SELECT * FROM downloads WHERE playlist_url = ? AND status = ? ORDER BY created_at",
                        (playlist_url, status)
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM downloads WHERE playlist_url = ? ORDER BY created_at",
                        (playlist_url,)
                    )
                
                return [DownloadRecord(**dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get downloads for playlist: {e}")
            return []
    
    def get_incomplete_downloads(self, playlist_url: str = None) -> List[DownloadRecord]:
        """Get all incomplete downloads (pending, downloading, failed)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if playlist_url:
                    cursor.execute("""
                        SELECT * FROM downloads 
                        WHERE playlist_url = ? AND status IN ('pending', 'downloading', 'failed')
                        ORDER BY created_at
                    """, (playlist_url,))
                else:
                    cursor.execute("""
                        SELECT * FROM downloads 
                        WHERE status IN ('pending', 'downloading', 'failed')
                        ORDER BY created_at
                    """)
                
                return [DownloadRecord(**dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get incomplete downloads: {e}")
            return []
    
    def is_video_downloaded(self, playlist_url: str, video_id: str) -> bool:
        """Check if a video is already downloaded successfully."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM downloads 
                    WHERE playlist_url = ? AND video_id = ? AND status = 'completed'
                """, (playlist_url, video_id))
                
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Failed to check video download status: {e}")
            return False
    
    def create_download_session(self, playlist_url: str, total_videos: int, 
                              config: Dict[str, Any] = None) -> str:
        """Create a new download session."""
        session_id = self._generate_session_id(playlist_url)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO download_sessions 
                    (id, playlist_url, started_at, status, total_videos, config)
                    VALUES (?, ?, ?, 'active', ?, ?)
                """, (
                    session_id, playlist_url, time.time(), total_videos,
                    json.dumps(config or {})
                ))
                conn.commit()
                return session_id
        except Exception as e:
            self.logger.error(f"Failed to create download session: {e}")
            return session_id
    
    def update_session_stats(self, session_id: str, completed: int = None, failed: int = None):
        """Update session statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                updates = []
                params = []
                
                if completed is not None:
                    updates.append("completed_videos = ?")
                    params.append(completed)
                
                if failed is not None:
                    updates.append("failed_videos = ?")
                    params.append(failed)
                
                if updates:
                    params.append(session_id)
                    cursor.execute(f"""
                        UPDATE download_sessions 
                        SET {', '.join(updates)}
                        WHERE id = ?
                    """, params)
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to update session stats: {e}")
    
    def complete_session(self, session_id: str, status: str = "completed"):
        """Mark a download session as completed."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE download_sessions 
                    SET completed_at = ?, status = ?
                    WHERE id = ?
                """, (time.time(), status, session_id))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to complete session: {e}")
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a download session."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM download_sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            self.logger.error(f"Failed to get session stats: {e}")
            return None
    
    def cleanup_old_sessions(self, days: int = 30):
        """Clean up old completed sessions."""
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM download_sessions 
                    WHERE status IN ('completed', 'cancelled') AND completed_at < ?
                """, (cutoff_time,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old download sessions")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old sessions: {e}")
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """Get overall download statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Count downloads by status
                cursor.execute("""
                    SELECT status, COUNT(*), SUM(file_size) as total_size
                    FROM downloads 
                    GROUP BY status
                """)
                status_counts = {row[0]: {'count': row[1], 'total_size': row[2] or 0} 
                               for row in cursor.fetchall()}
                
                # Get total statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_downloads,
                        COUNT(DISTINCT playlist_url) as total_playlists,
                        SUM(file_size) as total_size,
                        AVG(CASE WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
                            THEN completed_at - started_at END) as avg_download_time
                    FROM downloads
                """)
                totals = dict(cursor.fetchone())
                
                return {
                    'status_breakdown': status_counts,
                    'totals': totals,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get download statistics: {e}")
            return {}
    
    def _generate_session_id(self, playlist_url: str) -> str:
        """Generate a unique session ID."""
        timestamp = str(time.time())
        return hashlib.md5(f"{playlist_url}{timestamp}".encode()).hexdigest()[:12]
    
    def _generate_download_id(self, playlist_url: str, video_id: str) -> str:
        """Generate a unique download ID."""
        return hashlib.md5(f"{playlist_url}:{video_id}".encode()).hexdigest()[:16]


class ResumeManager:
    """Manages resume functionality for interrupted downloads."""
    
    def __init__(self, database: DownloadDatabase):
        self.db = database
        self.logger = logging.getLogger(__name__)
    
    def can_resume_playlist(self, playlist_url: str) -> bool:
        """Check if a playlist download can be resumed."""
        incomplete_downloads = self.db.get_incomplete_downloads(playlist_url)
        return len(incomplete_downloads) > 0
    
    def get_resume_info(self, playlist_url: str) -> Dict[str, Any]:
        """Get information about resumable downloads."""
        incomplete = self.db.get_incomplete_downloads(playlist_url)
        completed = self.db.get_downloads_by_playlist(playlist_url, "completed")
        failed = self.db.get_downloads_by_playlist(playlist_url, "failed")
        
        return {
            'playlist_url': playlist_url,
            'incomplete_count': len(incomplete),
            'completed_count': len(completed),
            'failed_count': len(failed),
            'total_count': len(incomplete) + len(completed) + len(failed),
            'incomplete_downloads': incomplete,
            'can_resume': len(incomplete) > 0
        }
    
    def prepare_resume_list(self, playlist_url: str) -> List[str]:
        """Prepare a list of video URLs to resume downloading."""
        incomplete_downloads = self.db.get_incomplete_downloads(playlist_url)
        
        # Reset 'downloading' status to 'pending' for stuck downloads
        for download in incomplete_downloads:
            if download.status == 'downloading':
                self.db.update_download_status(download.id, 'pending')
        
        # Return list of video URLs to download
        return [download.video_url for download in incomplete_downloads]
    
    def mark_for_retry(self, playlist_url: str, video_ids: List[str] = None):
        """Mark failed downloads for retry."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                if video_ids:
                    placeholders = ','.join(['?' for _ in video_ids])
                    cursor.execute(f"""
                        UPDATE downloads 
                        SET status = 'pending', error_message = '', started_at = NULL
                        WHERE playlist_url = ? AND video_id IN ({placeholders}) AND status = 'failed'
                    """, [playlist_url] + video_ids)
                else:
                    cursor.execute("""
                        UPDATE downloads 
                        SET status = 'pending', error_message = '', started_at = NULL
                        WHERE playlist_url = ? AND status = 'failed'
                    """, (playlist_url,))
                
                conn.commit()
                retry_count = cursor.rowcount
                
                if retry_count > 0:
                    self.logger.info(f"Marked {retry_count} downloads for retry")
                
                return retry_count
                
        except Exception as e:
            self.logger.error(f"Failed to mark downloads for retry: {e}")
            return 0