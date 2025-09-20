"""
Netlify Function: Get Settings
Return default settings for the downloader
"""

import json

def handler(event, context):
    """Get downloader settings"""
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
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
    
    if event['httpMethod'] != 'GET':
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success': True,
            'data': {
                'quality': 'best',
                'format': 'mp4',
                'audioGuarantee': True,
                'notifications': True,
                'outputPath': 'downloads',
                'maxConcurrentDownloads': 3,
                'retryAttempts': 3,
                'downloadTimeout': 300,
                'serverType': 'netlify-serverless',
                'note': 'Serverless API provides video analysis. Use local scripts for actual downloading.'
            }
        })
    }