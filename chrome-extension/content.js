// Content Script for YouTube Pages
// Integrates with YouTube's interface and extracts playlist/video information

class YouTubeContentScript {
    constructor() {
        this.pageData = {};
        this.downloadButton = null;
        this.setupMessageListener();
        this.init();
    }

    init() {
        // Wait for page to load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.analyzePage());
        } else {
            this.analyzePage();
        }

        // Watch for navigation changes (YouTube is a SPA)
        this.observeNavigation();
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'getPageDetails') {
                this.analyzePage();
                sendResponse({ success: true, data: this.pageData });
            }
            return true;
        });
    }

    analyzePage() {
        const url = window.location.href;
        this.pageData = {
            url: url,
            title: document.title,
            isPlaylist: url.includes('list='),
            isSingleVideo: url.includes('watch?v=') && !url.includes('list='),
            timestamp: Date.now()
        };

        if (this.pageData.isPlaylist) {
            this.analyzePlaylist();
        } else if (this.pageData.isSingleVideo) {
            this.analyzeSingleVideo();
        }

        this.addDownloadButton();
    }

    analyzePlaylist() {
        try {
            // Extract playlist information
            const playlistId = this.extractPlaylistId(window.location.href);
            
            // Try multiple selectors for playlist title
            const titleSelectors = [
                '[data-ytd-renderer="ytd-playlist-header-renderer"] #title',
                '.ytd-playlist-header-renderer #title',
                '.playlist-header-title',
                'h1.ytd-playlist-header-renderer'
            ];

            let playlistTitle = '';
            for (const selector of titleSelectors) {
                const titleElement = document.querySelector(selector);
                if (titleElement && titleElement.textContent.trim()) {
                    playlistTitle = titleElement.textContent.trim();
                    break;
                }
            }

            // Count videos in playlist
            const videoCountSelectors = [
                '[data-ytd-renderer="ytd-playlist-sidebar-primary-info-renderer"] .index-message',
                '.playlist-stats .index-message',
                '.ytd-playlist-sidebar-primary-info-renderer .stats'
            ];

            let videoCount = 0;
            for (const selector of videoCountSelectors) {
                const countElement = document.querySelector(selector);
                if (countElement) {
                    const countText = countElement.textContent;
                    const match = countText.match(/(\d+)/);
                    if (match) {
                        videoCount = parseInt(match[1]);
                        break;
                    }
                }
            }

            // Alternative: count video elements
            if (videoCount === 0) {
                const videoElements = document.querySelectorAll('[data-ytd-renderer="ytd-playlist-video-renderer"]');
                videoCount = videoElements.length;
            }

            // Extract video information
            const videos = this.extractPlaylistVideos();

            Object.assign(this.pageData, {
                playlistId: playlistId,
                playlistTitle: playlistTitle || 'Unknown Playlist',
                videoCount: videoCount,
                videos: videos,
                description: this.extractPlaylistDescription()
            });

        } catch (error) {
            console.error('Error analyzing playlist:', error);
            this.pageData.error = error.message;
        }
    }

    analyzeSingleVideo() {
        try {
            const videoId = this.extractVideoId(window.location.href);
            
            // Extract video title
            const titleSelectors = [
                'h1.ytd-video-primary-info-renderer',
                'h1.title',
                '.watch-main-col h1'
            ];

            let videoTitle = '';
            for (const selector of titleSelectors) {
                const titleElement = document.querySelector(selector);
                if (titleElement && titleElement.textContent.trim()) {
                    videoTitle = titleElement.textContent.trim();
                    break;
                }
            }

            // Extract channel information
            const channelSelectors = [
                '.ytd-channel-name a',
                '.channel-name a',
                '#owner-name a'
            ];

            let channelName = '';
            for (const selector of channelSelectors) {
                const channelElement = document.querySelector(selector);
                if (channelElement && channelElement.textContent.trim()) {
                    channelName = channelElement.textContent.trim();
                    break;
                }
            }

            // Extract duration
            let duration = '';
            const durationElement = document.querySelector('.ytp-time-duration');
            if (durationElement) {
                duration = durationElement.textContent;
            }

            Object.assign(this.pageData, {
                videoId: videoId,
                videoTitle: videoTitle || 'Unknown Video',
                channelName: channelName,
                duration: duration
            });

        } catch (error) {
            console.error('Error analyzing video:', error);
            this.pageData.error = error.message;
        }
    }

    extractPlaylistVideos() {
        const videos = [];
        try {
            const videoElements = document.querySelectorAll('[data-ytd-renderer="ytd-playlist-video-renderer"]');
            
            videoElements.forEach((element, index) => {
                try {
                    const linkElement = element.querySelector('a[href*="watch?v="]');
                    const titleElement = element.querySelector('#video-title');
                    const durationElement = element.querySelector('.ytd-thumbnail-overlay-time-status-renderer');
                    
                    if (linkElement && titleElement) {
                        const href = linkElement.getAttribute('href');
                        const videoId = this.extractVideoId(`https://youtube.com${href}`);
                        
                        videos.push({
                            index: index + 1,
                            videoId: videoId,
                            title: titleElement.textContent.trim(),
                            url: `https://youtube.com${href}`,
                            duration: durationElement ? durationElement.textContent.trim() : ''
                        });
                    }
                } catch (e) {
                    console.warn(`Error extracting video ${index}:`, e);
                }
            });
        } catch (error) {
            console.error('Error extracting playlist videos:', error);
        }
        
        return videos;
    }

    extractPlaylistDescription() {
        const descriptionSelectors = [
            '.ytd-playlist-header-renderer #description',
            '.playlist-description',
            '.ytd-expandable-metadata-renderer #content'
        ];

        for (const selector of descriptionSelectors) {
            const descElement = document.querySelector(selector);
            if (descElement && descElement.textContent.trim()) {
                return descElement.textContent.trim();
            }
        }
        
        return '';
    }

    addDownloadButton() {
        // Remove existing button
        if (this.downloadButton) {
            this.downloadButton.remove();
        }

        // Create download button based on page type
        if (this.pageData.isPlaylist) {
            this.addPlaylistDownloadButton();
        } else if (this.pageData.isSingleVideo) {
            this.addVideoDownloadButton();
        }
    }

    addPlaylistDownloadButton() {
        try {
            // Find a suitable location for the button
            const targetSelectors = [
                '.ytd-playlist-header-renderer .metadata-action-bar',
                '.playlist-header-content .metadata-buttons',
                '.ytd-playlist-header-renderer'
            ];

            let targetElement = null;
            for (const selector of targetSelectors) {
                targetElement = document.querySelector(selector);
                if (targetElement) break;
            }

            if (!targetElement) return;

            // Create button
            this.downloadButton = this.createDownloadButton('playlist');
            
            // Insert button
            targetElement.appendChild(this.downloadButton);

        } catch (error) {
            console.error('Error adding playlist download button:', error);
        }
    }

    addVideoDownloadButton() {
        try {
            // Find video action buttons
            const targetSelectors = [
                '.ytd-menu-renderer .top-level-buttons',
                '#actions .ytd-video-primary-info-actions',
                '.watch-action-buttons'
            ];

            let targetElement = null;
            for (const selector of targetSelectors) {
                targetElement = document.querySelector(selector);
                if (targetElement) break;
            }

            if (!targetElement) return;

            // Create button
            this.downloadButton = this.createDownloadButton('video');
            
            // Insert button
            targetElement.appendChild(this.downloadButton);

        } catch (error) {
            console.error('Error adding video download button:', error);
        }
    }

    createDownloadButton(type) {
        const button = document.createElement('button');
        button.className = 'yt-downloader-pro-btn';
        button.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C13.1 2 14 2.9 14 4V12L15.5 10.5L16.92 11.92L12 16.84L7.08 11.92L8.5 10.5L10 12V4C10 2.9 10.9 2 12 2ZM21 15L18 12H20C20.55 12 21 12.45 21 13V19C21 19.55 20.55 20 20 20H4C3.45 20 3 19.55 3 19V13C3 12.45 3.45 12 4 12H6L3 15H5V18H19V15H21Z"/>
            </svg>
            <span>${type === 'playlist' ? 'Download Playlist' : 'Download Video'}</span>
        `;

        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.triggerDownload(type);
        });

        return button;
    }

    triggerDownload(type) {
        // Send message to background script to trigger download
        const downloadData = {
            type: type,
            url: window.location.href,
            pageData: this.pageData
        };

        chrome.runtime.sendMessage({
            action: type === 'playlist' ? 'downloadPlaylist' : 'downloadVideo',
            data: downloadData
        }, (response) => {
            if (response && response.success) {
                this.showDownloadStartedMessage(type);
            } else {
                this.showErrorMessage(response ? response.error : 'Unknown error');
            }
        });
    }

    showDownloadStartedMessage(type) {
        const message = document.createElement('div');
        message.className = 'yt-downloader-pro-message success';
        message.innerHTML = `
            <div class="message-content">
                <span class="message-icon">✓</span>
                <span class="message-text">${type === 'playlist' ? 'Playlist' : 'Video'} download started!</span>
            </div>
        `;

        document.body.appendChild(message);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
            }
        }, 3000);
    }

    showErrorMessage(error) {
        const message = document.createElement('div');
        message.className = 'yt-downloader-pro-message error';
        message.innerHTML = `
            <div class="message-content">
                <span class="message-icon">✗</span>
                <span class="message-text">Download failed: ${error}</span>
            </div>
        `;

        document.body.appendChild(message);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
            }
        }, 5000);
    }

    observeNavigation() {
        // YouTube uses history API for navigation
        let lastUrl = location.href;

        const observer = new MutationObserver(() => {
            const currentUrl = location.href;
            if (currentUrl !== lastUrl) {
                lastUrl = currentUrl;
                // Wait a bit for page to update
                setTimeout(() => this.analyzePage(), 1000);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
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
}

// Initialize content script
const youtubeContentScript = new YouTubeContentScript();

console.log('YouTube Downloader Pro content script loaded');