#!/usr/bin/env python3
"""
Professional YouTube Downloader - Simple wrapper for the original playlist

This is a simple wrapper that maintains compatibility with your original script
while using the new professional downloader infrastructure.

For full features, use: python youtube_downloader.py [options] URL
"""

from youtube_downloader import YouTubeDownloader
from config import DownloadConfig

# Your original playlist URL
playlist_url = 'https://youtube.com/playlist?list=PLAVB8XcRx5WXhHTLHV4ZS3Zpiaq_nZnXj&si=aIf6i1-Ra8O2Y_G4'

def main():
    """Main function - maintains compatibility with original script."""
    print("🚀 Professional YouTube Downloader")
    print("=" * 50)
    
    # Create configuration (you can customize this)
    config = DownloadConfig(
        output_dir="./downloads",
        max_quality="1080",  # Use 1080p for better audio reliability
        video_format="mp4",
        concurrent_downloads=2,  # Reduced for stability
        retry_attempts=3,
        embed_thumbnail=True,
        write_metadata=True,
        use_database=True,
        log_level="INFO"
    )
    
    print(f"📂 Output directory: {config.output_dir}")
    print(f"🎥 Max quality: {config.max_quality}p")
    print(f"⚡ Concurrent downloads: {config.concurrent_downloads}")
    print(f"🔄 Retry attempts: {config.retry_attempts}")
    print()
    
    try:
        # Create downloader instance
        downloader = YouTubeDownloader(config)
        
        print(f"🎵 Starting download of playlist...")
        print(f"🔗 URL: {playlist_url}")
        print()
        
        # Start download
        success = downloader.download_playlist(playlist_url)
        
        if success:
            print("\n✅ All downloads completed successfully!")
        else:
            print("\n⚠️ Some downloads failed. Check logs for details.")
            
        print("\n📊 Check the downloads folder for:")
        print("  • Downloaded videos")
        print("  • HTML status report")
        print("  • JSON status report")
        print("  • Log files")
        
    except KeyboardInterrupt:
        print("\n🛑 Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 For advanced options, use: python youtube_downloader.py --help")

if __name__ == "__main__":
    main()
