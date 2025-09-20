# 🚀 YouTube Downloader Pro - Cloud Extension

A professional Chrome extension that uses a hosted serverless API for YouTube video analysis and provides local download instructions.

## 🌐 **Hosted vs Local Setup**

### **Option 1: Cloud-Hosted API (Recommended)**
- ✅ **No local server required**
- ✅ **Always accessible**  
- ✅ **Zero maintenance**
- ✅ **Video analysis in the cloud**
- ⚠️ **Provides download commands** (due to hosting limitations)

### **Option 2: Local API Server**
- ✅ **Full download automation**
- ✅ **Direct file downloads**
- ⚠️ **Requires running Python server**
- ⚠️ **Local setup needed**

## 🔧 **Setup Instructions**

### **For Cloud-Hosted Extension:**

1. **Deploy to Netlify:**
   - Fork this repository to GitHub
   - Connect your GitHub to Netlify
   - Deploy from the `/netlify` folder
   - Get your API URL (e.g., `https://your-app.netlify.app`)

2. **Configure Extension:**
   - Update `chrome-extension/config.js` with your API URL
   - Load extension in Chrome (Developer Mode)

3. **Use Extension:**
   - Visit YouTube videos/playlists
   - Click extension icon
   - Get video analysis and download commands
   - Run commands locally for actual downloads

### **For Local Setup:**
- Follow the original `EXTENSION_GUIDE.md` instructions
- Run `python extension_server.py` locally

## 📱 **How the Cloud Extension Works**

### **What It Does:**
1. **Analyzes** YouTube videos/playlists
2. **Extracts** metadata (title, duration, quality options)
3. **Provides** optimized yt-dlp commands 
4. **Guides** you through local download process

### **What You Get:**
- ✅ **Professional UI** with real-time analysis
- ✅ **Video metadata** and quality information  
- ✅ **Ready-to-use commands** with guaranteed audio
- ✅ **Zero server maintenance**
- ✅ **Always available** cloud API

### **Example Workflow:**
1. Open YouTube playlist
2. Click extension → "Analyze Playlist"
3. Get optimized command: `yt-dlp -f "best[acodec!=none]/best" [URL]`
4. Run command in your terminal
5. Enjoy clean, high-quality downloads!

## 🚀 **Deployment Guide**

### **Deploy to Netlify:**

1. **Create Netlify Account** at netlify.com

2. **Deploy via Git:**
   ```bash
   # Push to GitHub first
   git add .
   git commit -m "Add serverless functions"
   git push origin main
   ```

3. **Connect Repository:**
   - Go to Netlify Dashboard
   - Click "New site from Git"
   - Connect your GitHub repository
   - Set build settings:
     - **Build command:** `# No build needed`
     - **Publish directory:** `public`
     - **Functions directory:** `netlify/functions`

4. **Configure Environment:**
   - Netlify will auto-detect Python functions
   - No additional environment variables needed

5. **Get Your API URL:**
   - After deployment: `https://your-app-name.netlify.app`
   - Test health: `https://your-app-name.netlify.app/api/health`

### **Alternative: Deploy to Vercel**

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Deploy:**
   ```bash
   cd YT-Downloader
   vercel --prod
   ```

3. **Configure:**
   - Vercel will auto-detect the setup
   - Functions will be available at `/api/*`

## ⚙️ **Extension Configuration**

Create `chrome-extension/config.js`:

```javascript
// Extension Configuration
const CONFIG = {
    // For hosted API (recommended)
    API_BASE_URL: 'https://your-app.netlify.app/api',
    
    // For local development
    // API_BASE_URL: 'http://localhost:8080/api',
    
    // Extension settings
    DEFAULT_QUALITY: 'best',
    DEFAULT_FORMAT: 'mp4', 
    AUDIO_GUARANTEE: true,
    TIMEOUT: 30000
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
```

## 🔥 **Benefits of Cloud Setup**

### **For Users:**
- ✅ **No Python installation** required for analysis
- ✅ **Works from any computer** with Chrome
- ✅ **Always up-to-date** API
- ✅ **Fast analysis** via cloud processing
- ✅ **Professional experience** with hosted reliability

### **For Developers:**
- ✅ **Serverless scaling** handles any load
- ✅ **Zero server maintenance** 
- ✅ **Global CDN** for fast responses
- ✅ **Free hosting** on Netlify/Vercel free tiers
- ✅ **Easy updates** via Git deployments

## 📋 **API Endpoints Available**

- `GET /api/health` - Service health check
- `POST /api/download-playlist` - Analyze YouTube playlist  
- `POST /api/download-video` - Analyze single video
- `GET /api/settings` - Get default settings

## 🎯 **Perfect Workflow**

1. **One-time setup:** Deploy API to Netlify (5 minutes)
2. **Daily use:** 
   - Browse YouTube normally
   - Click extension for instant analysis
   - Copy provided command
   - Paste in terminal → Download!
3. **Result:** Professional downloads with guaranteed audio

## 💡 **Why This Approach?**

**Cloud analysis + Local downloads** gives you the best of both worlds:
- 🌐 **Cloud reliability** for analysis
- 💻 **Local control** for downloads  
- 🚀 **Zero maintenance** hosting
- ⚡ **Instant access** from anywhere
- 🔒 **Privacy-friendly** (no files stored in cloud)

Your extension users get a professional experience while you avoid the complexity of file hosting and download management!