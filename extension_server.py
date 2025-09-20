"""
YouTube Downloader Pro - Chrome Extension API Server
Professional API server to handle Chrome extension requests
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import time
import uuid
import queue
from dataclasses import dataclass, asdict

# Import our downloader modules
from youtube_downloader import YouTubeDownloader, DownloadConfig
from config import Config
from logging_config import setup_logging
from database import DatabaseManager
from progress_tracking import ProgressTracker

@dataclass
class DownloadTask:
    """Represents a download task"""
    id: str
    url: str
    type: str  # 'video' or 'playlist'
    status: str  # 'pending', 'downloading', 'completed', 'failed'
    progress: float = 0.0
    total_videos: int = 0
    completed_videos: int = 0
    current_video: str = ""
    speed: str = ""
    eta: str = ""
    error_message: str = ""
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

class ExtensionAPIServer:
    """Chrome Extension API Server"""
    
    def __init__(self, host='localhost', port=8080):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for extension requests
        
        self.host = host
        self.port = port
        
        # Initialize components
        self.config = Config()
        self.setup_logging()
        self.downloader = YouTubeDownloader(self.config)
        self.db = DatabaseManager(self.config.database_path)
        
        # Download management
        self.download_tasks: Dict[str, DownloadTask] = {}
        self.download_queue = queue.Queue()
        self.is_processing = False
        
        # Setup routes
        self.setup_routes()
        
        # Start background worker
        self.worker_thread = threading.Thread(target=self.download_worker, daemon=True)
        self.worker_thread.start()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Extension API Server initialized")

    def setup_logging(self):
        """Setup logging configuration"""
        setup_logging(self.config.log_level, self.config.log_file)

    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'downloads_active': len([t for t in self.download_tasks.values() 
                                       if t.status == 'downloading'])
            })

        @self.app.route('/api/download/playlist', methods=['POST'])
        def download_playlist():
            """Download a YouTube playlist"""
            try:
                data = request.get_json()
                if not data or 'url' not in data:
                    return jsonify({'success': False, 'error': 'URL is required'}), 400

                # Create download task
                task_id = str(uuid.uuid4())
                task = DownloadTask(
                    id=task_id,
                    url=data['url'],
                    type='playlist',
                    status='pending'
                )
                
                self.download_tasks[task_id] = task
                
                # Add to download queue
                download_config = self.create_download_config(data)
                self.download_queue.put((task_id, download_config))
                
                self.logger.info(f"Playlist download queued: {task_id}")
                
                return jsonify({
                    'success': True,
                    'data': {
                        'downloadId': task_id,
                        'status': 'queued'
                    }
                })

            except Exception as e:
                self.logger.error(f"Playlist download error: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/download/video', methods=['POST'])
        def download_video():
            """Download a single YouTube video"""
            try:
                data = request.get_json()
                if not data or 'url' not in data:
                    return jsonify({'success': False, 'error': 'URL is required'}), 400

                # Create download task
                task_id = str(uuid.uuid4())
                task = DownloadTask(
                    id=task_id,
                    url=data['url'],
                    type='video',
                    status='pending'
                )
                
                self.download_tasks[task_id] = task
                
                # Add to download queue
                download_config = self.create_download_config(data)
                self.download_queue.put((task_id, download_config))
                
                self.logger.info(f"Video download queued: {task_id}")
                
                return jsonify({
                    'success': True,
                    'data': {
                        'downloadId': task_id,
                        'status': 'queued'
                    }
                })

            except Exception as e:
                self.logger.error(f"Video download error: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/status/<task_id>', methods=['GET'])
        def get_download_status(task_id):
            """Get download status for a specific task"""
            try:
                if task_id not in self.download_tasks:
                    return jsonify({'success': False, 'error': 'Task not found'}), 404

                task = self.download_tasks[task_id]
                
                return jsonify({
                    'success': True,
                    'data': {
                        'id': task.id,
                        'status': task.status,
                        'progress': task.progress,
                        'totalVideos': task.total_videos,
                        'completedVideos': task.completed_videos,
                        'currentVideo': task.current_video,
                        'speed': task.speed,
                        'eta': task.eta,
                        'errorMessage': task.error_message,
                        'type': task.type,
                        'createdAt': task.created_at.isoformat(),
                        'updatedAt': task.updated_at.isoformat()
                    }
                })

            except Exception as e:
                self.logger.error(f"Status check error: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/downloads', methods=['GET'])
        def get_all_downloads():
            """Get all download tasks"""
            try:
                tasks_data = []
                for task in self.download_tasks.values():
                    tasks_data.append({
                        'id': task.id,
                        'url': task.url,
                        'type': task.type,
                        'status': task.status,
                        'progress': task.progress,
                        'totalVideos': task.total_videos,
                        'completedVideos': task.completed_videos,
                        'createdAt': task.created_at.isoformat(),
                        'updatedAt': task.updated_at.isoformat()
                    })

                return jsonify({
                    'success': True,
                    'data': {
                        'tasks': tasks_data,
                        'summary': {
                            'total': len(self.download_tasks),
                            'pending': len([t for t in self.download_tasks.values() if t.status == 'pending']),
                            'downloading': len([t for t in self.download_tasks.values() if t.status == 'downloading']),
                            'completed': len([t for t in self.download_tasks.values() if t.status == 'completed']),
                            'failed': len([t for t in self.download_tasks.values() if t.status == 'failed'])
                        }
                    }
                })

            except Exception as e:
                self.logger.error(f"Get downloads error: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/settings', methods=['GET'])
        def get_settings():
            """Get current downloader settings"""
            try:
                return jsonify({
                    'success': True,
                    'data': {
                        'quality': 'best',
                        'format': 'mp4',
                        'audioGuarantee': True,
                        'notifications': True,
                        'outputPath': str(self.config.output_dir),
                        'maxConcurrentDownloads': 3,
                        'retryAttempts': 3,
                        'downloadTimeout': 300
                    }
                })

            except Exception as e:
                self.logger.error(f"Get settings error: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/settings', methods=['POST'])
        def update_settings():
            """Update downloader settings"""
            try:
                data = request.get_json()
                # Here you would update the config
                # For now, just return success
                
                return jsonify({
                    'success': True,
                    'data': {
                        'message': 'Settings updated successfully'
                    }
                })

            except Exception as e:
                self.logger.error(f"Update settings error: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/dashboard', methods=['GET'])
        def dashboard():
            """Serve download dashboard"""
            return send_from_directory('static', 'dashboard.html')

        @self.app.route('/static/<path:filename>')
        def serve_static(filename):
            """Serve static files"""
            return send_from_directory('static', filename)

    def create_download_config(self, data: Dict[str, Any]) -> DownloadConfig:
        """Create download configuration from request data"""
        
        # Determine quality and format based on settings
        quality = data.get('quality', 'best')
        format_pref = data.get('format', 'mp4')
        audio_guarantee = data.get('audioGuarantee', True)
        
        if audio_guarantee:
            # Use simple format that guarantees audio
            format_string = 'best[acodec!=none]/best'
        else:
            # Use more specific quality if audio guarantee is off
            if quality == 'best':
                format_string = f'best[ext={format_pref}]/best'
            else:
                format_string = f'best[height<={quality}][ext={format_pref}]/best[height<={quality}]/best'

        return DownloadConfig(
            quality=quality,
            format=format_string,
            output_dir=self.config.output_dir,
            audio_quality='best',
            subtitle_langs=[],
            write_info_json=False,
            write_thumbnail=False,
            write_description=False,
            embed_subs=False,
            notifications=data.get('notifications', True)
        )

    def download_worker(self):
        """Background worker to process downloads"""
        while True:
            try:
                if not self.download_queue.empty():
                    task_id, config = self.download_queue.get()
                    
                    if task_id in self.download_tasks:
                        task = self.download_tasks[task_id]
                        task.status = 'downloading'
                        task.updated_at = datetime.now()
                        
                        # Create progress callback
                        def progress_callback(info):
                            self.update_task_progress(task_id, info)
                        
                        try:
                            # Perform the download
                            self.logger.info(f"Starting download: {task_id}")
                            
                            if task.type == 'playlist':
                                result = self.downloader.download_playlist(
                                    task.url, config, progress_callback
                                )
                            else:
                                result = self.downloader.download_video(
                                    task.url, config, progress_callback
                                )
                            
                            # Mark as completed
                            task.status = 'completed'
                            task.progress = 100.0
                            task.updated_at = datetime.now()
                            
                            self.logger.info(f"Download completed: {task_id}")
                            
                        except Exception as e:
                            # Mark as failed
                            task.status = 'failed'
                            task.error_message = str(e)
                            task.updated_at = datetime.now()
                            
                            self.logger.error(f"Download failed {task_id}: {str(e)}")
                
                # Sleep briefly before checking again
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Download worker error: {str(e)}")
                time.sleep(5)  # Wait longer on worker error

    def update_task_progress(self, task_id: str, info: Dict[str, Any]):
        """Update task progress from yt-dlp hook"""
        if task_id not in self.download_tasks:
            return
            
        task = self.download_tasks[task_id]
        
        # Update progress information
        if 'downloaded_bytes' in info and 'total_bytes' in info:
            progress = (info['downloaded_bytes'] / info['total_bytes']) * 100
            task.progress = min(progress, 100.0)
        
        if 'filename' in info:
            task.current_video = Path(info['filename']).name
            
        if 'speed' in info and info['speed']:
            # Convert speed to human readable format
            speed = info['speed']
            if speed > 1024 * 1024:
                task.speed = f"{speed / (1024 * 1024):.1f} MB/s"
            elif speed > 1024:
                task.speed = f"{speed / 1024:.1f} KB/s"
            else:
                task.speed = f"{speed:.1f} B/s"
        
        if 'eta' in info and info['eta']:
            task.eta = f"{info['eta']}s"
            
        task.updated_at = datetime.now()

    def cleanup_old_tasks(self, max_age_hours=24):
        """Clean up old completed tasks"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for task_id, task in self.download_tasks.items():
            if (task.status in ['completed', 'failed'] and 
                task.updated_at < cutoff_time):
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.download_tasks[task_id]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old tasks")

    def run(self, debug=False):
        """Start the API server"""
        self.logger.info(f"Starting Extension API Server on {self.host}:{self.port}")
        
        # Start cleanup timer
        cleanup_timer = threading.Timer(3600, self.cleanup_old_tasks)  # Every hour
        cleanup_timer.daemon = True
        cleanup_timer.start()
        
        try:
            self.app.run(host=self.host, port=self.port, debug=debug, threaded=True)
        except Exception as e:
            self.logger.error(f"Server error: {str(e)}")
            raise

def main():
    """Main function to start the server"""
    server = ExtensionAPIServer()
    
    print("🚀 YouTube Downloader Pro - Extension API Server")
    print("=" * 50)
    print(f"Server running at: http://localhost:8080")
    print(f"Health check: http://localhost:8080/api/health")
    print(f"Dashboard: http://localhost:8080/dashboard")
    print()
    print("Extension endpoints:")
    print("• POST /api/download/playlist - Download playlist")
    print("• POST /api/download/video - Download single video")
    print("• GET /api/status/<id> - Check download status")
    print("• GET /api/downloads - List all downloads")
    print("• GET /api/settings - Get settings")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        server.run(debug=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {str(e)}")

if __name__ == '__main__':
    main()