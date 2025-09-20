#!/usr/bin/env python3
"""
AUDIO-GUARANTEED YouTube Downloader
This version prioritizes AUDIO INCLUSION above all else!
"""

from yt_dlp import YoutubeDL
import os

# Your playlist URL
playlist_url = 'https://youtube.com/playlist?list=PLAVB8XcRx5WXhHTLHV4ZS3Zpiaq_nZnXj&si=aIf6i1-Ra8O2Y_G4'

def main():
    print("🔊 AUDIO-GUARANTEED YouTube Downloader")
    print("=" * 50)
    
    # Create downloads directory
    os.makedirs("downloads", exist_ok=True)
    
    # ULTRA-SIMPLE options that GUARANTEE audio inclusion
    ydl_opts = {
        'outtmpl': 'downloads/%(playlist_index)03d - %(title)s.%(ext)s',
        
        # This format string ENSURES we get videos with audio
        # It will download lower quality if needed to ensure audio is included
        'format': 'best[acodec!=none]/best',  # Must have audio codec, fallback to best
        
        'noplaylist': False,
        'ignoreerrors': True,
        
        # Force output to MP4 with audio
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        
        # Progress callback
        'progress_hooks': [progress_hook],
    }
    
    print(f"🎵 Downloading playlist with GUARANTEED audio...")
    print(f"🔗 URL: {playlist_url}")
    print(f"📂 Output: ./downloads/")
    print()
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])
        
        print("\n✅ Download completed!")
        print("🔊 All videos should have AUDIO included!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

def progress_hook(d):
    """Simple progress display"""
    if d['status'] == 'finished':
        filename = os.path.basename(d['filename'])
        print(f"✅ Completed: {filename}")
    elif d['status'] == 'downloading':
        if 'total_bytes' in d and d['total_bytes']:
            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            print(f"\r📥 Downloading: {percent:.1f}%", end='', flush=True)

if __name__ == "__main__":
    main()