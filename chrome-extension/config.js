// Extension Configuration for Cloud/Local API
const CONFIG = {
    // 🌐 For hosted API on Netlify/Vercel (recommended)
    // Replace with your actual deployed URL
    API_BASE_URL: 'https://your-app.netlify.app/api',
    
    // 💻 For local development (uncomment to use local server)
    // API_BASE_URL: 'http://localhost:8080/api',
    
    // Extension settings
    DEFAULT_QUALITY: 'best',
    DEFAULT_FORMAT: 'mp4',
    AUDIO_GUARANTEE: true,
    NOTIFICATIONS: true,
    TIMEOUT: 30000, // 30 seconds
    
    // UI settings
    ANIMATION_DURATION: 300,
    AUTO_REFRESH_INTERVAL: 5000,
    
    // Download settings
    MAX_RETRIES: 3,
    RETRY_DELAY: 2000,
    
    // Cloud mode settings
    CLOUD_MODE: true, // Set to false for full local downloads
    PROVIDE_COMMANDS: true, // Show yt-dlp commands for cloud mode
    
    // Error messages
    ERRORS: {
        NO_CONNECTION: 'Cannot connect to API server',
        INVALID_URL: 'Please provide a valid YouTube URL',
        TIMEOUT: 'Request timed out - please try again',
        SERVER_ERROR: 'Server error occurred',
        NOT_YOUTUBE: 'This extension only works on YouTube pages'
    },
    
    // Success messages
    MESSAGES: {
        ANALYSIS_COMPLETE: 'Video analysis completed successfully',
        PLAYLIST_FOUND: 'Playlist detected and analyzed',
        COMMAND_COPIED: 'Download command copied to clipboard'
    }
};

// Auto-detect environment and adjust config
if (typeof window !== 'undefined') {
    // Running in browser - check if we're on localhost
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        CONFIG.API_BASE_URL = 'http://localhost:8080/api';
        CONFIG.CLOUD_MODE = false;
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}