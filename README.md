# Professional YouTube Downloader

A production-ready YouTube playlist downloader with enterprise-grade features including database tracking, resume functionality, progress monitoring, email notifications, and comprehensive error handling.

## Features

### Core Functionality
- 🎥 **High-Quality Downloads**: Up to 4K video with perfect audio synchronization
- 📋 **Playlist Support**: Full playlist downloading with proper indexing
- 🔄 **Resume Capability**: Resume interrupted downloads seamlessly
- 📊 **Progress Tracking**: Real-time progress bars and status monitoring
- 🗃️ **Database Tracking**: SQLite database for download history and metadata

### Production Features
- ⚙️ **Configuration Management**: JSON config files, environment variables, CLI arguments
- 📧 **Email Notifications**: Automated status updates via email
- 📈 **Progress Reports**: Generate HTML and JSON status reports
- 🔒 **Security Features**: URL validation, path sanitization, rate limiting
- 🛡️ **Error Handling**: Comprehensive retry logic with exponential backoff
- 📝 **Professional Logging**: Structured logging with rotation and multiple levels

### Enterprise Features
- 🔀 **Concurrent Downloads**: Multi-threaded downloading with configurable limits
- 🔄 **Circuit Breakers**: Automatic failure recovery mechanisms
- 🚦 **Rate Limiting**: Built-in protection against API abuse
- 💾 **Database Management**: Full download history and statistics
- 🎛️ **Monitoring**: Comprehensive metrics and health checks

## Quick Start

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/professional-youtube-downloader.git
cd professional-youtube-downloader
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Basic usage:**
```bash
python youtube_downloader.py "https://youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

### Docker Installation (Coming Soon)

```bash
docker run -v $(pwd)/downloads:/app/downloads professional-yt-downloader "PLAYLIST_URL"
```

## Configuration

### Command Line Usage

```bash
# Basic download
python youtube_downloader.py "https://youtube.com/playlist?list=PLxxxxxx"

# High quality with custom output directory
python youtube_downloader.py --quality 2160 --output ./my_videos "PLAYLIST_URL"

# With custom configuration file
python youtube_downloader.py --config my_config.json "PLAYLIST_URL"

# Resume interrupted download
python youtube_downloader.py --resume "PLAYLIST_URL"

# List available formats
python youtube_downloader.py --list-formats "PLAYLIST_URL"

# Create sample configuration
python youtube_downloader.py --create-config
```

### Configuration File

Create a `config.json` file for persistent settings:

```json
{
  "output_dir": "./downloads",
  "max_quality": "2160",
  "video_format": "mp4",
  "concurrent_downloads": 3,
  "retry_attempts": 3,
  "rate_limit": "1M",
  "email_notifications": true,
  "email_smtp_server": "smtp.gmail.com",
  "email_smtp_port": 587,
  "email_username": "your-email@gmail.com",
  "email_password": "your-app-password",
  "email_to": "notifications@yourdomain.com",
  "log_level": "INFO",
  "log_file": "./yt_downloader.log"
}
```

### Environment Variables

Set environment variables for sensitive information:

```bash
export YT_EMAIL_PASSWORD="your-app-password"
export YT_OUTPUT_DIR="/path/to/downloads"
export YT_LOG_LEVEL="DEBUG"
export YT_RATE_LIMIT="2M"
```

## Advanced Usage

### Email Notifications

Configure email notifications for download status updates:

```json
{
  "email_notifications": true,
  "email_smtp_server": "smtp.gmail.com",
  "email_smtp_port": 587,
  "email_username": "your-email@gmail.com",
  "email_password": "your-app-password",
  "email_to": "notifications@yourdomain.com"
}
```

### Database Features

The downloader automatically tracks:
- Download history and status
- Playlist metadata
- Download sessions
- Error logs and statistics

Query the database:
```python
from database import DownloadDatabase

db = DownloadDatabase("downloads.db")
stats = db.get_download_statistics()
print(f"Total downloads: {stats['totals']['total_downloads']}")
```

### Progress Monitoring

Generate detailed reports:
```bash
# HTML report is automatically generated in output directory
# JSON reports are also created for programmatic access
```

### Security Features

Built-in security measures:
- URL validation and sanitization
- Path traversal protection
- File size limits
- Rate limiting
- Concurrent connection limits

Configure security settings:
```json
{
  "max_file_size_gb": 10.0,
  "max_downloads_per_hour": 100,
  "max_concurrent_ips": 5,
  "enable_rate_limiting": true,
  "enable_url_validation": true
}
```

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/yt-downloader.service`:

```ini
[Unit]
Description=YouTube Downloader Service
After=network.target

[Service]
Type=simple
User=ytdownloader
WorkingDirectory=/opt/yt-downloader
ExecStart=/usr/bin/python3 /opt/yt-downloader/youtube_downloader.py --config /etc/yt-downloader/config.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Windows Service

Use `nssm` or similar tools to create a Windows service:

```cmd
nssm install "YouTube Downloader" "python.exe" "C:\path\to\youtube_downloader.py"
nssm set "YouTube Downloader" AppDirectory "C:\path\to\downloader"
nssm set "YouTube Downloader" AppParameters "--config C:\path\to\config.json"
```

### Process Monitoring

Monitor with tools like:
- **Linux**: `systemctl`, `journalctl`
- **Windows**: Event Viewer, Services console
- **Cross-platform**: Supervisor, PM2

## API Reference

### Main Classes

#### `YouTubeDownloader`
Main downloader class with all functionality.

```python
from youtube_downloader import YouTubeDownloader
from config import DownloadConfig

config = DownloadConfig()
downloader = YouTubeDownloader(config)
success = downloader.download_playlist("PLAYLIST_URL")
```

#### `DownloadDatabase`
Database management for tracking downloads.

```python
from database import DownloadDatabase

db = DownloadDatabase("downloads.db")
stats = db.get_download_statistics()
```

#### `SecurityManager`
Security and validation features.

```python
from security import SecurityManager, SecurityConfig

security = SecurityManager(SecurityConfig())
validation = security.validate_download_request(url, output_path)
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   # Add to PATH
   ```

2. **Permission errors**
   ```bash
   # Ensure write permissions to output directory
   chmod 755 /path/to/downloads
   ```

3. **Network issues**
   ```bash
   # Check connectivity and proxy settings
   # Configure rate limiting if needed
   ```

4. **Database locked**
   ```bash
   # Ensure no other instances are running
   # Check file permissions on database
   ```

### Debug Mode

Enable debug logging:
```bash
python youtube_downloader.py --log-level DEBUG "PLAYLIST_URL"
```

### Log Analysis

Logs are structured JSON format for easy parsing:
```bash
# View recent errors
tail -f yt_downloader.log | jq 'select(.level == "ERROR")'

# Count download statistics
jq 'select(.message | contains("completed"))' yt_downloader.log | wc -l
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -e .[dev]

# Run tests
pytest

# Code formatting
black .

# Linting
flake8 .

# Type checking
mypy .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for the core downloading functionality
- [tqdm](https://github.com/tqdm/tqdm) for progress bars
- All contributors and testers

## Support

- 📖 [Documentation](https://github.com/yourusername/professional-youtube-downloader/wiki)
- 🐛 [Issue Tracker](https://github.com/yourusername/professional-youtube-downloader/issues)
- 💬 [Discussions](https://github.com/yourusername/professional-youtube-downloader/discussions)

---

**⚠️ Legal Notice**: This tool is for educational purposes and personal use only. Please respect YouTube's Terms of Service and copyright laws. Users are responsible for ensuring they have the right to download content.