"""
Netlify Function: Download Playlist
Serverless YouTube playlist downloader API
"""

import json
import os
import tempfile
import subprocess
import logging
from datetime import datetime
import uuid

def handler(event, context):
    """Handle playlist download requests"""
    
    # Setup CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    # Handle preflight OPTIONS request
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    if event['httpMethod'] != 'POST':
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Parse request body
        body = json.loads(event['body']) if event['body'] else {}
        url = body.get('url')
        
        if not url:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'success': False, 'error': 'URL is required'})
            }
        
        # Validate URL
        if 'youtube.com' not in url and 'youtu.be' not in url:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'success': False, 'error': 'Invalid YouTube URL'})
            }
        
        # Generate download ID
        download_id = str(uuid.uuid4())
        
        # Get quality settings
        quality = body.get('quality', 'best')
        audio_guarantee = body.get('audioGuarantee', True)
        
        # Create format selector based on settings
        if audio_guarantee:
            format_selector = 'best[acodec!=none]/best'
        else:
            format_selector = f'best[height<={quality}]/best' if quality.isdigit() else 'best'
        
        # Create temporary directory for download
        temp_dir = tempfile.mkdtemp()
        
        # Prepare yt-dlp command
        cmd = [
            'yt-dlp',
            '--format', format_selector,
            '--output', f'{temp_dir}/%(title)s.%(ext)s',
            '--no-write-info-json',
            '--no-write-thumbnail', 
            '--no-write-description',
            '--no-write-annotations',
            '--no-write-sub',
            '--no-write-auto-sub',
            '--extract-flat', 'in_playlist',
            '--print', '%(webpage_url)s',
            url
        ]
        
        # Execute yt-dlp to get playlist info
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                video_urls = result.stdout.strip().split('\n')
                video_count = len([url for url in video_urls if url.strip()])
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'success': True,
                        'data': {
                            'downloadId': download_id,
                            'status': 'analyzed',
                            'videoCount': video_count,
                            'message': f'Playlist analyzed: {video_count} videos found. Note: Actual downloading requires local setup due to Netlify limitations.',
                            'urls': video_urls[:10]  # First 10 URLs for preview
                        }
                    })
                }
            else:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'error': f'Failed to analyze playlist: {result.stderr}'
                    })
                }
                
        except subprocess.TimeoutExpired:
            return {
                'statusCode': 408,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Request timeout - playlist analysis took too long'
                })
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': f'Analysis error: {str(e)}'
                })
            }
    
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'success': False, 'error': 'Invalid JSON body'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'success': False, 'error': f'Server error: {str(e)}'})
        }