// Popup JavaScript for YouTube Downloader Pro Extension

class YouTubeDownloaderPopup {
    constructor() {
        this.currentTab = null;
        this.pageInfo = null;
        this.settings = null;
        this.downloadStatus = null;
        this.apiUrl = CONFIG.API_BASE_URL;
        this.isCloudMode = CONFIG.CLOUD_MODE;
        
        this.init();
    }

    async init() {
        try {
            // Get current tab
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            this.currentTab = tab;

            // Load settings
            await this.loadSettings();
            
            // Setup UI
            this.setupEventListeners();
            await this.updatePageInfo();
            this.populateSettings();
            
            // Start status updates
            this.startStatusUpdates();

        } catch (error) {
            console.error('Popup initialization error:', error);
            this.showError('Failed to initialize extension');
        }
    }

    setupEventListeners() {
        // Download buttons
        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.startPlaylistDownload();
        });

        document.getElementById('downloadSingleBtn').addEventListener('click', () => {
            this.startVideoDownload();
        });

        document.getElementById('openServerBtn').addEventListener('click', () => {
            this.openDownloadServer();
        });

        // Settings changes
        document.getElementById('quality').addEventListener('change', () => {
            this.saveSettings();
        });

        document.getElementById('format').addEventListener('change', () => {
            this.saveSettings();
        });

        document.getElementById('audioGuarantee').addEventListener('change', () => {
            this.saveSettings();
        });

        document.getElementById('notifications').addEventListener('change', () => {
            this.saveSettings();
        });

        // Footer buttons
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.openSettingsModal();
        });

        document.getElementById('helpBtn').addEventListener('click', () => {
            this.openHelp();
        });

        document.getElementById('aboutBtn').addEventListener('click', () => {
            this.openAbout();
        });
    }

    async loadSettings() {
        try {
            const response = await chrome.runtime.sendMessage({ action: 'getSettings' });
            if (response.success) {
                this.settings = response.data;
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    async saveSettings() {
        try {
            const newSettings = {
                quality: document.getElementById('quality').value,
                format: document.getElementById('format').value,
                audioGuarantee: document.getElementById('audioGuarantee').checked,
                notifications: document.getElementById('notifications').checked
            };

            Object.assign(this.settings, newSettings);

            await chrome.runtime.sendMessage({
                action: 'saveSettings',
                settings: this.settings
            });

        } catch (error) {
            console.error('Failed to save settings:', error);
        }
    }

    populateSettings() {
        if (!this.settings) return;

        document.getElementById('quality').value = this.settings.quality || 'best';
        document.getElementById('format').value = this.settings.format || 'mp4';
        document.getElementById('audioGuarantee').checked = this.settings.audioGuarantee !== false;
        document.getElementById('notifications').checked = this.settings.notifications !== false;
    }

    async updatePageInfo() {
        try {
            const response = await chrome.runtime.sendMessage({
                action: 'getPageInfo',
                tabId: this.currentTab.id
            });

            if (response.success) {
                this.pageInfo = response.data;
                this.updateUI();
            } else {
                throw new Error(response.error || 'Failed to get page info');
            }

        } catch (error) {
            console.error('Failed to get page info:', error);
            this.showError('Could not analyze current page');
        }
    }

    updateUI() {
        const pageInfo = this.pageInfo;
        
        // Update page status
        const pageStatus = document.getElementById('pageStatus');
        const pageUrl = document.getElementById('pageUrl');
        
        if (pageInfo.isYouTube) {
            if (pageInfo.isPlaylist) {
                pageStatus.innerHTML = '<i class="fas fa-list"></i> YouTube Playlist Detected';
                pageStatus.className = 'page-status success';
            } else if (pageInfo.isSingleVideo) {
                pageStatus.innerHTML = '<i class="fas fa-video"></i> YouTube Video Detected';
                pageStatus.className = 'page-status success';
            } else {
                pageStatus.innerHTML = '<i class="fas fa-globe"></i> YouTube Page';
                pageStatus.className = 'page-status';
            }
        } else {
            pageStatus.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Not a YouTube page';
            pageStatus.className = 'page-status warning';
        }

        pageUrl.textContent = this.truncateUrl(pageInfo.url);

        // Update playlist section
        const playlistSection = document.getElementById('playlistSection');
        const playlistInfo = document.getElementById('playlistInfo');
        const playlistTitle = document.getElementById('playlistTitle');
        const playlistMeta = document.getElementById('playlistMeta');

        if (pageInfo.isPlaylist && pageInfo.playlistTitle) {
            playlistSection.style.display = 'block';
            playlistTitle.textContent = pageInfo.playlistTitle;
            playlistMeta.textContent = pageInfo.videoCount ? 
                `${pageInfo.videoCount} videos` : 'Analyzing playlist...';
        } else if (pageInfo.isSingleVideo && pageInfo.videoTitle) {
            playlistSection.style.display = 'block';
            playlistTitle.textContent = pageInfo.videoTitle;
            playlistMeta.textContent = pageInfo.channelName ? 
                `by ${pageInfo.channelName}` : 'Single video';
        } else {
            playlistSection.style.display = 'none';
        }

        // Update buttons
        const downloadBtn = document.getElementById('downloadBtn');
        const downloadSingleBtn = document.getElementById('downloadSingleBtn');

        if (pageInfo.isPlaylist) {
            downloadBtn.disabled = false;
            downloadBtn.querySelector('span').textContent = 'Download Playlist';
            downloadSingleBtn.style.display = pageInfo.isSingleVideo ? 'block' : 'none';
            downloadSingleBtn.disabled = !pageInfo.isSingleVideo;
        } else if (pageInfo.isSingleVideo) {
            downloadBtn.disabled = false;
            downloadBtn.querySelector('span').textContent = 'Download Video';
            downloadSingleBtn.style.display = 'none';
        } else {
            downloadBtn.disabled = true;
            downloadSingleBtn.disabled = true;
        }

        // Update status message
        this.updateStatusMessage();
    }

    updateStatusMessage() {
        const statusMessage = document.getElementById('statusMessage');
        
        if (!this.pageInfo.isYouTube) {
            statusMessage.innerHTML = `
                <i class="fas fa-info-circle"></i>
                <span>Navigate to a YouTube playlist or video to start downloading.</span>
            `;
            statusMessage.className = 'status-message';
        } else if (this.pageInfo.isPlaylist) {
            statusMessage.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <span>Playlist detected! Ready to download ${this.pageInfo.videoCount || '?'} videos.</span>
            `;
            statusMessage.className = 'status-message success';
        } else if (this.pageInfo.isSingleVideo) {
            statusMessage.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <span>Video detected! Ready to download.</span>
            `;
            statusMessage.className = 'status-message success';
        } else {
            statusMessage.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <span>No downloadable content detected on this page.</span>
            `;
            statusMessage.className = 'status-message warning';
        }
    }

    async startPlaylistDownload() {
        try {
            this.setDownloadingState(true);

            const downloadData = {
                url: this.pageInfo.url,
                quality: document.getElementById('quality').value,
                format: document.getElementById('format').value,
                audioGuarantee: document.getElementById('audioGuarantee').checked,
                notifications: document.getElementById('notifications').checked
            };

            if (this.isCloudMode) {
                // Cloud mode - analyze and provide command
                const result = await this.analyzePlaylist(downloadData);
                this.showDownloadCommand(result, 'playlist');
            } else {
                // Local mode - actual download
                const response = await chrome.runtime.sendMessage({
                    action: 'downloadPlaylist',
                    data: downloadData
                });

                if (response.success) {
                    this.showSuccess('Download started successfully!');
                    this.downloadStatus = { 
                        id: response.data.downloadId, 
                        type: 'playlist',
                        status: 'started'
                    };
                } else {
                    throw new Error(response.error || 'Download failed');
                }
            }

        } catch (error) {
            console.error('Download error:', error);
            this.showError(error.message);
        } finally {
            this.setDownloadingState(false);
        }
    }

    async startVideoDownload() {
        try {
            this.setDownloadingState(true);

            const downloadData = {
                url: this.pageInfo.url,
                quality: document.getElementById('quality').value,
                format: document.getElementById('format').value,
                audioGuarantee: document.getElementById('audioGuarantee').checked,
                notifications: document.getElementById('notifications').checked
            };

            if (this.isCloudMode) {
                // Cloud mode - analyze and provide command
                const result = await this.analyzeVideo(downloadData);
                this.showDownloadCommand(result, 'video');
            } else {
                // Local mode - actual download
                const response = await chrome.runtime.sendMessage({
                    action: 'downloadVideo',
                    data: downloadData
                });

                if (response.success) {
                    this.showSuccess('Video download started!');
                    this.downloadStatus = { 
                        id: response.data.downloadId, 
                        type: 'video',
                        status: 'started'
                    };
                } else {
                    throw new Error(response.error || 'Download failed');
                }
            }

        } catch (error) {
            console.error('Download error:', error);
            this.showError(error.message);
        } finally {
            this.setDownloadingState(false);
        }
    }

    async openDownloadServer() {
        try {
            await chrome.runtime.sendMessage({ action: 'openDownloadServer' });
        } catch (error) {
            console.error('Failed to open server:', error);
            this.showError('Could not open download server');
        }
    }

    setDownloadingState(downloading) {
        const downloadBtn = document.getElementById('downloadBtn');
        const loadingSpinner = document.getElementById('loadingSpinner');

        if (downloading) {
            downloadBtn.disabled = true;
            loadingSpinner.style.display = 'block';
            downloadBtn.querySelector('span').textContent = 'Starting Download...';
        } else {
            downloadBtn.disabled = false;
            loadingSpinner.style.display = 'none';
            downloadBtn.querySelector('span').textContent = this.pageInfo.isPlaylist ? 
                'Download Playlist' : 'Download Video';
        }
    }

    startStatusUpdates() {
        // Check download status every few seconds
        setInterval(async () => {
            if (this.downloadStatus && this.downloadStatus.id) {
                try {
                    const response = await chrome.runtime.sendMessage({
                        action: 'getDownloadStatus',
                        downloadId: this.downloadStatus.id
                    });

                    if (response.success) {
                        this.updateProgress(response.data);
                    }
                } catch (error) {
                    console.error('Status update error:', error);
                }
            }
        }, 2000);
    }

    updateProgress(status) {
        const progressSection = document.getElementById('progressSection');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const progressSpeed = document.getElementById('progressSpeed');

        if (status.status === 'downloading' || status.status === 'started') {
            progressSection.style.display = 'block';
            progressSection.classList.add('fade-in');

            if (status.progress !== undefined) {
                progressFill.style.width = `${status.progress}%`;
                progressText.textContent = `${Math.round(status.progress)}% completed`;
            }

            if (status.speed) {
                progressSpeed.textContent = `Speed: ${status.speed}`;
            }
        } else if (status.status === 'completed') {
            progressFill.style.width = '100%';
            progressText.textContent = 'Download completed!';
            progressSpeed.textContent = 'Finished';
            
            setTimeout(() => {
                progressSection.style.display = 'none';
                this.downloadStatus = null;
            }, 3000);
        }
    }

    showSuccess(message) {
        this.showStatusMessage(message, 'success');
    }

    showError(message) {
        this.showStatusMessage(message, 'error');
    }

    showWarning(message) {
        this.showStatusMessage(message, 'warning');
    }

    showStatusMessage(message, type) {
        const statusMessage = document.getElementById('statusMessage');
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        statusMessage.innerHTML = `
            <i class="${icons[type] || icons.info}"></i>
            <span>${message}</span>
        `;
        statusMessage.className = `status-message ${type}`;
    }

    openSettingsModal() {
        // For now, just show a simple alert
        // In a full implementation, you'd create a modal
        alert('Advanced settings will be available in the options page. Use the gear icon to access basic settings.');
    }

    openHelp() {
        chrome.tabs.create({
            url: 'https://github.com/yourusername/youtube-downloader-pro/wiki'
        });
    }

    openAbout() {
        const aboutInfo = `
YouTube Downloader Pro v1.0.0

A professional YouTube playlist downloader with guaranteed audio quality.

Features:
• High-quality downloads up to 4K
• Guaranteed audio synchronization
• Progress tracking and notifications
• Professional interface
• Batch playlist downloading

Created with ❤️ for YouTube enthusiasts
        `.trim();
        
        alert(aboutInfo);
    }

    truncateUrl(url, maxLength = 50) {
        if (url.length <= maxLength) return url;
        return url.substring(0, maxLength - 3) + '...';
    }

    // Cloud API Functions
    async analyzePlaylist(downloadData) {
        const response = await fetch(`${this.apiUrl}/download-playlist`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(downloadData)
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || 'Analysis failed');
        }

        return result.data;
    }

    async analyzeVideo(downloadData) {
        const response = await fetch(`${this.apiUrl}/download-video`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(downloadData)
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || 'Analysis failed');
        }

        return result.data;
    }

    showDownloadCommand(result, type) {
        // Create format selector based on settings
        const audioGuarantee = document.getElementById('audioGuarantee').checked;
        const quality = document.getElementById('quality').value;
        
        let formatSelector;
        if (audioGuarantee) {
            formatSelector = 'best[acodec!=none]/best';
        } else if (quality === 'best') {
            formatSelector = 'best';
        } else {
            formatSelector = `best[height<=${quality}]/best`;
        }

        // Generate optimized command
        const command = `yt-dlp -f "${formatSelector}" --no-write-info-json --no-write-thumbnail "${this.pageInfo.url}"`;
        
        // Show command in a modal/alert for now
        const message = `
🎉 ${type === 'playlist' ? 'Playlist' : 'Video'} Analysis Complete!

${type === 'playlist' ? `📊 Found ${result.videoCount || '?'} videos` : `🎬 Title: ${result.title || 'Unknown'}`}

📋 Copy this command to download:

${command}

💡 Run this command in your terminal where you want to download the ${type === 'playlist' ? 'playlist' : 'video'}.

✅ This command includes:
• Guaranteed audio quality
• No metadata clutter 
• Optimized format selection
        `.trim();

        // Copy command to clipboard
        navigator.clipboard.writeText(command).then(() => {
            this.showSuccess('Download command copied to clipboard!');
        }).catch(() => {
            this.showSuccess('Command ready! Copy from the alert below.');
        });

        // Show the command
        alert(message);
        
        // Update UI to show analysis complete
        this.showStatusMessage(
            `${type === 'playlist' ? 'Playlist' : 'Video'} analyzed! Command copied to clipboard.`, 
            'success'
        );
    }
}

// Initialize popup when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeDownloaderPopup();
});