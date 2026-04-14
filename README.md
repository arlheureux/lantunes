# LanTunes

A self-hosted LAN music streaming server with multi-client sync and device casting.

## Features

- **Beautiful Web Interface** - Modern, responsive UI for desktop and mobile
- **Lossless Audio** - FLAC, ALAC, WAV, and other lossless formats supported
- **M4A/AAC Support** - Automatic transcoding for browser compatibility
- **Multi-Client Sync** - All connected devices stay in sync via WebSockets
- **Device Casting** - "Play To" feature to send audio to a specific device
- **Library Management** - Automatic scanning with metadata extraction
- **Playlists** - Create and manage playlists
- **Search** - Search across tracks, albums, and artists
- **Letter Filtering** - Filter Albums, Artists, and Genres by first letter
- **Play Random** - One-click to play a random album or artist
- **Stats Dashboard** - Home page shows library statistics
- **Mobile Optimized** - Touch-friendly with swipe gestures

## Requirements

- Python 3.8+
- FFmpeg (for M4A transcoding)

## Installation

### Quick Start

```bash
git clone https://github.com/arlheureux/lantunes.git
cd lantunes
python3 run.py
```

The server will:
1. Create a virtual environment with all dependencies
2. Start the server on http://0.0.0.0:8080
3. Open http://localhost:8080 in your browser

### First-Time Setup

1. Open http://localhost:8080
2. Go to Settings and set your music path
3. Click "Scan Library" to index your music

### For Other Devices on Your Network

Access from any device on your LAN:
```
http://<your-server-ip>:8080
```

## Usage

### Playing Music

- Click any track to play it
- Use shuffle buttons to play random tracks
- Use "Play Random" button on Albums or Artists page to play a random selection
- Swipe left/right on mobile player to skip tracks

### Library Navigation

- **Home** - Stats dashboard and recently added content
- **All Tracks** - Browse all tracks in your library
- **Albums** - Browse by album with letter filtering
- **Artists** - Browse by artist with letter filtering
- **Genres** - Browse by genre with letter filtering
- **Playlists** - Create and manage playlists

### Device Casting

When multiple devices are connected:
1. Select which device should play audio from the dropdown in the player bar
2. Click play on any device - audio will stream to the selected device
3. The other devices act as remote controls

## API Endpoints

### Health
- `GET /health` - Health check
- `GET /health/ready` - Readiness check

### Library
- `GET /api/library/tracks` - List tracks
- `GET /api/library/albums` - List albums
- `GET /api/library/artists` - List artists
- `GET /api/library/search?q=` - Search
- `POST /api/library/scan` - Scan library

### Playback
- `GET /api/playback/state` - Get playback state
- `POST /api/playback/play` - Play track
- `POST /api/playback/pause` - Pause
- `POST /api/playback/next` - Next track
- `POST /api/playback/previous` - Previous track
- `POST /api/playback/seek?position=` - Seek
- `GET /api/playback/stream/{id}` - Stream audio

### WebSocket
- `WS /ws` - Real-time sync for playback state and device management

## Configuration

Edit `config.yaml` to customize settings:

```yaml
library:
  music_path: "/path/to/your/music"
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development
cd backend
python main.py
```

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: Vue.js 3, Font Awesome
- **Database**: SQLite
- **Audio**: FFmpeg for transcoding

## License

Copyright (C) 2024 LanTunes

**NO COMMERCIAL USE** - This software is for personal use only.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

See the LICENSE file for full license text.

Commercial use, resale, or redistribution is strictly prohibited.