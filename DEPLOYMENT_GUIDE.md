# 🚀 Deploy Your YouTube Downloader Pro to the Cloud

Complete step-by-step guide to deploy your extension API to Netlify, Vercel, or other platforms.

## 🌟 Quick Start (5 Minutes)

### **Option 1: Deploy to Netlify (Recommended)**

1. **Create GitHub Repository:**
   ```powershell
   cd "C:\Users\G6 Ryzen 5 Pro\OneDrive\Desktop\YT-Downloader"
   git init
   git add .
   git commit -m "Initial commit - YouTube Downloader Pro"
   git remote add origin https://github.com/YOUR_USERNAME/youtube-downloader-pro.git
   git push -u origin main
   ```

2. **Deploy to Netlify:**
   - Go to [netlify.com](https://netlify.com) and sign up/login
   - Click "New site from Git"
   - Connect GitHub and select your repository
   - **Build settings:**
     - Build command: `# Leave empty`
     - Publish directory: `public`
     - Functions directory: `netlify/functions`
   - Click "Deploy site"

3. **Get Your API URL:**
   - After deployment: `https://your-app-name.netlify.app`
   - Your API endpoints: `https://your-app-name.netlify.app/api/health`

4. **Update Extension:**
   - Edit `chrome-extension/config.js`
   - Replace `API_BASE_URL` with your Netlify URL

### **Option 2: Deploy to Vercel**

1. **Install Vercel CLI:**
   ```powershell
   npm install -g vercel
   ```

2. **Deploy:**
   ```powershell
   cd "C:\Users\G6 Ryzen 5 Pro\OneDrive\Desktop\YT-Downloader"
   vercel --prod
   ```

3. **Follow prompts and get your URL**

### **Option 3: Deploy to Railway**

1. **Connect GitHub to Railway:**
   - Go to [railway.app](https://railway.app)
   - Connect your GitHub repository
   - Auto-deploy from the `netlify` folder

## 🔧 **Detailed Setup Guide**

### **File Structure Check**

Make sure your project has this structure:
```
YT-Downloader/
├── netlify/
│   ├── netlify.toml          # Netlify configuration
│   └── functions/            # Serverless functions
│       ├── requirements.txt  # Python dependencies
│       ├── download-playlist.py
│       ├── download-video.py
│       ├── health.py
│       └── settings.py
├── public/
│   └── index.html           # API landing page
├── chrome-extension/
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.css
│   ├── popup.js
│   ├── config.js           # ⚠️ UPDATE THIS
│   └── background.js
└── README.md
```

### **Configure Extension for Your API**

1. **Edit `chrome-extension/config.js`:**
   ```javascript
   const CONFIG = {
       // 🌐 Replace with your actual deployed URL
       API_BASE_URL: 'https://your-app-name.netlify.app/api',
       
       // Keep other settings as-is
       DEFAULT_QUALITY: 'best',
       DEFAULT_FORMAT: 'mp4',
       AUDIO_GUARANTEE: true,
       CLOUD_MODE: true,
       // ... rest of config
   };
   ```

2. **Load Extension in Chrome:**
   - Go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `chrome-extension` folder
   - Pin to toolbar

## 🎯 **Testing Your Deployment**

### **1. Test API Endpoints:**
```powershell
# Test health check
curl https://your-app-name.netlify.app/api/health

# Test video analysis (replace URL)
curl -X POST https://your-app-name.netlify.app/api/download-video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "audioGuarantee": true}'
```

### **2. Test Extension:**
1. Navigate to any YouTube video
2. Click extension icon
3. Click "Download Video" 
4. Should get analysis + copy command to clipboard

### **3. Test Commands:**
```powershell
# Use the command from extension (example)
yt-dlp -f "best[acodec!=none]/best" --no-write-info-json --no-write-thumbnail "https://youtube.com/watch?v=VIDEO_ID"
```

## 📊 **Platform Comparison**

| Platform | Free Tier | Setup Time | Best For |
|----------|-----------|------------|----------|
| **Netlify** | 100GB bandwidth | 5 min | Beginners, Git-based |
| **Vercel** | 100GB bandwidth | 3 min | CLI users, Next.js |
| **Railway** | $5/month | 2 min | Simple deployment |
| **Render** | 750 hours/month | 5 min | Docker support |

## 🔒 **Environment Variables (Optional)**

For enhanced security, set these in your platform:

```bash
# Netlify: Site settings → Environment variables
YOUTUBE_API_KEY=your_api_key_here
MAX_CONCURRENT_REQUESTS=10
RATE_LIMIT_PER_MINUTE=60
```

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **"Cannot connect to API"**
   - Check your API URL in `config.js`
   - Verify deployment is live
   - Test health endpoint in browser

2. **"CORS Error"**
   - Netlify functions handle CORS automatically
   - Check browser console for exact error

3. **"Function timeout"**
   - Large playlists may take longer
   - Functions have 10-second timeout on free tier

4. **Extension won't load**
   - Check `config.js` syntax
   - Reload extension in Chrome
   - Check Chrome DevTools console

### **Debug Commands:**
```powershell
# Test local development
cd netlify/functions
python download-video.py  # Local test

# Check deployment logs
netlify logs  # If using Netlify CLI
```

## 🎉 **Success Checklist**

- ✅ API deployed and health check returns 200
- ✅ Extension loads without errors
- ✅ Extension analyzes YouTube videos
- ✅ Commands copy to clipboard
- ✅ yt-dlp commands work locally
- ✅ Professional UI theme active

## 💡 **Pro Tips**

1. **Custom Domain:** Add your own domain in platform settings
2. **Analytics:** Add Google Analytics to `public/index.html`
3. **Monitoring:** Set up uptime monitoring with UptimeRobot
4. **Version Control:** Use Git tags for releases
5. **Documentation:** Update README with your API URL

## 🔄 **Updating Your Deployment**

```powershell
# Make changes to your code
git add .
git commit -m "Update API functions"
git push origin main

# Auto-deploys via Git integration
# Or manually deploy:
netlify deploy --prod  # Netlify CLI
vercel --prod          # Vercel CLI
```

## 🎊 **You're Done!**

Your YouTube Downloader Pro extension is now:
- 🌐 **Globally accessible** via cloud API
- 🚀 **Zero maintenance** serverless hosting
- 💰 **Free to run** on generous free tiers
- 📈 **Scalable** to handle any load
- 🔒 **Secure** with HTTPS and CORS

**Share your extension API URL with others and let them enjoy professional YouTube downloading!**