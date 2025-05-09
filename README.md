# Pinterest Video Downloader Web App

A web application that allows users to download videos from Pinterest links.

## Features

- Simple, user-friendly web interface
- Works with both Pinterest URLs and pin.it short links
- Downloads videos in highest available quality
- Supports both web UI and API usage
- Responsive design that works on mobile devices

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository
2. Navigate to the repository directory
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Web App

Start the web server:

```bash
python app.py
```

This will start the Flask web server at `http://localhost:5000`

For production deployment, use a WSGI server like Gunicorn:

```bash
gunicorn -w 4 app:app
```

### Using the Web Interface

1. Open your web browser and navigate to `http://localhost:5000`
2. Enter a Pinterest video URL in the input field
3. Click the "Download" button
4. The video will be downloaded to your device automatically

### API Usage

You can also use the API endpoint to integrate with other applications:

```
POST /api/download
Content-Type: application/json

{
    "pinterest_url": "https://pin.it/4iwAEab1N"
}
```

Response:

```json
{
    "success": true,
    "download_url": "http://localhost:5000/serve/pinterest_123456_abcdef.mp4",
    "filename": "pinterest_123456_abcdef.mp4"
}
```

## How It Works

1. The web app receives a Pinterest URL
2. It expands any short links to their full form
3. It scrapes the Pinterest page to extract the video URL
4. It downloads the video to the server
5. It serves the downloaded file to the user

## License

This project is open-source software. 