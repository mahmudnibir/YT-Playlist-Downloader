// Background Service Worker for YouTube Downloader Pro
// Handles API communication and download coordination

class YouTubeDownloaderBackground {
    constructor() {
        this.downloadServer = 'http://localhost:8080'; // Python server
        this.activeDownloads = new Map();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Extension installation
        chrome.runtime.onInstalled.addListener((details) => {
            if (details.reason === 'install') {
                this.showWelcomeNotification();
                this.setupDefaultSettings();
            }
        });

        // Message handling from popup and content scripts
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Keep channel open for async response
        });

        // Tab updates to detect YouTube pages
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.status === 'complete' && this.isYouTubeUrl(tab.url)) {
                this.analyzeYouTubePage(tab);
            }
        });

        // Download progress monitoring
        chrome.downloads.onChanged.addListener((downloadDelta) => {
            this.handleDownloadProgress(downloadDelta);
        });
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.action) {
                case 'getPageInfo':
                    const pageInfo = await this.getPageInfo(request.tabId);
                    sendResponse({ success: true, data: pageInfo });
                    break;

                case 'downloadPlaylist':
                    const downloadResult = await this.startPlaylistDownload(request.data);
                    sendResponse({ success: true, data: downloadResult });
                    break;

                case 'downloadVideo':
                    const videoResult = await this.startVideoDownload(request.data);
                    sendResponse({ success: true, data: videoResult });
                    break;

                case 'getDownloadStatus':
                    const status = this.getDownloadStatus(request.downloadId);
                    sendResponse({ success: true, data: status });
                    break;

                case 'cancelDownload':
                    const cancelResult = await this.cancelDownload(request.downloadId);
                    sendResponse({ success: true, data: cancelResult });
                    break;

                case 'openDownloadServer':
                    await this.openDownloadServer();
                    sendResponse({ success: true });
                    break;

                case 'getSettings':
                    const settings = await this.getSettings();
                    sendResponse({ success: true, data: settings });
                    break;

                case 'saveSettings':
                    await this.saveSettings(request.settings);
                    sendResponse({ success: true });
                    break;

                default:
                    sendResponse({ success: false, error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Background script error:', error);
            sendResponse({ success: false, error: error.message });
        }
    }

    isYouTubeUrl(url) {
        if (!url) return false;
        const youtubePatterns = [
            /^https?:\/\/(www\.)?youtube\.com/,
            /^https?:\/\/youtu\.be/,
            /^https?:\/\/music\.youtube\.com/
        ];
        return youtubePatterns.some(pattern => pattern.test(url));
    }

    async getPageInfo(tabId) {
        try {
            const tab = await chrome.tabs.get(tabId);
            const url = tab.url;
            
            const pageInfo = {
                url: url,
                title: tab.title,
                isYouTube: this.isYouTubeUrl(url),
                isPlaylist: url.includes('list='),
                isSingleVideo: url.includes('watch?v=') && !url.includes('list='),
                playlistId: this.extractPlaylistId(url),
                videoId: this.extractVideoId(url)
            };

            // Get additional info from content script
            try {
                const contentInfo = await chrome.tabs.sendMessage(tabId, { action: 'getPageDetails' });
                if (contentInfo && contentInfo.success) {
                    Object.assign(pageInfo, contentInfo.data);
                }
            } catch (e) {
                // Content script might not be loaded yet
                console.log('Content script not available:', e);
            }

            return pageInfo;
        } catch (error) {
            throw new Error(`Failed to get page info: ${error.message}`);
        }
    }

    extractPlaylistId(url) {
        const match = url.match(/[?&]list=([^&]+)/);
        return match ? match[1] : null;
    }

    extractVideoId(url) {
        const patterns = [
            /[?&]v=([^&]+)/,
            /youtu\.be\/([^?&]+)/
        ];
        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match) return match[1];
        }
        return null;
    }

    async startPlaylistDownload(data) {
        const downloadId = this.generateDownloadId();
        
        try {
            // Check if server is running
            const serverStatus = await this.checkServerStatus();
            if (!serverStatus.running) {
                throw new Error('Download server is not running. Please start the Python server.');
            }

            // Send download request to Python server
            const response = await fetch(`${this.downloadServer}/api/download/playlist`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: data.url,
                    quality: data.quality || 'best',
                    format: data.format || 'mp4',
                    audioGuarantee: data.audioGuarantee !== false,
                    downloadId: downloadId
                })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();
            
            // Track download
            this.activeDownloads.set(downloadId, {
                id: downloadId,
                type: 'playlist',
                url: data.url,
                status: 'started',
                startTime: Date.now(),
                progress: 0
            });

            // Show notification
            if (data.notifications !== false) {
                this.showNotification('Download Started', 'Playlist download has begun!', 'info');
            }

            return {
                downloadId: downloadId,
                message: 'Playlist download started successfully',
                serverResponse: result
            };

        } catch (error) {
            this.showNotification('Download Failed', error.message, 'error');
            throw error;
        }
    }

    async startVideoDownload(data) {
        const downloadId = this.generateDownloadId();
        
        try {
            const serverStatus = await this.checkServerStatus();
            if (!serverStatus.running) {
                throw new Error('Download server is not running. Please start the Python server.');
            }

            const response = await fetch(`${this.downloadServer}/api/download/video`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: data.url,
                    quality: data.quality || 'best',
                    format: data.format || 'mp4',
                    audioGuarantee: data.audioGuarantee !== false,
                    downloadId: downloadId
                })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();
            
            this.activeDownloads.set(downloadId, {
                id: downloadId,
                type: 'video',
                url: data.url,
                status: 'started',
                startTime: Date.now(),
                progress: 0
            });

            if (data.notifications !== false) {
                this.showNotification('Download Started', 'Video download has begun!', 'info');
            }

            return {
                downloadId: downloadId,
                message: 'Video download started successfully',
                serverResponse: result
            };

        } catch (error) {
            this.showNotification('Download Failed', error.message, 'error');
            throw error;
        }
    }

    async checkServerStatus() {
        try {
            const response = await fetch(`${this.downloadServer}/api/status`, {
                method: 'GET',
                timeout: 3000
            });
            
            if (response.ok) {
                const data = await response.json();
                return { running: true, ...data };
            }
            return { running: false };
        } catch (error) {
            return { running: false, error: error.message };
        }
    }

    getDownloadStatus(downloadId) {
        return this.activeDownloads.get(downloadId) || { status: 'not_found' };
    }

    async cancelDownload(downloadId) {
        try {
            const response = await fetch(`${this.downloadServer}/api/download/cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ downloadId })
            });

            if (response.ok) {
                this.activeDownloads.delete(downloadId);
                this.showNotification('Download Cancelled', 'Download has been cancelled', 'warning');
                return { cancelled: true };
            }
            
            throw new Error('Failed to cancel download');
        } catch (error) {
            throw new Error(`Cancel failed: ${error.message}`);
        }
    }

    async openDownloadServer() {
        try {
            // Try to open the server management page
            await chrome.tabs.create({
                url: `${this.downloadServer}/dashboard`,
                active: true
            });
        } catch (error) {
            // Fallback: open local file manager to downloads folder
            console.log('Server dashboard not available, opening downloads folder');
        }
    }

    async getSettings() {
        const defaults = {
            quality: 'best',
            format: 'mp4',
            audioGuarantee: true,
            notifications: true,
            serverUrl: 'http://localhost:8080',
            outputPath: './downloads'
        };

        try {
            const result = await chrome.storage.sync.get(defaults);
            return result;
        } catch (error) {
            return defaults;
        }
    }

    async saveSettings(settings) {
        try {
            await chrome.storage.sync.set(settings);
            this.downloadServer = settings.serverUrl || 'http://localhost:8080';
        } catch (error) {
            throw new Error(`Failed to save settings: ${error.message}`);
        }
    }

    generateDownloadId() {
        return `dl_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    showNotification(title, message, type = 'info') {
        const iconMap = {
            'info': 'icons/icon48.png',
            'success': 'icons/icon48.png',
            'warning': 'icons/icon48.png',
            'error': 'icons/icon48.png'
        };

        chrome.notifications.create({
            type: 'basic',
            iconUrl: iconMap[type] || iconMap['info'],
            title: title,
            message: message
        });
    }

    showWelcomeNotification() {
        this.showNotification(
            'YouTube Downloader Pro Installed!', 
            'Navigate to any YouTube playlist and click the extension icon to start downloading.',
            'success'
        );
    }

    async setupDefaultSettings() {
        const defaults = {
            quality: 'best',
            format: 'mp4',
            audioGuarantee: true,
            notifications: true,
            serverUrl: 'http://localhost:8080',
            outputPath: './downloads'
        };
        
        await chrome.storage.sync.set(defaults);
    }

    handleDownloadProgress(downloadDelta) {
        // Handle Chrome's built-in download progress
        if (downloadDelta.state && downloadDelta.state.current === 'complete') {
            // Find matching download
            for (const [id, download] of this.activeDownloads.entries()) {
                if (download.chromeDownloadId === downloadDelta.id) {
                    download.status = 'completed';
                    this.showNotification('Download Complete', 'Your video has been downloaded!', 'success');
                    break;
                }
            }
        }
    }

    analyzeYouTubePage(tab) {
        // Inject content script if needed
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
        }).catch(() => {
            // Script might already be injected
        });
    }
}

// Initialize the background service
const youtubeDownloader = new YouTubeDownloaderBackground();

console.log('YouTube Downloader Pro background service initialized');