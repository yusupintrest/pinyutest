import os
import re
import requests
import json
import uuid
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB limit

# Create downloads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class PinterestDownloader:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def expand_shortlink(self, shortlink):
        """Expand a Pinterest short link to its full URL"""
        response = requests.head(shortlink, headers=self.headers, allow_redirects=True)
        return response.url
    
    def extract_video_url(self, pinterest_url):
        """Extract the video URL from a Pinterest page"""
        try:
            # Fetch the page content
            response = requests.get(pinterest_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for JSON data within script tags
            for script in soup.find_all('script', type='application/json'):
                script_content = script.string
                if script_content and '"video":' in script_content:
                    data = json.loads(script_content)
                    
                    # Navigate through the JSON data to find video URL
                    # Different pins may have different structures, so we need to try multiple paths
                    try:
                        # Try to find video data in the resource response
                        resource_response = data.get('props', {}).get('initialReduxState', {}).get('pins', {})
                        if resource_response:
                            for pin_id, pin_data in resource_response.items():
                                if isinstance(pin_data, dict) and 'videos' in pin_data:
                                    video_list = pin_data.get('videos', {}).get('video_list', {})
                                    if video_list:
                                        # Get highest quality video
                                        formats = list(video_list.keys())
                                        formats.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0, reverse=True)
                                        for fmt in formats:
                                            video_url = video_list.get(fmt, {}).get('url')
                                            if video_url:
                                                return video_url
                    except Exception as e:
                        print(f"Error parsing primary structure: {e}")
                        
                    try:
                        # Alternative JSON structure
                        resource_response = data.get('resourceResponses', [{}])[0].get('response', {})
                        if resource_response and 'data' in resource_response:
                            video_data = resource_response.get('data', {})
                            if 'videos' in video_data:
                                video_list = video_data.get('videos', {}).get('video_list', {})
                                if video_list:
                                    # Get highest quality video
                                    formats = list(video_list.keys())
                                    formats.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0, reverse=True)
                                    for fmt in formats:
                                        video_url = video_list.get(fmt, {}).get('url')
                                        if video_url:
                                            return video_url
                    except Exception as e:
                        print(f"Error parsing secondary structure: {e}")
            
            # If we reach here, try to find meta og:video tag
            meta_tag = soup.find('meta', {'property': 'og:video'})
            if meta_tag and meta_tag.get('content'):
                return meta_tag.get('content')
            
            meta_tag = soup.find('meta', {'property': 'og:video:url'})
            if meta_tag and meta_tag.get('content'):
                return meta_tag.get('content')
            
            raise Exception("Could not find video URL in the Pinterest page")
            
        except Exception as e:
            raise Exception(f"Error extracting video URL: {str(e)}")
    
    def download_video(self, url, session_id):
        """Download a video from the given URL and return its path"""
        try:
            # If URL is a Pinterest shortlink, expand it
            if 'pin.it' in url:
                url = self.expand_shortlink(url)
            
            # Extract the video URL from the Pinterest page
            video_url = self.extract_video_url(url)
            
            # Generate unique filename using session_id
            parsed_url = urlparse(url)
            pin_id = parsed_url.path.strip('/').split('/')[0]
            filename = f"pinterest_{pin_id}_{session_id}.mp4"
            
            # Full path for saving
            filepath = os.path.join(self.output_dir, filename)
            
            # Download the video
            response = requests.get(video_url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return filename
            
        except Exception as e:
            raise Exception(f"Error downloading video: {str(e)}")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    # Get Pinterest URL from form
    pinterest_url = request.form.get('pinterest_url')
    
    if not pinterest_url:
        return render_template('index.html', error="Please enter a Pinterest URL")
    
    try:
        # Create a unique session ID for this download
        session_id = str(uuid.uuid4())[:8]
        
        # Initialize the downloader
        downloader = PinterestDownloader(app.config['UPLOAD_FOLDER'])
        
        # Download the video
        filename = downloader.download_video(pinterest_url, session_id)
        
        # Redirect to the download page
        return redirect(url_for('download_file', filename=filename))
        
    except Exception as e:
        return render_template('index.html', error=str(e), pinterest_url=pinterest_url)


@app.route('/downloads/<filename>')
def download_file(filename):
    # Validate filename to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return "Invalid filename", 400
        
    # Return the download page
    return render_template('download.html', filename=filename, download_url=url_for('serve_file', filename=filename))


@app.route('/serve/<filename>')
def serve_file(filename):
    # Validate filename to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return "Invalid filename", 400
        
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/api/download', methods=['POST'])
def api_download():
    # Get Pinterest URL from JSON
    data = request.get_json()
    pinterest_url = data.get('pinterest_url')
    
    if not pinterest_url:
        return jsonify({'error': 'Missing Pinterest URL'}), 400
    
    try:
        # Create a unique session ID for this download
        session_id = str(uuid.uuid4())[:8]
        
        # Initialize the downloader
        downloader = PinterestDownloader(app.config['UPLOAD_FOLDER'])
        
        # Download the video
        filename = downloader.download_video(pinterest_url, session_id)
        
        # Return success response with download URL
        return jsonify({
            'success': True,
            'download_url': url_for('serve_file', filename=filename, _external=True),
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 