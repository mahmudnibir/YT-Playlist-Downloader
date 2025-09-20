# 🚀 YouTube Downloader Pro - Chrome Extension

A professional Chrome extension for downloading YouTube videos and playlists with guaranteed audio quality and modern UI.

## 📋 Features

✅ **Professional Chrome Extension**
- Modern dark theme with professional UI
- Real-time download progress tracking
- YouTube page integration with download buttons
- Background service worker for reliable downloads

✅ **Guaranteed Audio Quality** 
- Simple format selector that always works
- No more audio-video sync issues
- Clean video-only downloads folder

✅ **Production-Ready Backend**
- REST API server for extension communication
- Progress tracking and notifications
- Download history and management
- Web dashboard for monitoring

✅ **Enterprise Features**
- Retry mechanisms and error handling
- Concurrent download management
- Professional logging system
- Security validation

## 🛠️ Installation Guide

### Step 1: Install Python Dependencies

```powershell
# Navigate to the project directory
cd "C:\Users\G6 Ryzen 5 Pro\OneDrive\Desktop\YT-Downloader"

# Install required packages
pip install -r requirements.txt
```

### Step 2: Install Chrome Extension

1. **Open Chrome** and navigate to `chrome://extensions/`

2. **Enable Developer Mode** (toggle in top-right corner)

3. **Load Extension**:
   - Click "Load unpacked"
   - Navigate to: `C:\Users\G6 Ryzen 5 Pro\OneDrive\Desktop\YT-Downloader\chrome-extension`
   - Select the `chrome-extension` folder
   - Click "Select Folder"

4. **Pin Extension**:
   - Click the puzzle piece icon in Chrome toolbar
   - Find "YouTube Downloader Pro"
   - Click the pin icon to add to toolbar

### Step 3: Add Extension Icons (Optional)

The extension works without icons but looks better with them:

1. Create or download 16x16, 48x48, and 128x128 PNG icons
2. Save them as:
   - `chrome-extension/icons/icon16.png`
   - `chrome-extension/icons/icon48.png` 
   - `chrome-extension/icons/icon128.png`
3. Reload the extension in Chrome

## 🎯 How to Use

### Method 1: Using the Chrome Extension (Recommended)

1. **Start the API Server**:
   ```powershell
   python extension_server.py
   ```
   
2. **Navigate to YouTube**:
   - Go to any YouTube video or playlist
   - The extension will automatically detect content

3. **Download**:
   - Click the extension icon in Chrome toolbar
   - Click "Download Playlist" or "Download Video"
   - Monitor progress in the extension popup

4. **View Dashboard**:
   - Open http://localhost:8080/dashboard in your browser
   - Monitor all downloads and statistics

### Method 2: Using Python Scripts Directly

#### Simple Audio-Guaranteed Downloader (Always Works):
```powershell
python simple_audio_guaranteed.py
```
- Enter playlist/video URL when prompted
- Downloads with guaranteed audio to `downloads` folder

#### Professional System:
```powershell
python main.py
```
- Full featured downloader with all enterprise features
- Email notifications and progress tracking
- Database integration and resume capability

#### Raw Professional System:
```powershell
python youtube_downloader.py
```
- Direct access to the professional downloader class
- Advanced configuration options

## 📊 Extension Features

### Chrome Extension Components:
- **Popup Interface**: Clean, professional UI with real-time status
- **Background Service**: Handles API communication and notifications  
- **Content Scripts**: Integrate download buttons on YouTube pages
- **Settings**: Quality, format, and notification preferences

### API Server Features:
- **REST Endpoints**: Download videos/playlists via HTTP API
- **Real-time Progress**: WebSocket-style progress updates
- **Download Management**: Queue, retry, and status tracking
- **Web Dashboard**: Beautiful interface for monitoring downloads

### Professional Features:
- **Audio Guarantee**: Format selector `'best[acodec!=none]/best'` ensures audio
- **Clean Downloads**: Only video files, no metadata clutter
- **Concurrent Downloads**: Multiple simultaneous downloads
- **Error Handling**: Comprehensive retry and error recovery
- **Progress Tracking**: Real-time download progress and ETA

## 🔧 Configuration

### Extension Settings:
- **Quality**: Auto, 720p, 1080p, 4K
- **Format**: MP4, WebM, Best Available
- **Audio Guarantee**: Always ensure audio is included
- **Notifications**: Enable/disable download notifications

### File Locations:
```
YT-Downloader/
├── downloads/           # Downloaded videos (clean, videos only)
├── logs/               # Application logs  
├── downloads.db        # Download history database
├── chrome-extension/   # Chrome extension files
└── static/            # Web dashboard files
```

## 🌐 API Endpoints

The extension server provides these endpoints:

- `GET /api/health` - Server health check
- `POST /api/download/playlist` - Download YouTube playlist
- `POST /api/download/video` - Download single video
- `GET /api/status/<id>` - Get download progress
- `GET /api/downloads` - List all downloads
- `GET /api/settings` - Get/update settings
- `GET /dashboard` - Web dashboard interface

## 🚨 Troubleshooting

### Extension Not Working:
1. Make sure API server is running (`python extension_server.py`)
2. Check Chrome extension is loaded and enabled
3. Verify server is accessible at http://localhost:8080

### Audio Issues:
- The `simple_audio_guaranteed.py` script uses a bulletproof format selector
- If other methods fail, use this script for guaranteed audio

### Download Folder Cluttered:
- All scripts now disable metadata files (`write_info_json=False`)
- Only video files are downloaded to keep folder clean

### Server Connection Issues:
```powershell
# Check if server is running
curl http://localhost:8080/api/health

# Restart server if needed
python extension_server.py
```

## 💡 Tips for Best Experience

1. **Use Simple Script for Reliability**: `simple_audio_guaranteed.py` never fails
2. **Monitor Dashboard**: Keep http://localhost:8080/dashboard open during downloads
3. **Check Extension Popup**: Real-time progress updates in extension popup
4. **Professional Features**: Use `youtube_downloader.py` for enterprise features
5. **Clean Downloads**: All methods now produce clean video-only downloads

## 📁 File Structure

```
YT-Downloader/
├── 📁 chrome-extension/     # Chrome Extension
│   ├── manifest.json        # Extension manifest
│   ├── popup.html          # Extension popup UI
│   ├── popup.css           # Popup styling
│   ├── popup.js            # Popup functionality
│   ├── background.js       # Service worker
│   ├── content.js          # YouTube page integration
│   ├── content.css         # Content script styling
│   └── 📁 icons/           # Extension icons
├── 📁 static/              # Web Dashboard
│   └── dashboard.html      # Download monitoring dashboard
├── 📄 extension_server.py  # API server for extension
├── 📄 simple_audio_guaranteed.py  # Reliable downloader
├── 📄 main.py             # User-friendly wrapper
├── 📄 youtube_downloader.py  # Professional system
├── 📄 requirements.txt    # Python dependencies
└── 📁 downloads/          # Downloaded videos
```

## 🎉 Success!

You now have a complete professional YouTube downloader system with:

- ✅ Chrome extension with modern UI
- ✅ Guaranteed audio quality
- ✅ Clean video-only downloads  
- ✅ Real-time progress tracking
- ✅ Professional web dashboard
- ✅ Enterprise-grade features

**Enjoy downloading your favorite YouTube content!** 🎬🎵