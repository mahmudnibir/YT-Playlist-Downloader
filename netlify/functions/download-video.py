"""
Netlify Function: Download Video
Serverless YouTube video downloader API
"""

import json
import os
import tempfile
import subprocess
import logging
from datetime import datetime
import uuid

def handler(event, context):
    """Handle single video download requests"""
    
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
        
        # Prepare yt-dlp command for video info extraction
        cmd = [
            'yt-dlp',
            '--print', '%(title)s',
            '--print', '%(uploader)s', 
            '--print', '%(duration)s',
            '--print', '%(view_count)s',
            '--no-download',
            url
        ]
        
        # Execute yt-dlp to get video info
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                title = lines[0] if len(lines) > 0 else 'Unknown Title'
                uploader = lines[1] if len(lines) > 1 else 'Unknown Channel'
                duration = lines[2] if len(lines) > 2 else '0'
                views = lines[3] if len(lines) > 3 else '0'
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'success': True,
                        'data': {
                            'downloadId': download_id,
                            'status': 'analyzed',
                            'title': title,
                            'uploader': uploader,
                            'duration': duration,
                            'views': views,
                            'message': 'Video analyzed successfully. Note: Actual downloading requires local setup due to Netlify limitations.',
                            'downloadUrl': f'yt-dlp -f "{format_selector}" "{url}"'
                        }
                    })
                }
            else:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'error': f'Failed to analyze video: {result.stderr}'
                    })
                }
                
        except subprocess.TimeoutExpired:
            return {
                'statusCode': 408,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Request timeout - video analysis took too long'
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