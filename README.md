# LanTunes

A self-hosted network music streaming server with multi-client sync.

## Features

- Web interface for browsing and playing music
- FLAC and other lossless format support
- Multi-client playback sync via WebSockets
- Any connected device can control playback
- Library scanning with metadata extraction
- Playlists support

## Installation

1. Install dependencies:

```bash
pip install fastapi uvicorn sqlalchemy mutagen pyyaml python-multipart
```

2. Edit `config.yaml` and set your music path:

```yaml
library:
  music_path: "/path/to/your/music"
```

3. Run the server:

```bash
cd backend
python main.py
```

4. Open http://localhost:8080 in your browser

## Usage

1. Go to Settings and set your music path
2. Click "Scan Library" to index your music
3. Browse albums, artists, or search
4. Click a track to play
5. Open the same URL on other devices (phones, tablets) - they will sync automatically
6. Any device can control playback

## API Endpoints

- `GET /api/library/tracks` - List tracks
- `GET /api/library/albums` - List albums
- `GET /api/library/artists` - List artists
- `GET /api/library/search?q=` - Search
- `POST /api/library/scan` - Scan library
- `GET /api/playback/state` - Get playback state
- `POST /api/playback/play` - Play
- `POST /api/playback/pause` - Pause
- `GET /api/playback/stream/{id}` - Stream audio
- `WS /ws` - WebSocket for real-time sync